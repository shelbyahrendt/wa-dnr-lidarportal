# WA DNR LidarPortal

This repository interfaces with the Washingotn DNR Lidar Portal (https://lidarportal.dnr.wa.gov/) for direct download and processing of lidar-derived products based on a user-defined AOI.

## Installation

Install with conda:

Clone the repository to your local machine:

```bash
git clone https://github.com/shelbyahrendt/wa-dnr-lidarportal.git
cd wa-dnr-lidarportal
```

Create the conda environment (this may take several minutes):

```bash
conda env create -f environment.yml
```

Activate the environment:

```bash
conda activate wa-dnr-portal
```

## Test Installation

Test the install by running the workflow on the example AOI included in `data/my_aoi.shp`. This AOI is located adjacent to the Nooksack River in the region of the Clay Banks landslide complex.

1. Navigate to the root directory. Check your env is activated.
2. Run `python main.py`
3. Check that you now have a series of seven DTMS in `cropped_DTMS` which correspond to all available lidar-derived DTM products in `my_aoi.shp`.

## Download DTMs for your AOI

1. Create a `.shp` or `.gpkg` file with a polygon AOI (any crs will do)
2. Save this in `data` (or your preferred dir)
3. Modify the `AOI` Path variable in `main.py` to point to the location of this shapefile or geopackage.
4. Modify the `OUTPUT` Path variable in `main.py` to point to your preferred download folder. 
* (Note: the `custom_download` folder will be overwritten with each run. This is preferred as the WA DNR tiles can be gigantic and we don't want to start accumulating a surplus of large data files.)