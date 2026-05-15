# =============================================================================
# Instats Seminar: Web Scraping and Data Collection
# Day 2 - From raw output to usable data
# Application 4: Social Sciences - Congress.gov (GovInfo)
# =============================================================================
# Goal: Clean and standardize raw JSON data into a usable tabular format.

library(jsonlite)
library(dplyr)
library(stringr)
library(fs)

clean_congress_data <- function() {
  raw_cache_file <- path(path_dir(path_dir(getwd())), "day1", "data", "cache", "day1_app4_congress_raw.json")
  clean_dir <- path(path_dir(path_dir(getwd())), "day2", "data", "cache")
  dir_create(clean_dir)
  clean_file <- path(clean_dir, "day2_app4_congress_clean.csv")
  
  cat("Loading raw data from", raw_cache_file, "\n")
  raw_data <- fromJSON(raw_cache_file, simplifyVector = TRUE)
  
  df <- raw_data$packages
  cat("Loaded", nrow(df), "records. Starting cleaning process...\n")
  
  # Select, clean, and rename
  clean_df <- df %>%
    select(any_of(c("packageId", "title", "congress", "dateIssued", "docClass"))) %>%
    mutate(
      title = str_squish(title),
      dateIssued = as.Date(dateIssued)
    ) %>%
    rename(
      BillID = packageId,
      Title = title,
      Congress = congress,
      DateIssued = dateIssued,
      DocumentClass = docClass
    )
  
  cat("Cleaning complete. Saving", nrow(clean_df), "records to", clean_file, "\n")
  write.csv(clean_df, clean_file, row.names = FALSE)
  
  cat("\nSample of cleaned data:\n")
  print(head(clean_df))
}

clean_congress_data()
