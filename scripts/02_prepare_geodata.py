import geopandas as gpd
import requests
import zipfile
import os
import shutil
from pathlib import Path
import urllib3
from tqdm import tqdm

# Suppress the InsecureRequestWarning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# --- Configuration ---
RAW_DATA_DIR = Path("../data/raw")
PROCESSED_DATA_DIR = Path("../data/processed")

# Ensure these directories exist
RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)


def download_with_progress(url, destination_path, description):
    """Downloads a file with a TQDM progress bar."""
    response = requests.get(url, verify=False, stream=True)
    response.raise_for_status()
    
    total_size = int(response.headers.get('content-length', 0))
    block_size = 1024  # 1 KB
    
    with open(destination_path, 'wb') as file, tqdm(
        desc=description,
        total=total_size,
        unit='iB',
        unit_scale=True,
        unit_divisor=1024,
    ) as bar:
        for chunk in response.iter_content(chunk_size=block_size):
            file.write(chunk)
            bar.update(len(chunk))

def process_single_shapefile(name, info_url, download_url):
    """
    Handles simple cases: checks for a GeoParquet file, and if not found,
    downloads a single zip, converts it, and cleans up.
    """
    output_filename = f"{name}.parquet"
    processed_path = PROCESSED_DATA_DIR / output_filename
    
    print(f"> CHECKING for '{output_filename}' in '{PROCESSED_DATA_DIR}'.")
    
    if processed_path.exists():
        print(f"> FOUND '{output_filename}'.")
        return

    print(f"> NOT FOUND '{output_filename}'.")
    print(f"> DOWNLOADING '{name}' shapefile from Analyze Boston...")
    print(f"  (More info here: {info_url})")
    
    zip_path = RAW_DATA_DIR / f"{name}.zip"
    download_with_progress(download_url, zip_path, name)
    
    print(f"> DOWNLOADED '{name}' shapefile ZIP to '{RAW_DATA_DIR}'")

    unzip_dir = RAW_DATA_DIR / name
    print(f"> UNZIPPING '{name}'")
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(unzip_dir)
        
    try:
        shp_path = next(unzip_dir.glob("*.shp"))
    except StopIteration:
        print(f"  ERROR: No .shp file found in the unzipped folder for {name}.")
        return

    print("> CREATING GeoParquet")
    gdf = gpd.read_file(shp_path)
    gdf.to_parquet(processed_path)
    print(f"> SAVING '{output_filename}' to '{PROCESSED_DATA_DIR}'")

    print("> DELETING raw data and ZIP File")
    os.remove(zip_path)
    shutil.rmtree(unzip_dir)


def filter_zips_by_state(zcta_shp_path, state_shp_path, state_abbr='MA'):
    """
    Loads national ZCTA and States shapefiles, filters ZCTAs for the
    given state, and returns the filtered GeoDataFrame.
    """
    print(f"> FILTERING Shapefile for {state_abbr} ZIPS")
    zctas_gdf = gpd.read_file(zcta_shp_path)
    states_gdf = gpd.read_file(state_shp_path)
    
    state_boundary = states_gdf[states_gdf['STUSPS'] == state_abbr]
    zctas_gdf = zctas_gdf.to_crs(state_boundary.crs)
    state_zctas = gpd.sjoin(zctas_gdf, state_boundary, how="inner", predicate="intersects")
    
    cols_to_drop = [c for c in state_boundary.columns if c != 'geometry'] + ['index_right']
    state_zctas = state_zctas.drop(columns=cols_to_drop)
    
    return state_zctas


def prepare_mass_zips_data():
    """
    Orchestrates the creation of the Massachusetts-specific zip code file.
    """
    name = "massachusetts_zip_boundaries"
    output_filename = f"{name}.parquet"
    processed_path = PROCESSED_DATA_DIR / output_filename

    print(f"> CHECKING for '{output_filename}' in '{PROCESSED_DATA_DIR}'.")
    if processed_path.exists():
        print(f"> FOUND '{output_filename}'.")
        return
    print(f"> NOT FOUND '{output_filename}'.")

    sources = {
        'zcta': {
            'name': 'tl_2024_us_zcta520',
            'url': 'https://www2.census.gov/geo/tiger/TIGER2024/ZCTA520/tl_2024_us_zcta520.zip',
            'print_name': 'ZIP Code Tabulation Areas'
        },
        'state': {
            'name': 'tl_2024_us_state',
            'url': 'https://www2.census.gov/geo/tiger/TIGER2024/STATE/tl_2024_us_state.zip',
            'print_name': 'State Boundaries'
        }
    }
    info_url = "https://www.census.gov/geographies/mapping-files/time-series/geo/tiger-line-file.html"
    
    downloaded_paths = {}
    for key, source in sources.items():
        print(f"> DOWNLOADING {source['print_name']} from US Census Bureau")
        print(f"  (More info here: {info_url})")
        
        zip_path = RAW_DATA_DIR / f"{source['name']}.zip"
        download_with_progress(source['url'], zip_path, source['name'])
        
        print(f"> DOWNLOADED '{source['name']}.zip' shapefile ZIP to '{RAW_DATA_DIR}'")
        downloaded_paths[key] = {'zip': zip_path, 'unzip_dir': RAW_DATA_DIR / source['name']}

    for key, paths in downloaded_paths.items():
        print(f"> UNZIPPING '{sources[key]['name']}'")
        with zipfile.ZipFile(paths['zip'], 'r') as zip_ref:
            zip_ref.extractall(paths['unzip_dir'])
    
    zcta_shp_path = next(downloaded_paths['zcta']['unzip_dir'].glob("*.shp"))
    state_shp_path = next(downloaded_paths['state']['unzip_dir'].glob("*.shp"))
    
    mass_zips_gdf = filter_zips_by_state(zcta_shp_path, state_shp_path, 'MA')

    print("> CREATING GeoParquet")
    mass_zips_gdf.to_parquet(processed_path)
    print(f"> SAVING '{output_filename}' to '{PROCESSED_DATA_DIR}'")
    
    for key, paths in downloaded_paths.items():
        print(f"> DELETING raw data and ZIP file for '{sources[key]['name']}'")
        os.remove(paths['zip'])
        shutil.rmtree(paths['unzip_dir'])


def main():
    """
    Main function to process all required geospatial datasets.
    """
    print("--- Preparing Geospatial Data ---")
    
    prepare_mass_zips_data()
    print("-" * 30)
    process_single_shapefile(
        name="boston_neighborhood_boundaries",
        info_url="https://data.boston.gov/dataset/bpda-neighborhood-boundaries",
        download_url="https://data.boston.gov/dataset/bf1a7b50-4c72-4637-b0fa-11d632e3aff1/resource/f6be6d34-7813-4b55-955d-4b2c236243d6/download/boston_neighborhood_boundaries.zip"
    )
    print("-" * 30)
    process_single_shapefile(
        name="live_street_address_management_sam_addresses",
        info_url="https://data.boston.gov/dataset/live-street-address-management-sam-addresses",
        download_url="https://data.boston.gov/dataset/fc9562ca-02df-40bf-b4db-a36effb52ccc/resource/b7f6856f-0e69-40e5-8c27-0a40c132802a/download/live_street_address_management_sam_addresses.zip"
    )
    
    print("\n--- Geospatial Data Preparation Complete ---")


if __name__ == "__main__":
    main()