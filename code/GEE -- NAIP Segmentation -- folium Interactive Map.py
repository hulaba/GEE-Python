#!/usr/bin/env python
# coding: utf-8

# ## Load packages and initiate earth engine

# In[1]:


import ee
ee.Initialize()

import folium
from folium import plugins
import palette
import geemap.eefolium as emap
import subprocess
#import geemap as emap
from IPython.display import Image


# ## Define aoi of NAIP images

# In[2]:


collection = ee.ImageCollection('USDA/NAIP/DOQQ')
aoi = ee.Geometry.Polygon([
    [-74.02,40.90],
          [-74.02,40.85],
          [-73.90,40.85],
          [-73.90,40.90]
])
centroid = aoi.centroid()
long, lat = centroid.getInfo()['coordinates']
print("long = {}, lat = {}".format(long,lat))


# ## Filter NAIP image collection by time and aoi

# In[3]:


long_lat = ee.Geometry.Point(long, lat)
naip = collection.filterBounds(aoi)
naip17 = collection.filterDate('2017-05-01','2017-8-05')
count = naip17.size().getInfo()
print('Count:', count)


# ## Interactive Display of Images 

# #### Set parameters/functions for interactive map  
# (code source: https://nbviewer.jupyter.org/github/giswqs/qgis-earthengine-examples/blob/master/Folium/ee-api-folium-setup.ipynb)

# In[5]:


## basemap
basemaps = {
    'Google Maps': folium.TileLayer(
        tiles = 'https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}',
        attr = 'Google',
        name = 'Google Maps',
        overlay = True,
        control = True
    ),
    'Google Satellite': folium.TileLayer(
        tiles = 'https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
        attr = 'Google',
        name = 'Google Satellite',
        overlay = True,
        control = True
    ),
    'Google Terrain': folium.TileLayer(
        tiles = 'https://mt1.google.com/vt/lyrs=p&x={x}&y={y}&z={z}',
        attr = 'Google',
        name = 'Google Terrain',
        overlay = True,
        control = True
    ),
    'Google Satellite Hybrid': folium.TileLayer(
        tiles = 'https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
        attr = 'Google',
        name = 'Google Satellite',
        overlay = True,
        control = True
    ),
    'Esri Satellite': folium.TileLayer(
        tiles = 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr = 'Esri',
        name = 'Esri Satellite',
        overlay = True,
        control = True
    )
}

# Define a method for displaying Earth Engine image tiles on a folium map.
def add_ee_layer(self, ee_object, vis_params, name):
    
    try:    
        # display ee.Image()
        if isinstance(ee_object, ee.image.Image):    
            map_id_dict = ee.Image(ee_object).getMapId(vis_params)
            folium.raster_layers.TileLayer(
            tiles = map_id_dict['tile_fetcher'].url_format,
            attr = 'Google Earth Engine',
            name = name,
            overlay = True,
            control = True
            ).add_to(self)
        # display ee.ImageCollection()
        elif isinstance(ee_object, ee.imagecollection.ImageCollection):    
            ee_object_new = ee_object.mosaic()
            map_id_dict = ee.Image(ee_object_new).getMapId(vis_params)
            folium.raster_layers.TileLayer(
            tiles = map_id_dict['tile_fetcher'].url_format,
            attr = 'Google Earth Engine',
            name = name,
            overlay = True,
            control = True
            ).add_to(self)
        # display ee.Geometry()
        elif isinstance(ee_object, ee.geometry.Geometry):    
            folium.GeoJson(
            data = ee_object.getInfo(),
            name = name,
            overlay = True,
            control = True
        ).add_to(self)
        # display ee.FeatureCollection()
        elif isinstance(ee_object, ee.featurecollection.FeatureCollection):  
            ee_object_new = ee.Image().paint(ee_object, 0, 2)
            map_id_dict = ee.Image(ee_object_new).getMapId(vis_params)
            folium.raster_layers.TileLayer(
            tiles = map_id_dict['tile_fetcher'].url_format,
            attr = 'Google Earth Engine',
            name = name,
            overlay = True,
            control = True
        ).add_to(self)
    
    except:
        print("Could not display {}".format(name))
    
# Add EE drawing method to folium.
folium.Map.add_ee_layer = add_ee_layer


# #### Display image (natural color)

# In[6]:


map = folium.Map(location = [lat,long], zoom_start=15, height=500)
basemaps['Google Satellite Hybrid'].add_to(map)
map.add_ee_layer(imgs,{'bands': ['R', 'G', 'B']} ,'imgs')
map


# #### Display image (false color)

# In[7]:


#map = folium.Map(location = [lat,long], zoom_start=15, height=500)
basemaps['Google Satellite Hybrid'].add_to(map)
map.add_ee_layer(imgs,{'bands': ['N', 'R', 'G']} ,'imgs_false')
map


# ## Calculate NDVI

# In[8]:


#nir, r = imgs.select('N'), imgs.select('R')
ndvi = imgs.normalizedDifference(["N", "R"])
ndvi_vis = {'min': -1, 'max': 1, 'palette':['red',  'yellow', 'green']}

map2 = folium.Map(location = [lat,long], zoom_start=15, height=500)
basemaps['Google Satellite Hybrid'].add_to(map2)
map2.add_ee_layer(ndvi,ndvi_vis ,'ndvi')
map2


# ## Show region with NDVI higher than 0.1

# In[9]:


veg_mask = ndvi.updateMask(ndvi.gte(0.1))
veg_vis = {'min': 0, 'max': 1, 'palette': ['blue']}
map2.add_ee_layer(veg_mask,veg_vis ,'ndvi')
map2


# ## Images segmentation

# In[10]:


seed = ee.Algorithms.Image.Segmentation.seedGrid(6)
#seg = ee.Algorithms.Image.Segmentation.GMeans(image=imgs,numIterations=100,pValue=50,neighborhoodSize=500)
seg = ee.Algorithms.Image.Segmentation.SNIC(image=imgs, size=10,compactness= 0, neighborhoodSize=500,connectivity= 8, seeds=seed).select(['R_mean', 'G_mean', 'B_mean', 'N_mean', 'clusters'], ['R', 'G', 'B', 'N', 'clusters'])
clusters = seg.select('clusters')


# In[11]:


map3 = folium.Map(location = [lat,long], zoom_start=15, height=500)
basemaps['Google Satellite'].add_to(map3)
map3.add_ee_layer(clusters.randomVisualizer(), {}, 'clusters')
map3


# ## Calculate per-cluster features (for future use)

# In[12]:


## ndvi
seg_ndvi = ndvi.addBands(clusters).reduceConnectedComponents(ee.Reducer.mean(),'clusters').rename('seg_ndvi')
Map.addLayer(seg_ndvi,{},'seg_ndvi')

## standard-deviation
std = ndvi.addBands(clusters).reduceConnectedComponents(ee.Reducer.stdDev(),'clusters').rename('std')
Map.addLayer(std,{},'StdDev')

## area
area = ee.Image.pixelArea().addBands(clusters).reduceConnectedComponents(ee.Reducer.sum(), 'clusters')
Map.addLayer(area,{}, 'Area')

## perimeter
minMax = clusters.reduceNeighborhood(ee.Reducer.minMax(), ee.Kernel.square(1))
perimeterPixels = minMax.select(0).neq(minMax.select(1)).rename('perimeter')
Map.addLayer(perimeterPixels,{},'perimeterPixels')
perimeter = perimeterPixels.addBands(clusters).reduceConnectedComponents(ee.Reducer.sum(), 'clusters')
Map.addLayer(perimeter, {}, 'Perimeter')

## width and height
sizes = ee.Image.pixelLonLat().addBands(clusters).reduceConnectedComponents(ee.Reducer.minMax(), 'clusters')
width = sizes.select('longitude_max').subtract(sizes.select('longitude_min')).rename('width')
height = sizes.select('latitude_max').subtract(sizes.select('latitude_min')).rename('height')
Map.addLayer(width, {},'Width')
Map.addLayer(height, {}, 'Height')


# ## Display objects with NDVI < 0.1

# In[13]:


seg_veg = seg_ndvi.updateMask(seg_ndvi.gte(0.1))

map4 = folium.Map(location = [lat,long], zoom_start=15, height=500)
basemaps['Google Satellite'].add_to(map4)
map4.add_ee_layer(seg_veg.randomVisualizer(), {}, 'clusters')
map4


# ###### Thanks to all the GEE communities and all the code available online. Special thanks to Dr. Qiusheng Wu (https://github.com/giswqs)
