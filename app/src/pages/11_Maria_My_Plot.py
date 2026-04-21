import logging
import requests
import streamlit as st
from modules.nav import SideBarLinks

logger = logging.getLogger(__name__)
st.set_page_config(layout='wide')
SideBarLinks()

API_BASE = "http://web-api:4000"
MARIA_USER_ID = 5

# helper functions for API calls
def api_get(path, params=None):
    try:
        r = requests.get(f"{API_BASE}{path}", params=params, timeout=5)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        logger.error("GET %s failed: %s", path, e)
        return None


# Fetch season summary and plot list for Maria
summary = api_get(f"/users/{MARIA_USER_ID}/season-summary") or {}
totals = summary.get("totals") or {}
active_plantings = summary.get("active_plantings") or []
recent_harvests = summary.get("recent_harvests") or []

plots = api_get(f"/users/{MARIA_USER_ID}/plots") or []

# Page content
st.title("My Plot")
st.caption(f"Logged in as {st.session_state.get('first_name', 'Maria')} Santos")

# Section 1: Season metrics
st.write("## Season Summary")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Yield", f"{float(totals.get('total_yield_lbs') or 0):.1f} lbs", border=True)
c2.metric("Active Plantings", int(totals.get("active_plantings") or 0), border=True)
c3.metric("Harvests Recorded", int(totals.get("harvests_recorded") or 0), border=True)
c4.metric("Distinct Crops", int(totals.get("distinct_crops") or 0), border=True)

st.divider()

# Section 2: My plots
st.write("## My Plots")
if not plots:
    st.info("No active plots assigned.")
else:
    h1, h2, h3 = st.columns([2, 3, 3])
    h1.markdown("**Plot**")
    h2.markdown("**Garden Site**")
    h3.markdown("**Assigned Since**")
    for p in plots:
        with st.container(border=True):
            c1, c2, c3 = st.columns([2, 3, 3])
            c1.write(p.get("plot_name", f"Plot {p['plot_id']}"))
            c2.write(p.get("site_name", "—"))
            c3.write(str(p.get("assigned_date", "—")))

st.divider()

# Section 3: Active plantings
st.write("## Active Plantings")
st.caption("Plantings logged but not yet harvested.")
if not active_plantings:
    st.info("No active plantings right now.")
else:
    h1, h2, h3, h4 = st.columns([2, 3, 2, 3])
    h1.markdown("**Plot**")
    h2.markdown("**Crop**")
    h3.markdown("**Type**")
    h4.markdown("**Expected Harvest**")
    for pl in active_plantings:
        with st.container(border=True):
            c1, c2, c3, c4 = st.columns([2, 3, 2, 3])
            c1.write(pl.get("plot_name", "—"))
            c2.write(pl.get("crop_name", "—"))
            c3.write(pl.get("crop_type", "—"))
            c4.write(str(pl.get("expected_harvest_date", "—")))

st.divider()

# Section 4: Recent harvests
st.write("## Recent Harvests")
if not recent_harvests:
    st.info("No harvests logged yet this season.")
else:
    h1, h2, h3, h4 = st.columns([2, 3, 3, 2])
    h1.markdown("**Plot**")
    h2.markdown("**Crop**")
    h3.markdown("**Date**")
    h4.markdown("**Quantity (lbs)**")
    for h in recent_harvests:
        with st.container(border=True):
            c1, c2, c3, c4 = st.columns([2, 3, 3, 2])
            c1.write(h.get("plot_name", "—"))
            c2.write(h.get("crop_name", "—"))
            c3.write(str(h.get("harvest_date", "—")))
            c4.write(f"{float(h.get('quantity_lbs') or 0):.2f}")