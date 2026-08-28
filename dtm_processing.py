from pathlib import Path
import shutil
import zipfile
import re

import geopandas as gpd
import numpy as np
import rasterio
from rasterio.merge import merge
from rasterio.mask import mask
from shapely.geometry import mapping


NODATA = -9999.0


def extract_download(zip_path, extract_dir):
    """Clean extraction directory and extract DNR download."""

    if extract_dir.exists():
        shutil.rmtree(extract_dir)

    print(f"\nExtracting {zip_path}...")
    with zipfile.ZipFile(zip_path, "r") as z:
        z.extractall(extract_dir)

    return extract_dir


def find_dtm_projects(extract_dir):
    """Find project-level DTM directories in DNR download."""

    dtm_dirs = sorted(
        p for p in extract_dir.rglob("dtm")
        if p.is_dir()
    )

    if not dtm_dirs:
        raise FileNotFoundError(
            f"No DTM directories found under {extract_dir}"
        )

    return dtm_dirs


def process_project(dtm_dir, aoi, output_dir, custom_file_stem=None):
    """Merge and crop one DNR DTM project.
    Optionally define custom file stem (helpful for batch processing naming convention)
    """

    project_name = dtm_dir.parent.name
    tif_files = sorted(dtm_dir.glob("*.tif"))

    if not tif_files:
        print(f"No TIFFs found for {project_name} -- skipping.")
        return

    print("\n" + "=" * 70)
    print(f"Processing: {project_name}")
    print("=" * 70)
    print(f"Found {len(tif_files)} DTM tile(s).")

    # Open all tiles belonging to this project
    srcs = [rasterio.open(tif) for tif in tif_files]

    try:
        project_crs = srcs[0].crs

        if project_crs is None:
            raise ValueError(
                f"{project_name} does not have a defined CRS."
            )

        print(f"Native CRS: {project_crs}")
        print(f"Resolution: {srcs[0].res}")
        print(f"Source NoData: {srcs[0].nodata}")

        # Make sure tiles within this project use the same CRS
        for src in srcs[1:]:
            if src.crs != project_crs:
                raise ValueError(
                    f"CRS mismatch within {project_name}:\n"
                    f"{src.name}"
                )

        # Reproject AOI to native project CRS
        project_aoi = aoi.to_crs(project_crs)
        aoi_geometry = project_aoi.geometry.union_all()

        # --------------------------------------------------
        # Merge only the rectangular area surrounding AOI
        # --------------------------------------------------

        mosaic, mosaic_transform = merge(
            srcs,
            bounds=aoi_geometry.bounds,
            nodata=NODATA,
            dtype="float32",
            masked=True,
        )

        mosaic = mosaic.filled(NODATA).astype("float32")

        profile = srcs[0].profile.copy()
        profile.update(
            dtype="float32",
            nodata=NODATA,
            height=mosaic.shape[1],
            width=mosaic.shape[2],
            transform=mosaic_transform,
            compress="deflate",
        )

    finally:
        for src in srcs:
            src.close()

    # --------------------------------------------------
    # Exact polygon crop
    # --------------------------------------------------

    # Rasterio mask() expects a raster dataset, so write only
    # the small AOI-bounded mosaic rather than the full project.
    temp_path = output_dir / f"_{project_name}_temp.tif"

    with rasterio.open(temp_path, "w", **profile) as dst:
        dst.write(mosaic)

    del mosaic

    with rasterio.open(temp_path) as src:
        cropped, cropped_transform = mask(
            src,
            [mapping(aoi_geometry)],
            crop=True,
            nodata=NODATA,
            filled=True,
        )

        cropped_profile = src.profile.copy()
        cropped_profile.update(
            height=cropped.shape[1],
            width=cropped.shape[2],
            transform=cropped_transform,
            nodata=NODATA,
            compress="deflate",
        )

    temp_path.unlink()

    # Check result
    valid = cropped[cropped != NODATA]

    if valid.size == 0:
        print("No valid DTM pixels within AOI -- skipping.")
        return

    print(f"Valid pixels:    {valid.size:,}")
    print(f"Elevation min:   {valid.min():.2f}")
    print(f"Elevation max:   {valid.max():.2f}")
    print(f"Elevation mean:  {valid.mean():.2f}")

    # Write final project DTM
    # by default name with project name
    if custom_file_stem is None:
        output_path = output_dir / f"{project_name}_dtm.tif"

    else:
        # Extract four-digit year from DNR project name
        year_match = re.search(r"(?:19|20)\d{2}", project_name)

        if not year_match:
            raise ValueError(
                f"Could not extract year from DNR project name: {project_name}"
            )

        project_year = year_match.group()
        output_path = output_dir / f"{custom_file_stem}_dtm_{project_year}.tif"

    with rasterio.open(output_path, "w", **cropped_profile) as dst:
        dst.write(cropped)

    print(f"Saved: {output_path}")


def process_dtms(zip_path, aoi_path, output_dir, custom_file_stem=None):
    """Extract, merge, and crop DNR DTMs project-by-project."""

    zip_path = Path(zip_path)
    aoi_path = Path(aoi_path)
    output_dir = Path(output_dir)

    # Temporary extraction sits beside ZIP
    extract_dir = zip_path.parent / "custom_download"

    output_dir.mkdir(parents=True, exist_ok=True)

    # Read AOI once
    aoi = gpd.read_file(aoi_path)

    if aoi.empty:
        raise ValueError("AOI contains no features.")

    if aoi.crs is None:
        raise ValueError("AOI does not have a defined CRS.")

    # Extract current download
    extract_download(zip_path, extract_dir)

    # Find independent DNR projects
    dtm_dirs = find_dtm_projects(extract_dir)

    print(f"\nFound {len(dtm_dirs)} DTM project(s):")
    for dtm_dir in dtm_dirs:
        print(f"- {dtm_dir.parent.name}")

    # Process each project independently
    for dtm_dir in dtm_dirs:
        process_project(dtm_dir, aoi, output_dir, custom_file_stem=custom_file_stem)

    print("\nFinished processing DTMs.")