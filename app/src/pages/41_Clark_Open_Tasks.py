import logging
import requests
import streamlit as st
from modules.nav import SideBarLinks
logger = logging.getLogger(__name__)

st.set_page_config(layout='wide')

SideBarLinks()

API_BASE = "http://api:4000"

def get_workdays():
    try:
        r = requests.get(f"{API_BASE}/workdays")
        if r.status_code == 200:
            workdays = r.json()
            # Transform API response to match frontend expectations if necessary
            for wd in workdays:
                wd['id'] = wd.get('workday_id')
                wd['title'] = wd.get('event_name')
                wd['date'] = wd.get('event_date')
                wd['time'] = "" # Backend doesn't return time in this format yet
                wd['location'] = f"Site {wd.get('site_id')}" # Site name needs another join or lookup
                wd['signed_up'] = wd.get('signup_count', 0)
                wd['capacity'] = wd.get('volunteers_needed', 0)
                wd['needs_help'] = wd.get('spots_remaining', 0) > 0
                
                # Fetch tasks for each workday
                tasks_r = requests.get(f"{API_BASE}/workdays/{wd['id']}/tasks")
                if tasks_r.status_code == 200:
                    wd['tasks'] = []
                    for t in tasks_r.json():
                        wd['tasks'].append({
                            "id": t['task_id'],
                            "name": t['task_description'],
                            "hours": 2.0, # Defaulting hours since it's not in DB
                            "spots_left": 1 if t['status'] == 'pending' else 0,
                            "full": t['status'] != 'pending'
                        })
                else:
                    wd['tasks'] = []
            return workdays
    except Exception as e:
        logger.error(f"Error fetching workdays: {e}")
    return []

def signup_for_task(workday_id, task_id, volunteer_id):
    try:
        # Note: The backend create_workday_signup only takes user_id and workday_id
        # and doesn't support task_id currently in the signup table schema
        r = requests.post(
            f"{API_BASE}/workdays/{workday_id}/signups",
            json={"user_id": volunteer_id},
        )
        return r.status_code in (200, 201)
    except Exception as e:
        logger.error(f"Error signing up: {e}")
        return False

def cancel_signup(signup_id):
    try:
        r = requests.delete(f"{API_BASE}/signups/{signup_id}")
        return r.status_code in (200, 204)
    except Exception:
        return False

st.set_page_config(page_title="Open Tasks – Sprouted", layout="wide")

st.markdown("""
<style>
    .needs-help-badge {
        background: #fcebeb; color: #a32d2d;
        border-radius: 4px; padding: 2px 9px;
        font-size: 0.75rem; font-weight: 500; margin-left: 8px;
    }
    .full-label { color: #999; font-size: 0.8rem; }
    .hours-bar {
        background: #e1f5ee;
        border: 1px solid #9fe1cb;
        border-radius: 6px;
        padding: 0.6rem 1rem;
        margin-top: 1rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
</style>
""", unsafe_allow_html=True)

user = st.session_state.get("user", {"id": 3, "name": "Clark Kent"})
volunteer_id = user.get("id", 3)

st.title("Open Tasks")
st.caption(f"Logged in as {user.get('name', 'Clark Kent')}")

col_f1, col_f2 = st.columns([2, 2])
with col_f1:
    date_filter = st.selectbox("Date", ["All Dates", "This Weekend", "This Week", "This Month"], label_visibility="collapsed")
with col_f2:
    urgency_filter = st.selectbox("Urgency", ["All", "Needs Help Only"], label_visibility="collapsed")

st.markdown("---")

workdays = get_workdays()

if urgency_filter == "Needs Help Only":
    workdays = [w for w in workdays if w.get("needs_help")]

if not workdays:
    st.info("No upcoming workdays match your filters.")

signed_up_tasks = st.session_state.get("signed_up_tasks", set())

for wd in workdays:
    pct = wd["signed_up"] / wd["capacity"] if wd["capacity"] else 0
    needs_help_html = '<span class="needs-help-badge">Needs Help</span>' if wd["needs_help"] else ""

    st.markdown(f"""
    <div style='margin-bottom:0.25rem'>
        <strong style='font-size:1.05rem'>{wd['title']}</strong>{needs_help_html}
        &nbsp;&nbsp;<span style='color:#666;font-size:0.85rem'>{wd['date']} {wd['time']} &nbsp;·&nbsp; {wd['location']}</span>
    </div>
    """, unsafe_allow_html=True)

    st.progress(pct, text=f"{wd['signed_up']}/{wd['capacity']} Signed Up")

    if st.button(f"View Details →", key=f"detail_{wd['id']}"):
        st.session_state["selected_workday_id"] = wd["id"]
        st.switch_page("pages/43_Clark_Event_Detail.py")

    h1, h2, h3, h4 = st.columns([4, 1, 1, 1])
    h1.markdown("<small><b>Task</b></small>", unsafe_allow_html=True)
    h2.markdown("<small><b>Time</b></small>", unsafe_allow_html=True)
    h3.markdown("<small><b>Spots</b></small>", unsafe_allow_html=True)
    h4.markdown("<small><b>Action</b></small>", unsafe_allow_html=True)

    for task in wd.get("tasks", []):
        task_key = f"{wd['id']}_{task['id']}"
        c1, c2, c3, c4 = st.columns([4, 1, 1, 1])
        c1.write(task["name"])
        c2.write(f"{task['hours']:.1f} hrs")

        if task["full"]:
            c3.markdown('<span class="full-label">Full</span>', unsafe_allow_html=True)
            c4.button("Full", key=f"full_{task_key}", disabled=True)
        elif task_key in signed_up_tasks:
            c3.write(f"{task['spots_left']} left")
            c4.markdown("✅ Signed Up")
        else:
            c3.write(f"{task['spots_left']} left")
            if c4.button("Sign Up", key=f"signup_{task_key}"):
                ok = signup_for_task(wd["id"], task["id"], volunteer_id)
                if ok:
                    signed_up_tasks.add(task_key)
                    st.session_state["signed_up_tasks"] = signed_up_tasks
                    upcoming = st.session_state.get("upcoming_signups", [])
                    upcoming.append({
                        "signup_id": task["id"] * 100,
                        "date": f"{wd['date']} {wd['time']}",
                        "task": task["name"],
                        "location": wd["location"],
                        "hours": task["hours"],
                    })
                    st.session_state["upcoming_signups"] = upcoming
                    st.success(f"Signed up for '{task['name']}'!")
                    st.rerun()
                else:
                    st.error("Sign-up failed. Please try again.")

    st.markdown("")

    my_tasks_here = [
        s for s in st.session_state.get("upcoming_signups", [])
        if s.get("location") == wd["location"] and wd["date"] in s.get("date", "")
    ]
    if my_tasks_here:
        st.markdown("**My Upcoming Task**")
        for su in my_tasks_here:
            ca, cb, cc = st.columns([3, 3, 1])
            ca.write(su["task"])
            cb.write(su["date"])
            if cc.button("Cancel", key=f"cancel_open_{su['signup_id']}"):
                ok = cancel_signup(su["signup_id"])
                if ok:
                    st.session_state["upcoming_signups"] = [
                        s for s in st.session_state["upcoming_signups"]
                        if s["signup_id"] != su["signup_id"]
                    ]
                    signed_up_tasks.discard(f"{wd['id']}_{su['signup_id'] // 100}")
                    st.session_state["signed_up_tasks"] = signed_up_tasks
                    st.success("Sign-up cancelled.")
                    st.rerun()
                else:
                    st.error("Could not cancel. Please try again.")

    st.markdown("---")

total_hrs = 30.0
goal_hrs = 60.0
remaining = goal_hrs - total_hrs
st.markdown(f"""
<div class="hours-bar">
    <div>
        <strong>My hours this semester</strong> &nbsp;
        <span style='color:#085041'>{total_hrs:.0f} hrs</span>
    </div>
    <div style='color:#5a7a5a; font-size:0.85rem'>{remaining:.0f} hours remaining to {goal_hrs:.0f}-hr goal</div>
</div>
""", unsafe_allow_html=True)
