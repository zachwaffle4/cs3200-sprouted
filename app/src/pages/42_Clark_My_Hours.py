import logging
import requests
import streamlit as st
from datetime import datetime, date
from modules.nav import SideBarLinks
logger = logging.getLogger(__name__)

st.set_page_config(layout='wide')

SideBarLinks()

API_BASE = "http://api:4000"

def get_volunteer_log(volunteer_id):
    try:
        r = requests.get(f"{API_BASE}/volunteers/{volunteer_id}/log")
        if r.status_code == 200:
            entries = r.json()
            total_hours = sum(e.get('hours_logged', 0) for e in entries)
            # Transform to match frontend expectations
            formatted_entries = []
            for e in entries:
                formatted_entries.append({
                    "id": e.get('log_id'),
                    "date": e.get('work_date'),
                    "event_task": e.get('task_description') or e.get('event_name') or "General Work",
                    "hours": float(e.get('hours_logged', 0)),
                    "status": "Verified" # Defaulting since status isn't in Volunteer_Log
                })
            return {
                "total_hours": float(total_hours),
                "goal_hours": 60.0,
                "entries": formatted_entries
            }
    except Exception as e:
        logger.error(f"Error fetching volunteer log: {e}")
    return {"total_hours": 0.0, "goal_hours": 60.0, "entries": []}

def log_hours(volunteer_id, payload):
    try:
        # Map frontend payload to backend expected fields
        backend_payload = {
            "work_date": payload.get("date"),
            "hours_logged": payload.get("hours"),
            "notes": payload.get("notes"),
            "task_id": payload.get("task_id")
        }
        r = requests.post(f"{API_BASE}/volunteers/{volunteer_id}/log", json=backend_payload)
        return r.status_code in (200, 201), r.json() if r.status_code in (200, 201) else {}
    except Exception as e:
        logger.error(f"Error logging hours: {e}")
        return False, {}

def cancel_signup(signup_id):
    try:
        r = requests.delete(f"{API_BASE}/signups/{signup_id}")
        return r.status_code in (200, 204)
    except Exception:
        return False

st.set_page_config(page_title="My Volunteer Hours – Sprouted", layout="wide")

st.markdown("""
<style>
    .metric-box {
        background: #f0f7f0;
        border: 1px solid #cce0cc;
        border-radius: 8px;
        padding: 1rem 1.25rem;
        text-align: center;
    }
    .metric-label { font-size: 0.75rem; color: #5a7a5a; margin-bottom: 0.25rem; }
    .metric-value { font-size: 1.6rem; font-weight: 600; color: #2d5a2d; }
    .verified-badge {
        background: #e1f5ee; color: #085041;
        border-radius: 4px; padding: 2px 8px; font-size: 0.75rem; font-weight: 500;
    }
    .pending-badge {
        background: #faeeda; color: #633806;
        border-radius: 4px; padding: 2px 8px; font-size: 0.75rem; font-weight: 500;
    }
</style>
""", unsafe_allow_html=True)

user = st.session_state.get("user", {"id": 3, "name": "Clark Kent"})
volunteer_id = user.get("id", 3)

st.title("My Volunteer Hours")
st.caption(f"Logged in as {user.get('name', 'Clark Kent')}")

data = get_volunteer_log(volunteer_id)
total = data.get("total_hours", 0)
goal = data.get("goal_hours", 60)
remaining = max(goal - total, 0)
entries = data.get("entries", [])

c1, c2, c3 = st.columns(3)
with c1:
    st.markdown(f"""
    <div class="metric-box">
        <div class="metric-label">Total Hours</div>
        <div class="metric-value">{total:.1f} hrs</div>
    </div>""", unsafe_allow_html=True)
with c2:
    st.markdown(f"""
    <div class="metric-box">
        <div class="metric-label">Goal Hours</div>
        <div class="metric-value">{goal:.0f} hrs</div>
    </div>""", unsafe_allow_html=True)
with c3:
    st.markdown(f"""
    <div class="metric-box">
        <div class="metric-label">Remaining</div>
        <div class="metric-value">{remaining:.1f} hrs</div>
    </div>""", unsafe_allow_html=True)

st.markdown("")
progress_pct = min(total / goal, 1.0) if goal > 0 else 0
st.progress(progress_pct, text=f"{total:.0f} / {goal:.0f} hours toward your {goal:.0f}-hr goal")

st.divider()

with st.expander("➕ Add Hours", expanded=False):
    with st.form("log_hours_form"):
        col_a, col_b = st.columns(2)
        with col_a:
            log_date = st.date_input("Date of activity", value=date.today())
            task_name = st.text_input("Event / Task name")
        with col_b:
            hours_logged = st.number_input("Hours worked", min_value=0.5, max_value=12.0, step=0.5, value=2.0)
            notes = st.text_area("Notes (optional)", height=80)
        submitted = st.form_submit_button("Log Hours")
        if submitted:
            if not task_name:
                st.warning("Please enter a task or event name.")
            else:
                payload = {
                    "date": str(log_date),
                    "event_task": task_name,
                    "hours": hours_logged,
                    "notes": notes,
                }
                ok, resp = log_hours(volunteer_id, payload)
                if ok:
                    st.success(f"Logged {hours_logged:.1f} hrs for '{task_name}'. Status: Pending verification.")
                    st.rerun()
                else:
                    st.error("Could not log hours right now. Please try again.")

st.divider()

col_head, col_filter = st.columns([3, 2])
with col_head:
    st.subheader("Activity Log")
with col_filter:
    time_filter = st.radio("Show", ["All Time", "This Semester"], horizontal=True, label_visibility="collapsed")

def in_semester(entry_date_str):
    try:
        d = datetime.strptime(entry_date_str, "%Y-%m-%d")
        return d.month >= 9
    except Exception:
        return True

filtered = entries if time_filter == "All Time" else [e for e in entries if in_semester(e.get("date", ""))]

if not filtered:
    st.info("No activity logged yet for this period.")
else:
    h1, h2, h3, h4 = st.columns([2, 4, 1, 1])
    h1.markdown("**Date**")
    h2.markdown("**Event / Task**")
    h3.markdown("**Hours**")
    h4.markdown("**Status**")
    st.divider()

    for entry in filtered:
        c1, c2, c3, c4 = st.columns([2, 4, 1, 1])
        c1.write(entry.get("date", "—"))
        c2.write(entry.get("event_task", "—"))
        c3.write(f"{entry.get('hours', 0):.1f}")
        status = entry.get("status", "Pending")
        badge = "verified-badge" if status == "Verified" else "pending-badge"
        c4.markdown(f'<span class="{badge}">{status}</span>', unsafe_allow_html=True)

    st.caption(f"Showing {len(filtered)} of {len(entries)} entries")

st.divider()

st.subheader("My Upcoming Sign-ups")
upcoming = st.session_state.get("upcoming_signups", [
    {"signup_id": 101, "date": "Nov 10, 2026 9:00 AM", "task": "Drip Line Inspection", "location": "Elm Street Garden", "hours": 2.0},
])

if not upcoming:
    st.info("No upcoming sign-ups.")
else:
    for su in upcoming:
        col_a, col_b, col_c = st.columns([3, 2, 1])
        col_a.write(f"**{su['task']}**  \n{su['location']}")
        col_b.write(su["date"])
        if col_c.button("Cancel", key=f"cancel_{su['signup_id']}"):
            ok = cancel_signup(su["signup_id"])
            if ok:
                st.success(f"Cancelled sign-up for '{su['task']}'.")
                st.session_state["upcoming_signups"] = [
                    s for s in upcoming if s["signup_id"] != su["signup_id"]
                ]
                st.rerun()
            else:
                st.error("Could not cancel. Please try again.")