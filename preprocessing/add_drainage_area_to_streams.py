import geopandas as gpd
import rasterio
import numpy as np
from shapely.geometry import LineString
from rasterio.mask import mask
from rasterio.enums import Resampling
import os
import fiona



def add_drainage_area_to_streams(flow_accum_path, segmented_CL_path, output_gpkg = None, drainage_area_path = None):
    # Define buffer distance in meters
    buffer_distance = 5  # 5 meters

    # Step 1: Compute Drainage Area Raster
    with rasterio.open(flow_accum_path) as src:
        # Read flow accumulation data
        flow_accum = src.read(1, masked=True)
        
        # Get raster resolution (assuming square pixels)
        cell_size_x, cell_size_y = src.res
        if cell_size_x != cell_size_y:
            raise ValueError("Raster cells are not square.")
        cell_size = cell_size_x  # in the same units as the raster CRS
        
        # Apply drainage area formula
        drainage_area = (flow_accum * (cell_size ** 2)) / 1_000_000  # Convert to square kilometers if units are meters
        
        # Define metadata for the new raster
        drainage_meta = src.meta.copy()
        drainage_meta.update({
            "dtype": rasterio.float32,
            "count": 1,
            "nodata": np.nan
        })
        
        if drainage_area_path is None:
            # Use a default path if not provided
            drainage_area_path = os.path.splitext(flow_accum_path)[0] + "_da.tif"
        # Save the drainage area raster
        with rasterio.open(drainage_area_path, 'w', **drainage_meta) as dst:
            dst.write(drainage_area.astype(rasterio.float32), 1)

    print(f"Drainage area raster created at {drainage_area_path}.")

    # Step 2: Load Streams and Assign Drainage Area
    try:
        gdf = gpd.read_file(segmented_CL_path)
        print("GeoPackage loaded successfully.")
    except Exception as e:
        print(f"Failed to read GeoPackage: {e}")
        # Optionally, exit or handle the error
        exit(1)


    # Open the drainage area raster
    with rasterio.open(drainage_area_path) as da_src:
        drainage_crs = da_src.crs
        
        # Reproject the GeoDataFrame if needed
        if gdf.crs != drainage_crs:
            print("Reprojecting GeoDataFrame to match raster CRS.")
            gdf = gdf.to_crs(drainage_crs)
        
        drainage_areas = []
        
        for idx, row in gdf.iterrows():
            line = row.geometry
            
            # Create a buffer around the line
            buffer_geom = line.buffer(buffer_distance)
            
            # Ensure geometry is valid for masking
            if buffer_geom.is_empty:
                drainage_areas.append(np.nan)
                continue
            
            try:
                # Mask the drainage area raster using the buffered geometry
                out_image, out_transform = mask(da_src, [buffer_geom], crop=True)
                
                # Extract valid values (non-nodata) from the masked raster
                valid_data = out_image[0]
                valid_data = valid_data[~np.isnan(valid_data)]
                
                if valid_data.size > 0:
                    # Calculate the maximum drainage area within the buffer
                    max_drainage_area = np.max(valid_data)
                else:
                    max_drainage_area = np.nan
            except Exception as e:
                print(f"Error processing feature {idx}: {e}")
                max_drainage_area = np.nan
            
            # Append the calculated drainage area
            drainage_areas.append(max_drainage_area)
        
        # Add the new 'DA' column to the GeoDataFrame
        gdf['DA'] = drainage_areas

    # Step 3: Save the Updated GeoDataFrame to a Shapefile
    # Ensure the output directory exists
    if output_gpkg is None:
        output_gpkg = os.path.splitext(segmented_CL_path)[0] + "_DA.gpkg"
    output_dir = os.path.dirname(output_gpkg)
    os.makedirs(output_dir, exist_ok=True)

    gdf.to_file(output_gpkg, driver="GPKG")

    print(f"Drainage areas calculated and saved to {output_gpkg}.")

if __name__ == "__main__":
    # Input file paths
    segmented_CL_path = r"Y:\ATD\GIS\Valley Bottom Testing\Control Valleys\Stream\VBET_Segmented\Segmented_Centerline.shp"
    output_gpkg = r"Y:\ATD\GIS\Valley Bottom Testing\Control Valleys\Stream\VBET_Segmented\Segmented_Centerline_DA.shp"
    flow_accum_path = r"Y:\ATD\GIS\Valley Bottom Testing\Control Valleys\Terrain\Individual\WBT_Outputs\flow_accumulation.tif"
    drainage_area_path = r"Y:\ATD\GIS\Valley Bottom Testing\Control Valleys\Terrain\Individual\WBT_Outputs\drainage_area.tif"
    add_drainage_area_to_streams(flow_accum_path, segmented_CL_path, output_gpkg, drainage_area_path)