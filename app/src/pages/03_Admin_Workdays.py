import logging
import requests
import streamlit as st
from modules.nav import SideBarLinks
logger = logging.getLogger(__name__)

st.set_page_config(layout='wide')

SideBarLinks()

API_BASE = "http://localhost:4000"

# TODO: GET /workdays?upcoming=true
existing_workdays = [
    {
        "id": 1,
        "name": "Spring Cleanup",
        "date": "Apr 5, 2026",
        "start_time": "9:00 AM",
        "end_time": "1:00 PM",
        "description": "Clearing debris, turning compost, repairing raised beds.",
        "signed_up": 8,
        "needed": 12,
        "tasks": [
            {
                "id": 101,
                "name": "Clear paths",
                "est_time": "2 hrs",
                "people_needed": 4
            },
            {
                "id": 102,
                "name": "Turn compost bins",
                "est_time": "1.5 hrs",
                "people_needed": 3
            },
        ],
    },
    {
        "id": 2,
        "name": "Irrigation Check",
        "date": "Apr 12, 2026",
        "start_time": "10:00 AM",
        "end_time": "11:00 AM",
        "description": "Inspect and repair drip lines before summer season.",
        "signed_up": 3,
        "needed": 6,
        "tasks": [
            {
                "id": 201,
                "name": "Inspect Section A drip lines",
                "est_time": "1 hr",
                "people_needed": 2
            },
        ],
    },
]

# Session states
if "new_tasks" not in st.session_state:
    st.session_state["new_tasks"] = []

if "expanded_workday" not in st.session_state:
    st.session_state["expanded_workday"] = None

#
st.title("Workdays Manager")
st.divider()

# Scheduled workdays
st.subheader("Scheduled Workdays")
st.caption("View, edit, or delete any upcoming community workdays that have been organized.")

for wd in existing_workdays:
    with st.container(border=True):
        col_info, col_del = st.columns([9, 1])
        with col_info:
            st.write(f"**{wd['name']}** — {wd['date']} at {wd['start_time']} to {wd['end_time']}")
            st.caption(wd["description"])
            st.progress(wd["signed_up"] / wd["needed"],
                        text=f"{wd['signed_up']}/{wd['needed']} volunteers signed up")
        with col_del: # Deleting a workday
            if st.button("🗑️", key=f"del_wd_{wd['id']}"):
                # TODO: DELETE /workdays/{id}
                st.success(f"Deleted '{wd['name']}'.")
                st.rerun()

        # Toggle task list
        if st.session_state["expanded_workday"] == wd["id"]:
            label = "Hide tasks ▲"
        else:
            label = "Show tasks ▼"

        if st.button(label, key=f"toggle_{wd['id']}"):
            if st.session_state["expanded_workday"] == wd["id"]:
                st.session_state["expanded_workday"] = None
            else:
                st.session_state["expanded_workday"] = wd["id"]
            st.rerun()

        if st.session_state["expanded_workday"] == wd["id"]:
            h1, h2, h3, h4 = st.columns([4, 2, 2, 1])
            h1.write("**Task**")
            h2.write("**Est. Time**")
            h3.write("**People**")
            h4.write("**Del.**")
            for task in wd["tasks"]: # Show tasks for a workday if toggled to expand
                c1, c2, c3, c4 = st.columns([4, 2, 2, 1])
                c1.write(task["name"])
                c2.write(task["est_time"])
                c3.write(f"{task['people_needed']}")
                if c4.button("🗑️", key=f"del_task_{task['id']}"): # Deleting a task in toggled task list
                    # TODO: DELETE /workdays/{wd_id}/tasks/{task_id}
                    st.success(f"Removed task '{task['name']}'.")
                    st.rerun()

st.divider()

# Scheduling a New Workday
st.subheader("Schedule a New Community Workday")
st.caption("Create a new workday event with tasks for volunteers.")

with st.form("new_workday_form"):
    # Fields for user to input workday details
    event_name = st.text_input("Event Name")
    date_col, time_col = st.columns(2)
    event_date = date_col.date_input("Date")
    event_start_time = time_col.time_input("Start Time")
    event_end_time = time_col.time_input("End Time")
    event_desc = st.text_area("Description")
    volunteers_needed = st.number_input("Volunteers Needed", min_value=1, max_value=100, value=12)

    submitted = st.form_submit_button("Create Workday")

    if submitted:
        if not event_name.strip():
            st.error("Please enter an event name.")
        else:
            payload = {
                "name": event_name,
                "date": str(event_date),
                "start_time": str(event_start_time),
                "end_time": str(event_end_time),
                "description": event_desc,
                "volunteers_needed": volunteers_needed,
                "tasks": st.session_state["new_tasks"],
            }
            # TODO: POST /workdays with payload
            st.success(f"Workday '{event_name}' created with {len(st.session_state['new_tasks'])} task(s)!")
            st.session_state["new_tasks"] = []
            st.rerun()

# Dynamic tasks (must be outside st.form)
st.write("**Tasks** *(volunteers will sign up for these)*")

if st.session_state["new_tasks"]:
    h1, h2, h3, h4 = st.columns([4, 2, 2, 1])
    h1.write("**Task**")
    h2.write("**Est. Time**")
    h3.write("**People**")
    h4.write("**Del.**")

    for i, task in enumerate(st.session_state["new_tasks"]):
        c1, c2, c3, c4 = st.columns([4, 2, 2, 1])
        # Name of task input field
        st.session_state["new_tasks"][i]["name"] = c1.text_input(
            "Task",
            value=task["name"],
            key=f"tname_{i}",
            label_visibility="collapsed"
            )
        # Estimate time input field
        st.session_state["new_tasks"][i]["est_time"] = c2.text_input(
            "Time",
            value=task["est_time"],
            key=f"ttime_{i}",
            label_visibility="collapsed",
            placeholder="e.g. 2 hrs"
            )
        # People needed input field
        st.session_state["new_tasks"][i]["people_needed"] = c3.number_input(
            "People",
            value=task["people_needed"],
            key=f"tpeople_{i}",
            label_visibility="collapsed",
            min_value=1
            )
        if c4.button("🗑️", key=f"rm_task_{i}"): # To remove a task before submitting
            st.session_state["new_tasks"].pop(i)
            st.rerun()
else:
    st.caption("No tasks yet.")

if st.button("+ Add Task"):
    st.session_state["new_tasks"].append({"name": "", "est_time": "", "people_needed": 2})
    st.rerun()
