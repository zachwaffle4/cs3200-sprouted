import logging
import requests
import streamlit as st
from datetime import datetime
from modules.nav import SideBarLinks

logger = logging.getLogger(__name__)
st.set_page_config(layout="wide")
SideBarLinks()

API_BASE = "http://api:4000"
SITE_ID = 1


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


def api_delete(path):
    try:
        url = f"{API_BASE}{path}"
        r = requests.delete(url, timeout=5)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        logger.error("DELETE %s failed: %s", path, e)
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


def fmt_date(d):
    try:
        return datetime.strptime(str(d)[:10], "%Y-%m-%d").strftime("%b %d, %Y")
    except Exception:
        return str(d)


# Fetch workdays and tasks for each from the API
workdays_raw = api_get("/workdays") or []
existing_workdays = []
for w in workdays_raw:
    tasks_raw = api_get(f"/workdays/{w['workday_id']}/tasks") or []
    tasks = [
        {
            "id": t["task_id"],
            "name": t.get("task_description", ""),
            "urgency": t.get("urgency", "—"),
            "location": t.get("location_note", "—"),
            "status": t.get("status", "pending"),
        }
        for t in tasks_raw
    ]
    existing_workdays.append(
        {
            "id": w["workday_id"],
            "name": w["event_name"],
            "date": fmt_date(w.get("event_date", "")),
            "description": w.get("description", ""),
            "signed_up": w.get("signup_count", 0),
            "needed": max(int(w.get("volunteers_needed", 1)), 1),
            "tasks": tasks,
        }
    )

# Session states
if "new_tasks" not in st.session_state:
    st.session_state["new_tasks"] = []

if "expanded_workday" not in st.session_state:
    st.session_state["expanded_workday"] = None

# Page Contents
st.title("Workdays Manager")
st.divider()

st.subheader("Scheduled Workdays")
st.caption(
    "View, edit, or delete any upcoming community workdays that have been organized."
)

if not existing_workdays:
    st.info("No upcoming workdays scheduled.")

for wd in existing_workdays:
    with st.container(border=True):
        col_info, col_del = st.columns([9, 1])
        with col_info:
            st.write(f"**{wd['name']}** — {wd['date']}")
            st.caption(wd["description"])
            ratio = wd["signed_up"] / wd["needed"]
            st.progress(
                ratio, text=f"{wd['signed_up']}/{wd['needed']} volunteers signed up"
            )
        with col_del:
            if st.button("🗑️", key=f"del_wd_{wd['id']}"):
                res = api_delete(f"/workdays/{wd['id']}")
                if res:
                    st.toast(f"Deleted '{wd['name']}'.")
                    st.rerun()
                else:
                    st.toast("Failed to delete workday.", icon="⚠️")

        # Toggle task list
        if st.session_state["expanded_workday"] == wd["id"]:
            label = "Hide tasks ▲"
        else:
            label = "Show tasks ▼"

        if st.button(label, key=f"toggle_{wd['id']}"):
            st.session_state["expanded_workday"] = (
                None if st.session_state["expanded_workday"] == wd["id"] else wd["id"]
            )
            st.rerun()

        if st.session_state["expanded_workday"] == wd["id"]:
            if wd["tasks"]:
                h1, h2, h3, h4 = st.columns([4, 2, 2, 1])
                h1.write("**Task**")
                h2.write("**Urgency**")
                h3.write("**Location**")
                h4.write("**Del.**")
                for task in wd["tasks"]:
                    c1, c2, c3, c4 = st.columns([4, 2, 2, 1])
                    c1.write(task["name"])
                    c2.write(task["urgency"])
                    c3.write(task["location"])
                    if c4.button("🗑️", key=f"del_task_{task['id']}"):
                        # Mark task completed via PUT — GET /tasks filters out completed tasks
                        result = api_put(
                            f"/workdays/{wd['id']}/tasks",
                            {"task_id": task["id"], "status": "completed"},
                        )
                        if result:
                            st.toast(f"Task '{task['name']}' removed.")
                        else:
                            st.toast("Failed to remove task.", icon="⚠️")
                        st.rerun()
            else:
                st.caption("No tasks for this workday.")

st.divider()

# Scheduling a New Workday
st.subheader("Schedule a New Community Workday")
st.caption("Create a new workday event with tasks for volunteers.")

with st.form("new_workday_form"):
    event_name = st.text_input("Event Name")
    date_col, start_col, end_col = st.columns(3)
    event_date = date_col.date_input("Date")
    event_start_time = start_col.time_input("Start Time")
    event_end_time = end_col.time_input("End Time")
    event_desc = st.text_area("Description")
    volunteers_needed = st.number_input(
        "Volunteers Needed", min_value=1, max_value=100, value=12
    )

    submitted = st.form_submit_button("Create Workday")

    if submitted:
        if not event_name.strip():
            st.error("Please enter an event name.")
        else:
            payload = {
                "site_id": SITE_ID,
                "event_name": event_name,
                "event_date": str(event_date),
                "start_time": str(event_start_time),
                "end_time": str(event_end_time),
                "description": event_desc,
                "volunteers_needed": volunteers_needed,
            }
            result = api_post("/workdays", payload)
            if result and result.get("workday_id"):
                new_wd_id = result["workday_id"]
                tasks_created = 0
                for task in st.session_state["new_tasks"]:
                    if task.get("name", "").strip():
                        task_payload = {
                            "task_description": task["name"],
                            "urgency": task.get("urgency", "low"),
                            "location_note": task.get("location", ""),
                        }
                        if api_post(f"/workdays/{new_wd_id}/tasks", task_payload):
                            tasks_created += 1
                st.toast(
                    f"Workday '{event_name}' created with {tasks_created} task(s)!"
                )
                st.session_state["new_tasks"] = []
                st.rerun()
            else:
                st.error(
                    "Failed to create workday. Ensure all required fields are filled."
                )

# Dynamic task builder (must be outside st.form to allow st.rerun)
st.write("**Tasks** *(volunteers will sign up for these)*")

if st.session_state["new_tasks"]:
    h1, h2, h3, h4 = st.columns([4, 2, 2, 1])
    h1.write("**Task**")
    h2.write("**Urgency**")
    h3.write("**Location**")
    h4.write("**Del.**")

    for i, task in enumerate(st.session_state["new_tasks"]):
        c1, c2, c3, c4 = st.columns([4, 2, 2, 1])
        st.session_state["new_tasks"][i]["name"] = c1.text_input(
            "Task", value=task["name"], key=f"tname_{i}", label_visibility="collapsed"
        )
        st.session_state["new_tasks"][i]["urgency"] = c2.selectbox(
            "Urgency",
            ["low", "medium", "high"],
            index=["low", "medium", "high"].index(task.get("urgency", "low")),
            key=f"turgency_{i}",
            label_visibility="collapsed",
        )
        st.session_state["new_tasks"][i]["location"] = c3.text_input(
            "Location",
            value=task.get("location", ""),
            key=f"tloc_{i}",
            label_visibility="collapsed",
            placeholder="e.g. Bed A",
        )
        if c4.button("🗑️", key=f"rm_task_{i}"):
            st.session_state["new_tasks"].pop(i)
            st.rerun()
else:
    st.caption("No tasks yet.")

if st.button("+ Add Task"):
    st.session_state["new_tasks"].append({"name": "", "urgency": "low", "location": ""})
    st.rerun()
