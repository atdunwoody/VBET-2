from preprocessing.combine_streams_less_than_50m import combine_streams_less_than_50m
from preprocessing.segment_stream import split_stream_by_lines
from preprocessing.add_drainage_area_to_streams import add_drainage_area_to_streams
from preprocessing.create_perpendiculars import create_smooth_perpendicular_lines
import os

input_stream_vector = r"Y:\ATD\GIS\Bennett\Valley Bottoms\VBET\streams_100k.gpkg"
flow_accumulation_raster = r"Y:\ATD\GIS\Bennett\Watershed Stats\flow accumulation.tif"
output_dir = r"Y:\ATD\GIS\Bennett\Valley Bottoms\VBET"
stream_spacing = 20

split_streams_gpkg = input_stream_vector.split('.')[0] + f'_segmented_{stream_spacing}m.gpkg'
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

perp_lines = create_smooth_perpendicular_lines(input_stream_vector, line_length=1, 
                                               spacing=stream_spacing, window=10)
perpendiculars_path = os.path.join(output_dir, f'Bennett perpendiculars {stream_spacing}m.gpkg')
perp_lines.to_file(perpendiculars_path, driver='GPKG')

print("Combining streams less than 50m...")
combined_streams = combine_streams_less_than_50m(input_stream_vector)
print("Segmenting streams...")
split_stream_by_lines(combined_streams, perpendiculars_path, split_streams_gpkg)
print("Adding drainage area to streams...")
add_drainage_area_to_streams(flow_accumulation_raster, split_streams_gpkg)