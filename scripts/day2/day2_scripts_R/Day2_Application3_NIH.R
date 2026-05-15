# =============================================================================
# Instats Seminar: Web Scraping and Data Collection
# Day 2 - From raw output to usable data
# Application 3: Life Sciences - NIH RePORTER
# =============================================================================
# Goal: Clean and standardize raw JSON data into a usable tabular format.

library(jsonlite)
library(dplyr)
library(purrr)
library(fs)
library(tidyr)

clean_nih_data <- function() {
  raw_cache_file <- path(path_dir(path_dir(getwd())), "day1", "data", "cache", "day1_app3_nih_raw.json")
  clean_dir <- path(path_dir(path_dir(getwd())), "day2", "data", "cache")
  dir_create(clean_dir)
  clean_file <- path(clean_dir, "day2_app3_nih_clean.csv")
  
  cat("Loading raw data from", raw_cache_file, "\n")
  raw_data <- fromJSON(raw_cache_file, simplifyVector = FALSE)
  
  records <- raw_data$results
  cat("Loaded", length(records), "records. Starting cleaning process...\n")
  
  df <- map_dfr(records, function(rec) {
    org_name <- if (!is.null(rec$organization) && !is.null(rec$organization$org_name)) rec$organization$org_name else "Unknown"
    agency_name <- if (!is.null(rec$agency_ic_admin) && !is.null(rec$agency_ic_admin$name)) rec$agency_ic_admin$name else "Unknown"
    award_amt <- if (!is.null(rec$award_amount)) as.numeric(rec$award_amount) else 0
    
    tibble(
      ProjectNumber = rec$project_num %||% "",
      Title = rec$project_title %||% "",
      Organization = org_name,
      Agency = agency_name,
      AwardAmount = award_amt
    )
  })
  
  # Ensure numeric
  df <- df %>%
    mutate(AwardAmount = replace_na(AwardAmount, 0))
  
  cat("Cleaning complete. Saving", nrow(df), "records to", clean_file, "\n")
  write.csv(df, clean_file, row.names = FALSE)
  
  cat("\nSample of cleaned data:\n")
  print(head(df))
}

clean_nih_data()
