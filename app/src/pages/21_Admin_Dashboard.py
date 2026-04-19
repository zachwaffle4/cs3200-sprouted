import logging
import requests
import streamlit as st
from modules.nav import SideBarLinks
logger = logging.getLogger(__name__)

st.set_page_config(layout='wide')

SideBarLinks()

# Stats for Plot Overview
site_stats = {
    "total": 67,
    "active": 61,
    "vacant": 4,
    "waitlisted": 1
    }
# TODO: replace with requests.get(f"{API_BASE}/plots/stats").json(


#  Plot Applications (for Pending Applications section)
pending_applications = [
    {"id": 1, "name": "James Okafar", "requested_plot": "Plot B-12"},
    {"id": 2, "name": "Priya Desai", "requested_plot": "Any Available"},
    {"id": 3, "name": "Tom Nguyễn", "requested_plot": "Plot A-3"},
] # TODO: replace with → requests.get(f"{API_BASE}/applications?status=pending").json()

# For Upcoming Workdays section
upcoming_workdays = [
    {"id": 1, "name": "Spring Cleanup",   "date": "Apr 5, 2026",  "time": "9:00 AM",  "signed_up": 8,  "needed": 12},
    {"id": 2, "name": "Spring Cleanup",   "date": "Apr 12, 2026", "time": "10:00 AM", "signed_up": 3,  "needed": 6},
] # TODO: replace with → requests.get(f"{API_BASE}/workdays?upcoming=true&limit=2").json()

water_budget = {
    "month": "April",
    "used_gal": 2400,
    "budget_gal": 8000,
} # TODO: replace with → requests.get(f"{API_BASE}/sites/{site_id}/water-log?month=current").json()

# For Pest Reports section
pest_reports = [
    {"id": 1, "plot": "A-7", "issue": "Aphids", "severity": "High", "status": "In Progress"},
    {"id": 2, "plot": "C-2", "issue": "Powdery Mildew", "severity": "Med",  "status": "Acknowledged"},
] # TODO: replace with → requests.get(f"{API_BASE}/pest-reports?status=open").json()


st.title('Garden Administration Dashboard')

# SECTION 1: Site Overview Metrics
st.write('## Site Overview')

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Plots", site_stats["total"], border=True)
col2.metric("Active", site_stats["active"], border=True)
col3.metric("Vacant", site_stats["vacant"], border=True)
col4.metric("Waitlisted", site_stats["waitlisted"], border=True)

st.divider()


# SECTION 2: Pending Plot Applications
st.write("## Pending Plot Applications")
h1, h2, h3 = st.columns([3, 3, 2])
h1.markdown("**Name**")
h2.markdown("**Requested Plot**")
h3.markdown("**Action**")

for app in pending_applications:
    c1, c2, c3, c4 = st.columns([3, 3, 1, 1])
    c1.write(app["name"])
    c2.write(app["requested_plot"])

    if c3.button("Assign", key=f"assign_{app['id']}"):
        # TODO: replace with:
        # requests.put(f"{API_BASE}/applications/{app['id']}", json={"status": "approved"})
        st.success(f"Assigned plot to {app['name']}!")
        st.rerun()

    if c4.button("Waitlist", key=f"waitlist_{app['id']}"):
        # TODO: replace with:
        # requests.put(f"{API_BASE}/applications/{app['id']}", json={"status": "waitlisted"})
        st.info(f"Moved {app['name']} to waitlist.")
        st.rerun()

st.divider()


# SECTION 3: Upcoming Workdays
st.write("## Upcoming Workdays")
wd_cols = st.columns(2)
for i, wd in enumerate(upcoming_workdays):
    # calculate ratio for progress bar, handles div by 0 error
    ratio = (wd["signed_up"] / wd["needed"]) if wd["needed"] > 0 else 0
    with wd_cols[i % 2]:
        with st.container(border=True):
            st.markdown(f"**{wd['date']} — {wd['time']}**")
            st.markdown(f"**{wd['name']}**")
            st.progress(
                ratio,
                text=f"{wd['signed_up']}/{wd['needed']} volunteers signed up"
            )

st.divider()


# SECTION 4: Water Budget + Pest Reports
st.write("## Water Management")
with st.container(border=True):
    wc1, wc2 = st.columns(2)
    wc1.markdown(f"**Water used this month**\n\n{water_budget['used_gal']:,} gal")
    wc2.markdown(f"**Seasonal Budget**\n\n{water_budget['budget_gal']:,} gal")
    water_ratio = water_budget["used_gal"] / water_budget["budget_gal"]
    st.progress(water_ratio, text=(
        f"{water_budget['used_gal']:,}  / {water_budget['budget_gal']:,} gal used"
    ))

st.divider()


# SECTION 5: Pest Reports
# Table header
st.subheader("Open Pest Reports")
c1, c2, c3, c4 = st.columns([2, 3, 2, 3])
c1.write("**Plot**") # col 1 labels the plot where the issue is occurring
c2.write("**Issue**") # col 2 describes the pest issue being reported
c3.write("**Severity**") # col 3 indicates how severe the issue is (e.g. low/med/high)
c4.write("**Status**") # col 4 indicates the current status of the report
for r in pest_reports:
    c1, c2, c3, c4 = st.columns([2, 3, 2, 3]) # create 4 cols for each report
    c1.write(r["plot"])
    c2.write(r["issue"])
    c3.write(r["severity"])
    c4.write(r["status"])
