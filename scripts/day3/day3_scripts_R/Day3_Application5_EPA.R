# =============================================================================
# Instats Seminar: Web Scraping and Data Collection
# Day 3 - From shared workflow to participants' own data
# Application 5: Sustainability & Environment - EPA / World Bank
# =============================================================================
# Goal: Explore and analyze the cleaned dataset.

library(dplyr)
library(fs)

explore_epa_data <- function() {
  clean_cache_file <- path(path_dir(path_dir(getwd())), "day2", "data", "cache", "day2_app5_co2_clean.csv")
  
  if (!file_exists(clean_cache_file)) {
    cat("Error: Cleaned data file not found at", clean_cache_file, "\n")
    return()
  }
  
  cat("Loading cleaned data from", clean_cache_file, "\n")
  df <- read.csv(clean_cache_file)
  
  cat("\n--- Exploratory Analysis: Environmental / Population Data ---\n")
  cat("Total records:", nrow(df), "\n")
  
  if ("Population" %in% names(df)) {
    cat("\nSummary Statistics for Population:\n")
    print(summary(df$Population))
    
    cat("\nTop 5 Regions/Countries by Population in 2020:\n")
    top_5 <- df %>% 
      arrange(desc(Population)) %>% 
      head(5) %>% 
      select(CountryName, Population)
    print(top_5)
  }
  
  cat("\nMissing Values Check:\n")
  print(colSums(is.na(df)))
}

explore_epa_data()
