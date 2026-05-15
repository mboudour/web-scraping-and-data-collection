import os
import json
import pandas as pd
import requests

# =============================================================================
# Instats Seminar: Web Scraping and Data Collection
# Day 1 - From web source to raw dataset
# Application 4: Social Sciences - Congress.gov API
# =============================================================================
# Goal: Extract raw structured data about legislative bills.
# Note: Since the Congress.gov API requires a key, we'll use a public alternative
# like the GovInfo API or simulate it if necessary. For this seminar, we'll use
# the ProPublica Congress API (or a similar open endpoint) or a mock structure 
# if a key is strictly required. Here we'll fetch from a public endpoint.
# Actually, the US Government provides a public bill status JSON from govinfo.
# We will use the public GovInfo API collections endpoint as an example.

def fetch_congress_data():
    """
    Fetches legislative collections data from the GovInfo API.
    Saves the raw JSON response to a local cache file.
    """
    cache_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'cache')
    os.makedirs(cache_dir, exist_ok=True)
    cache_file = os.path.join(cache_dir, 'day1_app4_congress_raw.json')

    if os.path.exists(cache_file):
        print(f"Loading cached data from {cache_file}")
        with open(cache_file, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
    else:
        print("Fetching fresh data from GovInfo API...")
        # GovInfo Collections API (Public, no key required for basic access)
        url = "https://api.govinfo.gov/collections/BILLS/2023-01-01T00:00:00Z"
        params = {"offset": 0, "pageSize": 50, "api_key": "DEMO_KEY"}
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        raw_data = response.json()
        
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(raw_data, f, indent=4)
        print(f"Saved raw data to {cache_file}")

    if 'packages' in raw_data and len(raw_data['packages']) > 0:
        first_record = raw_data['packages'][0]
        print("\nExample of raw extracted record:")
        print(json.dumps(first_record, indent=2))
    else:
        print("No records found.")

if __name__ == "__main__":
    fetch_congress_data()
