import geopandas as gpd
from shapely.ops import linemerge
from shapely.geometry import MultiLineString
import os

def combine_streams_less_than_50m(input_shapefile):
    gdf = gpd.read_file(input_shapefile)

    # Set the minimum length threshold for joining lines
    min_length = 50  # meters

    # Create a list to hold the merged lines
    merged_lines = []

    # Iterate over each line feature in the GeoDataFrame
    for idx, line in gdf.iterrows():
        # Check if the line length is less than the threshold
        if line.geometry.length < min_length:
            # Find the neighbor (the next line in the dataframe)
            if idx < len(gdf) - 1:
                # Merge the current line with its neighbor
                neighbor_line = gdf.loc[idx + 1, 'geometry']
                merged_line = linemerge([line.geometry, neighbor_line])
                # Update the next line with the merged geometry
                gdf.at[idx + 1, 'geometry'] = merged_line
            else:
                # If there is no neighbor, just append the current line
                merged_lines.append(line.geometry)
        else:
            # Append lines that do not need merging
            merged_lines.append(line.geometry)

    # Create a new GeoDataFrame with the merged lines
    merged_gdf = gpd.GeoDataFrame(geometry=merged_lines, crs=gdf.crs)

    # Save the output to a new shapefile
    if os.path.splitext(input_shapefile)[1] == ".shp":
        output_name = os.path.basename(input_shapefile).replace(".shp", "_merged.shp")
    elif os.path.splitext(input_shapefile)[1] == ".gpkg":
        output_name = os.path.basename(input_shapefile).replace(".gpkg", "_merged.gpkg")
    else:
        output_name = "merged.shp"
    output_shapefile = os.path.join(os.path.dirname(input_shapefile), "VBET Inputs", output_name)
    os.makedirs(os.path.dirname(output_shapefile), exist_ok=True)
    merged_gdf.to_file(output_shapefile)

    print(f"Merged shapefile saved to {output_shapefile}")
    return output_shapefile

if __name__ == "__main__":
    # Load the line shapefile into a GeoDataFrame
    input_shapefile = r"Y:\ATD\GIS\Bennett\Valley Widths\VBET\Streams\Single_Part_Bennett.shp"
    combine_streams_less_than_50m(input_shapefile)