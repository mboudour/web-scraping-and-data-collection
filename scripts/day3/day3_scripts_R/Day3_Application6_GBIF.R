# =============================================================================
# Instats Seminar: Web Scraping and Data Collection
# Day 3 - From shared workflow to participants' own data
# Application 6: Life Sciences - GBIF (Global Biodiversity Information Facility)
# =============================================================================
# Goal: Complete workflow (Extract -> Clean -> Explore) in one script.

library(httr2)
library(jsonlite)
library(dplyr)
library(purrr)
library(fs)

full_gbif_workflow <- function() {
  cache_dir <- path(path_dir(path_dir(getwd())), "data", "cache")
  dir_create(cache_dir)
  raw_file <- path(cache_dir, "day3_app6_gbif_raw.json")
  clean_file <- path(cache_dir, "day3_app6_gbif_clean.csv")
  
  # 1. Extract
  if (file_exists(raw_file)) {
    cat("Loading cached raw data from", raw_file, "\n")
    raw_data <- fromJSON(raw_file, simplifyVector = FALSE)
  } else {
    cat("Fetching fresh data from GBIF API (occurrences of Panthera leo)...\n")
    url <- "https://api.gbif.org/v1/occurrence/search"
    
    req <- request(url) %>%
      req_url_query(
        taxonKey = 5219404,
        limit = 100
      )
    
    resp <- req_perform(req)
    raw_data <- resp_body_json(resp, simplifyVector = FALSE)
    
    write_json(raw_data, raw_file, pretty = TRUE, auto_unbox = TRUE)
  }
  
  # 2. Clean
  records <- raw_data$results
  
  df <- map_dfr(records, function(rec) {
    tibble(
      Key = rec$key %||% "",
      ScientificName = rec$scientificName %||% "",
      Country = rec$country %||% "Unknown",
      Year = rec$year %||% NA_integer_,
      BasisOfRecord = rec$basisOfRecord %||% ""
    )
  })
  
  clean_df <- df %>% filter(!is.na(Year))
  write.csv(clean_df, clean_file, row.names = FALSE)
  
  # 3. Explore
  cat("\n--- Exploratory Analysis: GBIF Panthera leo Occurrences ---\n")
  cat("Total cleaned records:", nrow(clean_df), "\n")
  
  cat("\nOccurrences by Country:\n")
  print(head(sort(table(clean_df$Country), decreasing = TRUE), 5))
  
  cat("\nOccurrences by Record Type:\n")
  print(table(clean_df$BasisOfRecord))
}

full_gbif_workflow()
