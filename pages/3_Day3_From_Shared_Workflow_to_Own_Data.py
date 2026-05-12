"""
Day 3 — From Shared Workflow to Participants' Own Data
Applications: World Bank (explore), GBIF, and participant-uploaded data
+ Bring Your Own Data — Explore
"""

import os, json, io
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Day 3 — From Shared Workflow to Own Data", page_icon="🔍", layout="wide")

# Robust cache path — works locally and on Streamlit Cloud
import pathlib
_repo_root = pathlib.Path(__file__).resolve().parent
if _repo_root.name == "pages":
    _repo_root = _repo_root.parent
CACHE_DIR = str(_repo_root / "data" / "cache")
os.makedirs(CACHE_DIR, exist_ok=True)

def load_clean_csv(filename):
    path = os.path.join(CACHE_DIR, filename)
    if os.path.exists(path):
        return pd.read_csv(path)
    return None

# ── sidebar ───────────────────────────────────────────────────────────────────

st.sidebar.title("Day 3 Navigation")
app_choice = st.sidebar.radio(
    "Select Section",
    [
        "Overview",
        "App 5 — World Bank Population (Explore)",
        "App 6 — GBIF Biodiversity (Explore)",
        "🔍 Explore Your Own Data",
        "🔍 Bring Your Own Data — Explore",
        "⚖️ Ethics and Open Science",
    ],
)

# ── overview ──────────────────────────────────────────────────────────────────

if app_choice == "Overview":
    st.title("🔍 Day 3 — From Shared Workflow to Participants' Own Data")
    st.markdown("""
**Theme:** Enable participants to adapt the app to their own URLs or datasets
and interpret preliminary output.

### Day 3 Structure
| Section | Activity |
|---------|----------|
| App 5 — World Bank | Explore cleaned population data |
| App 6 — GBIF | Full extract-clean-explore pipeline on biodiversity data |
| Explore Your Own Data | Upload a CSV to explore |
| **Bring Your Own Data — Explore** | Full end-to-end exploration for data collected in Days 1–2 |
| Ethics | Legal, privacy, and server-load considerations |

### Entry Points into the Pipeline
Participants may enter at different stages depending on their situation:

- **I have a URL or API** → Use **Day 1 → 🔍 Bring Your Own Data — Collect**
- **I have raw data** → Use **Day 2 → 🔍 Bring Your Own Data — Clean**
- **I have clean data** → Use **Day 3 → 🔍 Bring Your Own Data — Explore** or **🔍 Explore Your Own Data**

Use the sidebar to navigate.
    """)

# ── App 5: World Bank explore ─────────────────────────────────────────────────

elif app_choice == "App 5 — World Bank Population (Explore)":
    st.title("🌱 App 5 — World Bank Population: Exploratory Analysis")

    df = load_clean_csv("day3_app5_worldbank_clean.csv")
    if df is None:
        df = load_clean_csv("day2_app5_co2_clean.csv")

    if df is None:
        st.error("Cache file not found.")
    else:
        st.subheader("Dataset Overview")
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Records", len(df))
        col2.metric("Countries", df["CountryCode"].nunique() if "CountryCode" in df.columns else "—")
        col3.metric("Years", df["Year"].nunique() if "Year" in df.columns else "—")

        st.subheader("Summary Statistics")
        st.dataframe(df.describe(), use_container_width=True)

        st.subheader("Missingness Check")
        miss = df.isnull().sum()
        if miss.sum() == 0:
            st.success("No missing values.")
        else:
            st.dataframe(miss[miss > 0].rename("Missing Count").to_frame(), use_container_width=True)

        if "Population" in df.columns and "Year" in df.columns:
            st.subheader("Population Over Time (Top 5 Countries by Max Population)")
            top5 = df.groupby("CountryCode")["Population"].max().nlargest(5).index.tolist()
            filtered = df[df["CountryCode"].isin(top5)]
            pivot = filtered.pivot_table(index="Year", columns="CountryCode", values="Population")
            st.line_chart(pivot)

        with st.expander("📌 Day 3 Teaching Note"):
            st.markdown("""
- Exploratory analysis checks **plausibility before inference**.
- Population values should be positive and consistent with known country sizes.
- Implausible values may indicate extraction errors, cleaning mistakes, or genuine source anomalies.
            """)

# ── App 6: GBIF explore ───────────────────────────────────────────────────────

elif app_choice == "App 6 — GBIF Biodiversity (Explore)":
    st.title("🦁 App 6 — GBIF: Biodiversity Occurrence Data")
    st.markdown("""
**Source:** [GBIF API](https://api.gbif.org/v1/occurrence/search)

The Global Biodiversity Information Facility (GBIF) aggregates species occurrence records
from institutions worldwide. This application demonstrates the **full pipeline**:
extract → clean → explore, using *Panthera leo* (lion) occurrence records.
    """)

    df = load_clean_csv("day3_app6_gbif_clean.csv")

    if df is None:
        st.error("Cache file not found.")
    else:
        st.subheader("Dataset Overview")
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Records", len(df))
        col2.metric("Countries", df["CountryCode"].nunique() if "CountryCode" in df.columns else "—")
        col3.metric("Years Range",
                    f"{int(df['Year'].min())}–{int(df['Year'].max())}"
                    if "Year" in df.columns and df["Year"].notna().any() else "—")

        st.subheader("Cleaned Dataset Preview")
        st.dataframe(df.head(20), use_container_width=True)

        st.subheader("Missingness Report")
        miss = df.isnull().sum()
        miss = miss[miss > 0]
        if miss.empty:
            st.success("No missing values in cleaned dataset.")
        else:
            st.dataframe(miss.rename("Missing Count").to_frame(), use_container_width=True)

        if "CountryCode" in df.columns:
            st.subheader("Records by Country")
            st.bar_chart(df["CountryCode"].value_counts().head(15))

        if "Year" in df.columns:
            st.subheader("Records by Year")
            year_counts = df["Year"].dropna().astype(int).value_counts().sort_index()
            st.bar_chart(year_counts)

        if "BasisOfRecord" in df.columns:
            st.subheader("Basis of Record")
            st.bar_chart(df["BasisOfRecord"].value_counts())

        with st.expander("📌 Day 3 Teaching Note"):
            st.markdown("""
- GBIF data illustrates **coverage bias**: records are concentrated in countries with
  active biodiversity monitoring institutions.
- The `basisOfRecord` field distinguishes human observations from preserved specimens —
  a structural feature that affects how the data can be used.
- Exploratory output should **feed back into research question refinement**:
  if coverage is too sparse for a country-level analysis, a regional or global question
  may be more defensible.
            """)

# ── Explore Your Own Data ─────────────────────────────────────────────────────

elif app_choice == "🔍 Explore Your Own Data":
    st.title("🔍 Explore Your Own Data")
    st.markdown("""
Upload a CSV or JSON file — from your own collection, a cleaned Day 2 output, or any other source —
and use the tools below to generate a preliminary exploratory analysis.
    """)

    uploaded = st.file_uploader("Upload file", type=["csv", "json"])

    if uploaded:
        try:
            if uploaded.name.endswith(".json"):
                raw = json.load(uploaded)
                if isinstance(raw, list):
                    df = pd.json_normalize(raw)
                elif isinstance(raw, dict):
                    list_keys = [k for k, v in raw.items() if isinstance(v, list)]
                    if list_keys:
                        chosen_key = st.selectbox("Select the records array:", list_keys)
                        df = pd.json_normalize(raw[chosen_key])
                    else:
                        df = pd.DataFrame([raw])
            else:
                df = pd.read_csv(uploaded)
            st.success(f"Loaded: {len(df)} rows × {len(df.columns)} columns")
        except Exception as e:
            st.error(f"Could not load file: {e}")
            df = None
    else:
        df = None

    if df is not None:
        st.subheader("Column Types")
        col_info = pd.DataFrame({
            "Column": df.columns,
            "Type": df.dtypes.astype(str).values,
            "Non-Null": df.notnull().sum().values,
            "Unique": df.nunique().values,
        })
        st.dataframe(col_info, use_container_width=True)

        st.subheader("Summary Statistics")
        st.dataframe(df.describe(include="all"), use_container_width=True)

        st.subheader("Missingness Report")
        miss = df.isnull().sum()
        miss = miss[miss > 0]
        if miss.empty:
            st.success("No missing values.")
        else:
            st.dataframe(miss.rename("Missing Count").to_frame(), use_container_width=True)

        st.subheader("Value Counts for a Selected Column")
        col_choice = st.selectbox("Select column", df.columns.tolist())
        if col_choice:
            vc = df[col_choice].value_counts().head(20)
            st.bar_chart(vc)

        st.subheader("Assess Against Four Criteria")
        st.markdown("""
Before using this dataset in your research, check:

1. **Coverage**: Does the dataset represent the population you intend to study?
2. **Completeness**: Are there systematic missing values in key fields?
3. **Consistency**: Are field values consistent across records?
4. **Plausibility**: Do numeric values fall within expected ranges?
        """)

        st.subheader("Download Exploratory Summary")
        summary = df.describe(include="all").to_csv().encode("utf-8")
        st.download_button("⬇️ Download Summary Statistics CSV", summary, "exploratory_summary.csv", "text/csv")
    else:
        st.info("Upload a file above to begin.")

# ── BYOD: Explore ─────────────────────────────────────────────────────────────

elif app_choice == "🔍 Bring Your Own Data — Explore":
    st.title("🔍 Bring Your Own Data — Step 3: Explore")
    st.markdown("""
This section provides a full exploratory analysis dashboard for the data you collected and
cleaned in Days 1 and 2. You can also upload a new file directly.

The same four criteria used to assess the case study datasets apply here:
**Coverage, Completeness, Consistency, and Plausibility.**
    """)

    # ── Four-Criteria Plain-English Guide ─────────────────────────────────────
    with st.expander("📖 What do the four criteria mean? (click to expand)"):
        st.markdown("""
Before analysing any dataset, researchers ask four questions. These are not technical checks —
they are **research quality checks** that apply to any data, from any source.

| Criterion | Plain-English Question | Why It Matters |
|---|---|---|
| **Coverage** | Does my data include all the cases I want to study? | A dataset that only covers some countries, years, or groups will produce conclusions that do not generalise. |
| **Completeness** | Are the important fields filled in for most records? | A column with many blank values cannot be used reliably for analysis. |
| **Consistency** | Are the same things described the same way throughout? | If `"United States"`, `"USA"`, and `"US"` all appear in a country column, counting by country will give wrong totals. |
| **Plausibility** | Do the numbers and values make sense? | A population of −500 or a date of 2099 signals an error in the source or the extraction. |

You will find a self-assessment section at the bottom of this page where you can record your
own notes on each criterion for your dataset.
        """)

    st.markdown("---")
    st.subheader("⚙️ Load Your Cleaned Data")

    st.info("""
**How to bring your data here:**
- If you cleaned data in **Day 2 → 🔍 Bring Your Own Data — Clean** and downloaded it,
  select **"Upload a file"** and upload that CSV or JSON file.
- If you are still in the same browser session as Day 2, select **"Carried forward from Day 2"**.
    """)

    data_source = st.radio(
        "Where is your data coming from?",
        [
            "Upload a file (CSV or JSON)",
            "Carried forward from Day 2 BYOD cleaning (same browser session only)",
        ],
    )

    df = None

    if data_source == "Carried forward from Day 2 BYOD cleaning (same browser session only)":
        if "byod_clean_df" in st.session_state:
            df = st.session_state["byod_clean_df"]
            st.success(f"Loaded from Day 2 session: {len(df)} rows × {len(df.columns)} columns.")
        elif "byod_flat_df" in st.session_state:
            df = st.session_state["byod_flat_df"]
            st.info(f"No cleaned data found — using raw collected data from Day 1 session: {len(df)} rows × {len(df.columns)} columns.")
        else:
            st.warning("""
**No session data found.** Session data is only available if you worked through Days 1 and 2
in the same browser session without refreshing the page.

👉 If you downloaded a CSV or JSON file from Day 2, select **"Upload a file"** above and upload it instead.
            """)

    else:
        uploaded = st.file_uploader(
            "Upload your cleaned data file",
            type=["csv", "json"],
            help="Upload the CSV or JSON file downloaded from Day 2, or any other clean data file.",
        )
        if uploaded:
            try:
                if uploaded.name.endswith(".json"):
                    raw = json.load(uploaded)
                    if isinstance(raw, list):
                        df = pd.json_normalize(raw)
                    elif isinstance(raw, dict):
                        list_keys = [k for k, v in raw.items() if isinstance(v, list)]
                        if list_keys:
                            if len(list_keys) == 1:
                                df = pd.json_normalize(raw[list_keys[0]])
                            else:
                                chosen_key = st.selectbox("Select the records array:", list_keys)
                                df = pd.json_normalize(raw[chosen_key])
                        else:
                            df = pd.DataFrame([raw])
                    st.success(f"Loaded JSON: {len(df)} rows × {len(df.columns)} columns.")
                else:
                    df = pd.read_csv(uploaded)
                    st.success(f"Loaded CSV: {len(df)} rows × {len(df.columns)} columns.")
            except Exception as e:
                st.error(f"Could not load file: {e}")

    # ── Exploration Dashboard ─────────────────────────────────────────────────
    if df is not None:
        st.markdown("---")

        # ── 1. Dataset Overview ───────────────────────────────────────────────
        st.subheader("1. Dataset Overview")
        col1, col2, col3 = st.columns(3)
        col1.metric("Rows", len(df))
        col2.metric("Columns", len(df.columns))
        col3.metric("Missing Cells", int(df.isnull().sum().sum()))

        # ── 2. Column Profile ─────────────────────────────────────────────────
        st.subheader("2. Column Profile")
        col_info = pd.DataFrame({
            "Column": df.columns,
            "Type": df.dtypes.astype(str).values,
            "Non-Null Count": df.notnull().sum().values,
            "Null Count": df.isnull().sum().values,
            "Unique Values": df.nunique().values,
        })
        st.dataframe(col_info, use_container_width=True)

        # ── 3. Summary Statistics ─────────────────────────────────────────────
        st.subheader("3. Summary Statistics")
        with st.expander("📖 How to read Summary Statistics"):
            st.markdown("""
Summary statistics describe the distribution of each column:

| Statistic | What it means |
|---|---|
| **count** | How many non-blank values are in this column |
| **mean** | The average value (numeric columns only) |
| **std** | Standard deviation — how spread out the values are |
| **min / max** | The smallest and largest values |
| **25% / 50% / 75%** | Quartiles — 50% is the median (middle value) |
| **unique** | How many different values appear (text columns) |
| **top** | The most common value (text columns) |
| **freq** | How many times the most common value appears |

**What to look for:** Very large `std` relative to `mean` suggests outliers. A `min` of 0 or negative for a count column suggests errors.
            """)
        st.dataframe(df.describe(include="all"), use_container_width=True)

        # ── 4. Missingness Report ─────────────────────────────────────────────
        st.subheader("4. Missingness Report")
        miss = df.isnull().sum()
        miss = miss[miss > 0]
        if miss.empty:
            st.success("No missing values in this dataset.")
        else:
            st.dataframe(miss.rename("Missing Count").to_frame(), use_container_width=True)
            miss_pct = (miss / len(df) * 100).round(1)
            st.bar_chart(miss_pct.rename("% Missing"))

        # ── 5. Value Distributions ────────────────────────────────────────────
        st.subheader("5. Value Distributions")
        st.markdown("Select a column to view its value distribution.")
        dist_col = st.selectbox("Select column for distribution chart:", df.columns.tolist(), key="byod_dist")
        if dist_col:
            if pd.api.types.is_numeric_dtype(df[dist_col]):
                st.bar_chart(df[dist_col].dropna().value_counts(bins=20).sort_index())
            else:
                vc = df[dist_col].value_counts().head(25)
                st.bar_chart(vc)

        # ── 6. Numeric Correlations ───────────────────────────────────────────
        num_cols = df.select_dtypes(include="number").columns.tolist()
        if len(num_cols) >= 2:
            st.subheader("6. Numeric Column Correlations")
            with st.expander("📖 What is a correlation matrix?"):
                st.markdown("""
A correlation matrix shows how strongly pairs of numeric columns move together.

- Values range from **−1 to +1**
- **+1** means the two columns increase together perfectly (e.g., height and weight)
- **−1** means one increases as the other decreases perfectly
- **0** means no linear relationship

**What to look for:**
- Values above **0.7** or below **−0.7** suggest a strong relationship worth investigating
- A column perfectly correlated with itself always shows **1.0** on the diagonal — this is normal
- Correlation does **not** mean causation

This is a **Pearson correlation**, which only detects straight-line (linear) relationships.
                """)
            corr = df[num_cols].corr().round(2)
            st.dataframe(corr, use_container_width=True)

        # ── 7. Four-Criteria Self-Assessment ─────────────────────────────────
        st.subheader("7. Four-Criteria Self-Assessment")
        st.markdown("""
Use the checks below to assess your dataset before using it in your research.
These are the same criteria applied to the case study datasets in Apps 5 and 6.
See the **"What do the four criteria mean?"** guide at the top of this page for plain-English explanations.
        """)

        with st.expander("Coverage — Does the dataset represent your target population?"):
            st.markdown("""
- Check whether all expected countries, time periods, or groups are present.
- Look for systematic absences (e.g., all records from one country, or only recent years).
- Ask: would a missing subgroup bias your conclusions?

**Example:** If you collected clinical trials data for "cancer" but only trials from the US appear,
your conclusions about global trial activity would be misleading.
            """)
            st.text_area("Your coverage notes:", key="byod_coverage_notes", height=80)

        with st.expander("Completeness — Are key fields sufficiently populated?"):
            st.markdown("""
- Review the Missingness Report above.
- A column with >20% missing values may be unreliable for analysis.
- Ask: is the missingness random, or does it follow a pattern (e.g., missing for certain countries)?

**Example:** If the `award_amount` column is blank for 40% of NIH grants, you cannot reliably
calculate average funding without understanding why those values are missing.
            """)
            st.text_area("Your completeness notes:", key="byod_completeness_notes", height=80)

        with st.expander("Consistency — Are values standardized across records?"):
            st.markdown("""
- Look for label variants (e.g., `"USA"` vs `"United States"` vs `"US"`).
- Check for mixed date formats or numeric formats.
- Use the Value Distributions section above to spot inconsistencies.

**Example:** If a country column contains `"United Kingdom"`, `"UK"`, and `"Great Britain"`,
a count of records by country will split them into three separate groups instead of one.
            """)
            st.text_area("Your consistency notes:", key="byod_consistency_notes", height=80)

        with st.expander("Plausibility — Do values fall within expected ranges?"):
            st.markdown("""
- Check minimum and maximum values for numeric columns (see Summary Statistics above).
- Look for impossible values: negative counts, future dates, values outside known bounds.
- Compare against external benchmarks if available.

**Example:** A population value of −500 or a year of 2099 in a historical dataset
signals an extraction error or a data entry mistake in the source.
            """)
            st.text_area("Your plausibility notes:", key="byod_plausibility_notes", height=80)

        # ── 8. Downloads ──────────────────────────────────────────────────────
        st.markdown("---")
        st.subheader("⬇️ Download Exploratory Output")
        st.markdown("All downloads are in CSV format, which can be opened in Excel, R, or any spreadsheet application.")

        summary_csv = df.describe(include="all").to_csv().encode("utf-8")
        st.download_button(
            "⬇️ Download Summary Statistics (CSV)",
            summary_csv,
            "byod_summary_statistics.csv",
            "text/csv",
        )

        col_csv = col_info.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Download Column Profile (CSV)",
            col_csv,
            "byod_column_profile.csv",
            "text/csv",
        )

        full_csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Download Full Dataset (CSV)",
            full_csv,
            "byod_full_dataset.csv",
            "text/csv",
        )

        full_json = df.to_json(orient="records", indent=2).encode("utf-8")
        st.download_button(
            "⬇️ Download Full Dataset (JSON)",
            full_json,
            "byod_full_dataset.json",
            "application/json",
        )

# ── Ethics ────────────────────────────────────────────────────────────────────

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
- **Publicly accessible ≠ appropriate to collect and publish**.
  Consider whether individuals would expect their information to be used for research.
- **Pseudonymization**: Remove or hash identifiers before sharing data.
- **Sensitive categories**: Health, political opinion, religion, and sexual orientation
  require extra care under most privacy frameworks.

---

### Responsible Scraping
| Practice | Why It Matters |
|----------|---------------|
| Use APIs when available | APIs are the intended access method; HTML scraping may violate ToS |
| Respect `robots.txt` | Signals which pages the site owner permits automated access to |
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
