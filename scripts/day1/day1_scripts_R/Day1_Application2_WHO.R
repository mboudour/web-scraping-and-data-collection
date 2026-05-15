# =============================================================================
# Instats Seminar: Web Scraping and Data Collection
# Day 1 - From web source to raw dataset
# Application 2: Health Sciences - WHO Global Health Observatory API
# =============================================================================
# Goal: Extract raw structured data from an online source (API) and cache it locally.

library(httr2)
library(jsonlite)
library(fs)

fetch_who_data <- function() {
  cache_dir <- path(path_dir(path_dir(getwd())), "data", "cache")
  dir_create(cache_dir)
  cache_file <- path(cache_dir, "day1_app2_who_raw.json")
  
  if (file_exists(cache_file)) {
    cat("Loading cached data from", cache_file, "\n")
    raw_data <- fromJSON(cache_file, simplifyVector = FALSE)
  } else {
    cat("Fetching fresh data from WHO Athena API...\n")
    url <- "https://ghoapi.azureedge.net/api/WHOSIS_000001"
    
    req <- request(url) %>%
      req_url_query(`$top` = 100)
    
    resp <- req_perform(req)
    raw_data <- resp_body_json(resp, simplifyVector = FALSE)
    
    write_json(raw_data, cache_file, pretty = TRUE, auto_unbox = TRUE)
    cat("Saved raw data to", cache_file, "\n")
  }
  
  if (!is.null(raw_data$value) && length(raw_data$value) > 0) {
    cat("\nExample of raw extracted record:\n")
    print(toJSON(raw_data$value[[1]], pretty = TRUE, auto_unbox = TRUE))
  } else {
    cat("No records found.\n")
  }
}

fetch_who_data()
