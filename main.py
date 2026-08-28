from pathlib import Path

from dnr_download import (
    read_aoi_for_dnr,
    query_datasets,
    get_dtms,
    choose_products,
    download_datasets,
)

from dtm_processing import process_dtms


# --------------------------------------------------
# Input: MODIFY ME FOR YOUR PREFERRED PATHS!
# --------------------------------------------------

# Define portal, should work with Alaska or Washington
# only tested with WA
PORTAL_URL = "https://lidarportal.dnr.wa.gov"
# PORTAL_URL = "https://elevation.alaska.gov" #UNTESTED!!

# AOI = Path("data/my_aoi.shp") # test with .shp
AOI = Path("data/nooksack1_AOI.kmz") # test with .kmz
DOWNLOAD_ZIP = Path("downloads/custom_download.zip") #this will get created, temp folder to dump downloads
OUTPUT_DIR = Path("cropped_dtms") #this will get created, final output folder for cropped dtms
# optionally set a target crs to ensure all our cropped DTMs are in same crs (for crude DoD or something)
# WA DNR crs is sometimes documented differently between datasets, usually 2927-ish thing, but let's make this consistent
# set to None if want to keep native crs
TARGET_CRS = "EPSG:2927"
# TARGET_CRS = None

# Optional custom output naming: helpful when you want to batch process a bunch of AOIs
# SET TO NONE IF YOU JUST WANT DEFAULTS! (your cropped tiffs will be named with DNR project name)
# Here I like to use the preface of my AOI files to associate cropped output
# Note: your AOIs have to end with `_AOI` for this to work, but you can modify the naming convention as needed
# CUSTOM_FILE_STEM = AOI.stem.removesuffix("_AOI")
CUSTOM_FILE_STEM = None 

# --------------------------------------------------
# Main Block (do not alter unless doing dev)
# --------------------------------------------------

def main():

    # Query DNR portal
    aoi_geojson = read_aoi_for_dnr(AOI)
    datasets = query_datasets(aoi_geojson, PORTAL_URL)
    # Break if no data in AOI
    if not datasets:
        return

    dtms = get_dtms(datasets)
    selected_products = choose_products(dtms)


    download_datasets(
        aoi_geojson,
        PORTAL_URL,
        selected_products,
        DOWNLOAD_ZIP
    )

    # Merge and Clip DTM

    process_dtms(
        zip_path=DOWNLOAD_ZIP,
        aoi_path=AOI,
        output_dir=OUTPUT_DIR,
        custom_file_stem=CUSTOM_FILE_STEM,
        target_crs=TARGET_CRS
    )

if __name__ == "__main__":
    main()
