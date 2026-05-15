# =============================================================================
# Instats Seminar: Web Scraping and Data Collection
# Day 2 - From raw output to usable data
# Application 1: Health Sciences - ClinicalTrials.gov
# =============================================================================
# Goal: Clean and standardize raw JSON data into a usable tabular format.

library(jsonlite)
library(dplyr)
library(purrr)
library(fs)

clean_clinical_trials_data <- function() {
  raw_cache_file <- path(path_dir(path_dir(getwd())), "day1", "data", "cache", "day1_app1_clinicaltrials_raw.json")
  clean_dir <- path(path_dir(path_dir(getwd())), "day2", "data", "cache")
  dir_create(clean_dir)
  clean_file <- path(clean_dir, "day2_app1_clinicaltrials_clean.csv")
  
  cat("Loading raw data from", raw_cache_file, "\n")
  raw_data <- fromJSON(raw_cache_file, simplifyVector = FALSE)
  
  studies <- raw_data$studies
  cat("Loaded", length(studies), "records. Starting cleaning process...\n")
  
  # Extract and flatten the nested list structure into a data frame
  df <- map_dfr(studies, function(study) {
    protocol <- study$protocolSection
    ident <- protocol$identificationModule
    status <- protocol$statusModule
    sponsor <- protocol$sponsorCollaboratorsModule
    cond <- protocol$conditionsModule
    
    tibble(
      NCTId = ident$nctId %||% "Unknown",
      Title = ident$briefTitle %||% "",
      Status = status$overallStatus %||% "Unknown",
      Sponsor = sponsor$leadSponsor$name %||% "Unknown",
      Conditions = paste(unlist(cond$conditions), collapse = ", ")
    )
  })
  
  # Clean and standardize
  df <- df %>%
    mutate(Status = toupper(Status)) %>%
    distinct(NCTId, .keep_all = TRUE)
  
  cat("Cleaning complete. Saving", nrow(df), "records to", clean_file, "\n")
  write.csv(df, clean_file, row.names = FALSE)
  
  cat("\nSample of cleaned data:\n")
  print(head(df))
}

clean_clinical_trials_data()
