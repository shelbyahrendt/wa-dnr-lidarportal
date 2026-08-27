import warnings
import requests

import geopandas as gpd
import json


def read_aoi_for_dnr(aoi_path):
    """Read AOI, check consistency with DNR query inputs
    and return EPSG:4326 GeoJSON.

    Parameters
    ----------
    aoi_path : Path
        Path to the AOI shapefile.

    Returns
    -------
    aoi_geojson : str
        GeoJSON formatted representation of the AOI.
    """

    aoi = gpd.read_file(aoi_path)
    if aoi.empty:
        raise ValueError("AOI contains no features.")
    
    if aoi.crs is None:
        raise ValueError("AOI does not have a defined CRS.")
    
    # print(f"Input AOI CRS: {aoi.crs}")

    # Convert AOI to WGS84 for DNR API
    aoi_wgs84 = aoi.to_crs(epsg=4326)

    #Combine multiple features into one geometry
    aoi_geometry = aoi_wgs84.geometry.union_all()

    # Handle bad aoi from empty file
    if aoi_geometry.is_empty:
        raise ValueError("AOI geometry is empty.")
    
    # Raise warning for MultiPolygon
    # I'm not sure if this will work with portal given their
    # user interface is built off bounding box
    if aoi_geometry.geom_type == 'MultiPolygon':
        warnings.warn(
            "AOI geometry is a MultiPolygon"
            "MultiPolygons is not tested with lidar portal"
            "Query/download may fail: "
            "If so, reduce AOI to singular polygon"
        )

    # Format GeoJSON
    aoi_geojson = json.dumps(aoi_geometry.__geo_interface__)

    return aoi_geojson


def query_datasets(aoi_geojson):
    """Query DNR for datasets intersecting the AOI."""

    print("\nQuerying DNR LiDAR portal for datasets...")

    query_url = "https://lidarportal.dnr.wa.gov/query"
    
    response = requests.post(
        query_url,
        data={"geojson": aoi_geojson},
        timeout=60,
    )

    # Raise HTTPError if one occured
    response.raise_for_status()
    # If this returns data, it means the query was successful
    datasets = response.json()

    # If no data is returned, there is no lidar data available
    if not datasets:
        print("\nNo DNR LiDAR data available within the AOI.")
        return []

    # Parse dataset available for each project
    projects = {}
    for dataset in datasets:
        project_name = dataset["project_name"]
        dataset_name = dataset["dataset_name"]

        if project_name not in projects:
            projects[project_name] = []

        projects[project_name].append(dataset_name)

    # Print summary
    print("\nAvailable DNR projects:")
    print("-" * 70)

    for project_name, data_types in projects.items():
        print(f"- {project_name}")
        print(f"    Products: {', '.join(data_types)}")

    return datasets


def get_dtms(datasets):
    """Return only DTM products."""
    # Find DTM products only 
    # NOTE: anticipate superceding this for general download
    # For now, we only want DTM products
    dtms = [
        d for d in datasets
        if d["dataset_name"].strip().upper() == "DTM"
    ]

    if not dtms:
        print("\nDNR data are available, but no DTMs were found within the AOI.")

    # Print DTM summary
    print("\nDTM Product Info:")
    print("-" * 70)

    for d in dtms:
        size_gb = d["bytes"] / 1e9

        print(
            f"- {d['project_name']:<35} "
            f"ID: {d['dataset_id']:<6} "
            f"Files: {d['files']:<4} "
            f"Size: {size_gb:.2f} GB"
        )
    return dtms

def choose_products(products):
    """Interactively select projects for a lidarportal product."""

    if not products:
        return []

    product_name = products[0]["dataset_name"]

    # Ask user which projects to download
    while True:
        choice = input(
            "\nSelect project(s) by number (e.g. 1,2), or type all: "
        ).strip().lower()

        # Select everything
        if choice == "all":
            selected_products = products
            break

        # Otherwise parse comma-separated numbers
        try:
            indices = [int(x.strip()) for x in choice.split(",")]

            # Validate selections
            if not indices:
                raise ValueError
            if any(i < 1 or i > len(products) for i in indices):
                raise ValueError

            # Remove duplicates while preserving order
            indices = list(dict.fromkeys(indices))

            # Identify selected products from indices
            selected_products = [products[i - 1] for i in indices]
            break

        except ValueError:
            print("Invalid selection. Enter something like '1', '1,3', or all.")

    # Print selected project info
    print(f"\nSelected {product_name} projects:")
    print("-" * 75)

    for d in selected_products:
        size_gb = d["bytes"] / 1e9
        print(
            f"- {d['project_name']:<35} "
            f"ID: {d['dataset_id']:<6} "
            f"Files: {d['files']:<4} "
            f"Size: {size_gb:.2f} GB"
        )

    # Calculate total download size and number of files
    total_bytes = sum(d["bytes"] for d in selected_products)
    total_files = sum(d["files"] for d in selected_products)
    total_gib = total_bytes / 1024**3
    total_gb = total_bytes / 1e9

    # Print summary
    print("-" * 75)
    print(f"Total files:          {total_files}")
    print(f"Estimated download:   {total_gib:.2f} GiB ({total_gb:.2f} GB)")
    print("-" * 75)

    # Confirm selection
    answer = input("\nProceed with selection? [y/N]: ").strip().lower()

    if answer not in ("y", "yes"):
        print("Selection cancelled.")
        raise SystemExit

    return selected_products


def download_datasets(geojson, selected_products, output_zip):
    """Download selected datasets from DNR."""

    download_url = "https://lidarportal.dnr.wa.gov/download"

    # Check we have a folder for our output zip file
    output_zip.parent.mkdir(parents=True, exist_ok=True)

    # Convert selected products to comma-separated dataset IDs
    dataset_ids = ",".join(str(d["dataset_id"]) for d in selected_products)

    print("\nRequesting DNR download...")
    print("-" * 75)
    print(f"Dataset IDs: {dataset_ids}")

    params = {
        "geojson": geojson,
        "ids": dataset_ids,
    }

    with requests.get(
        download_url,
        params=params,
        stream=True,
        timeout=300,
    ) as response:

        # Check for errors
        response.raise_for_status()

        content_length = int(response.headers.get("content-length", 0))
        downloaded = 0

        with open(output_zip, "wb") as f:
            for chunk in response.iter_content(chunk_size=1024*1024):
                if not chunk:
                    continue

                f.write(chunk)
                downloaded += len(chunk)

                if content_length:
                    percent = 100 * downloaded / content_length
                    print(
                        f"\rDownloading: "
                        f"{downloaded / 1e9:.2f} GB "
                        f"({percent:.2f}%)",
                        end="",
                        flush=True
                    )

        print("\nDownload complete.")
        print(f"Saved to: {output_zip.resolve()}")
