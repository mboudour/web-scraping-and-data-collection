"""
Day 2 — From Raw Output to Usable Data
Goal: Clean and preprocess JSON data collected in Day 1, then export as CSV.
Structure:
  - Overview
  - 🧹 Clean Your Data  (guided examples + BYOD wizard)
  - ⬇️ Export
"""

import json
import io
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
    [
        "Overview",
        "🧹 Clean Your Data",
        "⬇️ Export",
    ],
)

# ── helpers ────────────────────────────────────────────────────────────────────

def load_json_from_upload(uploaded_file):
    """Load a JSON file uploaded via st.file_uploader into a flat DataFrame."""
    raw = json.load(uploaded_file)
    if isinstance(raw, list):
        df = pd.json_normalize(raw)
        key_used = None
    elif isinstance(raw, dict):
        list_keys = [k for k, v in raw.items() if isinstance(v, list)]
        if len(list_keys) == 1:
            df = pd.json_normalize(raw[list_keys[0]])
            key_used = list_keys[0]
        elif len(list_keys) > 1:
            key_used = st.selectbox(
                "Your JSON has multiple record arrays. Select the one to use:",
                list_keys,
                key="json_key_selector",
            )
            df = pd.json_normalize(raw[key_used])
        else:
            df = pd.DataFrame([raw])
            key_used = None
    else:
        df = pd.DataFrame()
        key_used = None
    return df, key_used


def show_cleaning_ops(df, key_prefix):
    """Render the cleaning controls and return (result_df, log) after button click."""

    with st.expander("📖 What does each operation do?", expanded=False):
        st.markdown("""
| Operation | When to use it | What it does |
|---|---|---|
| **Remove duplicate rows** | Same record appears more than once | Keeps only the first occurrence |
| **Drop rows with missing values** | A key column has blanks you cannot fill | Removes rows where the selected column is empty |
| **Strip whitespace** | Text fields have invisible spaces | Trims spaces so `" insulin "` → `"insulin"` |
| **Rename a column** | Column name is unclear or has dots from JSON flattening | Gives the column a new name |
| **Convert to numeric** | A number column contains text (e.g. `"1,200"` or `"N/A"`) | Forces to numbers; unreadable values → blank |
| **Parse as dates** | A date column is stored as text in various formats | Converts to standard `YYYY-MM-DD` |
| **Standardize to UPPERCASE** | Text column has mixed case (`"Male"`, `"male"`, `"M"`) | Makes all values consistently uppercase |
| **Filter rows by value** | You only want a subset of the data | Keeps only rows matching the values you choose |
        """)

    c1, c2 = st.columns(2)

    with c1:
        st.markdown("**Row-level operations**")
        drop_dupes = st.checkbox("Remove duplicate rows", key=f"{key_prefix}_dupes")
        drop_na_cols = st.multiselect(
            "Drop rows where these columns are missing",
            df.columns.tolist(),
            key=f"{key_prefix}_dropna",
        )
        strip_ws = st.checkbox(
            "Strip leading/trailing whitespace from all text columns",
            key=f"{key_prefix}_strip",
        )

    with c2:
        st.markdown("**Column-level operations**")
        rename_col = st.selectbox(
            "Rename a column",
            ["— none —"] + df.columns.tolist(),
            key=f"{key_prefix}_rename_col",
        )
        new_name = None
        if rename_col != "— none —":
            new_name = st.text_input(
                f"New name for '{rename_col}'",
                value=rename_col,
                key=f"{key_prefix}_new_name",
            )
        coerce_col = st.selectbox(
            "Convert a column to numeric",
            ["— none —"] + df.columns.tolist(),
            key=f"{key_prefix}_coerce",
        )
        date_col = st.selectbox(
            "Parse a column as dates",
            ["— none —"] + df.columns.tolist(),
            key=f"{key_prefix}_date",
        )
        upper_col = st.selectbox(
            "Standardize a column to UPPERCASE",
            ["— none —"] + df.columns.tolist(),
            key=f"{key_prefix}_upper",
        )

    st.markdown("**Row filtering**")
    filter_col = st.selectbox(
        "Filter rows by column value",
        ["— none —"] + df.columns.tolist(),
        key=f"{key_prefix}_filter_col",
    )
    keep_vals = []
    if filter_col != "— none —":
        unique_vals = df[filter_col].dropna().unique().tolist()
        keep_vals = st.multiselect(
            f"Keep rows where '{filter_col}' equals:",
            unique_vals,
            default=unique_vals[: min(5, len(unique_vals))],
            key=f"{key_prefix}_keep_vals",
        )

    result = None
    log = []

    if st.button("✅ Apply All Cleaning Operations", key=f"{key_prefix}_apply"):
        result = df.copy()

        if drop_dupes:
            before = len(result)
            result = result.drop_duplicates()
            log.append(f"Removed {before - len(result)} duplicate rows.")

        if drop_na_cols:
            before = len(result)
            result = result.dropna(subset=drop_na_cols)
            log.append(
                f"Dropped {before - len(result)} rows with missing values in: {drop_na_cols}."
            )

        if strip_ws:
            str_cols = result.select_dtypes(include="object").columns
            result[str_cols] = result[str_cols].apply(lambda c: c.str.strip())
            log.append(f"Stripped whitespace from {len(str_cols)} text columns.")

        if rename_col != "— none —" and new_name and new_name != rename_col:
            result = result.rename(columns={rename_col: new_name})
            log.append(f"Renamed column '{rename_col}' → '{new_name}'.")

        if coerce_col != "— none —":
            result[coerce_col] = pd.to_numeric(result[coerce_col], errors="coerce")
            log.append(
                f"Converted '{coerce_col}' to numeric (non-numeric values → blank)."
            )

        if date_col != "— none —":
            try:
                result[date_col] = pd.to_datetime(
                    result[date_col], errors="coerce"
                ).dt.strftime("%Y-%m-%d")
                log.append(f"Parsed '{date_col}' as dates (format: YYYY-MM-DD).")
            except Exception as e:
                log.append(f"Could not parse '{date_col}' as dates: {e}")

        if upper_col != "— none —":
            result[upper_col] = result[upper_col].astype(str).str.upper()
            log.append(f"Standardized '{upper_col}' to UPPERCASE.")

        if filter_col != "— none —" and keep_vals:
            before = len(result)
            result = result[result[filter_col].isin(keep_vals)]
            log.append(
                f"Filtered '{filter_col}': kept {len(keep_vals)} value(s), "
                f"removed {before - len(result)} rows."
            )

    return result, log


def show_result(result, log, session_key="byod_clean_df"):
    """Display processing log, cleaned preview, missingness report, and save to session."""
    st.subheader("📋 Processing Log")
    if log:
        for entry in log:
            st.write(f"✅ {entry}")
    else:
        st.info("No operations were applied — the data is unchanged.")

    st.write(
        f"**Final dataset:** {len(result)} rows × {len(result.columns)} columns"
    )

    st.subheader("✅ Cleaned Dataset Preview")
    st.dataframe(result.head(20), use_container_width=True)

    st.subheader("🔍 Missingness Report")
    miss = result.isnull().sum()
    miss = miss[miss > 0]
    if miss.empty:
        st.success("No missing values in cleaned dataset.")
    else:
        st.dataframe(
            miss.rename("Missing Count").to_frame(), use_container_width=True
        )

    st.session_state[session_key] = result
    st.info(
        "✅ Cleaned data saved to this session. "
        "Go to **⬇️ Export** in the sidebar to download it, "
        "or carry it forward to **Day 3**."
    )


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

1. Load the JSON file you collected in Day 1 (from session or by uploading).
2. See how each cleaning problem appears in a real dataset (guided examples).
3. Apply cleaning operations interactively to your own data.
4. Export a clean CSV ready for Day 3.

Use the sidebar to go to **🧹 Clean Your Data** to start.
    """)

# ── CLEAN YOUR DATA ────────────────────────────────────────────────────────────

elif app_choice == "🧹 Clean Your Data":
    st.title("🧹 Clean Your Data")

    st.markdown("""
This section has two parts:

- **📌 Guided Examples** — see how the four Day 1 datasets are cleaned, step by step.
- **🔧 Clean Your Own Data** — apply the same operations to your own Day 1 JSON.
    """)

    # ── Guided Examples ────────────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("📌 Guided Examples")
    st.markdown(
        "Each example fetches the same dataset as the Day 1 preset, "
        "then applies a specific set of cleaning operations so you can see exactly what changes."
    )

    EXAMPLES = [
        {
            "label": "🏥 ClinicalTrials.gov — Flatten nested JSON, standardize phase labels",
            "key": "ct",
            "fetch": lambda: requests.get(
                "https://clinicaltrials.gov/api/v2/studies",
                params={
                    "query.cond": "diabetes",
                    "query.intr": "insulin",
                    "pageSize": 50,
                    "format": "json",
                },
                timeout=15,
            ).json(),
            "extract": lambda raw: pd.json_normalize(
                [
                    {
                        "nctId": s.get("protocolSection", {})
                        .get("identificationModule", {})
                        .get("nctId", ""),
                        "briefTitle": s.get("protocolSection", {})
                        .get("identificationModule", {})
                        .get("briefTitle", ""),
                        "overallStatus": s.get("protocolSection", {})
                        .get("statusModule", {})
                        .get("overallStatus", ""),
                        "phases": ", ".join(
                            s.get("protocolSection", {})
                            .get("designModule", {})
                            .get("phases", [])
                        )
                        or "N/A",
                        "conditions": ", ".join(
                            s.get("protocolSection", {})
                            .get("conditionsModule", {})
                            .get("conditions", [])
                        ),
                    }
                    for s in raw.get("studies", [])
                ]
            ),
            "clean": lambda df: (
                df.dropna(subset=["nctId"])
                .drop_duplicates(subset=["nctId"])
                .assign(
                    briefTitle=df["briefTitle"].str.strip(),
                    overallStatus=df["overallStatus"].str.upper(),
                )
                .rename(
                    columns={
                        "nctId": "NCT_ID",
                        "briefTitle": "Title",
                        "overallStatus": "Status",
                        "phases": "Phases",
                        "conditions": "Conditions",
                    }
                )
            ),
            "steps": [
                "Extracted `nctId`, `briefTitle`, `overallStatus`, `phases`, `conditions` from nested JSON",
                "Converted `phases` list to comma-separated string; filled empty with `N/A`",
                "Stripped whitespace from `briefTitle`",
                "Standardized `overallStatus` to UPPERCASE → renamed to `Status`",
                "Dropped records with missing `nctId`; removed duplicates",
            ],
        },
        {
            "label": "🌍 WHO GHO — Filter sex categories, rename columns",
            "key": "who",
            "fetch": lambda: requests.get(
                "https://ghoapi.azureedge.net/api/WHOSIS_000001",
                params={"$filter": "TimeDim ge 2000 and TimeDim le 2022"},
                timeout=15,
            ).json(),
            "extract": lambda raw: pd.DataFrame(
                [
                    {
                        "SpatialDim": r.get("SpatialDim"),
                        "TimeDim": r.get("TimeDim"),
                        "Dim1": r.get("Dim1"),
                        "NumericValue": r.get("NumericValue"),
                    }
                    for r in raw.get("value", [])
                ]
            ),
            "clean": lambda df: (
                df[df["Dim1"] == "SEX_BTSX"]
                .drop(columns=["Dim1"])
                .rename(
                    columns={
                        "SpatialDim": "CountryCode",
                        "TimeDim": "Year",
                        "NumericValue": "LifeExpectancy",
                    }
                )
                .dropna(subset=["LifeExpectancy"])
                .assign(LifeExpectancy=lambda d: d["LifeExpectancy"].round(1))
                .drop_duplicates()
                .reset_index(drop=True)
            ),
            "steps": [
                "Filtered to `Dim1 == 'SEX_BTSX'` (Both sexes) — removes sex-disaggregated duplicates",
                "Dropped the `Dim1` column (no longer needed after filtering)",
                "Renamed: `SpatialDim` → `CountryCode`, `TimeDim` → `Year`, `NumericValue` → `LifeExpectancy`",
                "Dropped records with missing `LifeExpectancy`",
                "Rounded `LifeExpectancy` to 1 decimal place",
            ],
        },
        {
            "label": "🔬 NIH RePORTER — Extract nested org fields, coerce award amounts",
            "key": "nih",
            "fetch": lambda: requests.post(
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
            ).json(),
            "extract": lambda raw: pd.json_normalize(
                [
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
                    for r in raw.get("results", [])
                ]
            ),
            "clean": lambda df: (
                df.dropna(subset=["project_num"])
                .drop_duplicates(subset=["project_num"])
                .assign(
                    award_amount=pd.to_numeric(df["award_amount"], errors="coerce"),
                    project_title=df["project_title"].str.strip(),
                )
                .rename(
                    columns={
                        "project_num": "ProjectNum",
                        "project_title": "Title",
                        "fiscal_year": "FiscalYear",
                        "award_amount": "AwardAmount",
                        "org_name": "OrgName",
                        "org_city": "OrgCity",
                        "org_state": "OrgState",
                        "agency_code": "Agency",
                    }
                )
            ),
            "steps": [
                "Extracted `org_name`, `org_city`, `org_state` from nested `organization` object",
                "Coerced `award_amount` to numeric — non-numeric values become blank (`NaN`)",
                "Stripped whitespace from `project_title`",
                "Dropped records with missing `project_num`; removed duplicates",
                "Renamed all columns to clean PascalCase names",
            ],
        },
        {
            "label": "🏛️ Congress.gov — Parse dates, standardize bill type labels",
            "key": "congress",
            "fetch": lambda: requests.get(
                "https://api.congress.gov/v3/bill/118",
                params={"format": "json", "limit": 50, "api_key": "DEMO_KEY"},
                timeout=15,
            ).json(),
            "extract": lambda raw: pd.DataFrame(
                [
                    {
                        "number": b.get("number"),
                        "type": b.get("type"),
                        "title": str(b.get("title", ""))[:80],
                        "originChamber": b.get("originChamber"),
                        "congress": b.get("congress"),
                        "latestActionDate": (b.get("latestAction") or {}).get(
                            "actionDate"
                        ),
                        "updateDate": b.get("updateDate"),
                    }
                    for b in raw.get("bills", [])
                ]
            ),
            "clean": lambda df: (
                df.dropna(subset=["number"])
                .drop_duplicates(subset=["number"])
                .assign(
                    type=df["type"].str.upper().str.strip(),
                    title=df["title"].str.strip(),
                    latestActionDate=pd.to_datetime(
                        df["latestActionDate"], errors="coerce"
                    ).dt.strftime("%Y-%m-%d"),
                    updateDate=pd.to_datetime(
                        df["updateDate"], errors="coerce"
                    ).dt.strftime("%Y-%m-%d"),
                )
                .rename(
                    columns={
                        "number": "BillNumber",
                        "type": "BillType",
                        "title": "Title",
                        "originChamber": "Chamber",
                        "congress": "Congress",
                        "latestActionDate": "LatestActionDate",
                        "updateDate": "UpdateDate",
                    }
                )
            ),
            "steps": [
                "Extracted `latestActionDate` from nested `latestAction` object",
                "Parsed `latestActionDate` and `updateDate` strings to `YYYY-MM-DD` format",
                "Stripped whitespace from `title`",
                "Standardized `type` to UPPERCASE",
                "Dropped records with missing `number`; removed duplicates",
                "Renamed all columns to clean PascalCase names",
            ],
        },
    ]

    for ex in EXAMPLES:
        with st.expander(ex["label"], expanded=False):
            if st.button(f"▶ Run this example", key=f"run_{ex['key']}"):
                with st.spinner("Fetching and cleaning data…"):
                    try:
                        raw = ex["fetch"]()
                        raw_df = ex["extract"](raw)
                        clean_df = ex["clean"](raw_df)

                        st.markdown("**Raw vs. Cleaned — Side-by-Side**")
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown(
                                f"**Raw** — {len(raw_df)} rows × {len(raw_df.columns)} cols"
                            )
                            st.dataframe(raw_df.head(10), use_container_width=True)
                        with col2:
                            st.markdown(
                                f"**Cleaned** — {len(clean_df)} rows × {len(clean_df.columns)} cols"
                            )
                            st.dataframe(clean_df.head(10), use_container_width=True)

                        st.markdown("**Cleaning Operations Applied**")
                        for i, step in enumerate(ex["steps"], 1):
                            st.write(f"{i}. {step}")

                        st.session_state["byod_clean_df"] = clean_df
                        st.success(
                            f"✅ Cleaned dataset saved to session ({len(clean_df)} rows × "
                            f"{len(clean_df.columns)} cols). "
                            "Go to **⬇️ Export** to download it."
                        )
                    except Exception as e:
                        st.error(f"Error: {e}")

    # ── BYOD Cleaning Wizard ───────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("🔧 Clean Your Own Data")

    st.markdown("""
Load the JSON file you downloaded from **Day 1**, or use the data carried forward
in the same browser session. Then apply cleaning operations interactively.
    """)

    st.markdown("#### ⚙️ Load Your Data")

    data_source = st.radio(
        "Where is your data coming from?",
        [
            "Upload a JSON file from Day 1",
            "Carried forward from Day 1 (same browser session)",
        ],
        key="byod_source",
    )

    df = None

    if data_source == "Carried forward from Day 1 (same browser session)":
        if "byod_flat_df" in st.session_state:
            df = st.session_state["byod_flat_df"]
            st.success(
                f"Loaded from Day 1 session: {len(df)} rows × {len(df.columns)} columns."
            )
        else:
            st.warning(
                "No session data found. Session data is only available if you collected "
                "data in Day 1 during the same browser session without refreshing. "
                "If you downloaded a JSON file from Day 1, select **'Upload a JSON file'** above."
            )
    else:
        uploaded = st.file_uploader(
            "Upload your Day 1 JSON file",
            type=["json"],
            key="byod_upload",
            help="Upload the JSON file downloaded from Day 1 (API data or scraped table).",
        )
        if uploaded:
            try:
                df, key_used = load_json_from_upload(uploaded)
                if key_used:
                    st.success(
                        f"Loaded JSON (key: `{key_used}`): "
                        f"{len(df)} rows × {len(df.columns)} columns."
                    )
                else:
                    st.success(
                        f"Loaded JSON: {len(df)} rows × {len(df.columns)} columns."
                    )
                with st.expander("📖 What happened when you uploaded a JSON file?"):
                    st.markdown("""
The app converted your JSON into a flat table using **JSON normalization**.
Each top-level key in each record became a column.

If a field contained a nested sub-object (e.g. `organism.scientificName`),
it was flattened into a column with a dot in its name.
You can rename these columns using the **Rename a column** operation below.
                    """)
            except Exception as e:
                st.error(f"Could not load file: {e}")

    if df is not None:
        st.markdown("---")
        st.subheader("🔍 Raw Data Preview")
        c1, c2, c3 = st.columns(3)
        c1.metric("Rows", len(df))
        c2.metric("Columns", len(df.columns))
        c3.metric("Missing Cells", int(df.isnull().sum().sum()))
        st.dataframe(df.head(20), use_container_width=True)

        st.markdown("---")
        st.subheader("🔎 Automatic Data Quality Scan")
        st.markdown(
            "The app has scanned your dataset and found the following issues. "
            "Each issue is **pre-selected** — untick any you want to skip, "
            "then click **Apply Selected Fixes**."
        )

        # ── Diagnostic detection ──────────────────────────────────────────────
        issues = []  # list of dicts: {id, label, description, fix_fn}

        # 1. Duplicate rows
        n_dupes = df.duplicated().sum()
        if n_dupes > 0:
            issues.append({
                "id": "dupes",
                "label": f"🔁 Remove {n_dupes} duplicate row(s)",
                "description": f"Found **{n_dupes}** rows that are exact copies of another row.",
                "fix": lambda d: (d.drop_duplicates(), f"Removed {n_dupes} duplicate rows."),
            })

        # 2. Missing values per column
        miss_counts = df.isnull().sum()
        miss_cols = miss_counts[miss_counts > 0]
        for col, cnt in miss_cols.items():
            pct = 100 * cnt / len(df)
            col_snap = col  # capture for lambda
            cnt_snap = int(cnt)
            issues.append({
                "id": f"miss_{col_snap}",
                "label": f"🕳️ Drop rows missing `{col_snap}` ({cnt_snap} rows, {pct:.0f}%)",
                "description": (
                    f"Column **`{col_snap}`** has **{cnt_snap}** empty values ({pct:.0f}% of rows). "
                    "Dropping these rows removes incomplete records."
                ),
                "fix": lambda d, c=col_snap, n=cnt_snap: (
                    d.dropna(subset=[c]),
                    f"Dropped {n} rows with missing values in '{c}'.",
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
                "id": "whitespace",
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

        # 4. Columns that look like dates stored as text
        date_candidates = []
        date_pattern = r"^\d{4}[-/]\d{2}[-/]\d{2}|^\d{2}[-/]\d{2}[-/]\d{4}"
        for c in str_cols:
            sample = df[c].dropna().astype(str).head(20)
            if sample.str.match(date_pattern).mean() > 0.7:
                date_candidates.append(c)
        for col in date_candidates:
            col_snap = col
            issues.append({
                "id": f"date_{col_snap}",
                "label": f"📅 Parse `{col_snap}` as dates",
                "description": (
                    f"Column **`{col_snap}`** appears to contain dates stored as text. "
                    "Converting to `YYYY-MM-DD` enables correct sorting and filtering."
                ),
                "fix": lambda d, c=col_snap: (
                    d.assign(**{c: pd.to_datetime(d[c], errors="coerce").dt.strftime("%Y-%m-%d")}),
                    f"Parsed '{c}' as dates (YYYY-MM-DD).",
                ),
            })

        # 5. Columns that look numeric but are stored as object
        numeric_candidates = []
        for c in str_cols:
            sample = df[c].dropna().astype(str).head(30)
            cleaned = sample.str.replace(r"[\$,\s%]", "", regex=True)
            if pd.to_numeric(cleaned, errors="coerce").notna().mean() > 0.7:
                numeric_candidates.append(c)
        for col in numeric_candidates:
            col_snap = col
            issues.append({
                "id": f"num_{col_snap}",
                "label": f"🔢 Convert `{col_snap}` to numeric",
                "description": (
                    f"Column **`{col_snap}`** contains mostly numbers stored as text. "
                    "Converting enables arithmetic, sorting, and statistics."
                ),
                "fix": lambda d, c=col_snap: (
                    d.assign(**{c: pd.to_numeric(d[c], errors="coerce")}),
                    f"Converted '{c}' to numeric.",
                ),
            })

        # 6. Mixed-case text columns (label inconsistency)
        mixed_case_cols = []
        for c in str_cols:
            vals = df[c].dropna().astype(str).unique()
            if len(vals) >= 2:
                lower_vals = set(v.lower() for v in vals)
                if len(lower_vals) < len(vals):
                    mixed_case_cols.append(c)
        for col in mixed_case_cols:
            col_snap = col
            issues.append({
                "id": f"case_{col_snap}",
                "label": f"🔤 Standardize `{col_snap}` to UPPERCASE (mixed case detected)",
                "description": (
                    f"Column **`{col_snap}`** has values that differ only in capitalisation "
                    f"(e.g. `Male` and `male`). Standardising prevents incorrect group counts."
                ),
                "fix": lambda d, c=col_snap: (
                    d.assign(**{c: d[c].astype(str).str.upper()}),
                    f"Standardized '{c}' to UPPERCASE.",
                ),
            })

        # 7. Dot-separated column names from JSON flattening
        dot_cols = [c for c in df.columns if "." in str(c)]
        if dot_cols:
            issues.append({
                "id": "dotcols",
                "label": f"🏷️ Rename {len(dot_cols)} dot-separated column(s) from JSON flattening",
                "description": (
                    f"These columns have dots in their names from nested JSON: "
                    f"**{', '.join(dot_cols[:5])}{'…' if len(dot_cols) > 5 else ''}**. "
                    "Dots are replaced with underscores for compatibility with most tools."
                ),
                "fix": lambda d, cols=dot_cols: (
                    d.rename(columns={c: c.replace(".", "_") for c in cols}),
                    f"Renamed {len(cols)} dot-separated column(s) (dots → underscores).",
                ),
            })

        # ── Render checkboxes ─────────────────────────────────────────────────
        if not issues:
            st.success(
                "✅ No common data quality issues detected in this dataset. "
                "Your data looks clean — you can go straight to **⬇️ Export**."
            )
        else:
            st.markdown(f"**{len(issues)} issue(s) detected:**")
            selected = {}
            for issue in issues:
                with st.container():
                    col_cb, col_desc = st.columns([0.05, 0.95])
                    with col_cb:
                        selected[issue["id"]] = st.checkbox(
                            "", value=True, key=f"diag_{issue['id']}"
                        )
                    with col_desc:
                        st.markdown(f"**{issue['label']}**")
                        st.caption(issue["description"])

            st.markdown("---")
            if st.button("✅ Apply Selected Fixes", key="byod_apply_diag"):
                result = df.copy()
                log = []
                for issue in issues:
                    if selected.get(issue["id"], False):
                        try:
                            result, entry = issue["fix"](result)
                            log.append(entry)
                        except Exception as e:
                            log.append(f"⚠️ Could not apply '{issue['label']}': {e}")

                st.subheader("📋 Processing Log")
                if log:
                    for entry in log:
                        st.write(f"✅ {entry}")
                else:
                    st.info("No fixes were selected.")

                st.write(
                    f"**Final dataset:** {len(result)} rows × {len(result.columns)} columns"
                )
                st.subheader("✅ Cleaned Dataset Preview")
                st.dataframe(result.head(20), use_container_width=True)

                miss = result.isnull().sum()
                miss = miss[miss > 0]
                st.subheader("🔍 Remaining Missingness")
                if miss.empty:
                    st.success("No missing values in cleaned dataset.")
                else:
                    st.dataframe(
                        miss.rename("Missing Count").to_frame(), use_container_width=True
                    )

                st.session_state["byod_clean_df"] = result
                st.info(
                    "✅ Cleaned data saved to this session. "
                    "Go to **⬇️ Export** in the sidebar to download it."
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
            "Go to **🧹 Clean Your Data** first and apply at least one cleaning operation "
            "(or run a guided example)."
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
            csv_out = result.to_csv(index=False).encode("utf-8")
            st.download_button(
                "⬇️ Download as CSV",
                csv_out,
                "day2_cleaned.csv",
                "text/csv",
                help="Best for Excel, SPSS, R, or any spreadsheet tool.",
            )

        with col2:
            json_out = result.to_json(orient="records", indent=2).encode("utf-8")
            st.download_button(
                "⬇️ Download as JSON",
                json_out,
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
