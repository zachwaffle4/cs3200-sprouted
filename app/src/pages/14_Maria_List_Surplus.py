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


# Fetch Maria's plots and the crop list
plots = api_get(f"/users/{MARIA_USER_ID}/plots") or []
plot_options = {p["plot_name"]: p["plot_id"] for p in plots}
my_plot_ids = set(plot_options.values())

all_surplus = api_get("/surplus") or []
crop_options = {}
for row in all_surplus:
    crop_options[row["crop_name"]] = row["crop_id"]

# Filter the global surplus list to Maria's plots only
my_listings = [row for row in all_surplus if row.get("plot_id") in my_plot_ids]

# Page content
st.title("List Surplus Produce")
st.caption(f"Logged in as {st.session_state.get('first_name', 'Maria')} Santos")

if not plot_options:
    st.warning("You have no active plots assigned. Contact the garden admin.")
    st.stop()

if not crop_options:
    st.warning("No crops exist in the database yet.")
    st.stop()

# Section 1: Create listing
st.subheader("Create a Listing")
st.caption("Share extra produce with partner food banks and shelters.")

with st.form("surplus_form"):
    plot_label = st.selectbox("Plot", list(plot_options.keys()))
    crop_label = st.selectbox("Crop", list(crop_options.keys()))
    quantity = st.number_input("Quantity (lbs)", min_value=0.25, step=0.5, value=3.00)
    freshness = st.text_input(
        "Freshness note (optional)",
        placeholder="e.g. Picked this morning, best used within 3 days.",
    )
    submitted = st.form_submit_button("Create Listing")

    if submitted:
        payload = {
            "plot_id": plot_options[plot_label],
            "crop_id": crop_options[crop_label],
            "quantity_lbs": float(quantity),
            "freshness_note": freshness.strip() or None,
        }
        result = api_post("/surplus", payload)
        if result and result.get("listing_id"):
            st.toast(f"Listed {quantity:.1f} lbs of {crop_label}.")
            st.rerun()
        else:
            st.toast("Failed to create listing.", icon="⚠️")

st.divider()

# Section 2: Active listings from Maria's plots
st.subheader("My Active Listings")
if not my_listings:
    st.info("You have no active surplus listings right now.")
else:
    h1, h2, h3, h4, h5 = st.columns([2, 3, 2, 2, 3])
    h1.markdown("**Plot**")
    h2.markdown("**Crop**")
    h3.markdown("**Qty (lbs)**")
    h4.markdown("**Listed**")
    h5.markdown("**Freshness**")
    for row in my_listings:
        with st.container(border=True):
            c1, c2, c3, c4, c5 = st.columns([2, 3, 2, 2, 3])
            c1.write(row.get("plot_name", "—"))
            c2.write(row.get("crop_name", "—"))
            c3.write(f"{float(row.get('quantity_lbs') or 0):.2f}")
            c4.write(str(row.get("listed_date", "—")))
            c5.write(row.get("freshness_note") or "—")
