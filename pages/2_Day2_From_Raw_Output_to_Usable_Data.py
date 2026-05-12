"""
Day 2 — From Raw Output to Usable Data
Applications: ClinicalTrials, WHO, NIH, Congress, World Bank (cleaning & validation)
+ Bring Your Own Data — Clean
"""

import os, json
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Day 2 — From Raw Output to Usable Data", page_icon="🧹", layout="wide")

# Robust cache path — works locally and on Streamlit Cloud
import pathlib
_repo_root = pathlib.Path(__file__).resolve().parent
if _repo_root.name == "pages":
    _repo_root = _repo_root.parent
CACHE_DIR = str(_repo_root / "data" / "cache")
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
        "🔍 Bring Your Own Data — Clean",
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

Use the sidebar to explore each application, the **🔧 Interactive Cleaning Module**, or
**🔍 Bring Your Own Data — Clean** to clean your own collected data.
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
Upload any CSV or XLSX file or select one of the cached datasets below, then apply
cleaning operations interactively. Preview the result before downloading.
    """)

    source = st.radio("Data source", ["Use cached dataset", "Upload your own file (CSV or XLSX)"])

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
        uploaded = st.file_uploader("Upload CSV or XLSX", type=["csv", "xlsx"])
        if uploaded:
            if uploaded.name.endswith(".xlsx"):
                df = pd.read_excel(uploaded)
            else:
                df = pd.read_csv(uploaded)
        else:
            df = None

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

# ── BYOD: Clean ───────────────────────────────────────────────────────────────

elif app_choice == "🔍 Bring Your Own Data — Clean":
    st.title("🔍 Bring Your Own Data — Step 2: Clean")
    st.markdown("""
This section lets you clean the data you collected in **Day 1 → 🔍 Bring Your Own Data — Collect**,
or upload your own raw file (CSV, XLSX, or JSON).

The same five cleaning problems encountered in the case studies apply to any dataset:
**label inconsistency, duplicates, irregular dates, missing values, and nested fields.**
Use the operations below to address them interactively.

Your cleaned data will be available for exploration in **Day 3 → 🔍 Bring Your Own Data — Explore**.
    """)

    st.markdown("---")
    st.subheader("📋 Five Common Cleaning Problems — Quick Reference")
    st.markdown("""
| Problem | What It Looks Like | How to Fix It |
|---|---|---|
| **Label inconsistency** | `"Male"`, `"male"`, `"M"` in the same column | Standardize to uppercase or a fixed vocabulary |
| **Duplicate records** | Same row appearing twice | Remove duplicate rows |
| **Irregular date formats** | `"2023-01-15"` and `"15/01/2023"` mixed | Parse to datetime and reformat |
| **Missing values** | `NaN`, `null`, empty cells | Drop rows, fill with a default, or flag |
| **Nested fields** | A column containing `{"city": "Boston", "state": "MA"}` | Flatten into separate columns (done in Day 1 wizard) |
    """)

    st.markdown("---")
    st.subheader("⚙️ Load Your Data")

    # ── Data source selection ─────────────────────────────────────────────────
    data_source = st.radio(
        "Where is your data coming from?",
        [
            "Carried forward from Day 1 BYOD collection",
            "Upload a file (CSV, XLSX, or JSON)",
        ],
    )

    df = None

    if data_source == "Carried forward from Day 1 BYOD collection":
        if "byod_flat_df" in st.session_state:
            df = st.session_state["byod_flat_df"]
            st.success(f"Loaded from Day 1 session: {len(df)} rows × {len(df.columns)} columns.")
        else:
            st.warning("""
No data found from Day 1. Either:
- Go to **Day 1 → 🔍 Bring Your Own Data — Collect** and complete the collection wizard, or
- Upload a file below instead.
            """)

    else:
        uploaded = st.file_uploader(
            "Upload your raw data file",
            type=["csv", "xlsx", "json"],
            help="CSV and XLSX files are loaded directly. JSON files must contain a list of records or a dict with a list value.",
        )
        if uploaded:
            try:
                if uploaded.name.endswith(".xlsx"):
                    df = pd.read_excel(uploaded)
                    st.success(f"Loaded XLSX: {len(df)} rows × {len(df.columns)} columns.")
                elif uploaded.name.endswith(".json"):
                    raw = json.load(uploaded)
                    if isinstance(raw, list):
                        df = pd.json_normalize(raw)
                    elif isinstance(raw, dict):
                        # Try to find the first list value
                        list_keys = [k for k, v in raw.items() if isinstance(v, list)]
                        if list_keys:
                            chosen_key = st.selectbox("Select the records array from the JSON:", list_keys)
                            df = pd.json_normalize(raw[chosen_key])
                        else:
                            df = pd.DataFrame([raw])
                    st.success(f"Loaded JSON: {len(df)} rows × {len(df.columns)} columns.")
                else:
                    df = pd.read_csv(uploaded)
                    st.success(f"Loaded CSV: {len(df)} rows × {len(df.columns)} columns.")
            except Exception as e:
                st.error(f"Could not load file: {e}")

    # ── Cleaning Operations ───────────────────────────────────────────────────
    if df is not None:
        st.markdown("---")
        st.subheader("🔍 Raw Data Preview")
        col1, col2, col3 = st.columns(3)
        col1.metric("Rows", len(df))
        col2.metric("Columns", len(df.columns))
        col3.metric("Missing Cells", int(df.isnull().sum().sum()))
        st.dataframe(df.head(20), use_container_width=True)

        st.markdown("---")
        st.subheader("🧹 Cleaning Operations")

        c1, c2 = st.columns(2)

        with c1:
            st.markdown("**Row-level operations**")
            drop_dupes = st.checkbox("Remove duplicate rows")
            drop_na_cols = st.multiselect(
                "Drop rows where these columns are missing",
                df.columns.tolist(),
                help="Rows with a missing value in any selected column will be removed.",
            )
            strip_ws = st.checkbox("Strip leading/trailing whitespace from all text columns")

        with c2:
            st.markdown("**Column-level operations**")
            rename_col = st.selectbox("Rename a column", ["— none —"] + df.columns.tolist())
            if rename_col != "— none —":
                new_name = st.text_input(f"New name for '{rename_col}'", value=rename_col, key="byod_rename")
            else:
                new_name = None

            coerce_col = st.selectbox(
                "Convert a column to numeric",
                ["— none —"] + df.columns.tolist(),
                help="Non-numeric values will become NaN.",
            )
            date_col = st.selectbox(
                "Parse a column as dates",
                ["— none —"] + df.columns.tolist(),
                help="Converts text dates to a standard YYYY-MM-DD format.",
            )
            upper_col = st.selectbox(
                "Standardize a column to UPPERCASE",
                ["— none —"] + df.columns.tolist(),
                help="Useful for fixing label inconsistency.",
            )

        st.markdown("**Row filtering**")
        filter_col = st.selectbox("Filter rows by column value", ["— none —"] + df.columns.tolist(), key="byod_filter")
        keep_vals = []
        if filter_col != "— none —":
            unique_vals = df[filter_col].dropna().unique().tolist()
            keep_vals = st.multiselect(
                f"Keep rows where '{filter_col}' equals:",
                unique_vals,
                default=unique_vals[:min(5, len(unique_vals))],
            )

        if st.button("✅ Apply All Cleaning Operations", key="byod_clean_btn"):
            result = df.copy()
            log = []

            if drop_dupes:
                before = len(result)
                result = result.drop_duplicates()
                log.append(f"Removed {before - len(result)} duplicate rows.")

            if drop_na_cols:
                before = len(result)
                result = result.dropna(subset=drop_na_cols)
                log.append(f"Dropped {before - len(result)} rows with missing values in: {drop_na_cols}.")

            if strip_ws:
                str_cols = result.select_dtypes(include="object").columns
                result[str_cols] = result[str_cols].apply(lambda c: c.str.strip())
                log.append(f"Stripped whitespace from {len(str_cols)} text columns.")

            if rename_col != "— none —" and new_name and new_name != rename_col:
                result = result.rename(columns={rename_col: new_name})
                log.append(f"Renamed column '{rename_col}' → '{new_name}'.")

            if coerce_col != "— none —":
                result[coerce_col] = pd.to_numeric(result[coerce_col], errors="coerce")
                log.append(f"Converted '{coerce_col}' to numeric (non-numeric values → NaN).")

            if date_col != "— none —":
                try:
                    result[date_col] = pd.to_datetime(result[date_col], errors="coerce").dt.strftime("%Y-%m-%d")
                    log.append(f"Parsed '{date_col}' as dates (format: YYYY-MM-DD).")
                except Exception as e:
                    log.append(f"Could not parse '{date_col}' as dates: {e}")

            if upper_col != "— none —":
                result[upper_col] = result[upper_col].astype(str).str.upper()
                log.append(f"Standardized '{upper_col}' to UPPERCASE.")

            if filter_col != "— none —" and keep_vals:
                before = len(result)
                result = result[result[filter_col].isin(keep_vals)]
                log.append(f"Filtered '{filter_col}': kept {len(keep_vals)} value(s), removed {before - len(result)} rows.")

            # ── Processing Log ────────────────────────────────────────────────
            st.subheader("📋 Processing Log")
            if log:
                for entry in log:
                    st.write(f"✅ {entry}")
            else:
                st.info("No operations were applied.")

            st.write(f"**Final dataset:** {len(result)} rows × {len(result.columns)} columns")

            # ── Cleaned Preview ───────────────────────────────────────────────
            st.subheader("✅ Cleaned Dataset Preview")
            st.dataframe(result.head(20), use_container_width=True)

            # ── Missingness Report ────────────────────────────────────────────
            st.subheader("🔍 Missingness Report")
            miss = result.isnull().sum()
            miss = miss[miss > 0]
            if miss.empty:
                st.success("No missing values in cleaned dataset.")
            else:
                st.dataframe(miss.rename("Missing Count").to_frame(), use_container_width=True)

            # ── Save to session for Day 3 ─────────────────────────────────────
            st.session_state["byod_clean_df"] = result
            st.info("Cleaned data saved. Go to **Day 3 → 🔍 Bring Your Own Data — Explore** to continue.")

            # ── Downloads ─────────────────────────────────────────────────────
            st.subheader("⬇️ Download Cleaned Data")
            csv_out = result.to_csv(index=False).encode("utf-8")
            st.download_button("Download as CSV", csv_out, "byod_cleaned.csv", "text/csv")

            try:
                import io
                buffer = io.BytesIO()
                result.to_excel(buffer, index=False, engine="openpyxl")
                buffer.seek(0)
                st.download_button("Download as XLSX", buffer, "byod_cleaned.xlsx",
                                   "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            except Exception:
                pass  # openpyxl not available — CSV only
