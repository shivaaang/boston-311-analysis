# Boston 311 Data Cleaning and Preparation Pipeline

![Python 3.11](https://img.shields.io/badge/Python-3.11-blue.svg)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
![Libraries](https://img.shields.io/badge/Libraries-Pandas%20%7C%20GeoPandas%20%7C%20Plotly-green.svg)
![Jupyter Notebook](https://img.shields.io/badge/Jupyter-Notebook-orange?logo=jupyter)
![Parquet](https://img.shields.io/badge/Data%20Format-Parquet-informational?logo=apacheparquet)

This repository contains the complete, reproducible data pipeline for acquiring, cleaning, and preparing over 2.5 million Boston 311 service requests from 2015 to 2024. The primary goal of this phase was to address significant data quality issues, particularly the recovery of over 660,000 records with missing location data, to create a robust, analysis-ready dataset.

**Project Status:** Data Acquisition and Cleaning phase is **complete**. The final output is a single, cleaned Parquet file located at `data/processed/boston_311_cleaned.parquet`.

---
## Key Features

* **Automated Data Acquisition**: Scripts automatically download ten years of 311 service request data and all required geospatial shapefiles from their official sources. The scripts are idempotent, checking for existing files before downloading.
* **Comprehensive Data Cleaning**: The `01_data_cleaning.ipynb` notebook merges all yearly files, standardizes data types, removes redundant columns, and handles systematic inconsistencies in the raw data.
* **Advanced Geospatial Imputation**: A multi-stage spatial imputation process was used to recover critical location data for records with valid coordinates:
    * **ZIP Codes**: Imputed for **551,260** records using a point-in-polygon join with a custom-filtered Massachusetts ZCTA shapefile.
    * **Street Names**: Imputed for **10,315** records using a nearest-neighbor join against the official Boston SAM address point database.
    * **Neighborhoods**: Imputed and standardized for **98,801** records using a point-in-polygon join with official neighborhood boundaries.
* **Rigorous Validation**: The accuracy of all geospatial data sources was confirmed through a suite of test notebooks that verify known locations against the shapefiles.
* **Reproducible Environment**: The project includes an `environment.yml` file to ensure the analysis can be reproduced reliably with all necessary dependencies.

---
## Folder Structure

The project is organized to separate raw data, processed data, notebooks, and scripts for clarity and reproducibility.

```
BOSTON-311-ANALYSIS/
│
├── .gitignore
├── environment.yml
├── README.md
│
├── data/
│   ├── processed/
│   │   ├── boston_311_cleaned.parquet
│   │   ├── (↓ these Parquets will be generated here by the script)
│   │   ├── boston_neighborhood_boundaries.parquet
│   │   ├── live_street_address_management_sam_addresses.parquet
│   │   └── massachusetts_zip_boundaries.parquet
│   └── raw/
│       └── (CSVs will be downloaded here by the script)
│
├── notebooks/
│   ├── 01_data_cleaning.ipynb
│   └── test_geocode/
│       ├── 00_test_geocode_neighborhood.ipynb
│       ├── 00_test_geocode_street_name.ipynb
│       └── 00_test_geocode_zip.ipynb
│
└── scripts/
    ├── 01_fetch_311_data.py
    └── 02_prepare_geodata.py
```

---
## How to Run This Project

To reproduce the data preparation pipeline, follow these steps:

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/shivaaang/boston-311-analysis.git
    cd boston-311-analysis
    ```

2.  **Create and activate the Conda environment:** This will install all the required packages listed in `environment.yml`.
    ```bash
    conda env create -f environment.yml
    conda activate boston311
    ```

3.  **Run the main notebook:** The entire data pipeline is orchestrated within the main Jupyter Notebook. Open and run all the cells in `notebooks/01_data_cleaning.ipynb`. The notebook will automatically:
    * Execute the necessary scripts to download all raw 311 data and geospatial files.
    * Perform all cleaning, imputation, and processing steps.
    * Save the final, analysis-ready dataset to `data/processed/boston_311_cleaned.parquet`.

---
## Data Sources

* **Boston 311 Service Requests (2015-2024)**: [Analyze Boston Open Data Portal](https://data.boston.gov/dataset/311-service-requests)
* **Geospatial Data (ZIP Codes, State Boundaries)**: [U.S. Census Bureau TIGER/Line Shapefiles](https://www.census.gov/geographies/mapping-files/time-series/geo/tiger-line-file.html)
* **Geospatial Data (Neighborhoods, SAM Addresses)**: [Analyze Boston Open Data Portal](https://data.boston.gov)