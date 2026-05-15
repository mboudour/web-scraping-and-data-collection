import os
import json
import pandas as pd
import requests

# =============================================================================
# Instats Seminar: Web Scraping and Data Collection
# Day 3 - From shared workflow to participants' own data
# Application 6: Life Sciences - GBIF (Global Biodiversity Information Facility)
# =============================================================================
# Goal: Complete workflow (Extract -> Clean -> Explore) in one script to show 
# how a participant might adapt the pipeline for their own source.

def full_gbif_workflow():
    """
    Demonstrates the full pipeline on a new source (GBIF species occurrences).
    """
    cache_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'cache')
    os.makedirs(cache_dir, exist_ok=True)
    raw_file = os.path.join(cache_dir, 'day3_app6_gbif_raw.json')
    clean_file = os.path.join(cache_dir, 'day3_app6_gbif_clean.csv')

    # 1. Extract
    if os.path.exists(raw_file):
        print(f"Loading cached raw data from {raw_file}")
        with open(raw_file, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
    else:
        print("Fetching fresh data from GBIF API (occurrences of Panthera leo)...")
        # Panthera leo (Lion) taxonKey is 5219404
        url = "https://api.gbif.org/v1/occurrence/search"
        params = {"taxonKey": 5219404, "limit": 100}
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        raw_data = response.json()
        
        with open(raw_file, 'w', encoding='utf-8') as f:
            json.dump(raw_data, f, indent=4)

    # 2. Clean
    records = raw_data.get('results', [])
    cleaned_records = []
    for rec in records:
        cleaned_records.append({
            'Key': rec.get('key', ''),
            'ScientificName': rec.get('scientificName', ''),
            'Country': rec.get('country', 'Unknown'),
            'Year': rec.get('year', None),
            'BasisOfRecord': rec.get('basisOfRecord', '')
        })
    
    df = pd.DataFrame(cleaned_records)
    df = df.dropna(subset=['Year'])  # Drop records without a year
    df.to_csv(clean_file, index=False)
    
    # 3. Explore
    print("\n--- Exploratory Analysis: GBIF Panthera leo Occurrences ---")
    print(f"Total cleaned records: {len(df)}")
    
    print("\nOccurrences by Country:")
    print(df['Country'].value_counts().head(5))
    
    print("\nOccurrences by Record Type:")
    print(df['BasisOfRecord'].value_counts())

if __name__ == "__main__":
    full_gbif_workflow()
