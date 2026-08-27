# WA DNR LidarPortal

This repository interfaces with the Washington DNR LiDAR Portal ([https://lidarportal.dnr.wa.gov/](https://lidarportal.dnr.wa.gov/)) for direct download and processing of lidar-derived products based on a user-defined AOI.

## Installation

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

Test the installation by running the workflow on the example AOI included at `data/my_aoi.shp`. This AOI is located adjacent to the Nooksack River in the region of the Clay Banks landslide complex.

Navigate to the repository root and confirm that the `wa-dnr-portal` environment is activated:

```bash
conda activate wa-dnr-portal
```

Run the workflow:

```bash
python main.py
```

The WA DNR LiDAR Portal will be queried for available data. Follow the interactive prompts to select the DTM projects to download.

After processing is complete, check `cropped_DTMs/` for the resulting cropped DTMs corresponding to the selected lidar projects.

## Download DTMs for Your AOI

Create a `.shp` or `.gpkg` file containing your polygon AOI. The AOI can use any defined CRS.

Save the AOI in `data/` (or another directory of your choice).

In `main.py`, modify the `AOI` path to point to your file:

```python
AOI = Path("data/my_aoi.shp")
```

Modify the `OUTPUT` path to specify where processed DTMs should be saved:

```python
OUTPUT = Path("cropped_DTMs")
```

Run the workflow:

```bash
python main.py
```

The program will:

1. Query the WA DNR LiDAR Portal for projects intersecting the AOI.
2. Display available lidar-derived products.
3. Prompt you to select which DTM projects to download.
4. Download the required DNR tiles.
5. Merge tiles belonging to the same lidar project.
6. Crop each project DTM to the exact AOI polygon.
7. Save the resulting DTMs to the output directory.

> **Note:** The temporary `custom_download` data are overwritten with each run. WA DNR source tiles can be very large, so retaining these files can quickly consume substantial disk space.