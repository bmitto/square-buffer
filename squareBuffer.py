#-------------------------------------------------------------------------------
# Name:       squareBuffer.py
# Purpose:    To generate square buffers around points
#
# Notes:      Assumes that the geometry is point and not a multipoint. For rectangular
#             polygons, see shapely.geometry.box(): http://toblerity.org/shapely/manual.html

# Author Benard Mitto
#-------------------------------------------------------------------------------
from shapely.geometry import Polygon 
from osgeo import ogr
from osgeo import osr

import shapefile
import numpy as np
import os
import sys

def squareBuffer(pointCoords, bufferDist = 100):
    # flatten the array into one dimension
    pointCoords = pointCoords.flatten()
    # compute delta x and y from the central point
    Xpos = pointCoords[0] + bufferDist
    Ypos = pointCoords[1] + bufferDist
    Xneg = pointCoords[0] - bufferDist
    Yneg = pointCoords[1] - bufferDist
    # form coordinate tuples for each of the quadrant corners
    quad1Coords = (Xpos, Ypos)
    quad2Coords = (Xneg, Ypos)
    quad3Coords = (Xneg, Yneg)
    quad4Coords = (Xpos, Yneg)
    # return the corner coordinates as a list noting that polygons must have
    #  at least 4 points and the last point must be the same as the first
    return [quad1Coords, quad2Coords, quad3Coords, quad4Coords, quad1Coords]

#-------------------------------------------------------------------------------
# Read in the shapefile using PyShp library
#-------------------------------------------------------------------------------
sf = shapefile.Reader("samplePoints") # read shapefile
#shapes = sf.shapes() # read geometry of shapefile
data = sf.shapeRecords() # reads shape/geometry and records simultaneosuly

# Extract field names: fields return (name, type, length, digits). First row
# is usually ('DeletionFlag', 'C', 1, 0)
fieldNames = sf.fields
# Store only fn's by stripping the first row ('DeletionFlag', 'C', 1, 0) from list
fn = [header[0] for header in fieldNames[1:]]

# loop through features in point shapefile extracting records, coordinates, drawing
# square buffers around them, and writing output as shapefile

squares = []; records = []
for row in data: # consider for row in sf.iter
    records.append(row.record) # record for a given feature
    xy = np.array(row.shape.points)
    cornerCoords = squareBuffer(xy)
    square = Polygon(cornerCoords)
    squares.append(square)

# create folder for our output shapefile in the directory of the script
folder = "output"
if os.path.exists(folder):
    # delete folder and its contents
    import shutil
    shutil.rmtree(folder)
    # otherwise create the folder
if not os.path.exists(folder):
    os.makedirs(folder)

# Set up OGR driver, datasource, spatial reference, layer, and feature definition
driver = ogr.GetDriverByName("ESRI Shapefile")
ds = driver.CreateDataSource(folder + "/squareBuffers.shp")

sr = osr.SpatialReference()
sr.ImportFromEPSG(2193)

layer = ds.CreateLayer(folder + "/squareBuffers", sr, ogr.wkbPolygon)
featDefn = layer.GetLayerDefn()
feat = ogr.Feature(featDefn)

# create fields (string, integer, and real) for the layer
# needs re-writing to automatically detect field widths etc. 
for i in range(len(fn)):
    if i <= 10:
        fieldName = ogr.FieldDefn(fn[i], ogr.OFTString)
        #fieldName.SetWidth(fn[i][2])
        layer.CreateField(fieldName)
    elif i > 10 and i <= 12:
        fieldName = ogr.FieldDefn(fn[i], ogr.OFTInteger)
        #fieldName.SetWidth(fn[i][2])
        layer.CreateField(fieldName)
    else:
        fieldName = ogr.FieldDefn(fn[i], ogr.OFTReal)
        #fieldName.SetWidth(fn[i][2])
        layer.CreateField(fieldName)

# populate fields and create shapefile for each square feature
for sq in xrange(0, len(squares)):

    for j in range(len(fn)):
        feat.SetField(fn[j], records[sq][j])

    geom = ogr.CreateGeometryFromWkb(squares[sq].wkb)
    feat.SetGeometry(geom)
    layer.CreateFeature(feat)

# some house keeping to clear memory
ds = layer = feat = geom = None
