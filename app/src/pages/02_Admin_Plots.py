import logging
import requests
import streamlit as st
from modules.nav import SideBarLinks

logger = logging.getLogger(__name__)
st.set_page_config(layout="wide")
SideBarLinks()

API_BASE = "http://api:4000"


# API helper functions
def api_get(path, params=None):
    try:
        url = f"{API_BASE}{path}"
        r = requests.get(url, params=params, timeout=5)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        logger.error("GET %s failed: %s", path, e)
        return None


def api_post(path, payload):
    try:
        url = f"{API_BASE}{path}"
        r = requests.post(url, json=payload, timeout=5)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        logger.error("POST %s failed: %s", path, e)
        return None


def api_put(path, payload):
    try:
        url = f"{API_BASE}{path}"
        r = requests.put(url, json=payload, timeout=5)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        logger.error("PUT %s failed: %s", path, e)
        return None


def api_delete(path):
    try:
        url = f"{API_BASE}{path}"
        r = requests.delete(url, timeout=5)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        logger.error("DELETE %s failed: %s", path, e)
        return None


# Plots from /plots
# occupancy_status is 'assigned' or 'vacant' — map to friendlier display labels
STATUS_DISPLAY = {"assigned": "Active", "vacant": "Vacant"}

plots_raw = api_get("/plots") or []
seen_plot_ids = set()
all_plots = []
for p in plots_raw:
    if p["plot_id"] in seen_plot_ids:
        continue
    seen_plot_ids.add(p["plot_id"])
    all_plots.append(
        {
            "id": p["plot_id"],
            "plot_label": p.get("plot_name", f"Plot {p['plot_id']}"),
            "status": STATUS_DISPLAY.get(
                p.get("occupancy_status", ""), p.get("occupancy_status", "Unknown")
            ),
            "owner": (
                f"User {p['assigned_user_id']}" if p.get("assigned_user_id") else "—"
            ),
            "owner_id": p.get("assigned_user_id"),
            "assignment_id": p.get("active_assignment_id"),
        }
    )

# Waitlist from GET /waitlist
waitlist_raw = api_get("/waitlist") or []
waitlist_queue = [
    {
        "id": a["application_id"],
        "member": a["name"],
        "requested": a.get("plot_name") or "Any Available",
        "date": str(a.get("requested_date", ""))[:16].strip(", "),
    }
    for a in waitlist_raw
]

if "editing_plot" not in st.session_state:
    st.session_state["editing_plot"] = None

st.title("Plot Manager")
st.divider()

# Edit form (shown when a plot is selected)
if st.session_state["editing_plot"] is not None:
    plot = st.session_state["editing_plot"]
    st.subheader(f"Editing Plot {plot['plot_label']}")
    st.caption("Enter a User ID to assign, or set to 0 to vacate the plot.")

    with st.form("edit_plot_form"):
        new_owner_id = st.number_input(
            "Assign User ID (0 = vacate)",
            value=int(plot["owner_id"]) if plot.get("owner_id") else 0,
            min_value=0,
            step=1,
        )
        save = st.form_submit_button("Save Changes")
        cancel = st.form_submit_button("Cancel")

        if save:
            existing_assignment = plot.get("assignment_id")
            if new_owner_id > 0:
                # If the plot is already assigned, vacate it first to avoid 409
                if existing_assignment:
                    api_delete(f"/assignments/{existing_assignment}")
                result = api_post(
                    f"/plots/{plot['id']}/assignments", {"user_id": int(new_owner_id)}
                )
                if result:
                    st.toast(
                        f"Plot {plot['plot_label']} assigned to User {new_owner_id}!"
                    )
                else:
                    st.toast(
                        "Failed to assign. Check that the User ID is valid.", icon="⚠️"
                    )
            elif existing_assignment:
                result = api_delete(f"/assignments/{existing_assignment}")
                if result:
                    st.toast(f"Plot {plot['plot_label']} vacated.")
                else:
                    st.toast("Failed to vacate plot.", icon="⚠️")
            st.session_state["editing_plot"] = None
            st.rerun()

        if cancel:
            st.session_state["editing_plot"] = None
            st.rerun()

    st.divider()

# Waitlist queue
st.subheader("Waitlist Queue")
h1, h2, h3, h4 = st.columns([3, 3, 2, 1])
h1.write("**Member**")
h2.write("**Requested**")
h3.write("**Date Applied**")
h4.write("**Promote**")

for entry in waitlist_queue:
    with st.container(border=True):
        c1, c2, c3, c4 = st.columns([3, 3, 2, 1])
        c1.write(entry["member"])
        c2.write(entry["requested"])
        c3.write(entry["date"])
        if c4.button("Promote", key=f"promote_{entry['id']}"):
            res = api_put(f"/waitlist/{entry['id']}/promote", {})
            if res:
                st.toast(f"Promoted {entry['member']} to plot owner!")
            else:
                st.toast(
                    "Promotion failed. No vacant plot may be available.", icon="⚠️"
                )
            st.rerun()

st.divider()

# Filter bar
status_filter = st.radio(
    "Filter by Status", ["All", "Active", "Vacant"], horizontal=True
)
filtered = [
    p for p in all_plots if status_filter == "All" or p["status"] == status_filter
]
st.caption(f"Showing {len(filtered)} of {len(all_plots)} plots")

# Plots table
st.subheader(f"{status_filter} Plots")
h1, h2, h3, h4 = st.columns([1, 2, 3, 1])
h1.write("**Plot**")
h2.write("**Status**")
h3.write("**Owner**")
h4.write("**Edit**")

for plot in filtered:
    with st.container(border=True):
        c1, c2, c3, c4 = st.columns([1, 2, 3, 1])
        c1.write(plot["plot_label"])
        c2.write(plot["status"])
        c3.write(plot["owner"])
        if c4.button("Edit", key=f"edit_{plot['id']}"):
            st.session_state["editing_plot"] = plot
            st.rerun()
