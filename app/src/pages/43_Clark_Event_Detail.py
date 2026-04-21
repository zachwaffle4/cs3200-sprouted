import logging
import requests
import streamlit as st
from modules.nav import SideBarLinks
logger = logging.getLogger(__name__)

st.set_page_config(layout='wide')

SideBarLinks()

API_BASE = "http://localhost:4001/api"

def get_workday_tasks(workday_id):
    try:
        r = requests.get(f"{API_BASE}/workdays/{workday_id}/tasks")
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return {
        "id": 2,
        "title": "Fall Greenhouse Prep",
        "date": "Nov 10, 2026",
        "time": "9:00 AM – 1:00 PM",
        "location": "Elm Street Community Garden, 42 Elm St",
        "signed_up": 3,
        "capacity": 12,
        "needs_help": True,
        "tasks": [
            {
                "id": 20,
                "name": "Winter Seedling Potting",
                "hours": 2.0,
                "spots_left": 1,
                "full": False,
                "urgent": True,
                "description": "Pot and label 60+ seedlings for winter storage. No experience needed, gloves provided.",
            },
            {
                "id": 21,
                "name": "Drip Line Inspection",
                "hours": 2.0,
                "spots_left": 4,
                "full": False,
                "urgent": False,
                "description": "Walk the garden beds and flag any broken or clogged drip emitters for repair. Bring a marker.",
            },
            {
                "id": 22,
                "name": "Tool Cleaning & Storage",
                "hours": 1.5,
                "spots_left": 0,
                "full": True,
                "urgent": False,
                "description": "Clean and oil hand tools before winter. All supplies at the shed.",
            },
        ],
    }

def signup_for_task(workday_id, task_id, volunteer_id):
    try:
        r = requests.post(
            f"{API_BASE}/workdays/{workday_id}/signups",
            json={"task_id": task_id, "volunteer_id": volunteer_id},
        )
        return r.status_code in (200, 201)
    except Exception:
        return False

st.set_page_config(page_title="Event Detail – Sprouted", layout="wide")

st.markdown("""
<style>
    .urgent-flag { color: #a32d2d; font-size: 0.78rem; font-weight: 500; }
    .task-desc { color: #555; font-size: 0.85rem; margin-top: 2px; }
    .signed-badge {
        background: #e1f5ee; color: #085041;
        border-radius: 4px; padding: 3px 10px; font-size: 0.8rem; font-weight: 500;
    }
    .needs-help-chip {
        background: #fcebeb; color: #a32d2d;
        border-radius: 4px; padding: 3px 10px; font-size: 0.8rem; font-weight: 500;
        margin-right: 6px;
    }
    .spots-chip {
        background: #e6f1fb; color: #0c447c;
        border-radius: 4px; padding: 3px 10px; font-size: 0.8rem; font-weight: 500;
    }
    .hours-bar {
        background: #e1f5ee;
        border: 1px solid #9fe1cb;
        border-radius: 6px;
        padding: 0.6rem 1rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
</style>
""", unsafe_allow_html=True)

user = st.session_state.get("user", {"id": 3, "name": "Clark Kent"})
volunteer_id = user.get("id", 3)

if st.button("← Back to Open Tasks"):
    st.switch_page("pages/41_Clark_Open_Tasks.py")

workday_id = st.session_state.get("selected_workday_id", 2)
wd = get_workday_tasks(workday_id)

st.markdown(f"## {wd['title']}")
st.caption(f"{wd['date']} · {wd['time']} · {wd['location']}")

spots_total_left = sum(t["spots_left"] for t in wd["tasks"] if not t["full"])
badge_html = ""
if wd.get("needs_help"):
    badge_html += '<span class="needs-help-chip">Needs Help</span>'
badge_html += f'<span class="spots-chip">{spots_total_left} spots left</span>'
st.markdown(badge_html, unsafe_allow_html=True)
st.markdown("")

pct = wd["signed_up"] / wd["capacity"] if wd["capacity"] else 0
st.progress(pct, text=f"{wd['signed_up']} / {wd['capacity']} signed up")

st.markdown(f"""
<div style="
    background:#f0f4f0; border:1px solid #c8d8c8; border-radius:8px;
    height:80px; display:flex; align-items:center; justify-content:center;
    color:#6a8a6a; font-size:0.85rem; margin-top:0.5rem; margin-bottom:1.25rem;
">
    📍 Map — {wd['location']}
</div>
""", unsafe_allow_html=True)

st.markdown("### Available Tasks")
st.caption("Sign up for one or more tasks. Urgent tasks are short on volunteers.")

h1, h2, h3, h4 = st.columns([4, 1, 1, 2])
h1.markdown("**Task**")
h2.markdown("**Time**")
h3.markdown("**Spots**")
h4.markdown("**Action**")
st.markdown("---")

signed_up_tasks = st.session_state.get("signed_up_tasks", set())

for task in wd.get("tasks", []):
    task_key = f"{wd['id']}_{task['id']}"
    c1, c2, c3, c4 = st.columns([4, 1, 1, 2])

    with c1:
        st.markdown(f"**{task['name']}**")
        if task["urgent"]:
            st.markdown(f'<span class="urgent-flag">● Urgent — only {task["spots_left"]} left</span>', unsafe_allow_html=True)
        elif task["full"]:
            st.markdown('<span style="color:#999;font-size:0.78rem">Full</span>', unsafe_allow_html=True)
        else:
            st.markdown(f'<span style="color:#555;font-size:0.78rem">{task["spots_left"]} spots remaining</span>', unsafe_allow_html=True)
        st.markdown(f'<div class="task-desc">{task["description"]}</div>', unsafe_allow_html=True)

    c2.write(f"{task['hours']:.1f} hrs")
    c3.write("Full" if task["full"] else str(task["spots_left"]))

    with c4:
        if task["full"]:
            st.button("Full", key=f"det_full_{task_key}", disabled=True)
        elif task_key in signed_up_tasks:
            st.markdown('<span class="signed-badge">Signed Up ✓</span>', unsafe_allow_html=True)
        else:
            if st.button("Sign Up", key=f"det_signup_{task_key}"):
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
                    st.success(f"You're signed up for '{task['name']}'! It'll be logged after the event.")
                    st.rerun()
                else:
                    st.error("Sign-up failed. Please try again.")

    st.markdown("---")

total_hrs = 30.0
goal_hrs = 60.0
remaining = goal_hrs - total_hrs

my_signed_up_hrs = sum(
    t["hours"] for t in wd["tasks"]
    if f"{wd['id']}_{t['id']}" in signed_up_tasks
)
note = ""
if my_signed_up_hrs > 0:
    note = f" &nbsp;·&nbsp; <span style='color:#085041'>{my_signed_up_hrs:.1f} hrs pending from this event</span>"

st.markdown(f"""
<div class="hours-bar">
    <div>
        <strong>My hours this semester</strong> &nbsp;
        <span style='color:#085041'>{total_hrs:.0f} hrs logged</span>{note}
    </div>
    <div style='color:#5a7a5a; font-size:0.85rem'>{remaining:.0f} remaining to {goal_hrs:.0f}-hr goal</div>
</div>
""", unsafe_allow_html=True)