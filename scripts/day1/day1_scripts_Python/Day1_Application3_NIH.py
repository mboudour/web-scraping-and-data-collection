import os
import json
import pandas as pd
import requests

# =============================================================================
# Instats Seminar: Web Scraping and Data Collection
# Day 1 - From web source to raw dataset
# Application 3: Life Sciences - NIH RePORTER API
# =============================================================================
# Goal: Extract raw structured data about funded research grants.

def fetch_nih_data():
    """
    Fetches NIH RePORTER data for projects related to 'genomics'.
    Saves the raw JSON response to a local cache file.
    """
    cache_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'cache')
    os.makedirs(cache_dir, exist_ok=True)
    cache_file = os.path.join(cache_dir, 'day1_app3_nih_raw.json')

    if os.path.exists(cache_file):
        print(f"Loading cached data from {cache_file}")
        with open(cache_file, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
    else:
        print("Fetching fresh data from NIH RePORTER API...")
        url = "https://api.reporter.nih.gov/v2/projects/search"
        payload = {
            "criteria": {
                "advanced_text_search": {
                    "operator": "and",
                    "search_field": "terms",
                    "search_text": "genomics"
                }
            },
            "limit": 50,
            "offset": 0
        }
        headers = {"Content-Type": "application/json"}
        
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        raw_data = response.json()
        
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(raw_data, f, indent=4)
        print(f"Saved raw data to {cache_file}")

    if 'results' in raw_data and len(raw_data['results']) > 0:
        first_record = raw_data['results'][0]
        print("\nExample of raw extracted record:")
        print(json.dumps(first_record, indent=2))
    else:
        print("No records found.")

if __name__ == "__main__":
    fetch_nih_data()
