import logging
import requests
import streamlit as st
from modules.nav import SideBarLinks
logger = logging.getLogger(__name__)

st.set_page_config(layout='wide')

SideBarLinks()

API_BASE = "http://web-api:4000"

def get_workdays():
    try:
        r = requests.get(f"{API_BASE}/workdays")
        if r.status_code == 200:
            workdays = r.json()
            result = []
            for w in workdays:
                tasks = []
                try:
                    tasks_r = requests.get(f"{API_BASE}/workdays/{w['workday_id']}/tasks")
                    if tasks_r.status_code == 200:
                        for t in tasks_r.json():
                            tasks.append({
                                "id": t["task_id"],
                                "name": t["task_description"],
                                "hours": 2.0,
                                "spots_left": 1,
                                "full": t.get("status") == "completed",
                            })
                except Exception:
                    pass
                result.append({
                    "id": w["workday_id"],
                    "title": w["event_name"],
                    "date": w["event_date"],
                    "time": "",
                    "location": f"Site {w['site_id']}",
                    "signed_up": w["signup_count"],
                    "capacity": w["volunteers_needed"],
                    "needs_help": w["spots_remaining"] < 5,
                    "tasks": tasks,
                })
            return result
    except Exception as e:
        st.warning(f"API error: {e}")
    return [
        {
            "id": 1,
            "title": "Fall Cleanup",
            "date": "Nov 1, 2026",
            "time": "9:00 AM",
            "location": "Elm Street Garden",
            "signed_up": 8,
            "capacity": 12,
            "needs_help": False,
            "tasks": [
                {"id": 10, "name": "Bed Weeding", "hours": 2.0, "spots_left": 1, "full": False},
                {"id": 11, "name": "Compost Turning", "hours": 2.0, "spots_left": 0, "full": True},
                {"id": 12, "name": "Path Raking", "hours": 1.5, "spots_left": 3, "full": False},
            ],
        },
        {
            "id": 2,
            "title": "Fall Greenhouse Prep",
            "date": "Nov 10, 2026",
            "time": "9:00 AM",
            "location": "Elm Street Garden",
            "signed_up": 3,
            "capacity": 12,
            "needs_help": True,
            "tasks": [
                {"id": 20, "name": "Winter Seedling Potting", "hours": 2.0, "spots_left": 4, "full": False},
                {"id": 21, "name": "Drip Line Inspection", "hours": 2.0, "spots_left": 4, "full": False},
            ],
        },
    ]

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
