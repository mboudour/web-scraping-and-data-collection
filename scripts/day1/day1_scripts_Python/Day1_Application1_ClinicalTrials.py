import os
import json
import pandas as pd
import requests

# =============================================================================
# Instats Seminar: Web Scraping and Data Collection
# Day 1 - From web source to raw dataset
# Application 1: Health Sciences - ClinicalTrials.gov API
# =============================================================================
# Goal: Extract raw structured data from an online source (API) and cache it locally.
# This script demonstrates how to identify a source, request data, and save the raw output.

def fetch_clinical_trials_data():
    """
    Fetches clinical trial data related to 'diabetes' from the ClinicalTrials.gov API.
    Saves the raw JSON response to a local cache file.
    """
    cache_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'cache')
    os.makedirs(cache_dir, exist_ok=True)
    cache_file = os.path.join(cache_dir, 'day1_app1_clinicaltrials_raw.json')

    # Check if we already have the data cached
    if os.path.exists(cache_file):
        print(f"Loading cached data from {cache_file}")
        with open(cache_file, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
    else:
        print("Fetching fresh data from ClinicalTrials.gov API...")
        # ClinicalTrials.gov v2 API endpoint for study search
        # We search for 'diabetes' and limit to 50 results for manageable size
        url = "https://clinicaltrials.gov/api/v2/studies"
        params = {
            "query.cond": "diabetes",
            "pageSize": 50,
            "fields": "NCTId,Condition,BriefTitle,OverallStatus,LeadSponsorName"
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()  # Check for request errors
        raw_data = response.json()
        
        # Save to cache
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(raw_data, f, indent=4)
        print(f"Saved raw data to {cache_file}")

    # Display the first study as an example of raw output
    if 'studies' in raw_data and len(raw_data['studies']) > 0:
        first_study = raw_data['studies'][0]
        print("\nExample of raw extracted record:")
        print(json.dumps(first_study, indent=2))
    else:
        print("No studies found.")

if __name__ == "__main__":
    fetch_clinical_trials_data()
