"""
Web Scraping and Data Collection — instats Seminar
Main entry point for the Streamlit application.
"""

import streamlit as st

st.set_page_config(
    page_title="Web Scraping and Data Collection",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("🌐 Web Scraping and Data Collection")
st.subheader("instats Seminar — May 13–15, 2026")

st.markdown("""
**Moses Boudourides, Moses.Boudourides@gmail.com**

Welcome to the interactive companion for the three-day instats seminar on
**Web Scraping and Data Collection for Health, Life, and Social Sciences**.

This application demonstrates every step of the data collection pipeline —
from identifying an online source to producing a clean, documented, analysis-ready dataset.
No coding is required: every operation is available through the menus on the left.

---

### How to Navigate

Use the **sidebar** to select a day:

| Day | Theme |
|-----|-------|
| **Day 1** | From Web Source to Raw Dataset |
| **Day 2** | From Raw Output to Usable Data |
| **Day 3** | From Shared Workflow to Participants' Own Data |

---

### Resources

- 📄 [Seminar manuscript (PDF)](https://github.com/mboudour/web-scraping-and-data-collection/blob/main/web_scraping_and_data_collection_paper.pdf)
- 💻 [Scripts and slides on GitHub](https://github.com/mboudour/web-scraping-and-data-collection)
- 📋 [Register / seminar info](https://instats.org/seminar/web-scraping-and-data-collection)
""")

st.info("👈 Select a day from the sidebar to begin.")
