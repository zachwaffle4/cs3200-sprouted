import logging
import requests
import streamlit as st
from modules.nav import SideBarLinks
logger = logging.getLogger(__name__)

st.set_page_config(layout='wide')

SideBarLinks()

# Mock Plot Data + Waitlist fot plots
# Stats (for Plot Overview)
all_plots = [
    {"id": 1, "plot_label": "A-1", "status": "Active", "owner": "Maria Lopez"},
    {"id": 2, "plot_label": "A-3", "status": "Vacant", "owner": "—"},
    {"id": 3, "plot_label": "A-5", "status": "Waitlisted", "owner": "—"},
    {"id": 4, "plot_label": "B-2", "status": "Active", "owner": "Carlos Ríos"},
    {"id": 5, "plot_label": "B-6", "status": "Vacant", "owner": "—"},
] # TODO: replace with → requests.get(f"{API_BASE}/plots").json()

# TODO: replace with → requests.get(f"{API_BASE}/waitlist").json()
waitlist_queue = [
    {"id": 1, "member": "James Okafor", "requested": "Plot B-12", "date": "Mar 10, 2026"},
    {"id": 2, "member": "Priya Desai", "requested": "Plot C-1", "date": "Mar 14, 2026"},
    {"id": 3, "member": "Tom Nguyen", "requested": "Plot A-3", "date": "Mar 22, 2026"},
]

if "editing_plot" not in st.session_state: # if the admin chooses to edit a plot
    st.session_state["editing_plot"] = None

st.title("Plot Manager")
st.divider()

# Filter: Admin can filter plots by status
status_filter = st.radio(
    "Filter by Status",
    ["All", "Active", "Vacant", "Waitlisted"],
    horizontal=True
)
filtered = [p for p in all_plots if status_filter in ("All", p["status"])]
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

# Edit form (shown when a plot is selected)
if st.session_state["editing_plot"] is not None:
    plot = st.session_state["editing_plot"]
    st.divider()
    st.subheader(f"Editing Plot {plot['plot_label']}")

    with st.form("edit_plot_form"):
        new_owner  = st.text_input(
            "Assigned Member", 
            value=plot["owner"] if plot["owner"] != "—" else ""
            )
        new_status = st.selectbox(
            "Status", 
            ["Active", "Vacant", "Waitlisted"],
            index=["Active", "Vacant", "Waitlisted"].index(plot["status"])
            )
        save = st.form_submit_button("Save Changes")
        cancel = st.form_submit_button("Cancel")

        if save:
            # TODO: PUT /plots/{id} with {"status": new_status, "owner": new_owner}
            st.success(f"Plot {plot['plot_label']} updated!")
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
    c1, c2, c3, c4 = st.columns([3, 3, 2, 1])
    c1.write(entry["member"])
    c2.write(entry["requested"])
    c3.write(entry["date"])
    if c4.button("Promote", key=f"promote_{entry['id']}"):
        # TODO: PUT /waitlist/{id}/promote
        st.success(f"Promoted {entry['member']}!")
        st.rerun()
