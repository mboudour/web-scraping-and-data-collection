# =============================================================================
# Instats Seminar: Web Scraping and Data Collection
# Day 2 - From raw output to usable data
# Application 2: Health Sciences - WHO Global Health Observatory
# =============================================================================
# Goal: Clean and standardize raw JSON data into a usable tabular format.

library(jsonlite)
library(dplyr)
library(fs)

clean_who_data <- function() {
  raw_cache_file <- path(path_dir(path_dir(getwd())), "day1", "data", "cache", "day1_app2_who_raw.json")
  clean_dir <- path(path_dir(path_dir(getwd())), "day2", "data", "cache")
  dir_create(clean_dir)
  clean_file <- path(clean_dir, "day2_app2_who_clean.csv")
  
  cat("Loading raw data from", raw_cache_file, "\n")
  # Use simplifyVector = TRUE to get a data frame directly if possible
  raw_data <- fromJSON(raw_cache_file, simplifyVector = TRUE)
  
  df <- raw_data$value
  cat("Loaded", nrow(df), "records. Starting cleaning process...\n")
  
  # Select, rename, and filter
  clean_df <- df %>%
    select(any_of(c("Id", "IndicatorCode", "SpatialDimType", "SpatialDim", 
                    "TimeDimType", "TimeDim", "Dim1Type", "Dim1", "NumericValue"))) %>%
    rename(
      CountryCode = SpatialDim,
      Year = TimeDim,
      Sex = Dim1,
      LifeExpectancy = NumericValue
    ) %>%
    filter(!is.na(LifeExpectancy)) %>%
    mutate(LifeExpectancy = round(LifeExpectancy, 1))
  
  cat("Cleaning complete. Saving", nrow(clean_df), "records to", clean_file, "\n")
  write.csv(clean_df, clean_file, row.names = FALSE)
  
  cat("\nSample of cleaned data:\n")
  print(head(clean_df))
}

clean_who_data()
