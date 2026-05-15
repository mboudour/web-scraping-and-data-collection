import os
import json
import pandas as pd

# =============================================================================
# Instats Seminar: Web Scraping and Data Collection
# Day 2 - From raw output to usable data
# Application 2: Health Sciences - WHO Global Health Observatory
# =============================================================================
# Goal: Clean and standardize raw JSON data into a usable tabular format.

def clean_who_data():
    """
    Reads raw cached data from Day 1, cleans it, and saves it as a CSV.
    Demonstrates handling missing values, filtering, and standardizing.
    """
    raw_cache_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                                  'day1', 'data', 'cache', 'day1_app2_who_raw.json')
    
    clean_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'cache')
    os.makedirs(clean_dir, exist_ok=True)
    clean_file = os.path.join(clean_dir, 'day2_app2_who_clean.csv')

    print(f"Loading raw data from {raw_cache_file}")
    with open(raw_cache_file, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)
        
    records = raw_data.get('value', [])
    print(f"Loaded {len(records)} records. Starting cleaning process...")

    df = pd.DataFrame(records)
    
    # Select relevant columns
    cols_to_keep = ['Id', 'IndicatorCode', 'SpatialDimType', 'SpatialDim', 'TimeDimType', 'TimeDim', 'Dim1Type', 'Dim1', 'NumericValue']
    # Only keep columns that exist in the dataframe
    cols_to_keep = [c for c in cols_to_keep if c in df.columns]
    df = df[cols_to_keep]
    
    # Rename columns for better readability
    rename_map = {
        'SpatialDim': 'CountryCode',
        'TimeDim': 'Year',
        'Dim1': 'Sex',
        'NumericValue': 'LifeExpectancy'
    }
    df = df.rename(columns=rename_map)
    
    # Drop rows where LifeExpectancy is missing
    df = df.dropna(subset=['LifeExpectancy'])
    
    # Round LifeExpectancy to 1 decimal place
    df['LifeExpectancy'] = df['LifeExpectancy'].round(1)
    
    print(f"Cleaning complete. Saving {len(df)} records to {clean_file}")
    df.to_csv(clean_file, index=False)
    
    print("\nSample of cleaned data:")
    print(df.head())

if __name__ == "__main__":
    clean_who_data()
