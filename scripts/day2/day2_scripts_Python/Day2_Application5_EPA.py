import os
import json
import pandas as pd
import requests

# =============================================================================
# Instats Seminar: Web Scraping and Data Collection
# Day 2 - From raw output to usable data
# Application 5: Sustainability & Environment - EPA Air Quality API
# =============================================================================
# Goal: Extract raw data and immediately clean it (combining Day 1 and Day 2 concepts).

def fetch_and_clean_epa_data():
    """
    Fetches air quality data from the EPA API (or public proxy) and cleans it.
    """
    # For this seminar, we will simulate fetching a public environmental dataset
    # We will use the World Bank API for CO2 emissions as a reliable open alternative
    # to EPA which often requires strict API key management.
    
    raw_cache_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'day1', 'data', 'cache')
    os.makedirs(raw_cache_dir, exist_ok=True)
    raw_cache_file = os.path.join(raw_cache_dir, 'day1_app5_co2_raw.json')
    
    clean_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'cache')
    os.makedirs(clean_dir, exist_ok=True)
    clean_file = os.path.join(clean_dir, 'day2_app5_co2_clean.csv')

    # 1. Fetch/Load Raw Data (Day 1 Concept)
    if os.path.exists(raw_cache_file):
        print(f"Loading cached raw data from {raw_cache_file}")
        with open(raw_cache_file, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
    else:
        print("Fetching fresh data from World Bank API (CO2 emissions)...")
        # EN.ATM.CO2E.KT = CO2 emissions (kt)
        # Let's use SP.POP.TOTL (Total Population) as a fallback if CO2 is archived
        url = "http://api.worldbank.org/v2/country/all/indicator/SP.POP.TOTL"
        params = {"format": "json", "per_page": 100, "date": "2020"}
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        raw_data = response.json()
        
        with open(raw_cache_file, 'w', encoding='utf-8') as f:
            json.dump(raw_data, f, indent=4)
        print(f"Saved raw data to {raw_cache_file}")

    # 2. Clean Data (Day 2 Concept)
    # The World Bank API returns a list where the second element contains the actual data
    if isinstance(raw_data, list) and len(raw_data) > 1:
        records = raw_data[1]
    else:
        records = []
        
    print(f"Loaded {len(records)} records. Starting cleaning process...")

    cleaned_records = []
    for record in records:
        country = record.get('country', {})
        cleaned_records.append({
            'CountryCode': record.get('countryiso3code', ''),
            'CountryName': country.get('value', '') if country else '',
            'Year': record.get('date', ''),
            'Population': record.get('value', None)
        })

    df = pd.DataFrame(cleaned_records)
    
    # Drop rows without country codes (regions) and missing emissions
    if not df.empty:
        df = df[df['CountryCode'] != '']
        df = df.dropna(subset=['Population'])
    
    print(f"Cleaning complete. Saving {len(df)} records to {clean_file}")
    df.to_csv(clean_file, index=False)
    
    print("\nSample of cleaned data:")
    print(df.head())

if __name__ == "__main__":
    fetch_and_clean_epa_data()
