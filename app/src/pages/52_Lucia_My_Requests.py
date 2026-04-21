import streamlit as st
import requests
#from modules.nav import SideBarLinks

API_BASE = "http://web-api:4000"

def parse_date(date_str):
    if not date_str:
        return ""
    try:
        from datetime import datetime
        d = datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S GMT")
        return d.strftime("%Y-%m-%d")
    except Exception:
        return str(date_str)

def get_my_requests(org_id):
    try:
        r = requests.get(f"{API_BASE}/surplus/requests")
        if r.status_code == 200:
            data = r.json()
            result = []
            for item in data:
                if item.get("org_id") == org_id:
                    status = item.get("status", "pending")
                    display_status = {"pending": "Pending", "approved": "Confirmed", "completed": "Completed", "denied": "Cancelled"}.get(status, status.capitalize())
                    result.append({
                        "id": item.get("request_id"),
                        "crop": item.get("crop_name", "Produce"),
                        "type": item.get("crop_type", "Vegetable"),
                        "lbs": float(item.get("quantity_lbs", 0)),
                        "site": item.get("site_name", "Garden"),
                        "plot": item.get("plot_name", "Plot"),
                        "preferred_date": parse_date(item.get("preferred_pickup_date", "")),
                        "status": display_status,
                        "confirmed_date": parse_date(item.get("preferred_pickup_date", "")) if status == "approved" else None,
                    })
            if result:
                return result
    except Exception:
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
    ]

def cancel_request(request_id):
    try:
        r = requests.delete(f"{API_BASE}/surplus/requests/{request_id}")
        return r.status_code in (200, 204)
    except Exception:
        return False

st.set_page_config(page_title="My Requests - Sprouted", layout="wide")
SideBarLinks()

user = st.session_state.get("user", {"id": 1, "name": "Lucia Tran"})
org_id = user.get("id", 1)

st.title("My Requests")
st.caption("Track and manage your pickup requests")

requests_data = get_my_requests(org_id)

total_lbs = sum(r["lbs"] for r in requests_data if r["status"] == "Completed")
pending_count = sum(1 for r in requests_data if r["status"] == "Pending")
confirmed_count = sum(1 for r in requests_data if r["status"] == "Confirmed")

st.markdown(f"""
<div style="background:#f0f7f0;border:1px solid #c8dcc8;border-radius:8px;padding:12px 16px;margin-bottom:16px;">
    <strong>Summary</strong> &nbsp;·&nbsp;
    <span style="color:#2d6a2d">{total_lbs:.1f} lbs received to date</span> &nbsp;·&nbsp;
    {confirmed_count} confirmed upcoming &nbsp;·&nbsp;
    {pending_count} pending approval
</div>
""", unsafe_allow_html=True)

status_filter = st.radio("Filter by status", ["All", "Pending", "Confirmed", "Completed", "Cancelled"], horizontal=True)
filtered = requests_data if status_filter == "All" else [r for r in requests_data if r["status"] == status_filter]

if not filtered:
    st.info("No requests found for this filter.")

for item in filtered:
    c1, c2, c3 = st.columns([4, 2, 1])
    with c1:
        st.markdown(f"**{item['crop']} - {item['lbs']:.1f} lbs**")
        st.caption(f"{item['site']} · {item['plot']} · Preferred: {item['preferred_date']}")
    with c2:
        colors = {"Pending": "#fff3e0", "Confirmed": "#e8f5e9", "Completed": "#f3f4f6", "Cancelled": "#fce4e4"}
        text_colors = {"Pending": "#e65100", "Confirmed": "#2d6a2d", "Completed": "#666", "Cancelled": "#a32d2d"}
        bg = colors.get(item["status"], "#f3f4f6")
        tc = text_colors.get(item["status"], "#666")
        st.markdown(f'<span style="background:{bg};color:{tc};border-radius:4px;padding:2px 10px;font-size:11px;font-weight:500">{item["status"]}</span>', unsafe_allow_html=True)
        if item["confirmed_date"]:
            st.caption(f"Date: {item['confirmed_date']}")
    with c3:
        if item["status"] == "Pending":
            if st.button("Cancel", key=f"cancel_req_{item['id']}"):
                ok = cancel_request(item["id"])
                if ok:
                    st.success("Cancelled.")
                    st.rerun()
                else:
                    st.error("Could not cancel.")
        elif item["status"] == "Confirmed":
            st.button("View details", key=f"view_{item['id']}")
    st.divider()

st.caption(f"Showing {len(filtered)} of {len(requests_data)} requests")
