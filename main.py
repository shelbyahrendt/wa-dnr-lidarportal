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
# Input Paths MODIFY ME FOR YOUR PREFERRED PATHS!
# --------------------------------------------------

AOI = Path("data/my_aoi.shp")
DOWNLOAD_ZIP = Path("downloads/custom_download.zip")
OUTPUT_DIR = Path("cropped_dtms")


# Main Block
# Do not alter unless doing dev

def main():

    # Query DNR portal
    aoi_geojson = read_aoi_for_dnr(AOI)
    datasets = query_datasets(aoi_geojson)
    # Break if no data in AOI
    if not datasets:
        return

    dtms = get_dtms(datasets)
    selected_products = choose_products(dtms)


    download_datasets(
        aoi_geojson,
        selected_products,
        DOWNLOAD_ZIP
    )

    # Merge and Clip DTM

    process_dtms(
        zip_path=DOWNLOAD_ZIP,
        aoi_path=AOI,
        output_dir=OUTPUT_DIR
    )

if __name__ == "__main__":
    main()
