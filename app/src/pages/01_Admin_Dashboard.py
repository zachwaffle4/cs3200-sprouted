import logging
import requests
import streamlit as st
from modules.nav import SideBarLinks

logger = logging.getLogger(__name__)
st.set_page_config(layout='wide')
SideBarLinks()

API_BASE = "http://web-api:4000"
SITE_ID = 1


def api_get(path, params=None):
    try:
        r = requests.get(f"{API_BASE}{path}", params=params, timeout=5)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        logger.error("GET %s failed: %s", path, e)
        return None


def api_put(path, payload):
    try:
        r = requests.put(f"{API_BASE}{path}", json=payload, timeout=5)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        logger.error("PUT %s failed: %s", path, e)
        return None


# Site stats: derive from /plots (occupancy_status is 'assigned' or 'vacant')
plots_data = api_get("/plots") or []
assigned_count = sum(1 for p in plots_data if p.get("occupancy_status") == "assigned")
vacant_count   = sum(1 for p in plots_data if p.get("occupancy_status") == "vacant")
site_stats = {
    "total":      len(plots_data),
    "active":     assigned_count,
    "vacant":     vacant_count,
    "waitlisted": len(plots_data) - assigned_count - vacant_count,
}

# Pending applications from GET /applications?status=pending
apps_raw = api_get("/applications", {"status": "pending"}) or []
pending_applications = [
    {
        "id":             a["application_id"],
        "name":           a["name"],
        "requested_plot": a.get("plot_name") or "Any Available",
    }
    for a in apps_raw
]

# Upcoming workdays from /workdays (take first 2)
workdays_raw = api_get("/workdays") or []
upcoming_workdays = [
    {
        "id":       w["workday_id"],
        "name":     w["event_name"],
        "date":     str(w.get("event_date", "")),
        "signed_up": w.get("signup_count", 0),
        "needed":   max(int(w.get("volunteers_needed", 1)), 1),
    }
    for w in workdays_raw[:2]
]

# Water budget — /sites/{id}/water-log not yet implemented; watering-schedules is a different concept
water_budget = {"month": "April", "used_gal": 2400, "budget_gal": 8000}
# TODO: replace with GET /sites/{SITE_ID}/water-log?month=current once route is implemented

# Pest reports from /pest-reports (already filtered to open + in-progress by the API)
pest_raw = api_get("/pest-reports") or []
pest_reports = [
    {
        "id":       r["report_id"],
        "plot":     str(r.get("plot_id", "—")),
        "issue":    r.get("description", "—"),
        "severity": r.get("severity", "—"),
        "status":   r.get("status", "—"),
    }
    for r in pest_raw
]

# ── UI ────────────────────────────────────────────────────────────────────────

st.title("Garden Administration Dashboard")

# Section 1: Site Overview
st.write("## Site Overview")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Plots",  site_stats["total"],      border=True)
col2.metric("Active",       site_stats["active"],     border=True)
col3.metric("Vacant",       site_stats["vacant"],     border=True)
col4.metric("Waitlisted",   site_stats["waitlisted"], border=True)

st.divider()

# Section 2: Pending Plot Applications
st.write("## Pending Plot Applications")
st.caption("Review and manage incoming plot applications from community members.")
h1, h2, h3 = st.columns([3, 3, 2])
h1.markdown("**Name**")
h2.markdown("**Requested Plot**")
h3.markdown("**Action**")

for app in pending_applications:
    with st.container(border=True):
        c1, c2, c3, c4 = st.columns([3, 3, 1, 1])
        c1.write(app["name"])
        c2.write(app["requested_plot"])
        if c3.button("Assign", key=f"assign_{app['id']}"):
            res = api_put(f"/applications/{app['id']}", {"status": "approved"})
            if res is not None:
                st.toast(f"Assigned plot to {app['name']}!")
            else:
                st.toast("Applications endpoint not yet implemented.", icon="⚠️")
            st.rerun()
        if c4.button("Waitlist", key=f"waitlist_{app['id']}"):
            res = api_put(f"/applications/{app['id']}", {"status": "waitlisted"})
            if res is not None:
                st.toast(f"Moved {app['name']} to waitlist.")
            else:
                st.toast("Applications endpoint not yet implemented.", icon="⚠️")
            st.rerun()

st.divider()

# Section 3: Upcoming Workdays
st.write("## Upcoming Workdays")
if upcoming_workdays:
    wd_cols = st.columns(2)
    for i, wd in enumerate(upcoming_workdays):
        ratio = wd["signed_up"] / wd["needed"]
        with wd_cols[i % 2]:
            with st.container(border=True):
                st.markdown(f"**{wd['date']}**")
                st.markdown(f"**{wd['name']}**")
                st.progress(ratio, text=f"{wd['signed_up']}/{wd['needed']} volunteers signed up")
else:
    st.info("No upcoming workdays scheduled.")

st.divider()

# Section 4: Water Management
st.write("## Water Management")
with st.container(border=True):
    wc1, wc2 = st.columns(2)
    wc1.markdown(f"**Water used this month**\n\n{water_budget['used_gal']:,} gal")
    wc2.markdown(f"**Seasonal Budget**\n\n{water_budget['budget_gal']:,} gal")
    water_ratio = water_budget["used_gal"] / water_budget["budget_gal"]
    st.progress(water_ratio, text=(
        f"{water_budget['used_gal']:,} / {water_budget['budget_gal']:,} gal used"
    ))

st.divider()

# Section 5: Pest Reports
st.subheader("Open Pest Reports")
if pest_reports:
    c1, c2, c3, c4 = st.columns([2, 3, 2, 3])
    c1.write("**Plot**")
    c2.write("**Issue**")
    c3.write("**Severity**")
    c4.write("**Status**")
    for r in pest_reports:
        with st.container(border=True):
            c1, c2, c3, c4 = st.columns([2, 3, 2, 3])
            c1.write(r["plot"])
            c2.write(r["issue"])
            c3.write(r["severity"])
            c4.write(r["status"])
else:
    st.info("No open pest reports.")
