from pathlib import Path

from dnr_download import (
    read_aoi_for_dnr,
    query_datasets,
    get_dtms,
    choose_projects,
    download_datasets,
)

from dtm_processing import process_dtms



# --------------------------------------------------
# Input Paths MODIFY ME FOR YOUR PREFERRED PATHS!
# --------------------------------------------------

AOI = Path("data/my_aoi.shp")
ZIP = Path("downloads/custom_download.zip")
OUTPUT = Path("cropped_dtms")


# --------------------------------------------------
# Main Block
# --------------------------------------------------

def main():

    # --------------------------------------------------
    # Query DNR
    # --------------------------------------------------

    aoi_geojson = read_aoi_for_dnr(AOI)
    datasets = query_datasets(aoi_geojson)
    dtms = get_dtms(datasets)
    selected_dtms = choose_projects(dtms)
    download_datasets(
        aoi_geojson,
        selected_dtms,
        ZIP
    )
    # --------------------------------------------------
    # Merge/Clip DTM
    # --------------------------------------------------

    process_dtms(
        zip_path=ZIP,
        aoi_path=AOI,
        output_dir=OUTPUT
    )

if __name__ == "__main__":
    main()
