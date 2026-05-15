import os
import json
import pandas as pd

# =============================================================================
# Instats Seminar: Web Scraping and Data Collection
# Day 2 - From raw output to usable data
# Application 4: Social Sciences - Congress.gov (GovInfo)
# =============================================================================
# Goal: Clean and standardize raw JSON data into a usable tabular format.

def clean_congress_data():
    """
    Reads raw cached data from Day 1, cleans it, and saves it as a CSV.
    Demonstrates string manipulation and standardizing date formats.
    """
    raw_cache_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                                  'day1', 'data', 'cache', 'day1_app4_congress_raw.json')
    
    clean_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'cache')
    os.makedirs(clean_dir, exist_ok=True)
    clean_file = os.path.join(clean_dir, 'day2_app4_congress_clean.csv')

    print(f"Loading raw data from {raw_cache_file}")
    with open(raw_cache_file, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)
        
    records = raw_data.get('packages', [])
    print(f"Loaded {len(records)} records. Starting cleaning process...")

    df = pd.DataFrame(records)
    
    # Select relevant columns
    cols_to_keep = ['packageId', 'title', 'congress', 'dateIssued', 'docClass']
    cols_to_keep = [c for c in cols_to_keep if c in df.columns]
    df = df[cols_to_keep]
    
    # Standardize dates
    if 'dateIssued' in df.columns:
        df['dateIssued'] = pd.to_datetime(df['dateIssued']).dt.strftime('%Y-%m-%d')
        
    # Clean titles (remove extra whitespace)
    if 'title' in df.columns:
        df['title'] = df['title'].str.strip()
        
    # Rename columns
    df = df.rename(columns={
        'packageId': 'BillID',
        'title': 'Title',
        'congress': 'Congress',
        'dateIssued': 'DateIssued',
        'docClass': 'DocumentClass'
    })
    
    print(f"Cleaning complete. Saving {len(df)} records to {clean_file}")
    df.to_csv(clean_file, index=False)
    
    print("\nSample of cleaned data:")
    print(df.head())

if __name__ == "__main__":
    clean_congress_data()
