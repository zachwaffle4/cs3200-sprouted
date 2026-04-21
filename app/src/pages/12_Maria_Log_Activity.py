import logging
import requests
import streamlit as st
from datetime import date
from modules.nav import SideBarLinks

logger = logging.getLogger(__name__)
st.set_page_config(layout='wide')
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

def api_delete(path):
    try:
        r = requests.delete(f"{API_BASE}{path}", timeout=5)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        logger.error("DELETE %s failed: %s", path, e)
        return None


# Fetch Maria's plots and the full crop list so we can build the form dropdowns
plots = api_get(f"/users/{MARIA_USER_ID}/plots") or []
plot_options = {p["plot_name"]: p["plot_id"] for p in plots}

# Reuse the surplus GET endpoint just to discover crop names — any query returning crop rows works.
# A dedicated /crops GET would be cleaner; keeping it simple here.
all_surplus = api_get("/surplus") or []
crop_options = {}
for row in all_surplus:
    crop_options[row["crop_name"]] = row["crop_id"]

# Page Content
st.title("Log a Planting or Harvest")
st.caption(f"Logged in as {st.session_state.get('first_name', 'Maria')} Santos")

if not plot_options:
    st.warning("You have no active plots assigned. Contact the garden admin.")
    st.stop()

# Section 1: Log new entry
st.subheader("New Entry")
st.caption("Select 'Planting' to record what you just planted, or 'Harvest' to record what you picked.")

with st.form("log_activity_form"):
    entry_type = st.radio(
        "Entry type",
        ["Planting (no yield yet)", "Harvest (with yield)"],
        horizontal=True,
    )
    plot_label = st.selectbox("Plot", list(plot_options.keys()))
    crop_label = st.selectbox(
        "Crop",
        list(crop_options.keys()) if crop_options else ["(no crops available)"],
    )

    if entry_type.startswith("Planting"):
        entry_date = st.date_input("Expected harvest date", value=date.today())
        qty = 0.0
    else:
        entry_date = st.date_input("Harvest date", value=date.today())
        qty = st.number_input("Quantity (lbs)", min_value=0.01, step=0.25, value=1.00)

    submitted = st.form_submit_button("Save Entry")

    if submitted:
        if not crop_options:
            st.error("No crops available to choose from. Seed the database first.")
        else:
            plot_id = plot_options[plot_label]
            crop_id = crop_options[crop_label]
            payload = {
                "crop_id": crop_id,
                "harvest_date": str(entry_date),
                "quantity_lbs": float(qty),
            }
            result = api_post(f"/plots/{plot_id}/harvests", payload)
            if result and result.get("harvest_id"):
                st.toast(f"Entry saved for {plot_label}!")
                st.rerun()
            else:
                st.toast("Failed to save entry.", icon="⚠️")

st.divider()

# Section 2: Past entries per plot (with delete)
st.subheader("Past Entries")
st.caption("Remove an entry if it was logged by mistake.")

for plot_name, pid in plot_options.items():
    with st.container(border=True):
        st.markdown(f"**{plot_name}**")
        rows = api_get(f"/plots/{pid}/harvests") or []
        if not rows:
            st.caption("No entries for this plot.")
            continue

        h1, h2, h3, h4, h5 = st.columns([2, 3, 2, 2, 1])
        h1.markdown("**Date**")
        h2.markdown("**Crop**")
        h3.markdown("**Type**")
        h4.markdown("**Qty (lbs)**")
        h5.markdown("**Del.**")

        for row in rows:
            c1, c2, c3, c4, c5 = st.columns([2, 3, 2, 2, 1])
            c1.write(str(row.get("harvest_date", "—")))
            c2.write(row.get("crop_name", "—"))
            qty = float(row.get("quantity_lbs") or 0)
            c3.write("Planting" if qty == 0 else "Harvest")
            c4.write(f"{qty:.2f}")
            if c5.button("🗑️", key=f"del_h_{row['harvest_id']}"):
                res = api_delete(f"/harvests/{row['harvest_id']}")
                if res:
                    st.toast("Entry removed.")
                    st.rerun()
                else:
                    st.toast("Failed to remove entry.", icon="⚠️")