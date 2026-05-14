"""
Day 3 — From Usable Data to Basic Statistics
Homogeneous six-step explore flow: four guided presets + BYOD
"""

import json
import io
import requests
import numpy as np
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Day 3 — From Usable Data to Basic Statistics",
    page_icon="📊",
    layout="wide",
)

# ── sidebar ────────────────────────────────────────────────────────────────────

st.sidebar.title("Day 3 Navigation")
app_choice = st.sidebar.radio(
    "Select section",
    [
        "Overview",
        "📊 Explore Your Data",
        "⚖️ Ethics and Open Science",
    ],
)

# ── helpers ────────────────────────────────────────────────────────────────────

def load_json_from_upload(uploaded_file):
    raw = json.load(uploaded_file)
    if isinstance(raw, list):
        df = pd.json_normalize(raw)
    elif isinstance(raw, dict):
        list_keys = [k for k, v in raw.items() if isinstance(v, list)]
        if len(list_keys) == 1:
            df = pd.json_normalize(raw[list_keys[0]])
        elif len(list_keys) > 1:
            key_used = st.selectbox(
                "Your JSON has multiple record arrays. Select the one to use:",
                list_keys, key="json_key_selector_d3",
            )
            df = pd.json_normalize(raw[key_used])
        else:
            df = pd.DataFrame([raw])
    else:
        df = pd.DataFrame()
    return df


# ── sentinel cleaner (mirrors Day 2 logic) ────────────────────────────────────
_SENTINELS = frozenset({"na", "n/a", "n.a.", "n.a", "none", "null", "nan",
                        "-", "--", "?", "unknown", "missing", ""})

def clean_sentinels(df: pd.DataFrame) -> pd.DataFrame:
    """Replace string-based missing-value placeholders with proper NaN."""
    df = df.copy()
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].apply(
            lambda v: float("nan")
            if isinstance(v, str) and v.strip().lower() in _SENTINELS
            else v
        )
    return df


def classify_columns(df):
    types = {}
    for col in df.columns:
        series = df[col].dropna()
        if series.empty:
            types[col] = "categorical"
            continue
        try:
            pd.to_numeric(series, errors="raise")
            types[col] = "numeric"
            continue
        except (ValueError, TypeError):
            pass
        try:
            parsed = pd.to_datetime(series, infer_datetime_format=True, errors="coerce")
            if parsed.notna().mean() > 0.7:
                types[col] = "date"
                continue
        except Exception:
            pass
        types[col] = "categorical"
    return types


def show_explore_flow(df, key_prefix, dataset_label):
    # Step 1
    st.markdown("### Step 1 — Dataset Overview")
    c1, c2, c3 = st.columns(3)
    c1.metric("Rows", len(df))
    c2.metric("Columns", len(df.columns))
    c3.metric("Missing Cells", int(df.isnull().sum().sum()))
    st.markdown("**First 20 rows:**")
    st.dataframe(df.head(20), use_container_width=True)

    # Step 2
    st.markdown("### Step 2 — Column Profile")
    col_types = classify_columns(df)
    profile_rows = []
    for col in df.columns:
        n_missing = int(df[col].isnull().sum())
        pct_missing = round(n_missing / len(df) * 100, 1) if len(df) > 0 else 0
        # Guard against unhashable types (lists/dicts from JSON flattening)
        try:
            n_unique = df[col].nunique()
        except TypeError:
            n_unique = df[col].apply(lambda v: str(v) if isinstance(v, (list, dict)) else v).nunique()
        profile_rows.append({
            "Column": col,
            "Detected Type": col_types[col],
            "Unique Values": n_unique,
            "Missing": n_missing,
            "% Missing": pct_missing,
        })
    st.dataframe(pd.DataFrame(profile_rows), use_container_width=True)

    # Step 3
    st.markdown("### Step 3 — Select Statistics to Compute")
    st.markdown(
        "All columns are pre-selected. Untick any column you want to skip, "
        "then click **Compute Statistics**."
    )

    # ── Select All / Select None buttons ──────────────────────────────────────
    col_list = list(df.columns)
    _btn1, _btn2, _ = st.columns([0.12, 0.12, 0.76])
    if _btn1.button("☑ Select All", key=f"{key_prefix}_selall"):
        for _c in col_list:
            st.session_state[f"{key_prefix}_sel_{_c}"] = True
    if _btn2.button("☐ Select None", key=f"{key_prefix}_selnone"):
        for _c in col_list:
            st.session_state[f"{key_prefix}_sel_{_c}"] = False

    selected_cols = []
    cols_per_row = 3
    for i in range(0, len(col_list), cols_per_row):
        row_cols = col_list[i:i + cols_per_row]
        check_cols = st.columns(cols_per_row)
        for j, col in enumerate(row_cols):
            ctype = col_types.get(col, "categorical")
            label = f"**{col}** _{ctype}_"
            if check_cols[j].checkbox(label, value=True, key=f"{key_prefix}_sel_{col}"):
                selected_cols.append(col)

    compute_btn = st.button("📊 Compute Statistics", key=f"{key_prefix}_compute")

    if compute_btn:
        if not selected_cols:
            st.warning("No columns selected.")
            return

        st.markdown("### Step 4 — Statistics")

        numeric_cols = [c for c in selected_cols if col_types.get(c) == "numeric"]
        categorical_cols = [c for c in selected_cols if col_types.get(c) == "categorical"]
        date_cols = [c for c in selected_cols if col_types.get(c) == "date"]

        if numeric_cols:
            st.markdown("#### Numeric Columns — Descriptive Statistics")
            desc = df[numeric_cols].describe().T.round(3)
            desc.index.name = "Column"
            st.dataframe(desc, use_container_width=True)

            st.markdown("#### Histograms")
            n_bins = st.slider(
                "Number of bins for histograms",
                min_value=5, max_value=100, value=20,
                key=f"{key_prefix}_bins",
            )
            for col in numeric_cols:
                series = df[col].dropna()
                if len(series) == 0:
                    continue
                st.markdown(f"**{col}**")
                try:
                    counts, bin_edges = np.histogram(series, bins=n_bins)
                    bin_labels = [f"{bin_edges[i]:.2f}-{bin_edges[i+1]:.2f}" for i in range(len(counts))]
                    hist_df = pd.DataFrame({"Bin": bin_labels, "Count": counts}).set_index("Bin")
                    st.bar_chart(hist_df)
                except Exception:
                    st.bar_chart(series.value_counts().sort_index().rename("Count"))

        if categorical_cols:
            st.markdown("#### Categorical Columns — Value Counts")
            for col in categorical_cols:
                series = df[col].dropna()
                if len(series) == 0:
                    continue
                vc = series.value_counts().head(20)
                pct = (vc / len(series) * 100).round(1)
                vc_df = pd.DataFrame({"Count": vc, "% of non-missing": pct})
                st.markdown(f"**{col}** — top {min(20, len(vc))} values")
                st.dataframe(vc_df, use_container_width=True)
                st.bar_chart(vc.rename("Count"))

        if date_cols:
            st.markdown("#### Date Columns — Records Over Time")
            for col in date_cols:
                try:
                    parsed = pd.to_datetime(df[col], infer_datetime_format=True, errors="coerce")
                    year_counts = parsed.dt.year.value_counts().sort_index()
                    st.markdown(f"**{col}** — records by year")
                    st.bar_chart(year_counts.rename("Count"))
                except Exception as ex:
                    st.warning(f"Could not parse {col} as dates: {ex}")

        st.markdown("#### Missingness Report")
        miss = df[selected_cols].isnull().sum()
        miss = miss[miss > 0]
        if miss.empty:
            st.success("No missing values in the selected columns.")
        else:
            miss_pct = (miss / len(df) * 100).round(1)
            miss_df = pd.DataFrame({"Missing Count": miss, "% Missing": miss_pct})
            st.dataframe(miss_df, use_container_width=True)
            st.bar_chart(miss_pct.rename("% Missing"))

        if len(numeric_cols) >= 2:
            st.markdown("#### Correlation Matrix (Numeric Columns)")
            with st.expander("What is a correlation matrix?"):
                st.markdown("""
A correlation matrix shows how strongly pairs of numeric columns move together.
Values range from -1 (perfect negative) to +1 (perfect positive). 0 means no linear relationship.
This is a Pearson correlation, which only detects straight-line relationships.
                """)
            corr = df[numeric_cols].corr().round(2)
            st.dataframe(corr, use_container_width=True)

        # Step 5
        st.markdown("### Step 5 — Four-Criteria Self-Assessment")
        with st.expander("What do the four criteria mean?"):
            st.markdown("""
1. **Representativeness** — Does the sample reflect the population you want to study?
2. **Completeness** — Are there systematic missing values in key fields?
3. **Consistency** — Are values recorded in the same format throughout?
4. **Validity** — Are values within expected and logically coherent ranges?
            """)

        # ── Auto-generate draft observations ──────────────────────────────────
        n_rows = len(df)
        # Representativeness
        rep_auto = f"This dataset contains {n_rows} records. "
        if n_rows < 50:
            rep_auto += "The sample is very small (<50 rows) — results may not generalise. Check whether the API page limit excluded relevant records."
            rep_light = "🔴"
        elif n_rows < 200:
            rep_auto += "The sample size is moderate. Consider whether the API page limit may have excluded relevant records or groups."
            rep_light = "🟡"
        else:
            rep_auto += "The sample size is reasonably large. Still verify that no systematic groups or time periods are excluded by the query or API limits."
            rep_light = "🟢"

        # Completeness
        if miss.empty:
            comp_auto = "No missing values were detected in the selected columns — completeness looks good."
            comp_light = "🟢"
        else:
            high_miss = miss_pct[miss_pct > 20]
            low_miss = miss_pct[(miss_pct > 0) & (miss_pct <= 20)]
            parts = []
            if not high_miss.empty:
                cols_str = ", ".join([f"`{c}` ({v:.1f}%)" for c, v in high_miss.items()])
                parts.append(f"Columns with >20% missing values: {cols_str}. These may be unreliable for analysis.")
            if not low_miss.empty:
                cols_str = ", ".join([f"`{c}` ({v:.1f}%)" for c, v in low_miss.items()])
                parts.append(f"Columns with minor missingness (≤20%): {cols_str}.")
            comp_auto = " ".join(parts)
            comp_light = "🔴" if not high_miss.empty else "🟡"

        # Consistency
        con_parts = []
        for col in categorical_cols:
            series = df[col].dropna().astype(str)
            lower_vals = series.str.lower().unique()
            actual_vals = series.unique()
            if len(lower_vals) < len(actual_vals):
                con_parts.append(f"`{col}` has values that differ only in capitalisation — consider standardising.")
            elif series.nunique() > 50:
                con_parts.append(f"`{col}` has {series.nunique()} unique values — check for spelling variants or encoding differences.")
        for col in date_cols:
            con_parts.append(f"`{col}` was detected as a date column — verify all values follow a consistent format after parsing.")
        if not con_parts:
            con_auto = "No obvious consistency issues detected in the selected columns."
            con_light = "🟢"
        else:
            con_auto = " ".join(con_parts)
            con_light = "🟡"

        # Validity
        val_parts = []
        for col in numeric_cols:
            series = df[col].dropna()
            if len(series) < 4:
                continue
            mean_val = series.mean()
            std_val = series.std()
            if std_val == 0:
                continue
            outliers = series[(series - mean_val).abs() > 3 * std_val]
            if len(outliers) > 0:
                val_parts.append(
                    f"`{col}`: {len(outliers)} value(s) are more than 3 standard deviations from the mean "
                    f"(range: {series.min():.2f} – {series.max():.2f}) — check for data entry errors or genuine extremes."
                )
        if not val_parts:
            val_auto = "No extreme outliers detected (>3 standard deviations from the mean) in numeric columns."
            val_light = "🟢"
        else:
            val_auto = " ".join(val_parts)
            val_light = "🟡"

        # ── Display the four criteria with traffic lights and editable text areas
        st.markdown(
            "**Traffic-light guide:** 🟢 No issues detected &nbsp;|&nbsp; "
            "🟡 Minor issues — review recommended &nbsp;|&nbsp; 🔴 Significant issues — action needed"
        )

        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"**1. Representativeness** {rep_light}")
            rep = st.text_area(
                "Does the sample represent your target population?",
                value=rep_auto,
                key=f"{key_prefix}_rep",
            )
            st.markdown(f"**3. Consistency** {con_light}")
            con = st.text_area(
                "Are values recorded consistently across rows?",
                value=con_auto,
                key=f"{key_prefix}_con",
            )
        with c2:
            st.markdown(f"**2. Completeness** {comp_light}")
            comp = st.text_area(
                "Are there systematic missing values?",
                value=comp_auto,
                key=f"{key_prefix}_comp",
            )
            st.markdown(f"**4. Validity** {val_light}")
            val = st.text_area(
                "Are values within expected ranges?",
                value=val_auto,
                key=f"{key_prefix}_val",
            )
        # Step 6
        st.markdown("### Step 6 — Download Summary")

        summary_parts = []
        if numeric_cols:
            desc_out = df[numeric_cols].describe().T.round(3).reset_index()
            desc_out.insert(0, "section", "Descriptive Statistics")
            summary_parts.append(desc_out.rename(columns={"index": "column"}))
        if categorical_cols:
            for col in categorical_cols:
                vc = df[col].dropna().value_counts().head(20).reset_index()
                vc.columns = ["value", "count"]
                vc.insert(0, "column", col)
                vc.insert(0, "section", "Value Counts")
                summary_parts.append(vc)
        if not miss.empty:
            miss_out = pd.DataFrame({"Missing Count": miss, "% Missing": miss_pct}).reset_index()
            miss_out.insert(0, "section", "Missingness")
            summary_parts.append(miss_out)

        if summary_parts:
            summary_csv = pd.concat(summary_parts, ignore_index=True)
            csv_bytes = summary_csv.to_csv(index=False).encode("utf-8")
            st.download_button(
                "Download Statistics Summary (CSV)",
                csv_bytes,
                f"{key_prefix}_statistics_summary.csv",
                "text/csv",
                key=f"{key_prefix}_dl_stats",
            )

        assessment_text = f"""Four-Criteria Self-Assessment -- {dataset_label}

1. Representativeness:
{rep if rep else "(not filled in)"}

2. Completeness:
{comp if comp else "(not filled in)"}

3. Consistency:
{con if con else "(not filled in)"}

4. Validity:
{val if val else "(not filled in)"}
"""
        st.download_button(
            "Download Self-Assessment (TXT)",
            assessment_text.encode("utf-8"),
            f"{key_prefix}_self_assessment.txt",
            "text/plain",
            key=f"{key_prefix}_dl_assess",
        )

        st.success(f"Exploration of **{dataset_label}** complete.")


# ══════════════════════════════════════════════════════════════════════════════
# OVERVIEW
# ══════════════════════════════════════════════════════════════════════════════

if app_choice == "Overview":
    st.title("📊 Day 3 — From Usable Data to Basic Statistics")
    st.markdown("""
**Theme:** Take the clean dataset from Day 2 and produce descriptive statistics, distributions,
and a structured self-assessment of data quality.

### What You Will Do Today
1. Load your cleaned dataset (guided example or your own Day 2 output).
2. Review the column profile — detected types, unique values, missingness.
3. Select which columns to analyse.
4. Compute descriptive statistics, histograms, value counts, and a correlation matrix.
5. Assess your dataset against four standard data quality criteria.
6. Download a statistics summary and your self-assessment.

### Four Data Quality Criteria
| Criterion | Key question |
|---|---|
| **Representativeness** | Does the sample reflect the population you want to study? |
| **Completeness** | Are there systematic missing values in key fields? |
| **Consistency** | Are values recorded in the same format throughout? |
| **Validity** | Are values within expected and logically coherent ranges? |

Use the sidebar to go to **📊 Explore Your Data** to start.
    """)

# ══════════════════════════════════════════════════════════════════════════════
# EXPLORE YOUR DATA
# ══════════════════════════════════════════════════════════════════════════════

elif app_choice == "📊 Explore Your Data":
    st.title("📊 Day 3 — Explore Your Data")
    st.markdown("""
Choose a guided example or load your own cleaned data from Day 2.
The same six-step flow applies to all datasets.
    """)

    dataset_choice = st.radio(
        "Select a dataset to explore:",
        [
            "🏥 Example 1 — ClinicalTrials.gov (Health)",
            "🌍 Example 2 — WHO Global Health Observatory (Health)",
            "🔬 Example 3 — NIH RePORTER (Life Sciences)",
            "🏛️ Example 4 — Congress.gov Bills (Social Sciences)",
            "📂 My Own Data (from Day 2)",
        ],
        key="d3_dataset_choice",
    )

    df = None
    dataset_label = ""

    if dataset_choice == "🏥 Example 1 — ClinicalTrials.gov (Health)":
        dataset_label = "ClinicalTrials.gov"
        st.markdown("**Dataset:** Clinical trials related to *diabetes* — status, phase, and conditions.")
        if st.button("▶ Fetch & Explore — ClinicalTrials.gov", key="d3_fetch_ct"):
            try:
                with st.spinner("Fetching ClinicalTrials.gov data..."):
                    r = requests.get(
                        "https://clinicaltrials.gov/api/v2/studies",
                        params={"query.cond": "diabetes", "pageSize": 50, "format": "json"},
                        timeout=30,
                    )
                    r.raise_for_status()
                    data = r.json()
                studies = data.get("studies", [])
                rows = []
                for s in studies:
                    proto = s.get("protocolSection", {})
                    id_mod = proto.get("identificationModule", {})
                    status_mod = proto.get("statusModule", {})
                    design_mod = proto.get("designModule", {})
                    cond_mod = proto.get("conditionsModule", {})
                    rows.append({
                        "NCT_ID": id_mod.get("nctId", ""),
                        "Title": str(id_mod.get("briefTitle", ""))[:60],
                        "Status": status_mod.get("overallStatus", ""),
                        "Phase": ", ".join(design_mod.get("phases", [])),
                        "Conditions": ", ".join(cond_mod.get("conditions", [])[:2]),
                    })
                df_fetched = clean_sentinels(pd.DataFrame(rows))
                st.session_state["d3_example_df"] = df_fetched
                st.session_state["d3_example_label"] = dataset_label
            except Exception as e:
                st.error(f"Could not load data: {e}")
        if "d3_example_df" in st.session_state and st.session_state.get("d3_example_label") == dataset_label:
            df = st.session_state["d3_example_df"]

    elif dataset_choice == "🌍 Example 2 — WHO Global Health Observatory (Health)":
        dataset_label = "WHO GHO"
        st.markdown("**Dataset:** Life expectancy at birth — country, year, and value (Both sexes only).")
        if st.button("▶ Fetch & Explore — WHO GHO", key="d3_fetch_who"):
            try:
                with st.spinner("Fetching WHO GHO data..."):
                    r = requests.get(
                        "https://ghoapi.azureedge.net/api/WHOSIS_000001",
                        params={"$top": 300}, timeout=30,
                    )
                    r.raise_for_status()
                    data = r.json()
                records = data.get("value", [])
                df_fetched = pd.DataFrame([{
                    "CountryCode": rec.get("SpatialDim", ""),
                    "Year": rec.get("TimeDim", ""),
                    "LifeExpectancy": rec.get("NumericValue", None),
                } for rec in records if rec.get("Dim1") == "SEX_BTSX"])
                st.session_state["d3_example_df"] = clean_sentinels(df_fetched)
                st.session_state["d3_example_label"] = dataset_label
            except Exception as e:
                st.error(f"Could not load data: {e}")
        if "d3_example_df" in st.session_state and st.session_state.get("d3_example_label") == dataset_label:
            df = st.session_state["d3_example_df"]

    elif dataset_choice == "🔬 Example 3 — NIH RePORTER (Life Sciences)":
        dataset_label = "NIH RePORTER"
        st.markdown("**Dataset:** NIH research grants related to *genomics* — title, agency, fiscal year, award amount.")
        if st.button("▶ Fetch & Explore — NIH RePORTER", key="d3_fetch_nih"):
            try:
                with st.spinner("Fetching NIH RePORTER data..."):
                    r = requests.post(
                        "https://api.reporter.nih.gov/v2/projects/search",
                        json={
                            "criteria": {"advanced_text_search": {
                                "operator": "and",
                                "search_field": "all",
                                "search_text": "genomics",
                            }},
                            "offset": 0, "limit": 50,
                        },
                        headers={"Content-Type": "application/json"},
                        timeout=30,
                    )
                    r.raise_for_status()
                    data = r.json()
                results = data.get("results", [])
                df_fetched = pd.DataFrame([{
                    "ProjectTitle": str(p.get("project_title", ""))[:60],
                    "AgencyCode": p.get("agency_code", ""),
                    "FiscalYear": p.get("fiscal_year", ""),
                    "AwardAmount": p.get("award_amount", None),
                    "ProjectStartDate": p.get("project_start_date", ""),
                } for p in results])
                st.session_state["d3_example_df"] = clean_sentinels(df_fetched)
                st.session_state["d3_example_label"] = dataset_label
            except Exception as e:
                st.error(f"Could not load data: {e}")
        if "d3_example_df" in st.session_state and st.session_state.get("d3_example_label") == dataset_label:
            df = st.session_state["d3_example_df"]

    elif dataset_choice == "🏙️ Example 4 — Congress.gov Bills (Social Sciences)":
        dataset_label = "Congress.gov Bills"
        st.markdown("**Dataset:** Bills introduced in the 118th US Congress — title, type, chamber, latest action.")
        congress_key = st.text_input("Congress.gov API Key", type="password", key="d3_congress_key")
        if st.button("▶ Fetch & Explore — Congress.gov", key="d3_fetch_congress"):
            if not congress_key:
                st.warning("Please enter your Congress.gov API key.")
            else:
                try:
                    with st.spinner("Fetching Congress.gov data..."):
                        r = requests.get(
                            "https://api.congress.gov/v3/bill/118",
                            params={"limit": 50, "api_key": congress_key},
                            timeout=30,
                        )
                        r.raise_for_status()
                        data = r.json()
                    bills = data.get("bills", [])
                    df_fetched = pd.DataFrame([{
                        "BillNumber": f"{b.get('type','')}{b.get('number','')}",
                        "Title": str(b.get("title", ""))[:60],
                        "BillType": b.get("type", ""),
                        "OriginChamber": b.get("originChamber", ""),
                        "LatestActionDate": b.get("latestAction", {}).get("actionDate", ""),
                    } for b in bills])
                    st.session_state["d3_example_df"] = clean_sentinels(df_fetched)
                    st.session_state["d3_example_label"] = dataset_label
                except Exception as e:
                    st.error(f"Could not load data: {e}")
        if "d3_example_df" in st.session_state and st.session_state.get("d3_example_label") == dataset_label:
            df = st.session_state["d3_example_df"]

    elif dataset_choice == "📂 My Own Data (from Day 2)":
        dataset_label = "My Own Data"
        data_source = st.radio(
            "How do you want to load your data?",
            [
                "Carried forward from Day 2 (same browser session)",
                "Upload a CSV file (downloaded from Day 2)",
                "Upload a JSON file (downloaded from Day 1 or Day 2)",
            ],
            key="d3_byod_source",
        )
        if data_source == "Carried forward from Day 2 (same browser session)":
            if "byod_clean_df" in st.session_state:
                df = st.session_state["byod_clean_df"]
                st.success(f"Loaded cleaned dataset from Day 2 session ({len(df)} rows x {len(df.columns)} cols).")
            elif "byod_flat_df" in st.session_state:
                df = st.session_state["byod_flat_df"]
                st.info(f"No cleaned dataset found -- using raw Day 1 dataset ({len(df)} rows x {len(df.columns)} cols).")
            else:
                st.warning("No dataset found in this session. Go to Day 1 to collect data, or upload a file below.")
        elif data_source == "Upload a CSV file (downloaded from Day 2)":
            uploaded = st.file_uploader("Upload your cleaned CSV file", type=["csv"], key="d3_upload_csv")
            if uploaded:
                try:
                    df = pd.read_csv(uploaded)
                    st.success(f"Loaded {len(df)} rows x {len(df.columns)} cols from CSV.")
                except Exception as e:
                    st.error(f"Could not read CSV: {e}")
        else:
            uploaded = st.file_uploader("Upload your JSON file", type=["json"], key="d3_upload_json")
            if uploaded:
                try:
                    df = load_json_from_upload(uploaded)
                    st.success(f"Loaded {len(df)} rows x {len(df.columns)} cols from JSON.")
                except Exception as e:
                    st.error(f"Could not read JSON: {e}")

    if df is not None and len(df) > 0:
        st.markdown("---")
        show_explore_flow(df, key_prefix=f"d3_{dataset_label.replace(' ', '_')}", dataset_label=dataset_label)
    elif df is not None and len(df) == 0:
        st.warning("The loaded dataset is empty. Please check your source.")

# ══════════════════════════════════════════════════════════════════════════════
# ETHICS AND OPEN SCIENCE
# ══════════════════════════════════════════════════════════════════════════════

elif app_choice == "⚖️ Ethics and Open Science":
    st.title("⚖️ Ethics of Web Scraping and Digital Data Collection")
    st.markdown("""
Ethical considerations in web scraping are **not optional** — they are part of research design.
---
### Legal Considerations
- **Terms of Service**: Review the ToS of every source before collecting data.
  Many platforms prohibit automated access.
- **Copyright**: Scraped content may be protected. Facts are generally not copyrightable,
  but compilations may be.
- **GDPR / Privacy law**: If data includes personal information about EU residents,
  GDPR applies regardless of where you are located.
---
### Privacy Considerations
- **Publicly accessible does not mean appropriate to collect and publish**.
  Consider whether individuals would expect their information to be used for research.
- **Pseudonymization**: Remove or hash identifiers before sharing data.
- **Sensitive categories**: Health, political opinion, religion, and sexual orientation
  require extra care under most privacy frameworks.
---
### Responsible Scraping
| Practice | Why It Matters |
|----------|---------------|
| Use APIs when available | APIs are the intended access method; HTML scraping may violate ToS |
| Respect robots.txt | Signals which pages the site owner permits automated access to |
| Add delays between requests | Avoids overloading servers (rate limiting) |
| Cache data locally | Reduces repeated requests to the same source |
| Preserve raw files | Enables replication and error detection |
---
### Open Science
- Publish your **processing log** and **metadata sheet** alongside the dataset.
- Deposit raw and cleaned data in an open repository (OSF, Zenodo, Harvard Dataverse).
- Link your data to the scripts that produced it (GitHub + DOI via Zenodo).
- Acknowledge limitations explicitly in your methods section.
---
### Key References
- Brown et al. (2025). Web scraping for research: Legal, ethical, institutional, and scientific considerations. *Big Data & Society*.
- Boudourides, M. (2025). *Web Scraping and Data Collection for Life and Social Sciences*. Northwestern University.
    """)
