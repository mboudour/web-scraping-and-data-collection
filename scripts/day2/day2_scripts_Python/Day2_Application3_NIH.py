import os
import json
import pandas as pd

# =============================================================================
# Instats Seminar: Web Scraping and Data Collection
# Day 2 - From raw output to usable data
# Application 3: Life Sciences - NIH RePORTER
# =============================================================================
# Goal: Clean and standardize raw JSON data into a usable tabular format.

def clean_nih_data():
    """
    Reads raw cached data from Day 1, cleans it, and saves it as a CSV.
    Demonstrates flattening nested dictionaries and date parsing.
    """
    raw_cache_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                                  'day1', 'data', 'cache', 'day1_app3_nih_raw.json')
    
    clean_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'cache')
    os.makedirs(clean_dir, exist_ok=True)
    clean_file = os.path.join(clean_dir, 'day2_app3_nih_clean.csv')

    print(f"Loading raw data from {raw_cache_file}")
    with open(raw_cache_file, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)
        
    records = raw_data.get('results', [])
    print(f"Loaded {len(records)} records. Starting cleaning process...")

    cleaned_records = []
    for record in records:
        # Extract basic info
        proj_num = record.get('project_num', '')
        title = record.get('project_title', '')
        
        # Extract nested info
        org = record.get('organization', {})
        org_name = org.get('org_name', 'Unknown') if org else 'Unknown'
        
        agency = record.get('agency_ic_admin', {})
        agency_name = agency.get('name', 'Unknown') if agency else 'Unknown'
        
        award_amount = record.get('award_amount', 0)
        
        cleaned_records.append({
            'ProjectNumber': proj_num,
            'Title': title,
            'Organization': org_name,
            'Agency': agency_name,
            'AwardAmount': award_amount
        })

    df = pd.DataFrame(cleaned_records)
    
    # Fill missing award amounts with 0 and convert to numeric
    df['AwardAmount'] = pd.to_numeric(df['AwardAmount']).fillna(0)
    
    print(f"Cleaning complete. Saving {len(df)} records to {clean_file}")
    df.to_csv(clean_file, index=False)
    
    print("\nSample of cleaned data:")
    print(df.head())

if __name__ == "__main__":
    clean_nih_data()
