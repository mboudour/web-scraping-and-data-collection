"""
Day 1 — From Web Source to Raw Dataset
Applications: ClinicalTrials.gov, WHO GHO, NIH RePORTER, Congress.gov
+ Bring Your Own Data — Collect
"""

import os, json, requests
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Day 1 — From Web Source to Raw Dataset", page_icon="📥", layout="wide")

# ── Robust cache directory: works locally and on Streamlit Cloud ──────────────
import pathlib
_repo_root = pathlib.Path(__file__).resolve().parent
if _repo_root.name == "pages":
    _repo_root = _repo_root.parent
CACHE_DIR = str(_repo_root / "data" / "cache")
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
        "🔍 Bring Your Own Data — Collect",
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

Use the sidebar to explore each application, or go to **🔍 Bring Your Own Data — Collect** to apply
the same workflow to your own research source.
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

# ── BYOD: Collect ─────────────────────────────────────────────────────────────

elif app_choice == "🔍 Bring Your Own Data — Collect":
    st.title("🔍 Bring Your Own Data — Step 1: Collect")
    st.markdown("""
This section lets you apply the **same data collection workflow** used in the case studies
to your own research source — without writing any code.

### How to use this section
1. **Find your source** in the reference tables below (API or webpage).
2. **Copy the Base URL** from the table.
3. **Scroll down to the wizard**, choose the right method, paste the URL, fill in the parameters, and click **Fetch Data**.

> ⚠️ **Important:** The URLs in the reference tables are *base URLs* — they are **incomplete on their own**.
> Clicking a base URL directly in your browser will return an error like *"query is a required parameter"*.
> This is normal. The base URL only works when combined with parameters, which the wizard does for you automatically.

### Three collection methods
| Method | When to use it |
|---|---|
| **Query an API (GET request)** | The API table shows `GET` in the Method column |
| **Query an API (POST request)** | The API table shows `POST` in the Method column (only NIH RePORTER in this list) |
| **Scrape a Webpage Table** | You want data from a Wikipedia or similar page that contains an HTML table |

Your collected data will be available for cleaning in **Day 2 → Bring Your Own Data — Clean**.
    """)

    # ── Reference: Verified APIs ──────────────────────────────────────────────
    st.markdown("---")
    st.subheader("📋 Reference: Verified Open APIs (No Key Required)")
    st.markdown("""
The following APIs have been confirmed working as of May 2026. They require no registration
or API key (or use a free demo key).

**How to use this table:**
1. Find the API you want to use.
2. **Highlight and copy the Base URL** (click the link, then copy from your browser address bar — or highlight the URL text directly).
3. Note the **Method** column (`GET` or `POST`) — this tells you which wizard tab to use below.
4. Click **▶ Show parameters** next to the API name to see the exact key–value pairs to enter in the wizard.
    """)

    # ── API reference with per-row parameter expanders ──────────────────────
    # Each entry: (Discipline, Name, URL, [(key, value), ...], Method)
    _apis = [
        ("Health", "ClinicalTrials.gov v2",
         "https://clinicaltrials.gov/api/v2/studies",
         [("query.cond", "diabetes"), ("pageSize", "50"), ("format", "json")], "GET"),
        ("Health", "WHO Global Health Observatory",
         "https://ghoapi.azureedge.net/api/WHOSIS_000001",
         [("$top", "300")], "GET"),
        ("Health", "PubMed E-utilities",
         "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
         [("db", "pubmed"), ("term", "cancer"), ("retmax", "50"), ("retmode", "json")], "GET"),
        ("Health", "OpenFDA Drug Adverse Events",
         "https://api.fda.gov/drug/event.json",
         [("limit", "50")], "GET"),
        ("Health", "OpenFDA Drug Labels",
         "https://api.fda.gov/drug/label.json",
         [("limit", "50")], "GET"),
        ("Life Sciences", "NIH RePORTER v2",
         "https://api.reporter.nih.gov/v2/projects/search",
         [], "POST"),
        ("Life Sciences", "GBIF Occurrence Search",
         "https://api.gbif.org/v1/occurrence/search",
         [("scientificName", "Panthera leo"), ("limit", "50")], "GET"),
        ("Life Sciences", "Europe PMC",
         "https://www.ebi.ac.uk/europepmc/webservices/rest/search",
         [("query", "malaria"), ("format", "json"), ("pageSize", "50")], "GET"),
        ("Life Sciences", "UniProt REST API",
         "https://rest.uniprot.org/uniprotkb/search",
         [("query", "insulin"), ("format", "json"), ("size", "50")], "GET"),
        ("Social Sciences", "World Bank Indicators",
         "https://api.worldbank.org/v2/country/US/indicator/SP.POP.TOTL",
         [("format", "json"), ("per_page", "50")], "GET"),
        ("Social Sciences", "Crossref Works",
         "https://api.crossref.org/works",
         [("query", "systematic review"), ("rows", "50")], "GET"),
        ("Social Sciences", "OpenAlex Works",
         "https://api.openalex.org/works",
         [("search", "climate change"), ("per-page", "50")], "GET"),
        ("Social Sciences", "Congress.gov Bills",
         "https://api.congress.gov/v3/bill/118",
         [("format", "json"), ("limit", "50"), ("api_key", "DEMO_KEY")], "GET"),
        ("Social Sciences", "OECD Stats (SDMX-JSON)",
         "https://stats.oecd.org/SDMX-JSON/data/QNA/AUS.B1_GE.VOBARSA.Q/all",
         [("startTime", "2020-Q1"), ("endTime", "2022-Q4")], "GET"),
    ]

    # Summary table (Discipline | Name | URL | Method)
    _md_rows = ["| Discipline | API Name | Base URL | Method |",
                "|---|---|---|---|"]
    for _disc, _name, _url, _pairs, _method in _apis:
        _md_rows.append(f"| {_disc} | {_name} | [{_url}]({_url}) | {_method} |")
    st.markdown("\n".join(_md_rows))

    # Per-API parameter expanders
    st.markdown("**▶ Click an API below to see the exact parameters to enter in the wizard:**")
    for _disc, _name, _url, _pairs, _method in _apis:
        with st.expander(f"{_name} ({_disc}) — {_method}"):
            st.markdown(f"**Base URL:** `{_url}`")
            if _method == "POST":
                st.markdown("This API uses a **POST request**. Select *Query an API (POST request)* in the wizard. The default JSON body is pre-filled for you.")
            elif _pairs:
                st.markdown(f"Set **Number of parameters** to **{len(_pairs)}** in the wizard, then enter:")
                _pair_rows = ["| Key | Value |", "|---|---|"]
                for _k, _v in _pairs:
                    _pair_rows.append(f"| `{_k}` | `{_v}` |")
                st.markdown("\n".join(_pair_rows))
            else:
                st.markdown("No parameters required — just paste the Base URL and click Fetch Data.")

    # ── Reference: Webpage Table Scraping ────────────────────────────────────
    st.markdown("---")
    st.subheader("🌐 Reference: Webpage Table Scraping — Example URLs")
    st.markdown("""
The **Scrape a Webpage Table** method works on any page that contains a static HTML `<table>`.
Below are confirmed examples across disciplines. Paste any of these (or your own URL) into the
scraper below.

> **Note:** This method works on *static* HTML tables only. Pages that load their tables
> dynamically via JavaScript (e.g., interactive dashboards) will not work with this approach —
> this is itself an important methodological distinction to understand.
    """)

    _scrape = [
        ("Health", "WHO — Life Expectancy by Country",
         "https://en.wikipedia.org/wiki/List_of_countries_by_life_expectancy"),
        ("Health", "Wikipedia — COVID-19 pandemic by country",
         "https://en.wikipedia.org/wiki/COVID-19_pandemic_by_country_and_territory"),
        ("Life Sciences", "Wikipedia — List of most endangered species",
         "https://en.wikipedia.org/wiki/Lists_of_endangered_species"),
        ("Life Sciences", "Wikipedia — Largest organisms",
         "https://en.wikipedia.org/wiki/Largest_organisms"),
        ("Social Sciences", "Wikipedia — World population by country",
         "https://en.wikipedia.org/wiki/List_of_countries_and_dependencies_by_population"),
        ("Social Sciences", "Wikipedia — Human Development Index",
         "https://en.wikipedia.org/wiki/List_of_countries_by_Human_Development_Index"),
        ("Social Sciences", "Wikipedia — Global Peace Index",
         "https://en.wikipedia.org/wiki/Global_Peace_Index"),
        ("Social Sciences", "Wikipedia — List of countries by GDP (nominal)",
         "https://en.wikipedia.org/wiki/List_of_countries_by_GDP_(nominal)"),
    ]

    # Render as Markdown table so URLs are clickable
    _s_rows = ["| Discipline | Description | URL |", "|---|---|---|"]
    for _disc, _desc, _url in _scrape:
        _s_rows.append(f"| {_disc} | {_desc} | [{_url}]({_url}) |")
    st.markdown("\n".join(_s_rows))

    # ── Interactive Collection Wizard ─────────────────────────────────────────
    st.markdown("---")
    st.subheader("⚙️ Interactive Collection Wizard")

    with st.expander("📖 Worked Example — UniProt REST API (click to expand)"):
        st.markdown("""
**Goal:** Fetch 50 records about *insulin* from the UniProt protein database.

**Step 1 — Find the row** in the API table above:
- API Name: UniProt REST API
- Base URL: `https://rest.uniprot.org/uniprotkb/search`
- Example Parameters: `query=insulin&format=json&size=50`
- Method: **GET**

**Step 2 — Select method:** Choose **Query an API (GET request)** in the wizard below.

**Step 3 — Paste the Base URL** into the *API Base URL* field:
```
https://rest.uniprot.org/uniprotkb/search
```

**Step 4 — Set the number of parameters to 3**, then fill in:
| Key | Value |
|---|---|
| `query` | `insulin` |
| `format` | `json` |
| `size` | `50` |

**Step 5 — Click 🚀 Fetch Data.**

The wizard assembles the full URL `https://rest.uniprot.org/uniprotkb/search?query=insulin&format=json&size=50`
and sends the request. You will see the raw JSON response appear below the button.

> **Why does clicking the Base URL directly give an error?**
> Because `query` is a required parameter — the API cannot return anything without knowing what to search for.
> The wizard adds the parameters for you; the browser address bar does not.
        """)

    method = st.radio(
        "Choose your data collection method:",
        ["Query an API (GET request)", "Query an API (POST request)", "Scrape a Webpage Table"],
        horizontal=True,
    )

    # ── Method 1: GET API ─────────────────────────────────────────────────────
    if method == "Query an API (GET request)":
        st.markdown("""
Paste the **Base URL** from the reference table above into the field below, then split the
**Example Parameters** into individual key–value pairs (one per row).

For example, `query=insulin&format=json&size=50` → set *Number of parameters* to **3** and enter:
- Key: `query` / Value: `insulin`
- Key: `format` / Value: `json`
- Key: `size` / Value: `50`
        """)

        base_url = st.text_input(
            "API Base URL",
            placeholder="e.g. https://api.crossref.org/works",
        )

        st.markdown("**Query Parameters** (key–value pairs)")
        n_params = st.number_input("Number of parameters", min_value=1, max_value=10, value=2, step=1)
        params = {}
        for i in range(int(n_params)):
            c1, c2 = st.columns(2)
            k = c1.text_input(f"Key {i+1}", key=f"get_key_{i}")
            v = c2.text_input(f"Value {i+1}", key=f"get_val_{i}")
            if k:
                params[k] = v

        api_key_header = st.text_input(
            "API Key (optional — leave blank if not required)",
            type="password",
            help="If the API requires a key in the Authorization header, enter it here.",
        )

        if st.button("🚀 Fetch Data", key="fetch_get"):
            if not base_url:
                st.warning("Please enter a base URL.")
            else:
                headers = {"User-Agent": "workshop-byod/1.0", "Accept": "application/json"}
                if api_key_header:
                    headers["Authorization"] = f"Bearer {api_key_header}"
                try:
                    with st.spinner("Fetching data…"):
                        r = requests.get(base_url, params=params, headers=headers, timeout=30)
                    st.info(f"HTTP Status: {r.status_code}")
                    if r.status_code == 200:
                        byod_raw = r.json()
                        st.session_state["byod_raw"] = byod_raw
                        st.session_state["byod_source"] = "api_get"
                        st.success("✅ Data fetched successfully! Download the JSON below or go to Day 2 to continue.")
                        _raw_bytes = json.dumps(byod_raw, indent=2).encode("utf-8")
                        st.download_button("⬇️ Download Raw JSON to your computer", _raw_bytes, "byod_raw.json", "application/json", key="dl_raw_get")
                        st.markdown("**Raw JSON preview** (first record):")
                        preview = byod_raw[0] if isinstance(byod_raw, list) else byod_raw
                        st.json(preview, expanded=True)
                    else:
                        st.error(f"Request failed: {r.text[:300]}")
                except Exception as e:
                    st.error(f"Error: {e}")

    # ── Method 2: POST API ────────────────────────────────────────────────────
    elif method == "Query an API (POST request)":
        st.markdown("""
Some APIs (like NIH RePORTER) require a **POST request** with a JSON body instead of URL parameters.
Paste the base URL and the JSON body below.
        """)

        base_url = st.text_input(
            "API Base URL",
            placeholder="e.g. https://api.reporter.nih.gov/v2/projects/search",
        )

        default_body = '{"criteria":{"advanced_text_search":{"operator":"and","search_field":"all","search_text":"genomics"}},"offset":0,"limit":50}'
        body_str = st.text_area(
            "Request Body (JSON)",
            value=default_body,
            height=150,
            help="Enter valid JSON. Use the example from the API reference table above.",
        )

        if st.button("🚀 Fetch Data", key="fetch_post"):
            if not base_url:
                st.warning("Please enter a base URL.")
            else:
                try:
                    body = json.loads(body_str)
                    with st.spinner("Fetching data…"):
                        r = requests.post(
                            base_url, json=body,
                            headers={"Content-Type": "application/json", "Accept": "application/json"},
                            timeout=30,
                        )
                    st.info(f"HTTP Status: {r.status_code}")
                    if r.status_code == 200:
                        byod_raw = r.json()
                        st.session_state["byod_raw"] = byod_raw
                        st.session_state["byod_source"] = "api_post"
                        st.success("✅ Data fetched successfully! Download the JSON below or go to Day 2 to continue.")
                        _raw_bytes = json.dumps(byod_raw, indent=2).encode("utf-8")
                        st.download_button("⬇️ Download Raw JSON to your computer", _raw_bytes, "byod_raw.json", "application/json", key="dl_raw_post")
                        st.markdown("**Raw JSON preview** (first record):")
                        preview = byod_raw[0] if isinstance(byod_raw, list) else byod_raw
                        st.json(preview, expanded=True)
                    else:
                        st.error(f"Request failed: {r.text[:300]}")
                except json.JSONDecodeError:
                    st.error("Invalid JSON in request body. Please check your syntax.")
                except Exception as e:
                    st.error(f"Error: {e}")

    # ── Method 3: Webpage Table Scraping ─────────────────────────────────────
    elif method == "Scrape a Webpage Table":
        st.markdown("""
Paste the URL of any webpage that contains an HTML `<table>`. The app will extract all tables
it finds and let you choose which one to use.
        """)

        page_url = st.text_input(
            "Webpage URL",
            placeholder="e.g. https://en.wikipedia.org/wiki/List_of_countries_by_life_expectancy",
        )

        if st.button("🔍 Find Tables", key="scrape_btn"):
            if not page_url:
                st.warning("Please enter a URL.")
            else:
                try:
                    with st.spinner("Fetching and parsing webpage…"):
                        from bs4 import BeautifulSoup
                        _resp = requests.get(
                            page_url,
                            headers={"User-Agent": "Mozilla/5.0 (workshop-byod)"},
                            timeout=30,
                        )
                        _resp.raise_for_status()
                        _soup = BeautifulSoup(_resp.text, "html.parser")
                        _html_tables = _soup.find_all("table")
                        tables = []
                        for _tbl in _html_tables:
                            try:
                                _df = pd.read_html(str(_tbl))[0]
                                tables.append(_df)
                            except Exception:
                                pass
                    if tables:
                        st.success(f"Found {len(tables)} table(s) on the page.")
                        st.session_state["byod_scraped_tables"] = tables
                        st.session_state["byod_source"] = "scrape"
                    else:
                        st.warning("No tables found on this page. The page may use JavaScript to render its tables — try a different URL.")
                except Exception as e:
                    st.error(f"Could not extract tables: {e}")
                    st.info("This may happen if the page uses JavaScript to render its tables, or if the URL is not publicly accessible.")

        if "byod_scraped_tables" in st.session_state:
            tables = st.session_state["byod_scraped_tables"]
            table_labels = [f"Table {i+1} — {t.shape[0]} rows × {t.shape[1]} cols" for i, t in enumerate(tables)]
            chosen = st.selectbox("Select the table you want to use:", table_labels)
            idx = table_labels.index(chosen)
            selected_table = tables[idx]
            st.dataframe(selected_table.head(20), use_container_width=True)

            if st.button("✅ Use This Table", key="use_table"):
                st.session_state["byod_flat_df"] = selected_table
                st.session_state["byod_source"] = "scrape"
                st.success("Table saved. Go to **Day 2 → 🔍 Bring Your Own Data — Clean** to continue.")

    # ── Day 2 prompt (shown once data has been fetched via API) ──────────────
    if "byod_raw" in st.session_state and st.session_state.get("byod_source") in ("api_get", "api_post"):
        st.markdown("---")
        st.info("✅ Your raw data has been collected and saved. When you are ready, go to **Day 2 → 🔍 Bring Your Own Data — Clean** to structure and clean it.")
