import streamlit as st
import requests
from datetime import datetime, date
from modules.nav import SideBarLinks

API_BASE = "http://web-api:4000"

def parse_date(date_str):
    if not date_str:
        return ""
    try:
        d = datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S GMT")
        return d.strftime("%Y-%m-%d")
    except Exception:
        return str(date_str)

def get_volunteer_log(volunteer_id):
    try:
        r = requests.get(f"{API_BASE}/volunteers/{volunteer_id}/log")
        if r.status_code == 200:
            entries = r.json()
            total = sum(float(e.get("hours_logged", 0)) for e in entries)
            result = []
            for e in entries:
                task_name = e.get("notes") or e.get("task_description") or e.get("event_name") or "Volunteer Activity"
                result.append({
                    "id": e.get("log_id"),
                    "date": parse_date(e.get("work_date", "")),
                    "event_task": task_name,
                    "hours": float(e.get("hours_logged", 0)),
                    "status": "Verified",
                })
            return {
                "total_hours": total,
                "goal_hours": 60.0,
                "entries": result,
            }
    except Exception:
        pass
    return {
        "total_hours": 30.0,
        "goal_hours": 60.0,
        "entries": [
            {"id": 1, "date": "2024-09-30", "event_task": "Fall Cleanup - Bed Weeding", "hours": 3.0, "status": "Verified"},
            {"id": 2, "date": "2024-09-21", "event_task": "Seedling Potting Workshop", "hours": 3.0, "status": "Verified"},
            {"id": 3, "date": "2024-09-11", "event_task": "Compost Turning", "hours": 3.0, "status": "Verified"},
            {"id": 4, "date": "2024-09-10", "event_task": "Tool Cleaning & Storage", "hours": 3.0, "status": "Verified"},
            {"id": 5, "date": "2024-09-01", "event_task": "Drip Line Inspection", "hours": 3.0, "status": "Pending"},
        ]
    }

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

st.set_page_config(page_title="My Volunteer Hours - Sprouted", layout="wide")
SideBarLinks()

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
    st.markdown(f'<div style="background:#f0f7f0;border:1px solid #cce0cc;border-radius:8px;padding:1rem;text-align:center"><div style="font-size:0.75rem;color:#5a7a5a">Total Hours</div><div style="font-size:1.6rem;font-weight:600;color:#2d5a2d">{total:.1f} hrs</div></div>', unsafe_allow_html=True)
with c2:
    st.markdown(f'<div style="background:#f0f7f0;border:1px solid #cce0cc;border-radius:8px;padding:1rem;text-align:center"><div style="font-size:0.75rem;color:#5a7a5a">Goal Hours</div><div style="font-size:1.6rem;font-weight:600;color:#2d5a2d">{goal:.0f} hrs</div></div>', unsafe_allow_html=True)
with c3:
    st.markdown(f'<div style="background:#f0f7f0;border:1px solid #cce0cc;border-radius:8px;padding:1rem;text-align:center"><div style="font-size:0.75rem;color:#5a7a5a">Remaining</div><div style="font-size:1.6rem;font-weight:600;color:#2d5a2d">{remaining:.1f} hrs</div></div>', unsafe_allow_html=True)

st.markdown("")
progress_pct = min(total / goal, 1.0) if goal > 0 else 0
st.progress(progress_pct, text=f"{total:.0f} / {goal:.0f} hours toward your {goal:.0f}-hr goal")

st.divider()

with st.expander("+ Add Hours", expanded=False):
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
                    "work_date": str(log_date),
                    "hours_logged": hours_logged,
                    "notes": task_name + (" - " + notes if notes else ""),
                }
                ok, resp = log_hours(volunteer_id, payload)
                if ok:
                    st.success(f"Logged {hours_logged:.1f} hrs for '{task_name}'!")
                    st.rerun()
                else:
                    st.error("Could not log hours right now. Please try again.")

st.divider()

col_head, col_filter = st.columns([3, 2])
with col_head:
    st.subheader("Activity Log")
with col_filter:
    time_filter = st.radio("Show", ["All Time", "This Semester"], horizontal=True, label_visibility="collapsed")

filtered = entries if time_filter == "All Time" else [e for e in entries if "2026" in str(e.get("date", ""))]

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
        c1.write(entry.get("date", "-"))
        c2.write(entry.get("event_task", "-"))
        c3.write(f"{entry.get('hours', 0):.1f}")
        status = entry.get("status", "Pending")
        badge_color = "#e1f5ee" if status == "Verified" else "#faeeda"
        text_color = "#085041" if status == "Verified" else "#633806"
        c4.markdown(f'<span style="background:{badge_color};color:{text_color};border-radius:4px;padding:2px 8px;font-size:0.75rem">{status}</span>', unsafe_allow_html=True)
    st.caption(f"Showing {len(filtered)} of {len(entries)} entries")

st.divider()

st.subheader("My Upcoming Sign-ups")
upcoming = st.session_state.get("upcoming_signups", [])
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
                st.session_state["upcoming_signups"] = [s for s in upcoming if s["signup_id"] != su["signup_id"]]
                st.rerun()
            else:
                st.error("Could not cancel. Please try again.")
