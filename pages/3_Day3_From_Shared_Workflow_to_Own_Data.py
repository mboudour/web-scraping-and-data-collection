"""
Day 3 — From Shared Workflow to Participants' Own Data
Applications: World Bank (explore), GBIF, and participant-uploaded data
+ Bring Your Own Data — Explore
"""

import os, json
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
| Exploratory analysis | Summary tables, distributions, missingness checks |
| App 5 — World Bank | Explore cleaned population data |
| App 6 — GBIF | Full extract-clean-explore pipeline on biodiversity data |
| Explore Your Own Data | Upload a CSV or XLSX to explore |
| **Bring Your Own Data — Explore** | Full end-to-end exploration for data collected in Days 1–2 |
| Ethics | Legal, privacy, and server-load considerations |

### Entry Points into the Pipeline
Participants may enter at different stages depending on their situation:

- **I have a URL or API** → Use **Day 1 → 🔍 Bring Your Own Data — Collect**
- **I have raw data** → Use **Day 2 → 🔍 Bring Your Own Data — Clean**
- **I have clean data** → Use **Day 3 → 🔍 Bring Your Own Data — Explore** (this section)

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

# ── Explore Your Own Data (original section) ──────────────────────────────────

elif app_choice == "🔍 Explore Your Own Data":
    st.title("🔍 Explore Your Own Data")
    st.markdown("""
Upload a CSV or XLSX file — from your own collection, a cleaned Day 2 output, or any other source —
and use the tools below to generate a preliminary exploratory analysis.
    """)

    uploaded = st.file_uploader("Upload CSV or XLSX", type=["csv", "xlsx"])

    if uploaded:
        if uploaded.name.endswith(".xlsx"):
            df = pd.read_excel(uploaded)
        else:
            df = pd.read_csv(uploaded)
        st.success(f"Loaded: {len(df)} rows × {len(df.columns)} columns")

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
        st.info("Upload a CSV or XLSX file above to begin.")

# ── BYOD: Explore ─────────────────────────────────────────────────────────────

elif app_choice == "🔍 Bring Your Own Data — Explore":
    st.title("🔍 Bring Your Own Data — Step 3: Explore")
    st.markdown("""
This section completes the end-to-end **Bring Your Own Data** pipeline.

You can load your cleaned data from the Day 2 session, or upload a file directly.
The exploration module applies the same four-criteria framework used in the case studies:
**Coverage, Completeness, Consistency, and Plausibility**.
    """)

    st.markdown("---")
    st.subheader("📋 Four Criteria for Evaluating Your Dataset")
    st.markdown("""
| Criterion | Question to Ask | What to Look For |
|---|---|---|
| **Coverage** | Does the dataset represent the population I intend to study? | Geographic gaps, time gaps, missing subgroups |
| **Completeness** | Are there systematic missing values in key fields? | Columns with high % missing; patterns in missingness |
| **Consistency** | Are field values consistent across records? | Mixed formats, label variants, impossible combinations |
| **Plausibility** | Do numeric values fall within expected ranges? | Negative counts, future dates, outliers |
    """)

    st.markdown("---")
    st.subheader("⚙️ Load Your Cleaned Data")

    data_source = st.radio(
        "Where is your cleaned data coming from?",
        [
            "Carried forward from Day 2 BYOD cleaning",
            "Upload a file (CSV or XLSX)",
        ],
    )

    df = None

    if data_source == "Carried forward from Day 2 BYOD cleaning":
        if "byod_clean_df" in st.session_state:
            df = st.session_state["byod_clean_df"]
            st.success(f"Loaded from Day 2 session: {len(df)} rows × {len(df.columns)} columns.")
        else:
            st.warning("""
No cleaned data found from Day 2. Either:
- Go to **Day 2 → 🔍 Bring Your Own Data — Clean** and complete the cleaning wizard, or
- Upload a file below instead.
            """)

    else:
        uploaded = st.file_uploader(
            "Upload your cleaned data file",
            type=["csv", "xlsx"],
            help="Upload a CSV or XLSX file to explore.",
        )
        if uploaded:
            try:
                if uploaded.name.endswith(".xlsx"):
                    df = pd.read_excel(uploaded)
                    st.success(f"Loaded XLSX: {len(df)} rows × {len(df.columns)} columns.")
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
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Rows", len(df))
        m2.metric("Columns", len(df.columns))
        m3.metric("Missing Cells", int(df.isnull().sum().sum()))
        m4.metric("Duplicate Rows", int(df.duplicated().sum()))

        st.dataframe(df.head(20), use_container_width=True)

        # ── 2. Column Profile ─────────────────────────────────────────────────
        st.subheader("2. Column Profile")
        col_info = pd.DataFrame({
            "Column": df.columns,
            "Data Type": df.dtypes.astype(str).values,
            "Non-Null Count": df.notnull().sum().values,
            "Missing (%)": (df.isnull().mean() * 100).round(1).values,
            "Unique Values": df.nunique().values,
        })
        st.dataframe(col_info, use_container_width=True)

        # ── 3. Summary Statistics ─────────────────────────────────────────────
        st.subheader("3. Summary Statistics")
        numeric_cols = df.select_dtypes(include="number").columns.tolist()
        if numeric_cols:
            st.dataframe(df[numeric_cols].describe().round(2), use_container_width=True)
        else:
            st.info("No numeric columns found.")

        # ── 4. Missingness Report ─────────────────────────────────────────────
        st.subheader("4. Missingness Report (Completeness)")
        miss = df.isnull().sum()
        miss = miss[miss > 0]
        if miss.empty:
            st.success("✅ No missing values — dataset is complete.")
        else:
            miss_df = pd.DataFrame({
                "Column": miss.index,
                "Missing Count": miss.values,
                "Missing (%)": (miss.values / len(df) * 100).round(1),
            })
            st.dataframe(miss_df, use_container_width=True)
            st.bar_chart(miss_df.set_index("Column")["Missing (%)"])

        # ── 5. Value Distributions ────────────────────────────────────────────
        st.subheader("5. Value Distributions (Consistency & Coverage)")

        cat_cols = df.select_dtypes(include="object").columns.tolist()
        if cat_cols:
            cat_choice = st.selectbox("Select a categorical column to inspect:", cat_cols, key="byod_cat")
            vc = df[cat_choice].value_counts().head(25)
            st.markdown(f"**Top values in '{cat_choice}'** ({df[cat_choice].nunique()} unique values)")
            st.bar_chart(vc)

        if numeric_cols:
            num_choice = st.selectbox("Select a numeric column to inspect:", numeric_cols, key="byod_num")
            col_data = df[num_choice].dropna()
            st.markdown(f"**Distribution of '{num_choice}'**")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Min", f"{col_data.min():.2f}")
            c2.metric("Max", f"{col_data.max():.2f}")
            c3.metric("Mean", f"{col_data.mean():.2f}")
            c4.metric("Std Dev", f"{col_data.std():.2f}")

            # Histogram using value_counts on bins
            try:
                hist = col_data.value_counts(bins=20, sort=False)
                st.bar_chart(hist)
            except Exception:
                st.write(col_data.describe())

        # ── 6. Cross-tabulation ───────────────────────────────────────────────
        if len(cat_cols) >= 2:
            st.subheader("6. Cross-tabulation (optional)")
            st.markdown("Compare two categorical columns to check for consistency or coverage gaps.")
            c1, c2 = st.columns(2)
            row_col = c1.selectbox("Row variable", cat_cols, key="byod_xtab_row")
            col_col = c2.selectbox("Column variable", [c for c in cat_cols if c != row_col], key="byod_xtab_col")
            if st.button("Generate Cross-tabulation", key="byod_xtab_btn"):
                xtab = pd.crosstab(df[row_col], df[col_col])
                st.dataframe(xtab, use_container_width=True)

        # ── 7. Four-Criteria Self-Assessment ─────────────────────────────────
        st.subheader("7. Four-Criteria Self-Assessment")
        st.markdown("""
Use the checks below to assess your dataset before using it in your research.
These are the same criteria applied to the case study datasets in Apps 5 and 6.
        """)

        with st.expander("Coverage — Does the dataset represent your target population?"):
            st.markdown("""
- Check whether all expected countries, time periods, or groups are present.
- Look for systematic absences (e.g., all records from one country, or only recent years).
- Ask: would a missing subgroup bias your conclusions?
            """)
            st.text_area("Your coverage notes:", key="byod_coverage_notes", height=80)

        with st.expander("Completeness — Are key fields sufficiently populated?"):
            st.markdown("""
- Review the Missingness Report above.
- A column with >20% missing values may be unreliable for analysis.
- Ask: is the missingness random, or does it follow a pattern (e.g., missing for certain countries)?
            """)
            st.text_area("Your completeness notes:", key="byod_completeness_notes", height=80)

        with st.expander("Consistency — Are values standardized across records?"):
            st.markdown("""
- Look for label variants (e.g., `"USA"` vs `"United States"` vs `"US"`).
- Check for mixed date formats or numeric formats.
- Use the Value Distributions section above to spot inconsistencies.
            """)
            st.text_area("Your consistency notes:", key="byod_consistency_notes", height=80)

        with st.expander("Plausibility — Do values fall within expected ranges?"):
            st.markdown("""
- Check minimum and maximum values for numeric columns.
- Look for impossible values (negative counts, future dates, values outside known bounds).
- Compare against external benchmarks if available.
            """)
            st.text_area("Your plausibility notes:", key="byod_plausibility_notes", height=80)

        # ── 8. Downloads ──────────────────────────────────────────────────────
        st.markdown("---")
        st.subheader("⬇️ Download Exploratory Output")

        summary_csv = df.describe(include="all").to_csv().encode("utf-8")
        st.download_button("Download Summary Statistics (CSV)", summary_csv,
                           "byod_summary_statistics.csv", "text/csv")

        col_csv = col_info.to_csv(index=False).encode("utf-8")
        st.download_button("Download Column Profile (CSV)", col_csv,
                           "byod_column_profile.csv", "text/csv")

        full_csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("Download Full Dataset (CSV)", full_csv,
                           "byod_full_dataset.csv", "text/csv")

        try:
            import io
            buffer = io.BytesIO()
            df.to_excel(buffer, index=False, engine="openpyxl")
            buffer.seek(0)
            st.download_button("Download Full Dataset (XLSX)", buffer,
                               "byod_full_dataset.xlsx",
                               "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        except Exception:
            pass

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
