import warnings

import geopandas as gpd
import json


def read_aoi_for_dnr(aoi_path):
    """Read AOI and return EPSG:4326 GeoJSON."""

    aoi = gpd.read_file(aoi_path)
    if aoi.empty:
        raise ValueError("AOI contains no features.")
    
    if aoi.crs is None:
        raise ValueError("AOI does not have a defined CRS.")
    
    print(f"Input AOI CRS: {aoi.crs}")

    # Convert AOI to WGS84 for DNR API
    aoi_wgs84 = aoi.to_crs(epsg=4326)

    #Combine multiple features into one geometry
    aoi_geometry = aoi_wgs84.geometry.union_all()

    if aoi_geometry.is_empty:
        raise ValueError("AOI geometry is empty.")

    if aoi_geometry.geom_type == 'MultiPolygon':
        warnings.warn(
            "AOI geometry is a MultiPolygon"
            "MultiPolygons is not tested with lidar portal"
            "Query/download may fail: "
            "If so, reduce AOI to singular polygon"
        )

    

    aoi_geojson = json.dumps(aoi_geometry.__geo_interface__)

    return aoi_geojson


def query_datasets(aoi_geojson):
    """Query DNR for datasets intersecting the AOI."""
    ...


def get_dtms(datasets):
    """Return only DTM products."""
    ...


def choose_projects(dtms):
    """Interactive project selection."""
    ...


def download_datasets(geojson, selected_dtms, output_zip):
    """Download selected datasets from DNR."""
    ...