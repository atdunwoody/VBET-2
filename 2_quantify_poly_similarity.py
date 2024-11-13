#!/usr/bin/env python3

import geopandas as gpd
import argparse
import os
import sys
from shapely.geometry import Polygon, MultiPolygon

def load_polygon(gpkg_path):
    """
    Loads the first polygon from a GeoPackage.

    Parameters:
        gpkg_path (str): Path to the GeoPackage file.

    Returns:
        shapely.geometry.Polygon or MultiPolygon: The geometry of the first feature.

    Raises:
        ValueError: If no polygon is found in the GeoPackage.
    """
    try:
        gdf = gpd.read_file(gpkg_path)
    except Exception as e:
        raise ValueError(f"Error reading {gpkg_path}: {e}")

    if gdf.empty:
        raise ValueError(f"No features found in {gpkg_path}.")

    # Iterate through features to find the first polygon
    for idx, row in gdf.iterrows():
        geom = row.geometry
        if isinstance(geom, (Polygon, MultiPolygon)):
            return geom

    raise ValueError(f"No polygon geometries found in {gpkg_path}.")

def compute_iou(poly1, poly2):
    """
    Computes the Intersection over Union (IoU) between two polygons.

    Parameters:
        poly1 (shapely.geometry.Polygon or MultiPolygon): First polygon.
        poly2 (shapely.geometry.Polygon or MultiPolygon): Second polygon.

    Returns:
        float: IoU value between 0 and 1.
    """
    if not poly1.is_valid:
        poly1 = poly1.buffer(0)
    if not poly2.is_valid:
        poly2 = poly2.buffer(0)

    intersection = poly1.intersection(poly2).area
    union = poly1.union(poly2).area

    if union == 0:
        return 0.0

    iou = intersection / union
    return iou

def find_most_similar(template_gpkg, test_gpkgs, metric='iou'):
    """
    Finds the most similar GeoPackage to the template based on the specified metric.

    Parameters:
        template_gpkg (str): Path to the template GeoPackage.
        test_gpkgs (list of str): List of paths to test GeoPackages.
        metric (str): Similarity metric to use ('iou').

    Returns:
        str: Path to the most similar GeoPackage.

    Raises:
        ValueError: If an unsupported metric is specified.
    """
    # Load template polygon
    try:
        template_poly = load_polygon(template_gpkg)
    except ValueError as e:
        print(f"Error loading template GeoPackage: {e}")
        sys.exit(1)

    best_score = -1  # Initialize with a value lower than the minimum possible IoU
    most_similar_path = None

    for test_path in test_gpkgs:
        if not os.path.isfile(test_path):
            print(f"Warning: Test GeoPackage '{test_path}' does not exist. Skipping.")
            continue

        try:
            test_poly = load_polygon(test_path)
        except ValueError as e:
            print(f"Warning: {e} Skipping '{test_path}'.")
            continue

        if metric == 'iou':
            score = compute_iou(template_poly, test_poly)
        else:
            raise ValueError(f"Unsupported metric '{metric}'. Supported metrics: 'iou'.")

        print(f"Computed IoU for '{test_path}': {score:.4f}")

        if score > best_score:
            best_score = score
            most_similar_path = test_path

    if most_similar_path is None:
        print("No valid test GeoPackages were processed.")
        sys.exit(1)

    return most_similar_path


def main():
    template_gpkg = 'data/template.gpkg'
    test_gpkgs = ['data/test1.gpkg', 'data/test2.gpkg']
    metric = 'iou'

    most_similar = find_most_similar(template_gpkg, test_gpkgs, metric=metric)

    print("\nMost similar GeoPackage:")
    print(most_similar)

if __name__ == "__main__":
    main()
