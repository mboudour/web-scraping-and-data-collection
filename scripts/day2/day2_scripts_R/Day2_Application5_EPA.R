# =============================================================================
# Instats Seminar: Web Scraping and Data Collection
# Day 2 - From raw output to usable data
# Application 5: Sustainability & Environment - EPA Air Quality API
# =============================================================================
# Goal: Extract raw data and immediately clean it (combining Day 1 and Day 2 concepts).

library(httr2)
library(jsonlite)
library(dplyr)
library(purrr)
library(fs)

fetch_and_clean_epa_data <- function() {
  raw_cache_dir <- path(path_dir(path_dir(getwd())), "day1", "data", "cache")
  dir_create(raw_cache_dir)
  raw_cache_file <- path(raw_cache_dir, "day1_app5_co2_raw.json")
  
  clean_dir <- path(path_dir(path_dir(getwd())), "day2", "data", "cache")
  dir_create(clean_dir)
  clean_file <- path(clean_dir, "day2_app5_co2_clean.csv")
  
  # 1. Fetch/Load Raw Data (Day 1 Concept)
  if (file_exists(raw_cache_file)) {
    cat("Loading cached raw data from", raw_cache_file, "\n")
    raw_data <- fromJSON(raw_cache_file, simplifyVector = FALSE)
  } else {
    cat("Fetching fresh data from World Bank API (CO2 emissions)...\n")
    url <- "http://api.worldbank.org/v2/country/all/indicator/SP.POP.TOTL"
    
    req <- request(url) %>%
      req_url_query(
        format = "json",
        per_page = 100,
        date = "2020"
      )
    
    resp <- req_perform(req)
    raw_data <- resp_body_json(resp, simplifyVector = FALSE)
    
    write_json(raw_data, raw_cache_file, pretty = TRUE, auto_unbox = TRUE)
    cat("Saved raw data to", raw_cache_file, "\n")
  }
  
  # 2. Clean Data (Day 2 Concept)
  if (length(raw_data) > 1) {
    records <- raw_data[[2]]
  } else {
    records <- list()
  }
  
  cat("Loaded", length(records), "records. Starting cleaning process...\n")
  
  df <- map_dfr(records, function(rec) {
    country_name <- if (!is.null(rec$country) && !is.null(rec$country$value)) rec$country$value else ""
    co2 <- if (!is.null(rec$value)) as.numeric(rec$value) else NA_real_
    
    tibble(
      CountryCode = rec$countryiso3code %||% "",
      CountryName = country_name,
      Year = rec$date %||% "",
      Population = co2
    )
  })
  
  # Clean and filter
  clean_df <- df %>%
    filter(CountryCode != "", !is.na(Population))
  
  cat("Cleaning complete. Saving", nrow(clean_df), "records to", clean_file, "\n")
  write.csv(clean_df, clean_file, row.names = FALSE)
  
  cat("\nSample of cleaned data:\n")
  print(head(clean_df))
}

fetch_and_clean_epa_data()
