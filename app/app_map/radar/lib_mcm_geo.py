# -------------------------------------------------------------------------------------
# Library
import logging
import numpy as np
import rasterio
import rasterio.crs
import os

from lib_mcm_io_generic import create_darray_2d

logging.getLogger('rasterio').setLevel(logging.WARNING)
# -------------------------------------------------------------------------------------


# --------------------------------------------------------------------------------
# Method to find XY geographical indexes
def find_geo_index(geo_x_ref, geo_y_ref, geo_x_var, geo_y_var, geo_cellsize_var):

    # Get geographical information
    yu_ref = np.max(geo_y_ref)
    xl_ref = np.min(geo_x_ref)
    # Compute index
    index_y_var = np.ceil((yu_ref - geo_y_var.ravel()) / geo_cellsize_var)
    index_x_var = np.ceil((geo_x_var.ravel() - xl_ref) / geo_cellsize_var)
    # From double to integer
    index_x_var = np.int32(index_x_var)
    index_y_var = np.int32(index_y_var)

    return index_x_var, index_y_var
# --------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to get a raster ascii file
def read_file_raster(file_name, file_proj='epsg:4326', var_name='land',
                     coord_name_x='west_east', coord_name_y='south_north',
                     dim_name_x='west_east', dim_name_y='south_north'):

    if os.path.exists(file_name):
        if file_name.endswith('.txt') or file_name.endswith('.asc'):

            crs = rasterio.crs.CRS({"init": file_proj})
            with rasterio.open(file_name, mode='r+') as dset:
                dset.crs = crs
                bounds = dset.bounds
                no_data = dset.nodata
                res = dset.res
                transform = dset.transform
                data = dset.read()
                proj = dset.crs.wkt
                values = data[0, :, :]

            decimal_round = 7

            center_right = bounds.right - (res[0] / 2)
            center_left = bounds.left + (res[0] / 2)
            center_top = bounds.top - (res[1] / 2)
            center_bottom = bounds.bottom + (res[1] / 2)

            lon = np.arange(center_left, center_right + np.abs(res[0] / 2), np.abs(res[0]), float)
            lat = np.arange(center_bottom, center_top + np.abs(res[0] / 2), np.abs(res[1]), float)
            lons, lats = np.meshgrid(lon, lat)

            min_lon_round = round(np.min(lons), decimal_round)
            max_lon_round = round(np.max(lons), decimal_round)
            min_lat_round = round(np.min(lats), decimal_round)
            max_lat_round = round(np.max(lats), decimal_round)

            center_right_round = round(center_right, decimal_round)
            center_left_round = round(center_left, decimal_round)
            center_bottom_round = round(center_bottom, decimal_round)
            center_top_round = round(center_top, decimal_round)

            assert min_lon_round == center_left_round
            assert max_lon_round == center_right_round
            assert min_lat_round == center_bottom_round
            assert max_lat_round == center_top_round

            lats = np.flipud(lats)

            dims = values.shape
            high = dims[0] # nrows
            wide = dims[1] # cols

            bounding_box = [min_lon_round, max_lat_round, max_lon_round, min_lat_round]

            da = create_darray_2d(values, lons, lats, coord_name_x=coord_name_x, coord_name_y=coord_name_y,
                                  dim_name_x=dim_name_x, dim_name_y=dim_name_y, name=var_name)

        else:
            logging.error(' ===> Geographical file ' + file_name + ' format unknown')
            raise NotImplementedError('File type reader not implemented yet')
    else:
        logging.error(' ===> Geographical file ' + file_name + ' not found')
        raise IOError('Geographical file location or name is wrong')

    return da, wide, high, proj, transform, bounding_box, no_data
# -------------------------------------------------------------------------------------
