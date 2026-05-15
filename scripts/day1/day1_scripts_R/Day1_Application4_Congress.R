# =============================================================================
# Instats Seminar: Web Scraping and Data Collection
# Day 1 - From web source to raw dataset
# Application 4: Social Sciences - Congress.gov API
# =============================================================================
# Goal: Extract raw structured data about legislative bills.

library(httr2)
library(jsonlite)
library(fs)

fetch_congress_data <- function() {
  cache_dir <- path(path_dir(path_dir(getwd())), "data", "cache")
  dir_create(cache_dir)
  cache_file <- path(cache_dir, "day1_app4_congress_raw.json")
  
  if (file_exists(cache_file)) {
    cat("Loading cached data from", cache_file, "\n")
    raw_data <- fromJSON(cache_file, simplifyVector = FALSE)
  } else {
    cat("Fetching fresh data from GovInfo API...\n")
    url <- "https://api.govinfo.gov/collections/BILLS/2023-01-01T00:00:00Z"
    
    req <- request(url) %>%
      req_url_query(
        offset = 0,
        pageSize = 50,
        api_key = "DEMO_KEY"
      )
    
    resp <- req_perform(req)
    raw_data <- resp_body_json(resp, simplifyVector = FALSE)
    
    write_json(raw_data, cache_file, pretty = TRUE, auto_unbox = TRUE)
    cat("Saved raw data to", cache_file, "\n")
  }
  
  if (!is.null(raw_data$packages) && length(raw_data$packages) > 0) {
    cat("\nExample of raw extracted record:\n")
    print(toJSON(raw_data$packages[[1]], pretty = TRUE, auto_unbox = TRUE))
  } else {
    cat("No records found.\n")
  }
}

fetch_congress_data()
