import os
import json
import pandas as pd

# =============================================================================
# Instats Seminar: Web Scraping and Data Collection
# Day 2 - From raw output to usable data
# Application 1: Health Sciences - ClinicalTrials.gov
# =============================================================================
# Goal: Clean and standardize raw JSON data into a usable tabular format.

def clean_clinical_trials_data():
    """
    Reads raw cached data from Day 1, cleans it, and saves it as a CSV.
    Demonstrates handling missing values, extracting nested fields, and standardizing.
    """
    raw_cache_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                                  'day1', 'data', 'cache', 'day1_app1_clinicaltrials_raw.json')
    
    clean_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'cache')
    os.makedirs(clean_dir, exist_ok=True)
    clean_file = os.path.join(clean_dir, 'day2_app1_clinicaltrials_clean.csv')

    print(f"Loading raw data from {raw_cache_file}")
    with open(raw_cache_file, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)
        
    studies = raw_data.get('studies', [])
    print(f"Loaded {len(studies)} records. Starting cleaning process...")

    cleaned_records = []
    for study in studies:
        protocol = study.get('protocolSection', {})
        ident_module = protocol.get('identificationModule', {})
        status_module = protocol.get('statusModule', {})
        sponsor_module = protocol.get('sponsorCollaboratorsModule', {})
        cond_module = protocol.get('conditionsModule', {})
        
        # Extract specific fields, handling potential missing data safely
        record = {
            'NCTId': ident_module.get('nctId', 'Unknown'),
            'Title': ident_module.get('briefTitle', ''),
            'Status': status_module.get('overallStatus', 'Unknown'),
            'Sponsor': sponsor_module.get('leadSponsor', {}).get('name', 'Unknown'),
            # Conditions might be a list
            'Conditions': ", ".join(cond_module.get('conditions', []))
        }
        cleaned_records.append(record)

    df = pd.DataFrame(cleaned_records)
    
    # Example cleaning operation: uppercase status for consistency
    df['Status'] = df['Status'].str.upper()
    
    # Drop duplicates if any
    df = df.drop_duplicates(subset=['NCTId'])
    
    print(f"Cleaning complete. Saving {len(df)} records to {clean_file}")
    df.to_csv(clean_file, index=False)
    
    print("\nSample of cleaned data:")
    print(df.head())

if __name__ == "__main__":
    clean_clinical_trials_data()
