import streamlit as st
import requests as req
from modules.nav import SideBarLinks

API_BASE = "http://localhost:4001/api"

def get_surplus_listings(crop_type=None, garden_site=None, min_qty=None):
    try:
        params = {}
        if crop_type and crop_type != "All types":
            params["crop_type"] = crop_type
        if garden_site and garden_site != "All sites":
            params["garden_site"] = garden_site
        if min_qty:
            params["min_qty"] = min_qty
        r = req.get(f"{API_BASE}/surplus", params=params)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return [
        {"id": 1, "crop": "Roma tomatoes", "type": "Vegetable", "lbs": 12,
         "site": "Elm Street Garden", "plot": "Plot 14", "owner": "Maria S.", "date": "Mar 24", "status": "available"},
        {"id": 2, "crop": "Sweet basil", "type": "Herb", "lbs": 3,
         "site": "Riverside Plots", "plot": "Plot 3", "owner": "James K.", "date": "Mar 23", "status": "available"},
        {"id": 3, "crop": "Zucchini", "type": "Vegetable", "lbs": 8,
         "site": "MLK Community Farm", "plot": "Plot 7", "owner": "Diane P.", "date": "Mar 22", "status": "available"},
        {"id": 4, "crop": "Jalapeño peppers", "type": "Vegetable", "lbs": 5,
         "site": "Elm Street Garden", "plot": "Plot 22", "owner": "Carlos M.", "date": "Mar 25", "status": "available"},
        {"id": 5, "crop": "Collard greens", "type": "Vegetable", "lbs": 6,
         "site": "Riverside Plots", "plot": "Plot 11", "owner": "Aisha T.", "date": "Mar 20", "status": "pending"},
    ]

def request_pickup(surplus_id, food_bank_id, preferred_date):
    try:
        r = req.post(f"{API_BASE}/surplus/{surplus_id}/requests",
                     json={"food_bank_id": food_bank_id, "preferred_date": preferred_date})
        return r.status_code in (200, 201)
    except Exception:
        return False

def cancel_request(surplus_id):
    try:
        r = req.delete(f"{API_BASE}/surplus/{surplus_id}/requests")
        return r.status_code in (200, 204)
    except Exception:
        return False

st.set_page_config(page_title="Browse Surplus – Sprouted", layout="wide")

SideBarLinks()

st.markdown("""
<style>
    .listing-card {
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 14px 16px;
        margin-bottom: 10px;
        background: #fff;
    }
    .crop-title { font-size: 15px; font-weight: 600; }
    .crop-sub { font-size: 12px; color: #888; margin-top: 2px; }
    .tag {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 11px;
        font-weight: 500;
        margin-left: 6px;
    }
    .tag-veg { background: #e8f5e9; color: #2d6a2d; }
    .tag-herb { background: #e3f2fd; color: #1565c0; }
    .tag-pending { background: #fff3e0; color: #e65100; }
    .lbs-label { font-size: 16px; font-weight: 700; color: #1a3a1a; }
</style>
""", unsafe_allow_html=True)

user = st.session_state.get("user", {"id": 1, "name": "Lucia Tran"})
food_bank_id = user.get("id", 1)

st.title("Browse surplus produce")
st.caption("View available surplus from all partner gardens")

f1, f2, f3, f4, f5 = st.columns([2, 1.5, 1.5, 1, 1])
with f1:
    search = st.text_input("Search crops", placeholder="e.g. tomatoes...", label_visibility="collapsed")
with f2:
    crop_type = st.selectbox("Crop type", ["All types", "Vegetable", "Herb", "Fruit", "Grain"], label_visibility="collapsed")
with f3:
    garden_site = st.selectbox("Garden site", ["All sites", "Elm Street Garden", "Riverside Plots", "MLK Community Farm"], label_visibility="collapsed")
with f4:
    min_qty = st.number_input("Min qty (lbs)", min_value=0, value=0, label_visibility="collapsed")
with f5:
    filter_btn = st.button("Filter")

listings = get_surplus_listings(crop_type, garden_site, min_qty if min_qty > 0 else None)

if search:
    listings = [l for l in listings if search.lower() in l["crop"].lower()]

st.caption(f"Showing {len(listings)} available listings")

requested = st.session_state.get("requested_surplus", set())

for listing in listings:
    col_main, col_action = st.columns([4, 1])

    tag_class = "tag-herb" if listing["type"] == "Herb" else "tag-veg"
    pending_tag = '<span class="tag tag-pending">Pickup pending</span>' if listing["status"] == "pending" else ""

    with col_main:
        st.markdown(f"""
        <div style="margin-bottom:4px;">
            <span class="crop-title">{listing['crop']}</span>
            <span class="tag {tag_class}">{listing['type']}</span>
            {pending_tag}
        </div>
        <div class="crop-sub">{listing['site']} · {listing['plot']} · {listing['owner']} · {listing['date']}</div>
        """, unsafe_allow_html=True)

    with col_action:
        st.markdown(f'<div class="lbs-label">{listing["lbs"]} lbs</div>', unsafe_allow_html=True)
        if listing["status"] == "pending" or listing["id"] in requested:
            if st.button("Cancel request", key=f"cancel_{listing['id']}", type="secondary"):
                ok = cancel_request(listing["id"])
                if ok:
                    requested.discard(listing["id"])
                    st.session_state["requested_surplus"] = requested
                    st.success("Request cancelled.")
                    st.rerun()
                else:
                    st.error("Could not cancel. Please try again.")
        else:
            if st.button("Request pickup", key=f"request_{listing['id']}"):
                ok = request_pickup(listing["id"], food_bank_id, "2026-04-01")
                if ok:
                    requested.add(listing["id"])
                    st.session_state["requested_surplus"] = requested
                    st.success(f"Pickup requested for {listing['crop']}!")
                    st.rerun()
                else:
                    st.error("Request failed. Please try again.")

    st.divider()

st.caption(f"1–{len(listings)} of {len(listings)} listings")