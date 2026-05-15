"""
Day 1 — From Web Source to Raw Dataset
Unified Collect Data interface: four presets + open API wizard + webpage scraping
"""

import os, json, requests
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Day 1 — From Web Source to Raw Dataset", page_icon="📥", layout="wide")

# ── Robust cache directory ────────────────────────────────────────────────────
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


def flatten_multiindex(tables):
    """Flatten MultiIndex column headers produced by pd.read_html on complex tables."""
    def _clean_level(s):
        s = str(s).strip()
        return s if s and s != "nan" and not s.startswith("Unnamed") else ""

    cleaned = []
    for t in tables:
        if isinstance(t.columns, pd.MultiIndex):
            new_cols = []
            for i, col in enumerate(t.columns):
                parts = [_clean_level(lvl) for lvl in col]
                parts = [p for p in parts if p]  # drop empty
                # deduplicate consecutive identical parts (e.g. 'Locations Locations')
                deduped = []
                for p in parts:
                    if not deduped or p != deduped[-1]:
                        deduped.append(p)
                new_cols.append(" ".join(deduped) if deduped else f"Col_{i}")
            t.columns = new_cols
        else:
            t.columns = [
                str(c) if (not str(c).startswith("Unnamed") and not isinstance(c, int))
                else f"Col_{i}"
                for i, c in enumerate(t.columns)
            ]
        cleaned.append(t)
    return cleaned


def save_and_display_result(df, raw, source_label):
    """Show preview, JSON inspector, download button, and Day 2 handoff for any fetched dataset."""
    st.success(f"✅ Loaded {len(df)} records from {source_label}.")

    st.markdown("#### Preview (first 20 rows)")
    st.dataframe(df.head(20), use_container_width=True)

    # ── JSON Inspector ────────────────────────────────────────────────────────
    raw_list = raw if isinstance(raw, list) else [raw]
    n_records = len(raw_list)

    with st.expander("🔍 Inspect Raw JSON Structure", expanded=False):
        st.markdown("""
**What you are looking at:** This is the raw JSON returned by the API — exactly as the server
sent it, before any processing. Each *record* is one item in the list (one trial, one country,
one grant, one bill …).

Use the selector below to browse individual records and see how the data is structured.
        """)

        record_idx = st.number_input(
            f"Inspect record (1 – {n_records})",
            min_value=1, max_value=max(n_records, 1), value=1, step=1,
            key=f"json_idx_{source_label.replace(' ', '_')}",
        ) - 1  # convert to 0-based index

        selected_record = raw_list[int(record_idx)]
        st.json(selected_record, expanded=True)

        # ── Field inventory table ─────────────────────────────────────────────
        st.markdown("##### Field inventory — what is in this record?")
        st.markdown("""
The table below lists every top-level field in this record, its Python type, and an example
value. Fields whose type is **dict** or **list** are *nested* — they contain sub-objects that
will need to be flattened or extracted during Day 2 cleaning.
        """)

        if isinstance(selected_record, dict):
            inventory_rows = []
            for field, value in selected_record.items():
                py_type = type(value).__name__
                if isinstance(value, dict):
                    example = "{" + ", ".join(list(value.keys())[:3]) + ("…" if len(value) > 3 else "") + "}"
                    note = "⚠️ Nested object — will need flattening"
                elif isinstance(value, list):
                    example = f"[{len(value)} item(s)]"
                    note = "⚠️ Nested list — will need flattening or joining"
                elif value is None:
                    example = "null"
                    note = "Missing value"
                else:
                    example = str(value)[:60] + ("…" if len(str(value)) > 60 else "")
                    note = ""
                inventory_rows.append({
                    "Field": field,
                    "Type": py_type,
                    "Example value": example,
                    "Note": note,
                })
            st.dataframe(
                pd.DataFrame(inventory_rows),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("This record is not a JSON object — it cannot be inventoried as a table.")

        st.markdown("""
> **Key observation for Day 2:** Fields marked ⚠️ cannot be used directly in a spreadsheet.
> On Day 2 we will extract or flatten them into separate columns.
        """)

    # ── Download + session save ───────────────────────────────────────────────
    _raw_bytes = json.dumps(raw, indent=2).encode("utf-8")
    st.download_button(
        "⬇️ Download Raw JSON to your computer",
        _raw_bytes, "byod_raw.json", "application/json",
        key=f"dl_raw_{source_label.replace(' ', '_')}",
    )

    st.session_state["byod_raw"] = raw
    st.session_state["byod_flat_df"] = df
    st.session_state["byod_source"] = "api_get"
    st.info("✅ Data saved. Go to **Day 2 → 🧹 Clean Your Data** when you are ready.")


# ── sidebar ───────────────────────────────────────────────────────────────────

st.sidebar.title("Day 1 Navigation")
app_choice = st.sidebar.radio(
    "Select section",
    ["Overview", "📡 Collect API Data", "🌐 Scrape Webpage Tables"],
)

# ══════════════════════════════════════════════════════════════════════════════
# OVERVIEW
# ══════════════════════════════════════════════════════════════════════════════

if app_choice == "Overview":
    st.title("📥 Day 1 — From Web Source to Raw Dataset")
    st.markdown("""
**Theme:** Help participants understand what kinds of online sources can be transformed into
research data and how the extraction process works in a no-code setting.

### What You Will Do Today
1. Identify a suitable online source for your research question.
2. Understand the structure of API responses and HTML tables.
3. Fetch raw data from a public source — using one of four guided examples or your own.
4. Inspect the raw output and note its limitations.
5. Save your dataset to carry forward into Day 2.

### Two types of online source
| Type | What it is | How we collect it |
|---|---|---|
| **API** | A structured data service that returns JSON | Send a request with parameters; receive records |
| **Webpage table** | An HTML `<table>` embedded in a webpage | Scrape the page; extract the table automatically |

Use the sidebar to go to **📡 Collect API Data** or **🌐 Scrape Webpage Tables** and choose your source.
    """)

# ══════════════════════════════════════════════════════════════════════════════
# COLLECT DATA
# ══════════════════════════════════════════════════════════════════════════════

elif app_choice == "📡 Collect API Data":
    st.title("🔍 Day 1 — Collect Data")
    st.markdown("""
This page lets you fetch data from a public online source — no code required.

**Choose one of the four guided examples below**, or scroll down to the
**Interactive Collection Wizard** to use any API or webpage of your choice.
Your data will be saved automatically so you can continue in Day 2.
    """)

    # ── SECTION 1: Four guided presets ───────────────────────────────────────
    st.markdown("---")
    st.subheader("📌 Guided Examples — Four Case Studies")
    st.markdown("""
Each example below uses a real public API with a pre-configured research question.
Click **▶ Run this example** to fetch the data, see a preview and a distribution chart,
and save it for Day 2.
    """)

    # ── Preset 1: ClinicalTrials.gov ─────────────────────────────────────────
    with st.expander("🏥 Example 1 — ClinicalTrials.gov (Health)"):
        st.markdown("""
**Source:** [ClinicalTrials.gov v2 API](https://clinicaltrials.gov/api/v2/studies)

**Research question:** What are the characteristics (phase, status, conditions) of recently
registered clinical trials related to *diabetes*?

**How it works:** The API is queried with `query.cond=diabetes&pageSize=50&format=json`.
It returns a JSON list of trial records, each containing nested sub-objects for status,
design, and conditions.
        """)
        if st.button("▶ Run Example 1 — ClinicalTrials.gov", key="run_preset1"):
            cache_path = os.path.join(CACHE_DIR, "day1_app1_clinicaltrials_raw.json")
            def fetch_ct():
                r = requests.get(
                    "https://clinicaltrials.gov/api/v2/studies",
                    params={"query.cond": "diabetes", "pageSize": 50, "format": "json"},
                    timeout=30,
                )
                r.raise_for_status()
                return r.json()
            try:
                with st.spinner("Fetching ClinicalTrials.gov data…"):
                    data = load_or_fetch_json(cache_path, fetch_ct)
                studies = data.get("studies", [])
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
                save_and_display_result(df, studies, "ClinicalTrials.gov")
                with st.expander("📌 Teaching note"):
                    st.markdown("""
- The raw JSON is **nested**: trial metadata, status, design, and conditions are in separate sub-objects.
- The `phases` field is a **list** — a single trial may have multiple phases.
- On **Day 2** we will flatten this structure into a clean tabular dataset.
                    """)
            except Exception as e:
                st.error(f"Could not load data: {e}")

    # ── Preset 2: WHO GHO ─────────────────────────────────────────────────────
    with st.expander("🌍 Example 2 — WHO Global Health Observatory (Health)"):
        st.markdown("""
**Source:** [WHO GHO OData API](https://ghoapi.azureedge.net/api/)

**Research question:** How does life expectancy at birth vary across countries and years?

**How it works:** The API is queried for indicator `WHOSIS_000001` (life expectancy at birth)
with `$top=300`. It returns country-year-sex records in a flat JSON list.
        """)
        if st.button("▶ Run Example 2 — WHO Global Health Observatory", key="run_preset2"):
            cache_path = os.path.join(CACHE_DIR, "day1_app2_who_raw.json")
            def fetch_who():
                r = requests.get(
                    "https://ghoapi.azureedge.net/api/WHOSIS_000001",
                    params={"$top": 300}, timeout=30,
                )
                r.raise_for_status()
                return r.json()
            try:
                with st.spinner("Fetching WHO GHO data…"):
                    data = load_or_fetch_json(cache_path, fetch_who)
                records = data.get("value", [])
                df = pd.DataFrame([{
                    "Country": r.get("SpatialDim", ""),
                    "Year": r.get("TimeDim", ""),
                    "Sex": r.get("Dim1", ""),
                    "Value": r.get("NumericValue", None),
                } for r in records])
                save_and_display_result(df, records, "WHO GHO")
                with st.expander("📌 Teaching note"):
                    st.markdown("""
- Each country-year combination appears **three times**: Both sexes, Male, and Female.
- This is a structural feature of the source — not an error — but it must be handled during
  cleaning on Day 2 (e.g., filtering to `SEX_BTSX` = Both sexes).
- The `NumericValue` field may be `null` for some country-year combinations.
                    """)
            except Exception as e:
                st.error(f"Could not load data: {e}")

    # ── Preset 3: NIH RePORTER ────────────────────────────────────────────────
    with st.expander("🔬 Example 3 — NIH RePORTER (Life Sciences)"):
        st.markdown("""
**Source:** [NIH RePORTER API v2](https://api.reporter.nih.gov/v2/projects/search)

**Research question:** What are the characteristics of NIH-funded projects related to *genomics*?

**How it works:** This API uses a **POST request** — instead of URL parameters, the query is
sent as a JSON body. The API returns structured records for funded research projects.
        """)
        if st.button("▶ Run Example 3 — NIH RePORTER", key="run_preset3"):
            cache_path = os.path.join(CACHE_DIR, "day1_app3_nih_raw.json")
            def fetch_nih():
                payload = {
                    "criteria": {"advanced_text_search": {
                        "operator": "and", "search_field": "all", "search_text": "genomics"
                    }},
                    "offset": 0, "limit": 50,
                    "fields": ["ProjectNum", "ProjectTitle", "FiscalYear", "AwardAmount",
                               "OrgName", "OrgCity", "OrgState", "AgencyCode",
                               "ProjectStartDate", "ProjectEndDate"],
                }
                r = requests.post(
                    "https://api.reporter.nih.gov/v2/projects/search",
                    json=payload, timeout=30,
                )
                r.raise_for_status()
                return r.json()
            try:
                with st.spinner("Fetching NIH RePORTER data…"):
                    data = load_or_fetch_json(cache_path, fetch_nih)
                results = data.get("results", [])
                df = pd.DataFrame([{
                    "Project #": r.get("project_num", ""),
                    "Title": str(r.get("project_title", ""))[:60],
                    "FY": r.get("fiscal_year", ""),
                    "Award ($)": r.get("award_amount", None),
                    "Agency": r.get("agency_code", ""),
                    "Org": str(r.get("org_name", ""))[:30],
                    "State": r.get("org_state", ""),
                } for r in results])
                save_and_display_result(df, results, "NIH RePORTER")
                with st.expander("📌 Teaching note"):
                    st.markdown("""
- The `award_amount` field may be `null` for some records — a common issue in grant databases.
- This API uses a **POST request**: the query is sent as a JSON body, not URL parameters.
  This is more powerful (supports complex filters) but less common than GET.
- On **Day 2** we will extract organisation and agency information into flat columns.
                    """)
            except Exception as e:
                st.error(f"Could not load data: {e}")

    # ── Preset 4: Congress.gov ────────────────────────────────────────────────
    with st.expander("🏛️ Example 4 — Congress.gov (Social Sciences)"):
        st.markdown("""
**Source:** [Congress.gov API v3](https://api.congress.gov/v3/bill/118)

**Research question:** What bills were introduced in the 118th Congress (2023–2024),
and what are their types, chambers of origin, and latest actions?

**How it works:** The API is queried with `format=json&limit=50&api_key=YOUR_KEY`.
It returns structured JSON records for bills, each with nested `latestAction` objects.
        """)
        st.info(
            "🔑 **API key required.** Congress.gov requires a free personal API key. "
            "Register in seconds at [api.congress.gov](https://api.congress.gov/) — "
            "you will receive your key by e-mail immediately. "
            "The other three examples (ClinicalTrials, WHO GHO, NIH RePORTER) work without any key."
        )
        congress_api_key = st.text_input(
            "Your Congress.gov API key",
            value="DEMO_KEY",
            help="Paste your personal key here. DEMO_KEY works but is heavily rate-limited.",
            key="congress_api_key",
        )
        if st.button("▶ Run Example 4 — Congress.gov", key="run_preset4"):
            _ckey = st.session_state.get("congress_api_key", "DEMO_KEY") or "DEMO_KEY"
            # Do not cache when a real key is used (personalised results)
            cache_path = os.path.join(CACHE_DIR, "day1_app4_congress_raw.json") \
                if _ckey == "DEMO_KEY" else None
            def fetch_congress():
                r = requests.get(
                    "https://api.congress.gov/v3/bill/118",
                    params={"format": "json", "limit": 50, "api_key": _ckey},
                    timeout=30,
                )
                r.raise_for_status()
                return r.json()
            try:
                with st.spinner("Fetching Congress.gov data…"):
                    data = load_or_fetch_json(cache_path, fetch_congress) \
                        if cache_path else fetch_congress()
                bills = data.get("bills", [])
                df = pd.DataFrame([{
                    "Number": b.get("number", ""),
                    "Type": b.get("type", ""),
                    "Title": str(b.get("title", ""))[:70],
                    "Chamber": b.get("originChamber", ""),
                    "Congress": b.get("congress", ""),
                    "Latest Action Date": b.get("latestAction", {}).get("actionDate", ""),
                    "Latest Action": str(b.get("latestAction", {}).get("text", ""))[:60],
                } for b in bills])
                save_and_display_result(df, bills, "Congress.gov")
                with st.expander("📌 Teaching note"):
                    st.markdown("""
- The `latestAction` field is a **nested object** containing both a date and a text description.
  On Day 2 we will extract these into separate flat columns.
- The `type` field encodes the bill category (e.g., `HR` = House Resolution, `S` = Senate bill).
- The `updateDate` field is a string that will be parsed as a proper date on Day 2.
                    """)
            except Exception as e:
                st.error(f"Could not load data: {e}")

    # ── SECTION 2: Open API reference + wizard ────────────────────────────────
    st.markdown("---")
    st.subheader("📋 Use Any Public API")
    st.markdown("""
Not finding what you need in the examples above? The table below lists verified open APIs
across disciplines. Copy a Base URL, choose the matching method in the wizard, and fetch your data.

> ⚠️ **Important:** The URLs below are *base URLs* — they are **incomplete on their own**.
> Clicking one directly in your browser will return an error like *"query is a required parameter"*.
> This is normal. The wizard adds the parameters for you automatically.
    """)

    # Each entry: (Discipline, Name, URL, params, Method, records_info, docs_url)
    _apis = [
        ("Health", "ClinicalTrials.gov v2",
         "https://clinicaltrials.gov/api/v2/studies",
         [("query.cond", "diabetes"), ("pageSize", "50"), ("format", "json")], "GET",
         "50 per request; max 1,000 per request",
         "https://clinicaltrials.gov/data-api/api"),
        ("Health", "WHO Global Health Observatory",
         "https://ghoapi.azureedge.net/api/WHOSIS_000001",
         [("$top", "300")], "GET",
         "No hard cap per request (use $top to set)",
         "https://www.who.int/data/gho/info/gho-odata-api"),
        ("Health", "PubMed E-utilities",
         "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
         [("db", "pubmed"), ("term", "cancer"), ("retmax", "50"), ("retmode", "json")], "GET",
         "20 per request (default); max 100,000 per request",
         "https://www.ncbi.nlm.nih.gov/books/NBK25499/"),
        ("Health", "OpenFDA Drug Adverse Events",
         "https://api.fda.gov/drug/event.json",
         [("limit", "50")], "GET",
         "1 per request (default); max 1,000 per request",
         "https://open.fda.gov/apis/"),
        ("Health", "OpenFDA Drug Labels",
         "https://api.fda.gov/drug/label.json",
         [("limit", "50")], "GET",
         "1 per request (default); max 1,000 per request",
         "https://open.fda.gov/apis/"),
        ("Life Sciences", "NIH RePORTER v2",
         "https://api.reporter.nih.gov/v2/projects/search",
         [], "POST",
         "50 per request (default); max 500 per request; up to 10,000 total",
         "https://api.reporter.nih.gov/"),
        ("Life Sciences", "GBIF Occurrence Search",
         "https://api.gbif.org/v1/occurrence/search",
         [("scientificName", "Panthera leo"), ("limit", "50")], "GET",
         "20 per request (default); max 300 per request; up to 100,000 total",
         "https://techdocs.gbif.org/en/openapi/v1/occurrence"),
        ("Life Sciences", "Europe PMC",
         "https://www.ebi.ac.uk/europepmc/webservices/rest/search",
         [("query", "malaria"), ("format", "json"), ("pageSize", "50")], "GET",
         "25 per request (default); max 1,000 per request",
         "https://europepmc.org/RestfulWebService"),
        ("Life Sciences", "UniProt REST API",
         "https://rest.uniprot.org/uniprotkb/search",
         [("query", "insulin"), ("format", "json"), ("size", "50")], "GET",
         "25 per request (default); max 500 per request",
         "https://www.uniprot.org/help/api_queries"),
        ("Social Sciences", "World Bank Indicators",
         "https://api.worldbank.org/v2/country/US/indicator/SP.POP.TOTL",
         [("format", "json"), ("per_page", "50")], "GET",
         "50 per request (default); max 32,767 per request",
         "https://datahelpdesk.worldbank.org/knowledgebase/articles/898581"),
        ("Social Sciences", "Crossref Works",
         "https://api.crossref.org/works",
         [("query", "systematic review"), ("rows", "50")], "GET",
         "20 per request (default); max 1,000 per request",
         "https://www.crossref.org/documentation/retrieve-metadata/rest-api/"),
        ("Social Sciences", "OpenAlex Works",
         "https://api.openalex.org/works",
         [("search", "climate change"), ("per-page", "50"), ("mailto", "your@email.com")], "GET",
         "25 per request (default); max 100 per request; up to 10,000 via pagination",
         "https://docs.openalex.org/"),
        ("Social Sciences", "Congress.gov Bills",
         "https://api.congress.gov/v3/bill/118",
         [("format", "json"), ("limit", "50"), ("api_key", "DEMO_KEY")], "GET",
         "20 per request (default); max 250 per request",
         "https://github.com/LibraryOfCongress/api.congress.gov"),
        ("Social Sciences", "OECD Stats (SDMX-JSON)",
         "https://stats.oecd.org/SDMX-JSON/data/QNA/AUS.B1_GE.VOBARSA.Q/all",
         [("startTime", "2020-Q1"), ("endTime", "2022-Q4")], "GET",
         "All matching records returned (no pagination; use time filters to limit)",
         "https://data.oecd.org/api/sdmx-json-documentation/"),
    ]

    _md_rows = [
        "| Discipline | API Name | Base URL | Method | Records per Request | Docs |",
        "|---|---|---|---|---|---|"
    ]
    for _disc, _name, _url, _pairs, _method, _records, _docs in _apis:
        _md_rows.append(
            f"| {_disc} | {_name} | [{_url}]({_url}) | {_method} | {_records} | {_docs} |"
        )
    st.markdown("\n".join(_md_rows))

    st.markdown("**▶ Click an API below to see the exact parameters to enter in the wizard:**")
    for _disc, _name, _url, _pairs, _method, _records, _docs in _apis:
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

    # ── Interactive Collection Wizard ─────────────────────────────────────────
    st.markdown("---")
    st.subheader("⚙️ Interactive Collection Wizard")

    with st.expander("📖 Worked Example — UniProt REST API (click to expand)"):
        st.markdown("""
**Goal:** Fetch 50 records about *insulin* from the UniProt protein database.

**Step 1 — Find the row** in the API table above:
- API Name: UniProt REST API
- Base URL: `https://rest.uniprot.org/uniprotkb/search`
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

The wizard assembles the full URL and sends the request. You will see the raw JSON response,
a preview table, a distribution chart, and a download button appear below.

> **Why does clicking the Base URL directly give an error?**
> Because `query` is a required parameter — the API cannot return anything without knowing
> what to search for. The wizard adds the parameters for you; the browser address bar does not.
        """)

    method = st.radio(
        "Choose your data collection method:",
        ["Query an API (GET request)", "Query an API (POST request)"],
        horizontal=True,
    )

    # ── Method 1: GET ─────────────────────────────────────────────────────────
    if method == "Query an API (GET request)":
        st.markdown("""
Paste the **Base URL** from the reference table above, then fill in the key–value parameters.

For example, `query=insulin&format=json&size=50` → set *Number of parameters* to **3** and enter:
- Key: `query` / Value: `insulin`
- Key: `format` / Value: `json`
- Key: `size` / Value: `50`
        """)
        base_url = st.text_input("API Base URL", placeholder="e.g. https://api.crossref.org/works")

        # ── OpenAlex field selector ──────────────────────────────────────────
        _is_openalex = base_url and "openalex.org" in base_url
        _openalex_select = ""
        if _is_openalex:
            _ALL_OPENALEX_FIELDS = [
                "id", "doi", "title", "display_name", "publication_year", "publication_date",
                "type", "cited_by_count", "is_retracted", "is_paratext",
                "open_access", "authorships", "primary_location", "locations",
                "concepts", "keywords", "topics", "mesh",
                "referenced_works", "related_works", "cited_by_api_url",
                "abstract_inverted_index", "biblio", "ids", "language",
                "grants", "apc_list", "apc_paid", "sustainable_development_goals",
            ]
            _DEFAULT_FIELDS = [
                "id", "doi", "title", "publication_year", "cited_by_count",
                "open_access", "authorships", "primary_location", "concepts",
            ]
            st.markdown(
                "🔍 **OpenAlex detected** — choose which fields to return. "
                "Selecting fewer fields avoids thousands of columns in the output."
            )
            _selected_fields = st.multiselect(
                "Fields to include (`select` parameter)",
                options=_ALL_OPENALEX_FIELDS,
                default=_DEFAULT_FIELDS,
                key="openalex_select_fields",
                help=(
                    "OpenAlex supports a `select` parameter that restricts which fields are returned. "
                    "The default selection covers the most useful fields for most research tasks. "
                    "Add or remove fields as needed."
                ),
            )
            if _selected_fields:
                _openalex_select = ",".join(_selected_fields)

        n_params = st.number_input("Number of parameters", min_value=1, max_value=10, value=2, step=1)
        params = {}
        for i in range(int(n_params)):
            c1, c2 = st.columns(2)
            k = c1.text_input(f"Key {i+1}", key=f"get_key_{i}")
            v = c2.text_input(f"Value {i+1}", key=f"get_val_{i}")
            if k:
                params[k] = v
        # inject select param for OpenAlex
        if _openalex_select:
            params["select"] = _openalex_select
        api_key_header = st.text_input(
            "API Key (optional — leave blank if not required)",
            type="password",
            help="If the API requires a key in the Authorization header, enter it here.",
        )
        use_pagination = st.checkbox(
            "Enable pagination (fetch all pages automatically)",
            value=False,
            key="get_pagination_on",
        )
        if use_pagination:
            pagination_method = st.radio(
                "Pagination method",
                [
                    "Cursor (next_cursor) — e.g. OpenAlex",
                    "Offset (page=1, 2, 3 …) — e.g. most REST APIs",
                ],
                key="get_pagination_method",
                help=(
                    "**Cursor**: the API returns a `next_cursor` token in each response — "
                    "pass it back as `cursor=` in the next request. Works for any number of records.\n\n"
                    "**Offset**: increment a `page` parameter (1, 2, 3 …). "
                    "Usually capped at 10,000 records total."
                ),
            )
            cursor_param_name = "cursor"
            next_cursor_key  = "next_cursor"
            if "Cursor" in pagination_method:
                col_c1, col_c2 = st.columns(2)
                cursor_param_name = col_c1.text_input(
                    "Cursor parameter name (sent in request)",
                    value="cursor",
                    key="cursor_param_name",
                    help="The URL parameter the API uses for the cursor. OpenAlex uses `cursor`.",
                )
                next_cursor_key = col_c2.text_input(
                    "Next-cursor key (in response JSON)",
                    value="next_cursor",
                    key="next_cursor_key",
                    help="The key inside the response `meta` object that holds the next cursor value. OpenAlex uses `next_cursor`.",
                )
            max_records = st.number_input(
                "Safety cap — stop after this many records (0 = no cap)",
                min_value=0, max_value=100_000, value=2000, step=100,
                key="get_max_records",
                help="Prevents runaway fetches. Set to 0 to collect everything.",
            )
            st.info(
                "💡 **How it works in Streamlit:** when you click Fetch All Pages below, "
                "the app runs a loop entirely on the server — each page is fetched one after "
                "another and a live counter shows progress. The full combined dataset is "
                "displayed and saved when the loop finishes."
            )

        st.markdown("---")

        # ── Single-page fetch ─────────────────────────────────────────────────
        if not use_pagination:
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
                            raw_list = byod_raw if isinstance(byod_raw, list) else \
                                       byod_raw.get("results", byod_raw.get("value",
                                       byod_raw.get("studies", byod_raw.get("bills",
                                       byod_raw.get("works", [byod_raw])))))
                            if not isinstance(raw_list, list):
                                raw_list = [raw_list]
                            try:
                                df = pd.json_normalize(raw_list, max_level=1)
                            except Exception:
                                df = pd.DataFrame(raw_list)
                            save_and_display_result(df, byod_raw, "API (GET)")
                        else:
                            st.error(f"Request failed: {r.text[:300]}")
                    except Exception as e:
                        st.error(f"Error: {e}")

        # ── Paginated fetch ───────────────────────────────────────────────────
        else:
            if st.button("🚀 Fetch All Pages", key="fetch_get_paginated"):
                if not base_url:
                    st.warning("Please enter a base URL.")
                else:
                    import time as _time
                    headers = {"User-Agent": "workshop-byod/1.0", "Accept": "application/json"}
                    if api_key_header:
                        headers["Authorization"] = f"Bearer {api_key_header}"

                    all_raw_list = []
                    status_box   = st.empty()
                    progress_bar = st.progress(0)
                    cap = int(max_records) if max_records > 0 else None

                    def _safe_get(url, prms, hdrs, status_box, page_num, max_retries=3):
                        """GET with 429/5xx retry and clear error messages.
                        Builds URL manually to avoid encoding cursor=* as cursor=%2A."""
                        import time as _t
                        from urllib.parse import urlencode, urlparse, urlunparse, parse_qs
                        # Build query string — keep * unencoded (safe='*')
                        qs = urlencode(prms, safe="*,")
                        parsed = urlparse(url)
                        full_url = urlunparse(parsed._replace(query=qs))
                        for attempt in range(1, max_retries + 1):
                            r = requests.get(full_url, headers=hdrs, timeout=30)
                            if r.status_code == 200:
                                try:
                                    return r.json()
                                except Exception:
                                    raise ValueError(
                                        f"Page {page_num}: HTTP 200 but response is not valid JSON. "
                                        f"First 300 chars: {r.text[:300]}"
                                    )
                            elif r.status_code == 429:
                                wait = min(int(r.headers.get("Retry-After", 10)), 60)
                                status_box.warning(
                                    f"Rate-limited (429) on page {page_num} — "
                                    f"waiting {wait}s before retry {attempt}/{max_retries}…"
                                )
                                _t.sleep(wait)
                            else:
                                raise ValueError(
                                    f"Page {page_num}: HTTP {r.status_code} — {r.text[:300]}"
                                )
                        raise ValueError(
                            f"Page {page_num}: gave up after {max_retries} retries (429 rate limit)."
                        )

                    try:
                        if "Cursor" in pagination_method:
                            # ── Cursor pagination ─────────────────────────────
                            cursor_val  = "*"
                            page_num    = 0
                            total_known = None

                            while True:
                                page_params = dict(params)
                                page_params[cursor_param_name] = cursor_val
                                data = _safe_get(base_url, page_params, headers, status_box, page_num + 1)

                                batch = data if isinstance(data, list) else \
                                        data.get("results", data.get("value",
                                        data.get("works",   data.get("items", []))))
                                if not isinstance(batch, list):
                                    batch = []

                                all_raw_list.extend(batch)
                                page_num += 1

                                meta = data.get("meta", {}) if isinstance(data, dict) else {}
                                if total_known is None and "count" in meta:
                                    total_known = meta["count"]

                                pct = min(len(all_raw_list) / total_known, 1.0) if total_known else 0
                                progress_bar.progress(pct)
                                status_box.info(
                                    f"Page {page_num} fetched — "
                                    f"{len(all_raw_list):,} records collected"
                                    + (f" of {total_known:,} total" if total_known else "")
                                    + (f" (cap: {cap:,})" if cap else "")
                                )

                                next_cur = meta.get(next_cursor_key)
                                if not next_cur or not batch:
                                    break
                                if cap and len(all_raw_list) >= cap:
                                    status_box.warning(
                                        f"Safety cap of {cap:,} records reached — stopping."
                                    )
                                    break
                                cursor_val = next_cur
                                _time.sleep(0.1)

                        else:
                            # ── Offset pagination ─────────────────────────────
                            page_num    = 1
                            total_known = None

                            while True:
                                page_params = dict(params)
                                page_params["page"] = str(page_num)
                                data = _safe_get(base_url, page_params, headers, status_box, page_num)

                                batch = data if isinstance(data, list) else \
                                        data.get("results", data.get("value",
                                        data.get("works",   data.get("items", []))))
                                if not isinstance(batch, list):
                                    batch = []

                                if not batch:
                                    break

                                all_raw_list.extend(batch)

                                meta = data.get("meta", {}) if isinstance(data, dict) else {}
                                if total_known is None and "count" in meta:
                                    total_known = meta["count"]

                                pct = min(len(all_raw_list) / total_known, 1.0) if total_known else 0
                                progress_bar.progress(pct)
                                status_box.info(
                                    f"Page {page_num} fetched — "
                                    f"{len(all_raw_list):,} records collected"
                                    + (f" of {total_known:,} total" if total_known else "")
                                    + (f" (cap: {cap:,})" if cap else "")
                                )

                                if cap and len(all_raw_list) >= cap:
                                    status_box.warning(
                                        f"Safety cap of {cap:,} records reached — stopping."
                                    )
                                    break
                                page_num += 1
                                _time.sleep(0.1)

                        progress_bar.progress(1.0)
                        status_box.success(
                            f"✅ Pagination complete — {len(all_raw_list):,} records collected "
                            f"across {page_num} page(s)."
                        )

                        if all_raw_list:
                            try:
                                df = pd.json_normalize(all_raw_list, max_level=1)
                            except Exception:
                                df = pd.DataFrame(all_raw_list)
                            save_and_display_result(df, all_raw_list, "API (GET — paginated)")
                        else:
                            st.warning("No records were collected. Check your URL and parameters.")

                    except Exception as e:
                        st.error(f"Pagination error on page {page_num}: {e}")

    # ── Method 2: POST ────────────────────────────────────────────────────────
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
            "Request Body (JSON)", value=default_body, height=150,
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
                        raw_list = byod_raw.get("results", [byod_raw]) if isinstance(byod_raw, dict) else byod_raw
                        if not isinstance(raw_list, list):
                            raw_list = [raw_list]
                        try:
                            df = pd.json_normalize(raw_list, max_level=1)
                        except Exception:
                            df = pd.DataFrame(raw_list)
                        save_and_display_result(df, byod_raw, "API (POST)")
                    else:
                        st.error(f"Request failed: {r.text[:300]}")
                except json.JSONDecodeError:
                    st.error("Invalid JSON in request body. Please check your syntax.")
                except Exception as e:
                    st.error(f"Error: {e}")

# ══════════════════════════════════════════════════════════════════════════════
# SCRAPE WEBPAGE TABLES
# ══════════════════════════════════════════════════════════════════════════════

elif app_choice == "🌐 Scrape Webpage Tables":
    st.title("🌐 Day 1 — Scrape Webpage Tables")
    st.markdown("""
Paste the URL of any webpage that contains an HTML `<table>`. The app will extract all tables
it finds and let you choose which one to use.
    """)

    # Example URLs reference table
    _scrape = [
        ("Health", "Wikipedia — Life Expectancy by Country",
         "https://en.wikipedia.org/wiki/List_of_countries_by_life_expectancy"),
        ("Health", "Wikipedia — COVID-19 pandemic by country",
         "https://en.wikipedia.org/wiki/COVID-19_pandemic_by_country_and_territory"),
        ("Life Sciences", "Wikipedia — Lists of endangered species",
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
    _s_rows = ["| Discipline | Description | URL |", "|---|---|---|"]
    for _disc, _desc, _url in _scrape:
        _s_rows.append(f"| {_disc} | {_desc} | [{_url}]({_url}) |")
    st.markdown("**Example URLs you can paste below:**")
    st.markdown("\n".join(_s_rows))

    st.markdown("""
> **Note:** This method works on *static* HTML tables only. Pages that load their tables
> dynamically via JavaScript (e.g., interactive dashboards) will not work with this approach —
> this is itself an important methodological distinction to understand.
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
                    from io import StringIO
                    _resp = requests.get(
                        page_url,
                        headers={"User-Agent": "Mozilla/5.0 (workshop-byod)"},
                        timeout=30,
                    )
                    _resp.raise_for_status()
                    tables = pd.read_html(StringIO(_resp.text))
                    tables = flatten_multiindex(tables)
                if tables:
                    st.success(f"Found {len(tables)} table(s) on the page.")
                    st.session_state["byod_scraped_dfs"] = tables
                    st.session_state["byod_source"] = "scrape"
                else:
                    st.warning("No tables found on this page. The page may use JavaScript to render its tables — try a different URL.")
            except Exception as e:
                st.error(f"Could not extract tables: {e}")
                st.info("This may happen if the page uses JavaScript to render its tables, or if the URL is not publicly accessible.")

    if "byod_scraped_dfs" in st.session_state:
        tables = st.session_state["byod_scraped_dfs"]
        table_labels = [f"Table {i+1} — {t.shape[0]} rows × {t.shape[1]} cols" for i, t in enumerate(tables)]
        chosen = st.selectbox("Select the table you want to use:", table_labels)
        idx = table_labels.index(chosen)
        selected_table = tables[idx]

        st.markdown("#### Preview (first 20 rows)")
        st.dataframe(selected_table.head(20), use_container_width=True)

        _json_bytes = selected_table.to_json(orient="records", indent=2).encode("utf-8")
        st.download_button(
            "⬇️ Download Table as JSON to your computer",
            _json_bytes, "byod_scraped_table.json", "application/json",
            key="dl_scrape_json",
        )

        # Auto-save the currently selected table to session immediately
        st.session_state["byod_flat_df"] = selected_table
        st.session_state["byod_source"] = "scrape"
        st.info(
            "✅ Table auto-saved to session. "
            "Go to **Day 2 → 🧹 Clean Your Data** when you are ready, "
            "or download the JSON above to use it in a later session."
        )
        if st.button("➡️ Go to Day 2 →", key="use_table"):
            st.success("✅ Navigate to Day 2 using the sidebar.")
