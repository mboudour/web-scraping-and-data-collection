import os
import pandas as pd

# =============================================================================
# Instats Seminar: Web Scraping and Data Collection
# Day 3 - From shared workflow to participants' own data
# Application 5: Sustainability & Environment - EPA / World Bank
# =============================================================================
# Goal: Explore and analyze the cleaned dataset.

def explore_epa_data():
    """
    Reads the cleaned dataset from Day 2 and performs preliminary exploratory analysis.
    """
    clean_cache_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                                    'day2', 'data', 'cache', 'day2_app5_co2_clean.csv')
    
    if not os.path.exists(clean_cache_file):
        print(f"Error: Cleaned data file not found at {clean_cache_file}")
        return

    print(f"Loading cleaned data from {clean_cache_file}")
    df = pd.read_csv(clean_cache_file)
    
    print("\n--- Exploratory Analysis: Environmental / Population Data ---")
    print(f"Total records: {len(df)}")
    
    if 'Population' in df.columns:
        print("\nSummary Statistics for Population:")
        print(df['Population'].describe())
        
        print("\nTop 5 Regions/Countries by Population in 2020:")
        top_5 = df.sort_values(by='Population', ascending=False).head(5)
        print(top_5[['CountryName', 'Population']])
        
    print("\nMissing Values Check:")
    print(df.isnull().sum())

if __name__ == "__main__":
    explore_epa_data()
