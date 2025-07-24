import requests
from pathlib import Path
from tqdm import tqdm
import urllib3

# Suppress InsecureRequestWarning for environments with SSL issues
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- Configuration ---
# Dictionary of year to direct CSV download URL
CSV_URLS = {
    2024: "https://data.boston.gov/dataset/8048697b-ad64-4bfc-b090-ee00169f2323/resource/dff4d804-5031-443a-8409-8344efd0e5c8/download/tmpm461rr5o.csv",
    2023: "https://data.boston.gov/dataset/8048697b-ad64-4bfc-b090-ee00169f2323/resource/e6013a93-1321-4f2a-bf91-8d8a02f1e62f/download/tmpwbgyud93.csv",
    2022: "https://data.boston.gov/dataset/8048697b-ad64-4bfc-b090-ee00169f2323/resource/81a7b022-f8fc-4da5-80e4-b160058ca207/download/tmpfm8veglw.csv",
    2021: "https://data.boston.gov/dataset/8048697b-ad64-4bfc-b090-ee00169f2323/resource/f53ebccd-bc61-49f9-83db-625f209c95f5/download/tmp88p9g82n.csv",
    2020: "https://data.boston.gov/dataset/8048697b-ad64-4bfc-b090-ee00169f2323/resource/6ff6a6fd-3141-4440-a880-6f60a37fe789/download/tmpcv_10m2s.csv",
    2019: "https://data.boston.gov/dataset/8048697b-ad64-4bfc-b090-ee00169f2323/resource/ea2e4696-4a2d-429c-9807-d02eb92e0222/download/tmpcje3ep_w.csv",
    2018: "https://data.boston.gov/dataset/8048697b-ad64-4bfc-b090-ee00169f2323/resource/2be28d90-3a90-4af1-a3f6-f28c1e25880a/download/tmp7602cia8.csv",
    2017: "https://data.boston.gov/dataset/8048697b-ad64-4bfc-b090-ee00169f2323/resource/30022137-709d-465e-baae-ca155b51927d/download/tmpzccn8u4q.csv",
    2016: "https://data.boston.gov/dataset/8048697b-ad64-4bfc-b090-ee00169f2323/resource/b7ea6b1b-3ca4-4c5b-9713-6dc1db52379a/download/tmpzxzxeqfb.csv",
    2015: "https://data.boston.gov/dataset/8048697b-ad64-4bfc-b090-ee00169f2323/resource/c9509ab4-6f6d-4b97-979a-0cf2a10c922b/download/tmphrybkxuh.csv"
}
INFO_URL = "https://data.boston.gov/dataset/311-service-requests"
OUTPUT_DIR = Path("../data/raw")

def download_311_data(year, url):
    """Downloads a single year's 311 data CSV with a TQDM progress bar."""
    filename = f"boston-311-{year}.csv"
    filepath = OUTPUT_DIR / filename
    
    print(f"> DOWNLOADING '{filename}' to '{OUTPUT_DIR}'")
    
    try:
        response = requests.get(url, stream=True, verify=False)
        response.raise_for_status()

        total_size = int(response.headers.get('content-length', 0))
        block_size = 8192  # Use a larger chunk size for faster downloads

        with open(filepath, 'wb') as file, tqdm(
            desc=filename,
            total=total_size,
            unit='iB',
            unit_scale=True,
            unit_divisor=1024,
        ) as bar:
            for chunk in response.iter_content(chunk_size=block_size):
                file.write(chunk)
                bar.update(len(chunk))
        
        return True
    except requests.exceptions.RequestException as e:
        print(f"  ERROR: Failed to download data for {year}. Error: {e}")
        return False

def main():
    """Checks for existing 311 data and downloads any missing files."""
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # --- 1. Checking Available Files ---
    print("--- 1. Checking Available Files ---")
    files_to_download = []
    # Sort by year to ensure chronological checking
    for year, url in sorted(CSV_URLS.items()):
        filename = f"boston-311-{year}.csv"
        filepath = OUTPUT_DIR / filename
        
        if filepath.exists() and filepath.stat().st_size > 0:
            print(f"> FOUND {year} Data: '{filename}'")
        else:
            print(f"> NOT FOUND {year} Data: '{filename}'")
            files_to_download.append((year, url))
    
    # --- 2. Downloading Files ---
    if files_to_download:
        print("\n--- 2. Downloading Missing Files ---")
        for year, url in files_to_download:
            download_311_data(year, url)
    
    # --- 3. Completion ---
    print("\n--- 3. 311 Data Fetch Complete ---")
    print(f"(More info here: {INFO_URL})")

if __name__ == "__main__":
    main()