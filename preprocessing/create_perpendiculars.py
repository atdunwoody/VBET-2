import geopandas as gpd
from shapely.geometry import LineString, MultiLineString
from shapely.ops import linemerge
import numpy as np
import os


def create_smooth_perpendicular_lines(centerline_path, line_length=60, spacing=5, window=20, output_path=None):

    # Load the centerline from the geopackage
    gdf = gpd.read_file(centerline_path)
    
    try:
        # Dissolve and merge the centerlines into one continuous geometry
        merged_geometry = linemerge(gdf.geometry.unary_union)

    except Exception as e:
        print(f"Error merging centerlines: {e}")
        merged_geometry = gdf.geometry.unary_union
    # Handle MultiLineString appropriately using `geoms`
    if isinstance(merged_geometry, MultiLineString):
        line_parts = merged_geometry.geoms
    else:
        line_parts = [merged_geometry]

    # Initialize an empty list to store perpendicular lines
    perpendiculars = []
    
    # Process each line part
    for line in line_parts:
        length = line.length
        num_samples = int(np.floor(length / spacing))
        for i in range(num_samples + 1):
            # Calculate the point at each interval along the centerline
            point = line.interpolate(i * spacing)
            
            # Get points window meters ahead and behind
            point_back = line.interpolate(max(0, i * spacing - window))
            point_forward = line.interpolate(min(length, i * spacing + window))
            
            # Calculate vectors to these points
            dx_back, dy_back = point.x - point_back.x, point.y - point_back.y
            dx_forward, dy_forward = point_forward.x - point.x, point_forward.y - point.y
            
            # Average the vectors
            dx_avg = (dx_back + dx_forward) / 2
            dy_avg = (dy_back + dy_forward) / 2
            
            # Calculate the perpendicular vector
            len_vector = np.sqrt(dx_avg**2 + dy_avg**2)
            perp_vector = (-dy_avg, dx_avg)
            
            # Normalize and scale the perpendicular vector
            perp_vector = (perp_vector[0] / len_vector * line_length, perp_vector[1] / len_vector * line_length)
            
            # Create the perpendicular line segment
            perp_line = LineString([
                (point.x + perp_vector[0], point.y + perp_vector[1]),
                (point.x - perp_vector[0], point.y - perp_vector[1])
            ])
            
            # Append the perpendicular line to the list
            perpendiculars.append({'geometry': perp_line})
    
    # Convert list to GeoDataFrame
    perpendiculars_gdf = gpd.GeoDataFrame(perpendiculars, crs=gdf.crs)
    
    # Save the perpendicular lines to the output geopackage
    if output_path is not None:
        perpendiculars_gdf.to_file(output_path, driver='GPKG')
    return perpendiculars_gdf