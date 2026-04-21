import streamlit as st
import requests
from modules.nav import SideBarLinks

API_BASE = "http://api:4000"

def get_my_requests(food_bank_id):
    try:
        # Backend doesn't have a direct /food-banks/{id}/requests,
        # but we can filter surplus listings or requests if there was an endpoint.
        # Looking at surplus_routes, there is no GET /surplus/requests.
        # Let's check if we can add one or if we should use a different approach.
        # For now, I'll update the cancel_request to the correct endpoint.
        pass
    except Exception as e:
        st.error(f"Error: {e}")
    return [
        {"id": 101, "crop": "Roma tomatoes", "type": "Vegetable", "lbs": 12,
         "site": "Elm Street Garden", "plot": "Plot 14", "preferred_date": "Apr 1, 2026",
         "status": "Confirmed", "confirmed_date": "Apr 1, 2026"},
        {"id": 102, "crop": "Zucchini", "type": "Vegetable", "lbs": 8,
         "site": "MLK Community Farm", "plot": "Plot 7", "preferred_date": "Apr 3, 2026",
         "status": "Pending", "confirmed_date": None},
        {"id": 103, "crop": "Sweet basil", "type": "Herb", "lbs": 3,
         "site": "Riverside Plots", "plot": "Plot 3", "preferred_date": "Apr 5, 2026",
         "status": "Pending", "confirmed_date": None},
        {"id": 104, "crop": "Collard greens", "type": "Vegetable", "lbs": 6,
         "site": "Riverside Plots", "plot": "Plot 11", "preferred_date": "Mar 28, 2026",
         "status": "Completed", "confirmed_date": "Mar 28, 2026"},
        {"id": 105, "crop": "Jalapeño peppers", "type": "Vegetable", "lbs": 5,
         "site": "Elm Street Garden", "plot": "Plot 22", "preferred_date": "Mar 25, 2026",
         "status": "Completed", "confirmed_date": "Mar 25, 2026"},
    ]

def cancel_request(request_id):
    try:
        # Correct endpoint from surplus_routes.py
        r = requests.delete(f"{API_BASE}/surplus/requests/{request_id}")
        return r.status_code in (200, 204)
    except Exception:
        return False

st.set_page_config(page_title="My Requests – Sprouted", layout="wide")

SideBarLinks()

st.markdown("""
<style>
    .status-confirmed {
        background: #e8f5e9; color: #2d6a2d;
        border-radius: 4px; padding: 2px 10px; font-size: 11px; font-weight: 500;
    }
    .status-pending {
        background: #fff3e0; color: #e65100;
        border-radius: 4px; padding: 2px 10px; font-size: 11px; font-weight: 500;
    }
    .status-completed {
        background: #f3f4f6; color: #666;
        border-radius: 4px; padding: 2px 10px; font-size: 11px; font-weight: 500;
    }
    .req-title { font-size: 14px; font-weight: 600; }
    .req-sub { font-size: 12px; color: #888; margin-top: 2px; }
    .summary-box {
        background: #f0f7f0;
        border: 1px solid #c8dcc8;
        border-radius: 8px;
        padding: 12px 16px;
        margin-bottom: 16px;
    }
</style>
""", unsafe_allow_html=True)

user = st.session_state.get("user", {"id": 1, "name": "Lucia Tran"})
food_bank_id = user.get("id", 1)

st.title("My Requests")
st.caption("Track and manage your pickup requests")

requests_data = get_my_requests(food_bank_id)

total_lbs = sum(r["lbs"] for r in requests_data if r["status"] == "Completed")
pending_count = sum(1 for r in requests_data if r["status"] == "Pending")
confirmed_count = sum(1 for r in requests_data if r["status"] == "Confirmed")

st.markdown(f"""
<div class="summary-box">
    <strong>Summary</strong> &nbsp;·&nbsp;
    <span style="color:#2d6a2d">{total_lbs} lbs received to date</span> &nbsp;·&nbsp;
    {confirmed_count} confirmed upcoming &nbsp;·&nbsp;
    {pending_count} pending approval
</div>
""", unsafe_allow_html=True)

status_filter = st.radio("Filter by status", ["All", "Pending", "Confirmed", "Completed"], horizontal=True)

filtered = requests_data if status_filter == "All" else [r for r in requests_data if r["status"] == status_filter]

if not filtered:
    st.info("No requests found for this filter.")

for req in filtered:
    c1, c2, c3 = st.columns([4, 2, 1])

    status_class = f"status-{req['status'].lower()}"

    with c1:
        st.markdown(f"""
        <div class="req-title">{req['crop']} — {req['lbs']} lbs</div>
        <div class="req-sub">{req['site']} · {req['plot']} · Preferred: {req['preferred_date']}</div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown(f'<span class="{status_class}">{req["status"]}</span>', unsafe_allow_html=True)
        if req["confirmed_date"]:
            st.caption(f"Date: {req['confirmed_date']}")

    with c3:
        if req["status"] == "Pending":
            if st.button("Cancel", key=f"cancel_req_{req['id']}"):
                ok = cancel_request(req["id"])
                if ok:
                    st.success(f"Request for {req['crop']} cancelled.")
                    st.rerun()
                else:
                    st.error("Could not cancel. Please try again.")
        elif req["status"] == "Confirmed":
            st.button("View details", key=f"view_{req['id']}") 

    st.divider()

st.caption(f"Showing {len(filtered)} of {len(requests_data)} requests")