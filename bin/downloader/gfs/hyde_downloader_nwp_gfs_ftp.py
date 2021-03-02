#!/usr/bin/python3

"""
HyDE Downloading Tool - NWP GFS 0.25 backup procedure UCAR server

__date__ = '20210212'
__version__ = '1.0.0'
__author__ =
        'Andrea Libertino (andrea.libertino@cimafoundation.org',
        'Fabio Delogu (fabio.delogu@cimafoundation.org',
        'Alessandro Masoero (alessandro.masoero@cimafoundation.org',
__library__ = 'HyDE'

General command line:
python3 hyde_downloader_nwp_gfs_ftp.py -settings_file configuration.json -time YYYY-MM-DD HH:MM

Version(s):
20210212 (1.0.0) --> Beta release
"""
# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Complete library
import logging
from argparse import ArgumentParser
from datetime import timedelta, datetime
from siphon.catalog import TDSCatalog
from siphon.ncss import NCSS
from xarray.backends import NetCDF4DataStore
import xarray as xr
import pandas as pd
from copy import deepcopy
import os
import time
import json

# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Algorithm information
alg_name = 'HYDE DOWNLOADING TOOL - NWP GFS BACKUP PROCEDURE'
alg_version = '1.0.0'
alg_release = '2021-02-12'
# Algorithm parameter(s)
time_format = '%Y%m%d%H%M'
# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Script Main
def main():

    # -------------------------------------------------------------------------------------
    # Get algorithm settings
    alg_settings, alg_time = get_args()

    # Set algorithm settings
    data_settings = read_file_json(alg_settings)

    # Set algorithm logging
    os.makedirs(data_settings['data']['log']['folder'], exist_ok=True)
    set_logging(logger_file=os.path.join(data_settings['data']['log']['folder'], data_settings['data']['log']['filename']))

    # -------------------------------------------------------------------------------------
    # Info algorithm
    logging.info(' ============================================================================ ')
    logging.info(' ==> ' + alg_name + ' (Version: ' + alg_version + ' Release_Date: ' + alg_release + ')')
    logging.info(' ==> START ... ')
    logging.info(' ')

    # Time algorithm information
    start_time = time.time()
    # -------------------------------------------------------------------------------------

    timeRun = datetime.strptime(alg_time,'%Y-%m-%d %H:%M')
    timeEnd = timeRun + pd.Timedelta(str(data_settings["data"]["dynamic"]["time"]["time_forecast_period"]) + data_settings["data"]["dynamic"]["time"]["time_forecast_frequency"])

    outFolder = data_settings["data"]["dynamic"]["outcome"]["folder"]

    var_dic = deepcopy(data_settings["algorithm"]["template"])
    for keys in data_settings["algorithm"]["template"].keys():
        var_dic[keys] = timeRun.strftime(data_settings["algorithm"]["template"][keys])

    outFolder=outFolder.format(**var_dic)
    os.makedirs(outFolder, exist_ok=True)

    # Starting info
    logging.info(' --> TIME RUN: ' + str(timeRun))
    logging.info(' --> TIME END: ' + str(timeEnd))

    variables = data_settings["data"]["dynamic"]["variables"]

    # Query remote UCAR server for data
    logging.info(' ---> Search files on UCAR server ... ')
    lastFrc = TDSCatalog('https://thredds.ucar.edu/thredds/catalog/grib/NCEP/GFS/Global_0p25deg/GFS_Global_0p25deg_' + timeRun.strftime('%Y%m%d') + '_' + timeRun.strftime('%H%M') + '.grib2/catalog.xml')
    lastFrcDS = list(lastFrc.datasets.values())[0]
    ncss = NCSS(lastFrcDS.access_urls['NetcdfSubset'])

    logging.info(' ---> Forecast GFS_Global_0p25deg_' + timeRun.strftime('%Y%m%d') + '_' + timeRun.strftime('%H%M') + '.grib2 found')

    variablesGFS = [varGFS for varHMC in variables.keys() for varGFS in variables[varHMC]]

    # Remove variables not contained in dataset
    presentVariables = ()
    for v in variablesGFS:
        if v in ncss.variables:
            presentVariables = presentVariables + (v,)

    logging.info(' ---> Download forecast file ... ')
    query = ncss.query()
    query.lonlat_box(data_settings["data"]["static"]["bounding_box"]["lon_left"], data_settings["data"]["static"]["bounding_box"]["lon_right"], data_settings["data"]["static"]["bounding_box"]["lat_bottom"], data_settings["data"]["static"]["bounding_box"]["lat_top"])
    query.accept('netcdf4')
    query.variables(*presentVariables)

    # Download variables
    if timeRun is not None and timeEnd is not None:
        query.time_range(timeRun, timeEnd)
    else:
        query.all_times()
    data = ncss.get_data(query)
    data = xr.open_dataset(NetCDF4DataStore(data))
    logging.info(' ---> Download forecast file ... OK ')

    # Merge and reformat downloaded file to be consistent with the outcomes of the NOMADS gfs download procedure
    logging.info(' ---> Compute output files ... ')
    for varHMC in variables.keys():
        logging.info(' ---> Elaborate ' + varHMC + ' file...')
        for varGFS in variables[varHMC].keys():
            logging.info(' ----> Compute ' + varGFS + ' variable...')
            if len(data[varGFS].shape)==4:
                varIn = data[varGFS].loc[:,[variables[varHMC][varGFS]["height"]],:,:]
                codHeight = str(variables[varHMC][varGFS]["height"]) + 'm'
                varIn = varIn.rename({varIn.dims[0]: 'time', varIn.dims[1]:"height"})
            elif len(data[varGFS].shape)==3:
                varIn = data[varGFS]
                codHeight = 'srf'
                varIn = varIn.rename({varIn.dims[0]: 'time'})
            else:
                print('Problem in data shape for variable ' + varGFS)

            timeRange = pd.date_range(timeRun + pd.Timedelta(variables[varHMC][varGFS]["freq"]), timeEnd + pd.Timedelta(variables[varHMC][varGFS]["freq"]), freq=variables[varHMC][varGFS]["freq"])
            varFilled = varIn.reindex({'time': timeRange}, method='bfill')

            if varGFS=="Precipitation_rate_surface_Mixed_intervals_Average":
                temp = deepcopy(varFilled)*3600
                varFilled = temp.cumsum(dim=temp.dims[0], keep_attrs=True)

            outName = data_settings["algorithm"]["ancillary"]["domain"] + "_gfs.t" + timeRun.strftime('%H') + "z.0p25." + timeRun.strftime('%Y%m%d') + "_" + codHeight + "_" + varHMC + ".nc"

            try:
                varFilled.to_dataset(name=variables[varHMC][varGFS]["varName"]).to_netcdf(path= os.path.join(outFolder, outName), mode='a')
            except:
                varFilled.to_dataset(name=variables[varHMC][varGFS]["varName"]).to_netcdf(path= os.path.join(outFolder, outName), mode='w')
            logging.info(' ----> Compute ' + varGFS + ' variable...OK')
        logging.info(' ---> Elaborate ' + varHMC + ' file...OK')

    # -------------------------------------------------------------------------------------
    # Info algorithm
    time_elapsed = round(time.time() - start_time, 1)

    logging.info(' ')
    logging.info(' ==> ' + alg_name + ' (Version: ' + alg_version + ' Release_Date: ' + alg_release + ')')
    logging.info(' ==> TIME ELAPSED: ' + str(time_elapsed) + ' seconds')
    logging.info(' ==> ... END')
    logging.info(' ==> Bye, Bye')
    logging.info(' ============================================================================ ')
    # -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Method to read file json
def read_file_json(file_name):

    env_ws = {}
    for env_item, env_value in os.environ.items():
        env_ws[env_item] = env_value

    with open(file_name, "r") as file_handle:
        json_block = []
        for file_row in file_handle:

            for env_key, env_value in env_ws.items():
                env_tag = '$' + env_key
                if env_tag in file_row:
                    env_value = env_value.strip("'\\'")
                    file_row = file_row.replace(env_tag, env_value)
                    file_row = file_row.replace('//', '/')

            # Add the line to our JSON block
            json_block.append(file_row)

            # Check whether we closed our JSON block
            if file_row.startswith('}'):
                # Do something with the JSON dictionary
                json_dict = json.loads(''.join(json_block))
                # Start a new block
                json_block = []

    return json_dict
# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Method to get script argument(s)
def get_args():
    parser_handle = ArgumentParser()
    parser_handle.add_argument('-settings_file', action="store", dest="alg_settings")
    parser_handle.add_argument('-time', action="store", dest="alg_time")
    parser_values = parser_handle.parse_args()

    if parser_values.alg_settings:
        alg_settings = parser_values.alg_settings
    else:
        alg_settings = 'configuration.json'

    if parser_values.alg_time:
        alg_time = parser_values.alg_time
    else:
        alg_time = None

    return alg_settings, alg_time
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to set logging information
def set_logging(logger_file='log.txt', logger_format=None):

    if logger_format is None:
        logger_format = '%(asctime)s %(name)-12s %(levelname)-8s ' \
                        '%(filename)s:[%(lineno)-6s - %(funcName)20s()] %(message)s'

    # Remove old logging file
    if os.path.exists(logger_file):
        os.remove(logger_file)

    # Set level of root debugger
    logging.root.setLevel(logging.DEBUG)

    # Open logging basic configuration
    logging.basicConfig(level=logging.DEBUG, format=logger_format, filename=logger_file, filemode='w')

    # Set logger handle
    logger_handle_1 = logging.FileHandler(logger_file, 'w')
    logger_handle_2 = logging.StreamHandler()
    # Set logger level
    logger_handle_1.setLevel(logging.DEBUG)
    logger_handle_2.setLevel(logging.DEBUG)
    # Set logger formatter
    logger_formatter = logging.Formatter(logger_format)
    logger_handle_1.setFormatter(logger_formatter)
    logger_handle_2.setFormatter(logger_formatter)

    # Add handle to logging
    logging.getLogger('').addHandler(logger_handle_1)
    logging.getLogger('').addHandler(logger_handle_2)

# -------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------
# Call script from external library
if __name__ == "__main__":
    main()
# ----------------------------------------------------------------------------





