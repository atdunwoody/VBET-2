import os
import geopandas as gpd
from shapely.geometry import LineString, MultiLineString
from shapely import ops
from shapely.errors import TopologicalError

def split_stream_by_lines(line_gpkg: str, splitter_lines_gpkg: str, output_gpkg: str = None, min_length: float = 50.0):
    """
    Splits lines by intersecting splitter lines and merges any resulting segments
    that are shorter than the specified minimum length with the previous segment.

    Parameters:
    line_gpkg (str or gpd.GeoDataFrame): Path to the input GeoPackage containing the lines to be split, or a GeoDataFrame.
    splitter_lines_gpkg (str or gpd.GeoDataFrame): Path to the input GeoPackage containing the splitter lines, or a GeoDataFrame.
    output_gpkg (str, optional): Path to the output GeoPackage for storing the split lines. If None, returns a GeoDataFrame.
    min_length (float, optional): Minimum length (in meters) for each split segment. Default is 50 meters.

    Returns:
    str or gpd.GeoDataFrame: Path to the output GeoPackage if provided, otherwise a GeoDataFrame of split lines.
    """

    # Handle output GeoPackage existence
    if output_gpkg is not None:
        if os.path.exists(output_gpkg):
            print(f"Output GeoPackage already exists: {output_gpkg}")
            return output_gpkg
        else:
            print(f"Output GeoPackage will be saved to: {output_gpkg}")

    # Read input lines to split
    if isinstance(line_gpkg, gpd.GeoDataFrame):
        lines_to_split = line_gpkg.copy()
    else:
        lines_to_split = gpd.read_file(line_gpkg)
        print(f"Loaded {len(lines_to_split)} lines to split from {line_gpkg}")

    # Read splitter lines
    if isinstance(splitter_lines_gpkg, gpd.GeoDataFrame):
        splitter_lines = splitter_lines_gpkg.copy()
    else:
        splitter_lines = gpd.read_file(splitter_lines_gpkg)
        print(f"Loaded {len(splitter_lines)} splitter lines from {splitter_lines_gpkg}")

    # Validate input GeoDataFrames
    if lines_to_split.empty:
        raise ValueError("The input lines to split are empty.")
    if splitter_lines.empty:
        raise ValueError("The splitter lines are empty.")

    # Ensure both GeoDataFrames have the same CRS
    if lines_to_split.crs != splitter_lines.crs:
        print("CRS mismatch between input lines and splitter lines. Reprojecting splitter lines to match input lines CRS.")
        splitter_lines = splitter_lines.to_crs(lines_to_split.crs)

    # Ensure the CRS is projected (units in meters)
    if not lines_to_split.crs.is_projected:
        raise ValueError("Input GeoDataFrame CRS must be projected (units in meters) for accurate length calculations.")

    # Dissolve all splitter lines into a single geometry for efficient splitting
    splitter_union = splitter_lines.unary_union

    if splitter_union.is_empty:
        raise ValueError("The splitter lines layer has no valid geometries.")

    # Function to split a single LineString or MultiLineString by the splitter geometry
    def split_line(line, splitter):
        try:
            split_result = ops.split(line, splitter)
            return list(split_result)
        except TopologicalError as e:
            print(f"TopologicalError encountered while splitting line: {e}")
            return [line]

    # Prepare to collect split lines with their original line IDs
    split_records = []
    for idx, line in lines_to_split.geometry.iteritems():
        if isinstance(line, (LineString, MultiLineString)):
            try:
                split_geometries = split_line(line, splitter_union)
                # Filter out empty geometries and ensure they are LineStrings
                for geom in split_geometries:
                    if isinstance(geom, (LineString, MultiLineString)) and not geom.is_empty:
                        if isinstance(geom, MultiLineString):
                            for part in geom.geoms:
                                if not part.is_empty:
                                    split_records.append({'original_id': idx, 'geometry': part})
                        else:
                            split_records.append({'original_id': idx, 'geometry': geom})
            except Exception as e:
                print(f"Error processing line at index {idx}: {e}")
        else:
            print(f"Skipping non-line geometry at index {idx}.")

    if not split_records:
        raise ValueError("No valid lines were created from the splitting process.")

    # Create a GeoDataFrame for the split lines with original IDs
    split_gdf = gpd.GeoDataFrame(split_records, crs=lines_to_split.crs)

    # Optional: Retain original attributes by repeating or aggregating as needed
    # For simplicity, this example does not carry over attributes beyond 'original_id'

    # Function to merge short segments within each group
    def merge_short_segments(group, min_len):
        merged = []
        buffer = None  # Temporary buffer for short segments

        for geom in group.geometry:
            length = geom.length
            if length >= min_len:
                if buffer:
                    # Merge buffer with current geom
                    merged_geom = ops.linemerge([buffer, geom])
                    merged.append(merged_geom)
                    buffer = None
                else:
                    merged.append(geom)
            else:
                if buffer:
                    # Merge existing buffer with current geom
                    buffer = ops.linemerge([buffer, geom])
                else:
                    buffer = geom

        # After iterating, check if there's any remaining buffer
        if buffer:
            if merged:
                # Merge the remaining buffer with the last merged segment
                last = merged.pop()
                merged_geom = ops.linemerge([last, buffer])
                merged.append(merged_geom)
            else:
                # If there are no merged segments yet, just append the buffer
                merged.append(buffer)

        return merged

    # Apply the merging function to each group of split segments
    merged_records = []
    for original_id, group in split_gdf.groupby('original_id'):
        # It's crucial to maintain the order of segments as they appear along the original line
        # Assuming split_geometries are in order
        merged_segments = merge_short_segments(group, min_length)
        for geom in merged_segments:
            merged_records.append({'original_id': original_id, 'geometry': geom})

    if not merged_records:
        raise ValueError("No valid lines remain after merging short segments.")

    # Create the final GeoDataFrame
    final_split_gdf = gpd.GeoDataFrame(merged_records, crs=lines_to_split.crs)

    # Optionally, reset the index
    final_split_gdf.reset_index(drop=True, inplace=True)

    # Write the split lines to the output GeoPackage or return the GeoDataFrame
    if output_gpkg is not None:
        final_split_gdf.to_file(output_gpkg, driver='GPKG')
        print(f"Split lines saved to {output_gpkg}")
        return output_gpkg
    else:
        return final_split_gdf
