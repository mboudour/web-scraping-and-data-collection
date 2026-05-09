"""
Day 1 — From Web Source to Raw Dataset
Applications: ClinicalTrials.gov, WHO GHO, NIH RePORTER, Congress.gov
"""

import os, json, requests
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Day 1 — From Web Source to Raw Dataset", page_icon="📥", layout="wide")

# ── Robust cache directory: works locally and on Streamlit Cloud ──────────────
CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "cache")
# Fallback: if the above does not exist, use repo root / data / cache
if not os.path.isdir(CACHE_DIR):
    CACHE_DIR = os.path.join(os.getcwd(), "data", "cache")
os.makedirs(CACHE_DIR, exist_ok=True)

# ── helpers ───────────────────────────────────────────────────────────────────

def load_or_fetch_json(cache_path, fetch_fn):
    """Load from cache if available, otherwise fetch and save."""
    if os.path.exists(cache_path):
        with open(cache_path, encoding="utf-8") as f:
            return json.load(f)
    data = fetch_fn()
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return data

# ── sidebar ───────────────────────────────────────────────────────────────────

st.sidebar.title("Day 1 Navigation")
app_choice = st.sidebar.radio(
    "Select Application",
    [
        "Overview",
        "App 1 — ClinicalTrials.gov",
        "App 2 — WHO Global Health Observatory",
        "App 3 — NIH RePORTER",
        "App 4 — Congress.gov (U.S. Bills)",
    ],
)

# ── overview ──────────────────────────────────────────────────────────────────

if app_choice == "Overview":
    st.title("📥 Day 1 — From Web Source to Raw Dataset")
    st.markdown("""
**Theme:** Help participants understand what kinds of online sources can be transformed into
research data and how the extraction process works in a no-code setting.

### What You Will Do Today
1. Identify suitable online sources for your research question.
2. Understand the structure of API responses and HTML pages.
3. Fetch raw data from four public sources.
4. Inspect the raw output and note its limitations.

### Applications
| # | Source | Domain | Data Type |
|---|--------|--------|-----------|
| 1 | ClinicalTrials.gov | Health | Structured JSON (API) |
| 2 | WHO Global Health Observatory | Health | Structured JSON (OData API) |
| 3 | NIH RePORTER | Life Sciences | Structured JSON (API) |
| 4 | Congress.gov | Social Sciences | Structured JSON (API) |

Use the sidebar to explore each application.
    """)

# ── App 1: ClinicalTrials.gov ─────────────────────────────────────────────────

elif app_choice == "App 1 — ClinicalTrials.gov":
    st.title("🏥 App 1 — ClinicalTrials.gov")
    st.markdown("""
**Source:** [ClinicalTrials.gov v2 API](https://clinicaltrials.gov/api/v2/studies)

ClinicalTrials.gov is a registry of publicly and privately supported clinical studies.
Its v2 API returns structured JSON records for each registered trial.

**Research question:** What are the characteristics (phase, status, conditions) of
recently registered trials related to *diabetes*?
    """)

    cache_path = os.path.join(CACHE_DIR, "day1_app1_clinicaltrials_raw.json")

    def fetch_clinicaltrials():
        url = "https://clinicaltrials.gov/api/v2/studies"
        params = {"query.cond": "diabetes", "pageSize": 50, "format": "json"}
        r = requests.get(url, params=params, timeout=30)
        r.raise_for_status()
        return r.json()

    with st.spinner("Loading ClinicalTrials.gov data…"):
        try:
            data = load_or_fetch_json(cache_path, fetch_clinicaltrials)
            studies = data.get("studies", [])
            st.success(f"Loaded {len(studies)} trial records.")

            st.subheader("Raw JSON Structure (first record, truncated)")
            if studies:
                st.json(studies[0], expanded=False)

            st.subheader("Flat Preview Table")
            rows = []
            for s in studies:
                proto = s.get("protocolSection", {})
                id_mod = proto.get("identificationModule", {})
                status_mod = proto.get("statusModule", {})
                design_mod = proto.get("designModule", {})
                cond_mod = proto.get("conditionsModule", {})
                rows.append({
                    "NCT ID": id_mod.get("nctId", ""),
                    "Title": str(id_mod.get("briefTitle", ""))[:60],
                    "Status": status_mod.get("overallStatus", ""),
                    "Phase": ", ".join(design_mod.get("phases", [])),
                    "Conditions": ", ".join(cond_mod.get("conditions", [])[:2]),
                })
            df = pd.DataFrame(rows)
            st.dataframe(df, use_container_width=True)

            st.subheader("Status Distribution")
            st.bar_chart(df["Status"].value_counts())

            with st.expander("📌 Day 1 Teaching Note"):
                st.markdown("""
- The raw JSON is **nested**: trial metadata, status, design, and conditions are in separate sub-objects.
- The `phases` field is a **list** — a single trial may have multiple phases.
- On **Day 2** we will flatten this structure into a clean tabular CSV.
                """)
        except Exception as e:
            st.error(f"Could not load data: {e}")

# ── App 2: WHO GHO ────────────────────────────────────────────────────────────

elif app_choice == "App 2 — WHO Global Health Observatory":
    st.title("🌍 App 2 — WHO Global Health Observatory")
    st.markdown("""
**Source:** [WHO GHO OData API](https://ghoapi.azureedge.net/api/)

The WHO Global Health Observatory exposes country-level health indicators through the
Athena OData API. Indicator `WHOSIS_000001` is life expectancy at birth.

**Research question:** How does life expectancy at birth vary across countries and years?
    """)

    cache_path = os.path.join(CACHE_DIR, "day1_app2_who_raw.json")

    def fetch_who():
        url = "https://ghoapi.azureedge.net/api/WHOSIS_000001"
        params = {"$top": 300}
        r = requests.get(url, params=params, timeout=30)
        r.raise_for_status()
        return r.json()

    with st.spinner("Loading WHO GHO data…"):
        try:
            data = load_or_fetch_json(cache_path, fetch_who)
            records = data.get("value", [])
            st.success(f"Loaded {len(records)} records.")

            st.subheader("Raw JSON Structure (first record)")
            if records:
                st.json(records[0], expanded=True)

            st.subheader("Flat Preview Table")
            df = pd.DataFrame([{
                "Country": r.get("SpatialDim", ""),
                "Year": r.get("TimeDim", ""),
                "Sex": r.get("Dim1", ""),
                "Value": r.get("NumericValue", None),
            } for r in records])
            st.dataframe(df.head(50), use_container_width=True)

            st.subheader("Records per Sex Category")
            st.bar_chart(df["Sex"].value_counts())

            with st.expander("📌 Day 1 Teaching Note"):
                st.markdown("""
- Each country-year combination appears **three times**: for Both sexes, Male, and Female.
- This is a **structural feature** of the source — not an error — but it must be handled
  during cleaning on Day 2 (e.g., filtering to `BTSX` = Both sexes).
- The `NumericValue` field may be `null` for some country-year combinations.
                """)
        except Exception as e:
            st.error(f"Could not load data: {e}")

# ── App 3: NIH RePORTER ───────────────────────────────────────────────────────

elif app_choice == "App 3 — NIH RePORTER":
    st.title("🔬 App 3 — NIH RePORTER")
    st.markdown("""
**Source:** [NIH RePORTER API](https://api.reporter.nih.gov/v2/projects/search)

NIH RePORTER provides access to NIH-funded research projects. The API accepts
keyword-based searches and returns structured JSON records.

**Research question:** What are the characteristics of NIH-funded projects related to *genomics*?
    """)

    cache_path = os.path.join(CACHE_DIR, "day1_app3_nih_raw.json")

    def fetch_nih():
        url = "https://api.reporter.nih.gov/v2/projects/search"
        payload = {
            "criteria": {"advanced_text_search": {"operator": "and", "search_field": "all", "search_text": "genomics"}},
            "offset": 0, "limit": 50,
            "fields": ["ProjectNum", "ProjectTitle", "FiscalYear", "AwardAmount",
                       "OrgName", "OrgCity", "OrgState", "AgencyCode", "ProjectStartDate", "ProjectEndDate"]
        }
        r = requests.post(url, json=payload, timeout=30)
        r.raise_for_status()
        return r.json()

    with st.spinner("Loading NIH RePORTER data…"):
        try:
            data = load_or_fetch_json(cache_path, fetch_nih)
            results = data.get("results", [])
            st.success(f"Loaded {len(results)} project records.")

            st.subheader("Raw JSON Structure (first record)")
            if results:
                st.json(results[0], expanded=False)

            st.subheader("Flat Preview Table")
            df = pd.DataFrame([{
                "Project #": r.get("project_num", ""),
                "Title": str(r.get("project_title", ""))[:60],
                "FY": r.get("fiscal_year", ""),
                "Award ($)": r.get("award_amount", None),
                "Agency": r.get("agency_code", ""),
                "Org": str(r.get("org_name", ""))[:30],
                "State": r.get("org_state", ""),
            } for r in results])
            st.dataframe(df, use_container_width=True)

            with st.expander("📌 Day 1 Teaching Note"):
                st.markdown("""
- The `award_amount` field may be `null` for some records — a common issue in grant databases.
- Organization and agency information is **nested** in sub-objects in the raw JSON.
- On **Day 2** we will extract `org_name`, `org_city`, and `agency_code` into flat columns.
                """)
        except Exception as e:
            st.error(f"Could not load data: {e}")

# ── App 4: Congress.gov ───────────────────────────────────────────────────────

elif app_choice == "App 4 — Congress.gov (U.S. Bills)":
    st.title("🏛️ App 4 — Congress.gov (U.S. Legislative Bills)")
    st.markdown("""
**Source:** [Congress.gov API v3](https://api.congress.gov/v3/bill)

The Congress.gov API provides structured access to U.S. legislative bills.
The v3 endpoint returns JSON records for bills introduced in any Congress session.

**Research question:** What bills were introduced in the 118th Congress (2023-2024),
and what are their types, chambers of origin, and latest actions?
    """)

    cache_path = os.path.join(CACHE_DIR, "day1_app4_congress_raw.json")

    def fetch_congress():
        url = "https://api.congress.gov/v3/bill/118"
        params = {"format": "json", "limit": 50, "api_key": "DEMO_KEY"}
        r = requests.get(url, params=params, timeout=30)
        r.raise_for_status()
        return r.json()

    with st.spinner("Loading Congress.gov data…"):
        try:
            data = load_or_fetch_json(cache_path, fetch_congress)
            bills = data.get("bills", [])
            st.success(f"Loaded {len(bills)} bill records from the 118th Congress.")

            st.subheader("Raw JSON Structure (first record)")
            if bills:
                st.json(bills[0], expanded=True)

            st.subheader("Flat Preview Table")
            df = pd.DataFrame([{
                "Number": b.get("number", ""),
                "Type": b.get("type", ""),
                "Title": str(b.get("title", ""))[:70],
                "Chamber": b.get("originChamber", ""),
                "Congress": b.get("congress", ""),
                "Latest Action Date": b.get("latestAction", {}).get("actionDate", ""),
                "Latest Action": str(b.get("latestAction", {}).get("text", ""))[:60],
            } for b in bills])
            st.dataframe(df, use_container_width=True)

            st.subheader("Bills by Type")
            st.bar_chart(df["Type"].value_counts())

            st.subheader("Bills by Chamber of Origin")
            st.bar_chart(df["Chamber"].value_counts())

            with st.expander("📌 Day 1 Teaching Note"):
                st.markdown("""
- The `latestAction` field is a **nested object** containing both a date and a text description.
  On Day 2 we will extract these into separate flat columns.
- The `type` field encodes the bill category (e.g., `HR` = House Resolution, `S` = Senate bill).
- The `updateDate` field is a string that will be parsed as a proper date on Day 2.
                """)
        except Exception as e:
            st.error(f"Could not load data: {e}")
