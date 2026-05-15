# =============================================================================
# Instats Seminar: Web Scraping and Data Collection
# Day 1 - From web source to raw dataset
# Application 3: Life Sciences - NIH RePORTER API
# =============================================================================
# Goal: Extract raw structured data about funded research grants.

library(httr2)
library(jsonlite)
library(fs)

fetch_nih_data <- function() {
  cache_dir <- path(path_dir(path_dir(getwd())), "data", "cache")
  dir_create(cache_dir)
  cache_file <- path(cache_dir, "day1_app3_nih_raw.json")
  
  if (file_exists(cache_file)) {
    cat("Loading cached data from", cache_file, "\n")
    raw_data <- fromJSON(cache_file, simplifyVector = FALSE)
  } else {
    cat("Fetching fresh data from NIH RePORTER API...\n")
    url <- "https://api.reporter.nih.gov/v2/projects/search"
    
    payload <- list(
      criteria = list(
        advanced_text_search = list(
          operator = "and",
          search_field = "terms",
          search_text = "genomics"
        )
      ),
      limit = 50,
      offset = 0
    )
    
    req <- request(url) %>%
      req_headers("Content-Type" = "application/json") %>%
      req_body_json(payload)
    
    resp <- req_perform(req)
    raw_data <- resp_body_json(resp, simplifyVector = FALSE)
    
    write_json(raw_data, cache_file, pretty = TRUE, auto_unbox = TRUE)
    cat("Saved raw data to", cache_file, "\n")
  }
  
  if (!is.null(raw_data$results) && length(raw_data$results) > 0) {
    cat("\nExample of raw extracted record:\n")
    print(toJSON(raw_data$results[[1]], pretty = TRUE, auto_unbox = TRUE))
  } else {
    cat("No records found.\n")
  }
}

fetch_nih_data()
