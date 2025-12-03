"""
some utils func with qgis sauce

not sure the import are necessary, but keep em if we want a standalone script without qgis launched
"""
from qgis.core import QgsProcessing, QgsRasterLayer, QgsVectorLayer
from qgis import processing
from osgeo import gdal
import numpy as np

def reproject_raster( raster_path, target_crs, return_path = False ):
    # func to reproject a raster to target CRS
    # return temporary qgis temp path or 
    # raster path : str or QgsRasterLayer
    # target_crs : int

    result = processing.run("gdal:warpreproject", {
        'INPUT': raster_path,  # The input raster
        'TARGET_CRS': target_crs,  # The CRS to reproject to
        'RESAMPLING': 0,  # Resampling method: nearest neighbor (0) or bilinear (1)
        'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT  # Temporary output
    })

    # Get the reprojected raster's path
    reprojected_raster_path = result['OUTPUT']

    if return_path:
        return reprojected_raster_path
    else:
        return QgsRasterLayer(reprojected_raster_path, "Reprojected_Raster")


def reproject_vector( vector_path, target_crs, return_path = False ):
    # func to reproject a raster to target CRS
    # return temporary qgis temp path
    # vector_path path : str or QgsVectorLayer
    # target_crs : int
    result = processing.run("native:reprojectlayer", {
        'INPUT':vector_path,
        'TARGET_CRS': target_crs,  # The CRS to reproject to
        'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT  # Temporary output
    })

    # Get the reprojected raster's path
    reprojected_vector_path = result['OUTPUT']

    if return_path:
        return reprojected_vector_path
    else:
        return QgsVectorLayer(reprojected_vector_path, "Reprojected_Vector")

def cut_raster( raster_path, vector_path, input_crs, output_crs, crop = True, return_path = False, nodata =0):
    # nodata : valeurs sur les zones en dehors du découpage
    result = processing.run("gdal:cliprasterbymasklayer",{
            'INPUT':raster_path,
            'MASK':vector_path,
            'CROP_TO_CUTLINE': crop,
            'NODATA':nodata,
            'SOURCE_CRS': input_crs,
            'TARGET_CRS': output_crs,
            'KEEP_RESOLUTION':True,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
    })

    if return_path:
        return result['OUTPUT']
    else:
        return QgsRasterLayer( result['OUTPUT'], "clip_raster")
    
def layerAsArray(layer, nodata=None, unfold = False):
    """ 
    read the data from a single-band layer into a numpy/Numeric array
    nodata : value to set for nodata value, if none keep the original one
    unfold : return layer as a np array N,3 of points coordinates 
    """
    if isinstance(layer, str):
        p = layer # assume its layer path
    else:
        p = layer.source() # assume it's QgsRasterLayer()
    gd = gdal.Open(p)
    array = gd.ReadAsArray()
    nd = gd.GetRasterBand(1).GetNoDataValue()
    if nodata is not None:
        array[ array == nd ] = nodata

    if unfold:

        transform = gd.GetGeoTransform()
        x_size, y_size = array.shape

        # Compute grid of coordinates
        x_coords = np.arange(y_size) * transform[1] + transform[0] + transform[1] / 2
        y_coords = np.arange(x_size) * transform[5] + transform[3] + transform[5] / 2


        # Generate meshgrid
        xx, yy = np.meshgrid(x_coords, y_coords, indexing='ij')

        # array = array.transpose(1,0)
        
        # Flatten and stack (N, 3) format
        coords_values = np.column_stack((xx.ravel(), yy.ravel(), array.transpose(1,0).ravel()))

        return coords_values, transform, nd, array.shape

    return array, gd.GetGeoTransform()[1] # pixel_size
