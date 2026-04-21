import logging
import requests
import streamlit as st
from modules.nav import SideBarLinks

logger = logging.getLogger(__name__)
st.set_page_config(layout="wide")
SideBarLinks()

API_BASE = "http://api:4000"
MARIA_USER_ID = 5


# API helper functions
def api_get(path, params=None):
    try:
        r = requests.get(f"{API_BASE}{path}", params=params, timeout=5)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        logger.error("GET %s failed: %s", path, e)
        return None


def api_post(path, payload):
    try:
        r = requests.post(f"{API_BASE}{path}", json=payload, timeout=5)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        logger.error("POST %s failed: %s", path, e)
        return None


# Fetch Maria's plots and the crop list (derived from surplus listings)
plots = api_get(f"/users/{MARIA_USER_ID}/plots") or []
plot_options = {p["plot_name"]: p["plot_id"] for p in plots}

all_surplus = api_get("/surplus") or []
crop_options = {"(no specific crop)": None}
for row in all_surplus:
    crop_options[row["crop_name"]] = row["crop_id"]

# Pull Maria's own reports out of the global list so she can see her past submissions
all_reports = api_get("/pest-reports") or []
maria_reports = [r for r in all_reports if r.get("user_id") == MARIA_USER_ID]

# Page content
st.title("Report a Pest or Disease")
st.caption(f"Logged in as {st.session_state.get('first_name', 'Maria')} Santos")

if not plot_options:
    st.warning("You have no active plots assigned. Contact the garden admin.")
    st.stop()

# Section 1: Submit form
st.subheader("Submit a Report")
st.caption(
    "Flagging issues helps the garden admin prevent spread to neighboring plots."
)

with st.form("pest_report_form"):
    plot_label = st.selectbox("Plot", list(plot_options.keys()))
    crop_label = st.selectbox("Affected crop", list(crop_options.keys()))
    severity = st.selectbox("Severity", ["low", "medium", "high", "critical"])
    description = st.text_area(
        "Description",
        placeholder="What does it look like? Which plants are affected?",
        height=120,
    )
    submitted = st.form_submit_button("Submit Report")

    if submitted:
        if not description.strip():
            st.error("Please describe the issue before submitting.")
        else:
            payload = {
                "plot_id": plot_options[plot_label],
                "crop_id": crop_options[crop_label],
                "user_id": MARIA_USER_ID,
                "description": description.strip(),
                "severity": severity,
            }
            result = api_post("/pest-reports", payload)
            if result and result.get("report_id"):
                st.toast(f"Report submitted for {plot_label}.")
                st.rerun()
            else:
                st.toast("Failed to submit report.", icon="⚠️")

st.divider()

# Section 2: My past reports
st.subheader("My Past Reports")
if not maria_reports:
    st.info("No open or in-progress reports from you right now.")
else:
    h1, h2, h3, h4, h5 = st.columns([2, 2, 4, 2, 2])
    h1.markdown("**Date**")
    h2.markdown("**Plot**")
    h3.markdown("**Issue**")
    h4.markdown("**Severity**")
    h5.markdown("**Status**")
    for r in maria_reports:
        with st.container(border=True):
            c1, c2, c3, c4, c5 = st.columns([2, 2, 4, 2, 2])
            c1.write(str(r.get("date_reported", "—")))
            c2.write(f"Plot {r.get('plot_id', '—')}")
            c3.write(r.get("description", "—"))
            c4.write(r.get("severity", "—"))
            c5.write(r.get("status", "—"))
