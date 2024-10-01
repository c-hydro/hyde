"""
MODIS Processing Tool - SNOW PRODUCT

__date__ = '20201202'
__version__ = '3.5.0'
__author__ = 'Fabio Delogu (fabio.delogu@cimafoundation.org'
__library__ = 'hyde'

General command line:
python3 S3MResampler.py -settings_file configuration.json -time "YYYY-MM-DD HH:MM"

Version:
20201202 (3.5.0) --> Hyde package refactor
20180910 (3.0.0) --> Beta release to put algorithm into FloodProofs library
20151015 (2.0.0) --> Updated codes, classes and methods
20150725 (1.5.0) --> Updated codes, classes and methods
20150715 (1.0.6) --> Added filter to compute quality index
20150522 (1.0.5) --> Added merging between tiles
20150514 (1.0.4) --> Updated output file attributes
20150513 (1.0.3) --> Added mosaic tile(s) option, update settings file and reader
20141210 (1.0.2) --> Added checking no data available on FTP server
20140808 (1.0.1) --> Re-arranged some functions and other stuff
20140807 (1.0.0) --> First Release
20140805 (0.0.1) --> First Code
"""
# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Complete library
import logging

from argparse import ArgumentParser
from time import time, strftime, gmtime

from src.hyde.driver.configuration.satellite.modis.drv_configuration_algorithm_modis import DriverAlgorithm
from src.hyde.driver.configuration.satellite.modis.drv_configuration_time_modis import DriverTime

from src.hyde.driver.dataset.satellite.modis.drv_data_modis_geo import DriverGeo
from src.hyde.driver.dataset.satellite.modis.drv_data_modis_io import DriverData
# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Algorithm information
alg_project = 'HyDE'
alg_name = 'MODIS PROCESSING TOOL SNOW'
alg_version = '3.5.0'
alg_release = '2020-12-02'
alg_type = 'DataDynamic'
# Algorithm parameter(s)
time_format = '%Y-%m-%d %H:%M'
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Script Main
def main():

    # -------------------------------------------------------------------------------------
    # Get script argument(s)
    [file_script, file_settings, time_arg] = get_args()

    # Set algorithm configuration
    driver_algorithm = DriverAlgorithm(file_settings)
    driver_algorithm.set_algorithm_logging()
    data_settings, dataset_paths, colormap_paths = driver_algorithm.set_algorithm_info()
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Start Program
    logging.info('[' + alg_project + ' ' + alg_type + ' - ' + alg_name + ' (Version ' + alg_version + ')]')
    logging.info('[' + alg_project + '] Execution Time: ' + strftime("%Y-%m-%d %H:%M", gmtime()) + ' GMT')
    logging.info('[' + alg_project + '] Reference Time: ' + time_arg + ' GMT')
    logging.info('[' + alg_project + '] Start Program ... ')

    # Time algorithm information
    start_time = time()
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Get data time
    logging.info(' --> Set algorithm time ... ')
    driver_time = DriverTime(time_arg, data_settings['time'])
    time_run, time_exec, time_range = driver_time.set_algorithm_time()
    logging.info(' --> Set algorithm time ... DONE')
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Set data geo
    logging.info(' --> Set geographical data ... ')
    driver_geo = DriverGeo(src_dict=data_settings['data']['static']['source'],
                           ancillary_dict=data_settings['data']['static']['ancillary'],
                           flag_updating_ancillary=data_settings['algorithm']['flag']['update_static_data_ancillary'])
    geo_collections = driver_geo.composer_geo()
    logging.info(' --> Set geographical data ... DONE')
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Iterate over time steps
    for time_step in time_range:

        # -------------------------------------------------------------------------------------
        # Get data dynamic
        driver_data_dynamic = DriverData(
            time_step=time_step,
            geo_collections=geo_collections,
            src_dict=data_settings['data']['dynamic']['source'],
            ancillary_dict=data_settings['data']['dynamic']['ancillary'],
            dst_dict=data_settings['data']['dynamic']['destination'],
            time_dict=data_settings['data']['dynamic']['time'],
            variable_src_dict=data_settings['variables']['source'],
            variable_dst_dict=data_settings['variables']['destination'],
            info_dict=data_settings['algorithm']['info'],
            template_dict=data_settings['algorithm']['template'],
            flag_updating_ancillary=data_settings['algorithm']['flag']['update_dynamic_data_ancillary'],
            flag_updating_destination=data_settings['algorithm']['flag']['update_dynamic_data_destination'],
            flag_cleaning_tmp=data_settings['algorithm']['flag']['clean_temporary_data'])

        # Method to organize datasets
        driver_data_dynamic.organize_data()
        # Method to dump datasets
        driver_data_dynamic.dump_data()
        # Method to delete tmp
        driver_data_dynamic.clean_tmp()
        # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Note about script parameter(s)
    logging.info('NOTE - Algorithm parameter(s)')
    logging.info('Script: ' + str(file_script))
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # End Program
    elapsed_time = round(time() - start_time, 1)

    logging.info('[' + alg_project + ' ' + alg_type + ' - ' + alg_name + ' (Version ' + alg_version + ')]')
    logging.info('End Program - Time elapsed: ' + str(elapsed_time) + ' seconds')
    # -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to get script argument(s)
def get_args():

    parser_handle = ArgumentParser()
    parser_handle.add_argument('-settings_file', action="store", dest="alg_settings")
    parser_handle.add_argument('-time', action="store", dest="alg_time")
    parser_values = parser_handle.parse_args()

    alg_script = parser_handle.prog

    if parser_values.alg_settings:
        alg_settings = parser_values.alg_settings
    else:
        alg_settings = 'configuration.json'

    if parser_values.alg_time:
        alg_time = parser_values.alg_time
    else:
        alg_time = None

    return alg_script, alg_settings, alg_time

# -------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------
# Call script from external library
if __name__ == "__main__":
    main()
# ----------------------------------------------------------------------------
