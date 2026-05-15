import os
import json
import pandas as pd
import requests

# =============================================================================
# Instats Seminar: Web Scraping and Data Collection
# Day 1 - From web source to raw dataset
# Application 2: Health Sciences - WHO Global Health Observatory API
# =============================================================================
# Goal: Extract raw structured data from an online source (API) and cache it locally.
# This script demonstrates fetching indicator data from the WHO Athena API.

def fetch_who_data():
    """
    Fetches WHO Global Health Observatory data for life expectancy.
    Saves the raw JSON response to a local cache file.
    """
    cache_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'cache')
    os.makedirs(cache_dir, exist_ok=True)
    cache_file = os.path.join(cache_dir, 'day1_app2_who_raw.json')

    if os.path.exists(cache_file):
        print(f"Loading cached data from {cache_file}")
        with open(cache_file, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
    else:
        print("Fetching fresh data from WHO Athena API...")
        # Indicator WHOSIS_000001: Life expectancy at birth (years)
        url = "https://ghoapi.azureedge.net/api/WHOSIS_000001"
        # We limit the results using OData top parameter to keep data manageable
        params = {"$top": 100}
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        raw_data = response.json()
        
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(raw_data, f, indent=4)
        print(f"Saved raw data to {cache_file}")

    if 'value' in raw_data and len(raw_data['value']) > 0:
        first_record = raw_data['value'][0]
        print("\nExample of raw extracted record:")
        print(json.dumps(first_record, indent=2))
    else:
        print("No records found.")

if __name__ == "__main__":
    fetch_who_data()
