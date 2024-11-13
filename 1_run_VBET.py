import classVBET
import os
import geopandas as gpd
import rasterio
#Default parameters
# base__params = {
#     'network': '/path/to/stream/network.shp',
#     'dem': '/path/to/dem.tif',
#     'out': '/path/to/vbet/output.shp',
#     'scratch': 'path/to/scratch/workspace',
#     'lg_da': 250,
#     'med_da': 25,
#     'lg_slope': 3,
#     'med_slope': 4,
#     'sm_slope': 5,
#     'lg_buf': 500,
#     'med_buf': 200,
#     'sm_buf': 80,
#     'min_buf': 10,
#     'dr_area': None,
#     'da_field': 'TotDASqKm',
#     'lg_depth': 3,
#     'med_depth': 2,
#     'sm_depth': 1.5
#     }

stream_network = r"Y:\ATD\GIS\Bennett\Valley Geometry\Valleys\Valley Bottom Testing\VBET\streams_100k_segmented_DA.gpkg"
raw_dem = r"Y:\ATD\GIS\Bennett\DEMs\LIDAR\OT 2021\dem 2021 bennett clip.tif"
output_folder = r"Y:\ATD\GIS\Bennett\Valley Geometry\Valleys\Valley Bottom Testing\VBET\VBET Outputs"
scratch_folder = os.path.join(os.path.dirname(output_folder), 'Scratch')

from rasterio.crs import CRS

def match_vector_to_raster_crs(vector_path, raster_path, output_vector_path):
    # Load the raster to get its CRS
    with rasterio.open(raster_path) as src:
        raster_crs = src.crs

    # Load the vector file
    vector_data = gpd.read_file(vector_path)

    # Check if the vector CRS matches the raster CRS
    if vector_data.crs != raster_crs:
        # Reproject vector to match raster CRS
        vector_data = vector_data.to_crs(raster_crs)
        print(f"Reprojected vector to match raster CRS: {raster_crs}")
    else:
        print("Vector CRS matches raster CRS. No reprojection needed.")

    # Save the reprojected vector data
    vector_data.to_file(output_vector_path, driver='GPKG')
    print(f"Saved reprojected vector to: {output_vector_path}")
    return output_vector_path

stream_network_matched = stream_network.split('.')[0] + '_crs_matched.shp'
match_vector_to_raster_crs(stream_network, raw_dem, stream_network_matched)

base_params = {
                'network': stream_network_matched,
                'dem': raw_dem,
                'out': output_folder,
                'scratch': scratch_folder,
                'lg_da': 250,
                'med_da': 100,
                'lg_slope': 3,
                'med_slope': 4,
                'sm_slope': 20,
                'lg_buf': 100,
                'med_buf': 70,
                'sm_buf': 15,
                'min_buf': 4,
                'dr_area': None,
                'da_field': 'DA',
                'lg_depth': 3,
                'med_depth': 2,
                'sm_depth': 6
                }
import numpy as np
sm_slope_array = [5]
sm_depth_array = [1]
sm_buf_array = [5]
test_values = []

for sm_slope in sm_slope_array:
    for sm_depth in sm_depth_array:
        for sm_buf in sm_buf_array:
            output_file = os.path.join(output_folder, f'Bennett_channels_20m_sm_slope_{sm_slope}_depth_{sm_depth}_buf_{sm_buf}.gpkg')
            test_values.append({'sm_slope': sm_slope, 'sm_depth': sm_depth, 'sm_buf': sm_buf, 'min_buf': 1, 'out': output_file})

for idx, test_param in enumerate(test_values):
    class RunVBET:
        def __init__(self):
            params = base_params.copy()
            params.update(test_param)
            self.params = params
            #print(f"Running VBET with parameters: {params}")
            print(f"\nTest parameters: \nsm_slope:{test_param['sm_slope']}, \nsm_depth {test_param['sm_depth']},\nsm_buf {test_param['sm_buf']}\n")
            
        def run(self):
            vb = classVBET.VBET(**self.params)
            if self.params['da_field'] is None:
                vb.add_da()
            vb.valley_bottom()


    vbrun = RunVBET()
    vbrun.run()

