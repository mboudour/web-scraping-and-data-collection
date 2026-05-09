"""
Day 2 — From Raw Output to Usable Data
Applications: ClinicalTrials, WHO, NIH, Congress, World Bank (cleaning & validation)
"""

import os, json
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Day 2 — From Raw Output to Usable Data", page_icon="🧹", layout="wide")

# Robust cache path: works locally and on Streamlit Cloud
_here = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.join(_here, "..", "data", "cache")
if not os.path.isdir(CACHE_DIR):
    CACHE_DIR = os.path.join(os.getcwd(), "data", "cache")
os.makedirs(CACHE_DIR, exist_ok=True)

# ── helpers ───────────────────────────────────────────────────────────────────

def load_raw_json(filename):
    path = os.path.join(CACHE_DIR, filename)
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return None

def load_clean_csv(filename):
    path = os.path.join(CACHE_DIR, filename)
    if os.path.exists(path):
        return pd.read_csv(path)
    return None

def show_comparison(raw_df, clean_df, raw_label="Raw", clean_label="Cleaned"):
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**{raw_label}** — {len(raw_df)} rows × {len(raw_df.columns)} cols")
        st.dataframe(raw_df.head(20), use_container_width=True)
    with col2:
        st.markdown(f"**{clean_label}** — {len(clean_df)} rows × {len(clean_df.columns)} cols")
        st.dataframe(clean_df.head(20), use_container_width=True)

# ── sidebar ───────────────────────────────────────────────────────────────────

st.sidebar.title("Day 2 Navigation")
app_choice = st.sidebar.radio(
    "Select Application",
    [
        "Overview",
        "App 1 — ClinicalTrials.gov (Clean)",
        "App 2 — WHO GHO (Clean)",
        "App 3 — NIH RePORTER (Clean)",
        "App 4 — GovInfo Congress (Clean)",
        "App 5 — World Bank Population (Clean)",
        "🔧 Interactive Cleaning Module",
    ],
)

# ── overview ──────────────────────────────────────────────────────────────────

if app_choice == "Overview":
    st.title("🧹 Day 2 — From Raw Output to Usable Data")
    st.markdown("""
**Theme:** Show participants how messy outputs are cleaned, standardized, documented, and validated.

### Five Common Problems in Raw Web-Derived Data
| Problem | Description |
|---------|-------------|
| **Label inconsistency** | Same category under different names across records |
| **Duplicate records** | Same entity appearing through multiple access paths |
| **Irregular date formats** | Dates as strings in varying formats |
| **Missing values** | Absent information, extraction failure, or source norms |
| **Nested fields** | Related entities embedded as sub-objects in JSON |

### Applications Today
| # | Source | Cleaning Focus |
|---|--------|---------------|
| 1 | ClinicalTrials.gov | Flatten nested JSON, standardize phase labels |
| 2 | WHO GHO | Filter to Both sexes, select and rename columns |
| 3 | NIH RePORTER | Extract org/agency fields, coerce award amounts |
| 4 | GovInfo (Congress) | Parse dates, clean title strings |
| 5 | World Bank Population | Reshape, filter, validate numeric ranges |

Use the sidebar to explore each application or the **Interactive Cleaning Module**.
    """)

# ── App 1: ClinicalTrials clean ───────────────────────────────────────────────

elif app_choice == "App 1 — ClinicalTrials.gov (Clean)":
    st.title("🏥 App 1 — ClinicalTrials.gov: Cleaning")

    raw_data = load_raw_json("day1_app1_clinicaltrials_raw.json")
    clean_df = load_clean_csv("day2_app1_clinicaltrials_clean.csv")

    if raw_data is None or clean_df is None:
        st.error("Cache files not found. Please run Day 1 scripts first.")
    else:
        studies = raw_data.get("studies", [])
        raw_rows = []
        for s in studies:
            proto = s.get("protocolSection", {})
            id_mod = proto.get("identificationModule", {})
            status_mod = proto.get("statusModule", {})
            design_mod = proto.get("designModule", {})
            cond_mod = proto.get("conditionsModule", {})
            raw_rows.append({
                "nctId": id_mod.get("nctId", ""),
                "briefTitle": id_mod.get("briefTitle", ""),
                "overallStatus": status_mod.get("overallStatus", ""),
                "phases": str(design_mod.get("phases", [])),
                "conditions": str(cond_mod.get("conditions", [])),
            })
        raw_df = pd.DataFrame(raw_rows)

        st.subheader("Raw vs. Cleaned: Side-by-Side Comparison")
        show_comparison(raw_df, clean_df, "Raw (nested JSON flattened)", "Cleaned CSV")

        st.subheader("Cleaning Operations Applied")
        st.markdown("""
1. Extracted `nctId`, `briefTitle`, `overallStatus`, `phases`, `conditions` from nested JSON
2. Converted `phases` list to comma-separated string
3. Stripped whitespace from all string fields
4. Dropped records with missing `nctId`
        """)

        st.subheader("Validation: Status Distribution")
        st.bar_chart(clean_df["Status"].value_counts() if "Status" in clean_df.columns
                     else clean_df.iloc[:, 2].value_counts())

        with st.expander("📌 Day 2 Teaching Note"):
            st.markdown("""
- Every cleaning operation is a **measurement decision**: choosing which fields to keep
  defines what the dataset can and cannot represent.
- The raw file is preserved in `data/cache/` so the cleaning steps can be replicated independently.
            """)

# ── App 2: WHO clean ──────────────────────────────────────────────────────────

elif app_choice == "App 2 — WHO GHO (Clean)":
    st.title("🌍 App 2 — WHO GHO: Cleaning")

    raw_data = load_raw_json("day1_app2_who_raw.json")
    clean_df = load_clean_csv("day2_app2_who_clean.csv")

    if raw_data is None or clean_df is None:
        st.error("Cache files not found.")
    else:
        records = raw_data.get("value", [])
        raw_df = pd.DataFrame([{
            "SpatialDim": r.get("SpatialDim"),
            "TimeDim": r.get("TimeDim"),
            "Dim1": r.get("Dim1"),
            "NumericValue": r.get("NumericValue"),
        } for r in records])

        st.subheader("Raw vs. Cleaned: Side-by-Side Comparison")
        show_comparison(raw_df, clean_df, "Raw (all sex categories)", "Cleaned (Both sexes only)")

        st.subheader("Cleaning Operations Applied")
        st.markdown("""
1. Filtered to `Dim1 == 'BTSX'` (Both sexes) to remove sex-disaggregated duplicates
2. Renamed columns: `SpatialDim` → `CountryCode`, `TimeDim` → `Year`, `NumericValue` → `LifeExpectancy`
3. Dropped records with missing `LifeExpectancy`
4. Rounded `LifeExpectancy` to 1 decimal place
        """)

        st.subheader("Life Expectancy Distribution (Cleaned)")
        if "LifeExpectancy" in clean_df.columns:
            st.bar_chart(clean_df["LifeExpectancy"].dropna().value_counts(bins=10).sort_index())

        with st.expander("📌 Day 2 Teaching Note"):
            st.markdown("""
- Filtering to Both sexes is a **unit definition decision**: one row = one country-year.
- The raw data had 3× as many rows because each country-year appeared for Male, Female, and Both.
            """)

# ── App 3: NIH clean ──────────────────────────────────────────────────────────

elif app_choice == "App 3 — NIH RePORTER (Clean)":
    st.title("🔬 App 3 — NIH RePORTER: Cleaning")

    raw_data = load_raw_json("day1_app3_nih_raw.json")
    clean_df = load_clean_csv("day2_app3_nih_clean.csv")

    if raw_data is None or clean_df is None:
        st.error("Cache files not found.")
    else:
        results = raw_data.get("results", [])
        raw_df = pd.DataFrame([{
            "project_num": r.get("project_num"),
            "project_title": str(r.get("project_title", ""))[:50],
            "fiscal_year": r.get("fiscal_year"),
            "award_amount": r.get("award_amount"),
            "org_name": r.get("org_name"),
            "agency_code": r.get("agency_code"),
        } for r in results])

        st.subheader("Raw vs. Cleaned: Side-by-Side Comparison")
        show_comparison(raw_df, clean_df, "Raw", "Cleaned")

        st.subheader("Cleaning Operations Applied")
        st.markdown("""
1. Extracted `org_name`, `org_city`, `org_state` from nested organization object
2. Coerced `award_amount` to numeric; replaced non-numeric values with `NaN`
3. Stripped HTML tags from `project_title`
4. Dropped records with missing `project_num`
        """)

        st.subheader("Award Amount Summary")
        if "AwardAmount" in clean_df.columns:
            st.write(clean_df["AwardAmount"].describe())

        with st.expander("📌 Day 2 Teaching Note"):
            st.markdown("""
- `award_amount` is sometimes `null` in the source — this is **source-level missingness**,
  not an extraction error.
- Coercing to numeric forces a decision: treat nulls as 0, or exclude them from analysis?
            """)

# ── App 4: Congress clean ─────────────────────────────────────────────────────

elif app_choice == "App 4 — GovInfo Congress (Clean)":
    st.title("🏛️ App 4 — GovInfo Congress: Cleaning")

    raw_data = load_raw_json("day1_app4_congress_raw.json")
    clean_df = load_clean_csv("day2_app4_congress_clean.csv")

    if raw_data is None or clean_df is None:
        st.error("Cache files not found.")
    else:
        bills = raw_data.get("bills", [])
        raw_df = pd.DataFrame([{
            "number": b.get("number"),
            "type": b.get("type"),
            "title": str(b.get("title", ""))[:60],
            "originChamber": b.get("originChamber"),
            "congress": b.get("congress"),
            "latestActionDate": b.get("latestAction", {}).get("actionDate"),
            "updateDate": b.get("updateDate"),
        } for b in bills])

        st.subheader("Raw vs. Cleaned: Side-by-Side Comparison")
        show_comparison(raw_df, clean_df, "Raw (Congress.gov)", "Cleaned")

        st.subheader("Cleaning Operations Applied")
        st.markdown("""
1. Extracted `latestActionDate` from nested `latestAction` object
2. Parsed `updateDate` string to `datetime`; extracted `Year` and `Month`
3. Stripped leading/trailing whitespace from `title`
4. Standardized `type` labels to uppercase
5. Dropped records with missing `number`
        """)

        st.subheader("Bills by Type (Cleaned)")
        if "Type" in clean_df.columns:
            st.bar_chart(clean_df["Type"].value_counts())
        elif "type" in clean_df.columns:
            st.bar_chart(clean_df["type"].value_counts())

        with st.expander("📌 Day 2 Teaching Note"):
            st.markdown("""
- The `latestAction` field is a **nested object** — extracting it is a flattening operation.
- Date parsing is one of the most common cleaning tasks in web-derived data.
- The `type` field encodes bill category — standardizing it enables consistent grouping.
            """)

# ── App 5: World Bank clean ───────────────────────────────────────────────────

elif app_choice == "App 5 — World Bank Population (Clean)":
    st.title("🌱 App 5 — World Bank Population: Cleaning")

    clean_df = load_clean_csv("day2_app5_co2_clean.csv")

    if clean_df is None:
        st.error("Cache file not found.")
    else:
        st.subheader("Cleaned Dataset Preview")
        st.dataframe(clean_df.head(30), use_container_width=True)

        st.subheader("Cleaning Operations Applied")
        st.markdown("""
1. Fetched population data (indicator `SP.POP.TOTL`) from World Bank API
2. Filtered to years 2000–2022
3. Dropped aggregated regional rows (kept only country-level records)
4. Renamed columns: `country` → `CountryName`, `countryiso3code` → `CountryCode`
5. Validated: no negative population values; no future years
        """)

        st.subheader("Population Summary Statistics")
        if "Population" in clean_df.columns:
            st.write(clean_df["Population"].describe())
            st.subheader("Top 10 Countries by Population (most recent year)")
            latest = clean_df.sort_values("Year", ascending=False)
            top10 = latest.drop_duplicates("CountryCode").nlargest(10, "Population")
            st.bar_chart(top10.set_index("CountryName")["Population"])

        with st.expander("📌 Day 2 Teaching Note"):
            st.markdown("""
- The World Bank API returns **both country-level and regional aggregate** rows.
  Filtering to country-level only is a unit-definition decision.
- Validating numeric ranges (no negative populations) is an example of **analytic validation**.
            """)

# ── Interactive Cleaning Module ───────────────────────────────────────────────

elif app_choice == "🔧 Interactive Cleaning Module":
    st.title("🔧 Interactive Cleaning Module")
    st.markdown("""
Upload any CSV file or select one of the cached datasets below, then apply
cleaning operations interactively. Preview the result before downloading.
    """)

    source = st.radio("Data source", ["Use cached dataset", "Upload your own CSV"])

    if source == "Use cached dataset":
        dataset_name = st.selectbox("Select dataset", [
            "day2_app1_clinicaltrials_clean.csv",
            "day2_app2_who_clean.csv",
            "day2_app3_nih_clean.csv",
            "day2_app4_congress_clean.csv",
            "day2_app5_co2_clean.csv",
        ])
        df = load_clean_csv(dataset_name)
    else:
        uploaded = st.file_uploader("Upload CSV", type=["csv"])
        df = pd.read_csv(uploaded) if uploaded else None

    if df is not None:
        st.subheader(f"Dataset: {len(df)} rows × {len(df.columns)} columns")
        st.dataframe(df.head(10), use_container_width=True)

        st.subheader("Cleaning Operations")

        col1, col2 = st.columns(2)

        with col1:
            drop_dupes = st.checkbox("Remove duplicate rows")
            drop_na_col = st.multiselect("Drop rows where these columns are missing", df.columns.tolist())
            strip_ws = st.checkbox("Strip whitespace from all string columns")

        with col2:
            rename_col = st.selectbox("Rename column (optional)", ["— none —"] + df.columns.tolist())
            if rename_col != "— none —":
                new_name = st.text_input(f"New name for '{rename_col}'", value=rename_col)
            filter_col = st.selectbox("Filter by column value (optional)", ["— none —"] + df.columns.tolist())
            if filter_col != "— none —":
                unique_vals = df[filter_col].dropna().unique().tolist()
                keep_vals = st.multiselect(f"Keep rows where '{filter_col}' is:", unique_vals, default=unique_vals[:5])

        if st.button("Apply Cleaning Operations"):
            result = df.copy()
            log = []

            if drop_dupes:
                before = len(result)
                result = result.drop_duplicates()
                log.append(f"Removed {before - len(result)} duplicate rows.")

            if drop_na_col:
                before = len(result)
                result = result.dropna(subset=drop_na_col)
                log.append(f"Dropped {before - len(result)} rows with missing values in: {drop_na_col}.")

            if strip_ws:
                str_cols = result.select_dtypes(include="object").columns
                result[str_cols] = result[str_cols].apply(lambda c: c.str.strip())
                log.append(f"Stripped whitespace from {len(str_cols)} string columns.")

            if rename_col != "— none —" and new_name and new_name != rename_col:
                result = result.rename(columns={rename_col: new_name})
                log.append(f"Renamed '{rename_col}' → '{new_name}'.")

            if filter_col != "— none —" and keep_vals:
                before = len(result)
                result = result[result[filter_col].isin(keep_vals)]
                log.append(f"Filtered '{filter_col}': kept {len(keep_vals)} values, dropped {before - len(result)} rows.")

            st.subheader("Processing Log")
            for entry in log:
                st.write(f"✅ {entry}")
            st.write(f"**Final dataset:** {len(result)} rows × {len(result.columns)} columns")

            st.subheader("Cleaned Dataset Preview")
            st.dataframe(result.head(20), use_container_width=True)

            st.subheader("Missingness Report")
            miss = result.isnull().sum()
            miss = miss[miss > 0]
            if miss.empty:
                st.success("No missing values in cleaned dataset.")
            else:
                st.dataframe(miss.rename("Missing Count").to_frame(), use_container_width=True)

            csv_out = result.to_csv(index=False).encode("utf-8")
            st.download_button("⬇️ Download Cleaned CSV", csv_out, "cleaned_output.csv", "text/csv")
