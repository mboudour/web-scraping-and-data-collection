"""
Day 2 — From Raw Output to Usable Data
Goal: Clean and preprocess JSON data collected in Day 1, then export as CSV.

Uniform 6-step flow for both guided examples and BYOD:
  1. Display raw data
  2. Detect issues (auto-scan + dataset-specific) → pre-ticked checkboxes
  3. Apply selected fixes
  4. Display cleaned data
  5. Report changes
  6. Save to session + carry-forward button
"""

import json
import requests
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Day 2 — From Raw Output to Usable Data",
    page_icon="🧹",
    layout="wide",
)

# ── sidebar ────────────────────────────────────────────────────────────────────

st.sidebar.title("Day 2 Navigation")
app_choice = st.sidebar.radio(
    "Select section",
    ["Overview", "🧹 Clean Your Data", "⬇️ Export"],
)

# ── shared helpers ─────────────────────────────────────────────────────────────

def load_json_from_upload(uploaded_file):
    """Load a JSON file into a flat DataFrame; returns (df, key_used)."""
    raw = json.load(uploaded_file)
    if isinstance(raw, list):
        return pd.json_normalize(raw), None
    elif isinstance(raw, dict):
        list_keys = [k for k, v in raw.items() if isinstance(v, list)]
        if len(list_keys) == 1:
            return pd.json_normalize(raw[list_keys[0]]), list_keys[0]
        elif len(list_keys) > 1:
            key = st.selectbox(
                "Your JSON has multiple record arrays — select the one to use:",
                list_keys,
                key="json_key_selector",
            )
            return pd.json_normalize(raw[key]), key
        else:
            return pd.DataFrame([raw]), None
    return pd.DataFrame(), None


def auto_detect_issues(df, prefix, extra_issues=None):
    """
    Scan df for common data quality issues.
    extra_issues: list of dicts {id, label, description, fix} for dataset-specific fixes.
    Returns list of issue dicts.
    """
    issues = extra_issues or []

    # 1. Duplicate rows
    n_dupes = int(df.duplicated().sum())
    if n_dupes > 0:
        issues.append({
            "id": f"{prefix}_dupes",
            "label": f"🔁 Remove {n_dupes} duplicate row(s)",
            "description": f"Found **{n_dupes}** rows that are exact copies of another row.",
            "fix": lambda d, n=n_dupes: (d.drop_duplicates(), f"Removed {n} duplicate rows."),
        })

    # 2. Missing values per column
    miss_counts = df.isnull().sum()
    for col, cnt in miss_counts[miss_counts > 0].items():
        pct = 100 * cnt / max(len(df), 1)
        c, n = col, int(cnt)
        issues.append({
            "id": f"{prefix}_miss_{c}",
            "label": f"🕳️ Drop rows missing `{c}` ({n} rows, {pct:.0f}%)",
            "description": (
                f"Column **`{c}`** has **{n}** empty values ({pct:.0f}% of rows). "
                "Dropping these rows removes incomplete records."
            ),
            "fix": lambda d, col=c, n=n: (
                d.dropna(subset=[col]),
                f"Dropped {n} rows with missing values in '{col}'.",
            ),
        })

    # 3. Whitespace in text columns
    str_cols = df.select_dtypes(include="object").columns.tolist()
    ws_cols = [
        c for c in str_cols
        if df[c].dropna().astype(str).str.match(r"^\s+|\s+$").any()
    ]
    if ws_cols:
        issues.append({
            "id": f"{prefix}_ws",
            "label": f"✂️ Strip whitespace from {len(ws_cols)} text column(s)",
            "description": (
                f"Found leading or trailing spaces in: **{', '.join(ws_cols)}**. "
                "This can cause mismatches when grouping or filtering."
            ),
            "fix": lambda d, cols=ws_cols: (
                d.assign(**{c: d[c].str.strip() for c in cols if c in d.columns}),
                f"Stripped whitespace from: {cols}.",
            ),
        })

    # 4. Date columns stored as text
    date_pat = r"^\d{4}[-/]\d{2}[-/]\d{2}|^\d{2}[-/]\d{2}[-/]\d{4}"
    for c in str_cols:
        sample = df[c].dropna().astype(str).head(20)
        if sample.str.match(date_pat).mean() > 0.7:
            issues.append({
                "id": f"{prefix}_date_{c}",
                "label": f"📅 Parse `{c}` as dates",
                "description": (
                    f"Column **`{c}`** appears to contain dates stored as text. "
                    "Converting to `YYYY-MM-DD` enables correct sorting and filtering."
                ),
                "fix": lambda d, col=c: (
                    d.assign(**{col: pd.to_datetime(d[col], errors="coerce").dt.strftime("%Y-%m-%d")}),
                    f"Parsed '{col}' as dates (YYYY-MM-DD).",
                ),
            })

    # 5. Numeric columns stored as text
    for c in str_cols:
        sample = df[c].dropna().astype(str).head(30)
        cleaned = sample.str.replace(r"[\$,\s%]", "", regex=True)
        if pd.to_numeric(cleaned, errors="coerce").notna().mean() > 0.7:
            issues.append({
                "id": f"{prefix}_num_{c}",
                "label": f"🔢 Convert `{c}` to numeric",
                "description": (
                    f"Column **`{c}`** contains mostly numbers stored as text. "
                    "Converting enables arithmetic, sorting, and statistics."
                ),
                "fix": lambda d, col=c: (
                    d.assign(**{col: pd.to_numeric(d[col], errors="coerce")}),
                    f"Converted '{col}' to numeric.",
                ),
            })

    # 6. Mixed-case label inconsistency
    for c in str_cols:
        vals = df[c].dropna().astype(str).unique()
        if len(vals) >= 2:
            if len(set(v.lower() for v in vals)) < len(vals):
                issues.append({
                    "id": f"{prefix}_case_{c}",
                    "label": f"🔤 Standardize `{c}` to UPPERCASE (mixed case detected)",
                    "description": (
                        f"Column **`{c}`** has values that differ only in capitalisation. "
                        "Standardising prevents incorrect group counts."
                    ),
                    "fix": lambda d, col=c: (
                        d.assign(**{col: d[col].astype(str).str.upper()}),
                        f"Standardized '{col}' to UPPERCASE.",
                    ),
                })

    # 7. Dot-separated column names from JSON flattening
    dot_cols = [c for c in df.columns if "." in str(c)]
    if dot_cols:
        issues.append({
            "id": f"{prefix}_dotcols",
            "label": f"🏷️ Rename {len(dot_cols)} dot-separated column(s) from JSON flattening",
            "description": (
                f"Columns with dots: **{', '.join(dot_cols[:5])}{'…' if len(dot_cols) > 5 else ''}**. "
                "Dots are replaced with underscores for compatibility with most tools."
            ),
            "fix": lambda d, cols=dot_cols: (
                d.rename(columns={c: c.replace(".", "_") for c in cols}),
                f"Renamed {len(cols)} dot-separated column(s) (dots → underscores).",
            ),
        })

    return issues


def render_cleaning_flow(raw_df, prefix, session_key="byod_clean_df", extra_issues=None):
    """
    Render the full 6-step cleaning flow for any dataframe.
    Steps: display raw → detect → checkboxes → apply → display cleaned → report → save
    """
    # ── Step 1: Display raw data ───────────────────────────────────────────────
    st.markdown("#### Step 1 — Raw Data")
    c1, c2, c3 = st.columns(3)
    c1.metric("Rows", len(raw_df))
    c2.metric("Columns", len(raw_df.columns))
    c3.metric("Missing Cells", int(raw_df.isnull().sum().sum()))
    st.dataframe(raw_df.head(20), use_container_width=True)

    st.markdown("---")

    # ── Step 2: Detect issues ──────────────────────────────────────────────────
    st.markdown("#### Step 2 — Detected Issues")
    issues = auto_detect_issues(raw_df, prefix=prefix, extra_issues=extra_issues)

    if not issues:
        st.success(
            "✅ No common data quality issues detected. "
            "Your data looks clean — go to **⬇️ Export**."
        )
        st.session_state[session_key] = raw_df
        return

    st.markdown(
        f"The app found **{len(issues)} issue(s)**. "
        "All are pre-selected — untick any you want to skip."
    )

    selected = {}
    for issue in issues:
        with st.container():
            col_cb, col_desc = st.columns([0.04, 0.96])
            with col_cb:
                selected[issue["id"]] = st.checkbox(
                    "", value=True, key=f"chk_{issue['id']}"
                )
            with col_desc:
                st.markdown(f"**{issue['label']}**")
                st.caption(issue["description"])

    st.markdown("---")

    # ── Steps 3–6: Apply, display, report, save ────────────────────────────────
    if st.button("✅ Apply Selected Fixes", key=f"apply_{prefix}"):
        result = raw_df.copy()
        log = []

        # Step 3: Apply
        for issue in issues:
            if selected.get(issue["id"], False):
                try:
                    result, entry = issue["fix"](result)
                    log.append(entry)
                except Exception as e:
                    log.append(f"⚠️ Could not apply '{issue['label']}': {e}")

        # Step 4: Display cleaned data
        st.markdown("#### Step 4 — Cleaned Data")
        c1, c2, c3 = st.columns(3)
        c1.metric("Rows", len(result))
        c2.metric("Columns", len(result.columns))
        c3.metric("Missing Cells", int(result.isnull().sum().sum()))
        st.dataframe(result.head(20), use_container_width=True)

        st.markdown("---")

        # Step 5: Report changes
        st.markdown("#### Step 5 — Cleaning Report")
        if log:
            for entry in log:
                st.write(f"✅ {entry}")
        else:
            st.info("No fixes were selected — data is unchanged.")

        miss = result.isnull().sum()
        miss = miss[miss > 0]
        if miss.empty:
            st.success("No missing values remain in the cleaned dataset.")
        else:
            st.markdown("**Remaining missing values:**")
            st.dataframe(miss.rename("Missing Count").to_frame(), use_container_width=True)

        st.markdown("---")

        # Step 6: Save to session
        st.markdown("#### Step 6 — Save")
        st.session_state[session_key] = result
        st.success(
            f"✅ Cleaned dataset saved to this session "
            f"({len(result)} rows × {len(result.columns)} columns). "
            "Go to **⬇️ Export** in the sidebar to download it or carry it to Day 3."
        )
        if st.button("➡️ Use This Data → Day 3", key=f"day3_{prefix}"):
            st.session_state["byod_clean_df"] = result
            st.success("✅ Data ready for Day 3.")


# ── OVERVIEW ───────────────────────────────────────────────────────────────────

if app_choice == "Overview":
    st.title("🧹 Day 2 — From Raw Output to Usable Data")
    st.markdown("""
**Theme:** Raw JSON from APIs and scraped tables is rarely analysis-ready.
Day 2 teaches participants how to identify and fix the five most common problems
in web-derived data, then export a clean CSV for Day 3.

### Five Common Problems in Raw Web-Derived Data

| Problem | What it looks like | Why it matters |
|---|---|---|
| **Label inconsistency** | `"Male"`, `"male"`, `"M"` in the same column | Counts and groups will be wrong |
| **Duplicate records** | Same row appearing twice | Inflates counts and averages |
| **Irregular date formats** | `"2023-01-15"` and `"15/01/2023"` mixed | Sorting and filtering by date fails |
| **Missing values** | `NaN`, `null`, empty cells | Analyses silently exclude rows |
| **Nested fields** | A column containing `{"city": "Boston", "state": "MA"}` | Cannot filter or group on sub-fields |

### What You Will Do Today

1. Load a dataset (guided example or your own Day 1 JSON).
2. The app scans it and detects data quality issues automatically.
3. Confirm which fixes to apply (all pre-selected).
4. Review the cleaned dataset and the cleaning report.
5. Save and export as CSV for Day 3.

Use the sidebar to go to **🧹 Clean Your Data** to start.
    """)

# ── CLEAN YOUR DATA ────────────────────────────────────────────────────────────

elif app_choice == "🧹 Clean Your Data":
    st.title("🧹 Clean Your Data")
    st.markdown("""
Choose a **guided example** to see how a real Day 1 dataset is cleaned,
or load **your own Day 1 JSON** to clean it interactively.
Both follow the same six-step flow.
    """)

    # ── Dataset selector ───────────────────────────────────────────────────────
    dataset_choice = st.radio(
        "Which dataset do you want to clean?",
        [
            "📌 Guided — ClinicalTrials.gov (diabetes + insulin trials)",
            "📌 Guided — WHO GHO (life expectancy, 2000–2022)",
            "📌 Guided — NIH RePORTER (genomics grants)",
            "📌 Guided — Congress.gov (118th Congress bills)",
            "🔧 My Own Data (upload Day 1 JSON or use session)",
        ],
        key="dataset_choice",
    )

    st.markdown("---")

    raw_df = None
    prefix = "ds"
    extra_issues = []

    # ── Guided: ClinicalTrials ─────────────────────────────────────────────────
    if dataset_choice.startswith("📌 Guided — ClinicalTrials"):
        prefix = "ct"
        if st.button("▶ Fetch Data", key="fetch_ct"):
            with st.spinner("Fetching from ClinicalTrials.gov…"):
                try:
                    resp = requests.get(
                        "https://clinicaltrials.gov/api/v2/studies",
                        params={
                            "query.cond": "diabetes",
                            "query.intr": "insulin",
                            "pageSize": 50,
                            "format": "json",
                        },
                        timeout=15,
                    ).json()
                    raw_df = pd.json_normalize([
                        {
                            "nctId": s.get("protocolSection", {}).get("identificationModule", {}).get("nctId", ""),
                            "briefTitle": s.get("protocolSection", {}).get("identificationModule", {}).get("briefTitle", ""),
                            "overallStatus": s.get("protocolSection", {}).get("statusModule", {}).get("overallStatus", ""),
                            "phases": ", ".join(s.get("protocolSection", {}).get("designModule", {}).get("phases", [])) or "N/A",
                            "conditions": ", ".join(s.get("protocolSection", {}).get("conditionsModule", {}).get("conditions", [])),
                        }
                        for s in resp.get("studies", [])
                    ])
                    st.session_state["guided_ct_raw"] = raw_df
                except Exception as e:
                    st.error(f"Fetch failed: {e}")

        if "guided_ct_raw" in st.session_state:
            raw_df = st.session_state["guided_ct_raw"]
            extra_issues = [
                {
                    "id": "ct_rename",
                    "label": "🏷️ Rename columns to clean PascalCase names",
                    "description": (
                        "Rename `nctId` → `NCT_ID`, `briefTitle` → `Title`, "
                        "`overallStatus` → `Status`, `phases` → `Phases`, `conditions` → `Conditions`."
                    ),
                    "fix": lambda d: (
                        d.rename(columns={
                            "nctId": "NCT_ID", "briefTitle": "Title",
                            "overallStatus": "Status", "phases": "Phases",
                            "conditions": "Conditions",
                        }),
                        "Renamed columns to PascalCase.",
                    ),
                },
            ]

    # ── Guided: WHO GHO ────────────────────────────────────────────────────────
    elif dataset_choice.startswith("📌 Guided — WHO"):
        prefix = "who"
        if st.button("▶ Fetch Data", key="fetch_who"):
            with st.spinner("Fetching from WHO GHO…"):
                try:
                    resp = requests.get(
                        "https://ghoapi.azureedge.net/api/WHOSIS_000001",
                        params={"$filter": "TimeDim ge 2000 and TimeDim le 2022"},
                        timeout=15,
                    ).json()
                    raw_df = pd.DataFrame([
                        {
                            "SpatialDim": r.get("SpatialDim"),
                            "TimeDim": r.get("TimeDim"),
                            "Dim1": r.get("Dim1"),
                            "NumericValue": r.get("NumericValue"),
                        }
                        for r in resp.get("value", [])
                    ])
                    st.session_state["guided_who_raw"] = raw_df
                except Exception as e:
                    st.error(f"Fetch failed: {e}")

        if "guided_who_raw" in st.session_state:
            raw_df = st.session_state["guided_who_raw"]
            extra_issues = [
                {
                    "id": "who_filter",
                    "label": "🔍 Filter to Both Sexes only (Dim1 == 'SEX_BTSX')",
                    "description": (
                        "The dataset contains three rows per country per year: both sexes, male, female. "
                        "Keeping only `SEX_BTSX` (both sexes) removes the sex-disaggregated duplicates."
                    ),
                    "fix": lambda d: (
                        d[d["Dim1"] == "SEX_BTSX"].drop(columns=["Dim1"]),
                        "Filtered to SEX_BTSX (both sexes) and dropped Dim1 column.",
                    ),
                },
                {
                    "id": "who_rename",
                    "label": "🏷️ Rename columns: SpatialDim → CountryCode, TimeDim → Year, NumericValue → LifeExpectancy",
                    "description": "Gives the columns clear, self-explanatory names.",
                    "fix": lambda d: (
                        d.rename(columns={
                            "SpatialDim": "CountryCode",
                            "TimeDim": "Year",
                            "NumericValue": "LifeExpectancy",
                        }),
                        "Renamed SpatialDim → CountryCode, TimeDim → Year, NumericValue → LifeExpectancy.",
                    ),
                },
                {
                    "id": "who_round",
                    "label": "🔢 Round LifeExpectancy to 1 decimal place",
                    "description": "Reduces noise in the numeric values (e.g. 72.3141 → 72.3).",
                    "fix": lambda d: (
                        d.assign(LifeExpectancy=pd.to_numeric(d.get("LifeExpectancy", d.get("NumericValue")), errors="coerce").round(1))
                        if "LifeExpectancy" in d.columns or "NumericValue" in d.columns
                        else (d, "LifeExpectancy column not found — skipped."),
                        "Rounded LifeExpectancy to 1 decimal place.",
                    ),
                },
            ]

    # ── Guided: NIH RePORTER ───────────────────────────────────────────────────
    elif dataset_choice.startswith("📌 Guided — NIH"):
        prefix = "nih"
        if st.button("▶ Fetch Data", key="fetch_nih"):
            with st.spinner("Fetching from NIH RePORTER…"):
                try:
                    resp = requests.post(
                        "https://api.reporter.nih.gov/v2/projects/search",
                        json={
                            "criteria": {
                                "advanced_text_search": {
                                    "operator": "and",
                                    "search_field": "all",
                                    "search_text": "genomics",
                                }
                            },
                            "limit": 50,
                            "offset": 0,
                        },
                        timeout=15,
                    ).json()
                    raw_df = pd.json_normalize([
                        {
                            "project_num": r.get("project_num"),
                            "project_title": str(r.get("project_title", ""))[:80],
                            "fiscal_year": r.get("fiscal_year"),
                            "award_amount": r.get("award_amount"),
                            "org_name": (r.get("organization") or {}).get("org_name"),
                            "org_city": (r.get("organization") or {}).get("org_city"),
                            "org_state": (r.get("organization") or {}).get("org_state"),
                            "agency_code": r.get("agency_code"),
                        }
                        for r in resp.get("results", [])
                    ])
                    st.session_state["guided_nih_raw"] = raw_df
                except Exception as e:
                    st.error(f"Fetch failed: {e}")

        if "guided_nih_raw" in st.session_state:
            raw_df = st.session_state["guided_nih_raw"]
            extra_issues = [
                {
                    "id": "nih_rename",
                    "label": "🏷️ Rename columns to clean PascalCase names",
                    "description": (
                        "Rename `project_num` → `ProjectNum`, `project_title` → `Title`, "
                        "`fiscal_year` → `FiscalYear`, `award_amount` → `AwardAmount`, etc."
                    ),
                    "fix": lambda d: (
                        d.rename(columns={
                            "project_num": "ProjectNum", "project_title": "Title",
                            "fiscal_year": "FiscalYear", "award_amount": "AwardAmount",
                            "org_name": "OrgName", "org_city": "OrgCity",
                            "org_state": "OrgState", "agency_code": "Agency",
                        }),
                        "Renamed columns to PascalCase.",
                    ),
                },
            ]

    # ── Guided: Congress ──────────────────────────────────────────────────────
    elif dataset_choice.startswith("📌 Guided — Congress"):
        prefix = "congress"
        if st.button("▶ Fetch Data", key="fetch_congress"):
            with st.spinner("Fetching from Congress.gov…"):
                try:
                    resp = requests.get(
                        "https://api.congress.gov/v3/bill/118",
                        params={"format": "json", "limit": 50, "api_key": "DEMO_KEY"},
                        timeout=15,
                    ).json()
                    raw_df = pd.DataFrame([
                        {
                            "number": b.get("number"),
                            "type": b.get("type"),
                            "title": str(b.get("title", ""))[:80],
                            "originChamber": b.get("originChamber"),
                            "congress": b.get("congress"),
                            "latestActionDate": (b.get("latestAction") or {}).get("actionDate"),
                            "updateDate": b.get("updateDate"),
                        }
                        for b in resp.get("bills", [])
                    ])
                    st.session_state["guided_congress_raw"] = raw_df
                except Exception as e:
                    st.error(f"Fetch failed: {e}")

        if "guided_congress_raw" in st.session_state:
            raw_df = st.session_state["guided_congress_raw"]
            extra_issues = [
                {
                    "id": "congress_rename",
                    "label": "🏷️ Rename columns to clean PascalCase names",
                    "description": (
                        "Rename `number` → `BillNumber`, `type` → `BillType`, "
                        "`originChamber` → `Chamber`, `latestActionDate` → `LatestActionDate`, etc."
                    ),
                    "fix": lambda d: (
                        d.rename(columns={
                            "number": "BillNumber", "type": "BillType",
                            "title": "Title", "originChamber": "Chamber",
                            "congress": "Congress",
                            "latestActionDate": "LatestActionDate",
                            "updateDate": "UpdateDate",
                        }),
                        "Renamed columns to PascalCase.",
                    ),
                },
            ]

    # ── BYOD ──────────────────────────────────────────────────────────────────
    elif dataset_choice.startswith("🔧"):
        prefix = "byod"
        data_source = st.radio(
            "Where is your data coming from?",
            [
                "Upload a JSON file from Day 1",
                "Carried forward from Day 1 (same browser session)",
            ],
            key="byod_source",
        )
        if data_source == "Carried forward from Day 1 (same browser session)":
            if "byod_flat_df" in st.session_state:
                raw_df = st.session_state["byod_flat_df"]
                st.success(
                    f"Loaded from Day 1 session: {len(raw_df)} rows × {len(raw_df.columns)} columns."
                )
            else:
                st.warning(
                    "No session data found. If you downloaded a JSON file from Day 1, "
                    "select **'Upload a JSON file'** above."
                )
        else:
            uploaded = st.file_uploader(
                "Upload your Day 1 JSON file",
                type=["json"],
                key="byod_upload",
            )
            if uploaded:
                try:
                    raw_df, key_used = load_json_from_upload(uploaded)
                    label = f"(key: `{key_used}`)" if key_used else ""
                    st.success(
                        f"Loaded JSON {label}: {len(raw_df)} rows × {len(raw_df.columns)} columns."
                    )
                    with st.expander("📖 What happened when you uploaded a JSON file?"):
                        st.markdown("""
The app converted your JSON into a flat table using **JSON normalization**.
Each top-level key in each record became a column.
If a field contained a nested sub-object (e.g. `organism.scientificName`),
it was flattened into a column with a dot in its name — these are automatically
detected and offered for renaming in the scan below.
                        """)
                except Exception as e:
                    st.error(f"Could not load file: {e}")

    # ── Run the uniform 6-step flow ────────────────────────────────────────────
    if raw_df is not None:
        st.markdown("---")
        render_cleaning_flow(
            raw_df,
            prefix=prefix,
            session_key="byod_clean_df",
            extra_issues=extra_issues if extra_issues else None,
        )

# ── EXPORT ─────────────────────────────────────────────────────────────────────

elif app_choice == "⬇️ Export":
    st.title("⬇️ Export Your Cleaned Data")
    st.markdown("""
Download your cleaned dataset as **CSV** or **JSON**, or carry it forward to **Day 3**
for exploration and analysis.
    """)

    if "byod_clean_df" not in st.session_state:
        st.warning(
            "No cleaned dataset found in this session. "
            "Go to **🧹 Clean Your Data** first, apply fixes, and reach Step 6."
        )
    else:
        result = st.session_state["byod_clean_df"]

        st.subheader("Dataset Summary")
        c1, c2, c3 = st.columns(3)
        c1.metric("Rows", len(result))
        c2.metric("Columns", len(result.columns))
        c3.metric("Missing Cells", int(result.isnull().sum().sum()))

        st.subheader("Preview (first 20 rows)")
        st.dataframe(result.head(20), use_container_width=True)

        st.markdown("---")
        st.subheader("Download")
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                "⬇️ Download as CSV",
                result.to_csv(index=False).encode("utf-8"),
                "day2_cleaned.csv",
                "text/csv",
                help="Best for Excel, SPSS, R, or any spreadsheet tool.",
            )
        with col2:
            st.download_button(
                "⬇️ Download as JSON",
                result.to_json(orient="records", indent=2).encode("utf-8"),
                "day2_cleaned.json",
                "application/json",
                help="Same format as the Day 1 output — useful if you want to re-upload in Day 3.",
            )

        st.markdown("---")
        st.subheader("Carry Forward to Day 3")
        st.info(
            "Your cleaned data is already saved in this browser session. "
            "Navigate to **Day 3** and select "
            "**'Carried forward from Day 2 (same browser session)'** to continue "
            "without re-uploading."
        )
        if st.button("➡️ Use This Data → Day 3"):
            st.session_state["byod_clean_df"] = result
            st.success(
                "✅ Data saved for Day 3. Navigate to Day 3 using the page links at the top of the sidebar."
            )
