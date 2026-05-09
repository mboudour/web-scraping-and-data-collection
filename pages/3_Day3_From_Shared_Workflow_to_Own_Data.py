"""
Day 3 — From Shared Workflow to Participants' Own Data
Applications: World Bank (explore), GBIF, and participant-uploaded data
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
| Your own data | Upload a CSV or enter a URL to explore |
| Ethics | Legal, privacy, and server-load considerations |

### Entry Points into the Pipeline
Participants may enter at different stages depending on their situation:

- **I have a URL** → Use the Day 1 extraction templates
- **I have raw data** → Use the Day 2 cleaning module
- **I have clean data** → Use the Day 3 explore module below

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
Upload a CSV file — from your own collection, a cleaned Day 2 output, or any other source —
and use the tools below to generate a preliminary exploratory analysis.
    """)

    uploaded = st.file_uploader("Upload CSV", type=["csv"])

    if uploaded:
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
        st.info("Upload a CSV file above to begin.")

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
