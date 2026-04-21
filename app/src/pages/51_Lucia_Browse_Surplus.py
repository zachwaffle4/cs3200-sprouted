import streamlit as st
import requests as req
from modules.nav import SideBarLinks

API_BASE = "http://web-api:4000"

def get_surplus_listings():
    try:
        r = req.get(f"{API_BASE}/surplus")
        if r.status_code == 200:
            listings = r.json()
            result = []
            for l in listings:
                result.append({
                    "id": l.get("listing_id"),
                    "crop": l.get("crop_name", f"Crop {l.get('crop_id', '?')}"),
                    "type": l.get("crop_type", "Vegetable"),
                    "lbs": l.get("quantity_lbs", 0),
                    "site": l.get("site_name", f"Site {l.get('site_id', '?')}"),
                    "plot": l.get("plot_name", f"Plot {l.get('plot_id', '?')}"),
                    "date": str(l.get("listed_date", ""))[:16].strip(", "),
                    "status": l.get("status", "available"),
                })
            return result
    except Exception:
        pass
    return [
        {"id": 1, "crop": "Roma tomatoes", "type": "Vegetable", "lbs": 12,
         "site": "Elm Street Garden", "plot": "Plot 14", "date": "Mar 24", "status": "available"},
        {"id": 2, "crop": "Sweet basil", "type": "Herb", "lbs": 3,
         "site": "Riverside Plots", "plot": "Plot 3", "date": "Mar 23", "status": "available"},
        {"id": 3, "crop": "Zucchini", "type": "Vegetable", "lbs": 8,
         "site": "MLK Community Farm", "plot": "Plot 7", "date": "Mar 22", "status": "available"},
        {"id": 4, "crop": "Jalapeño peppers", "type": "Vegetable", "lbs": 5,
         "site": "Elm Street Garden", "plot": "Plot 22", "date": "Mar 25", "status": "available"},
        {"id": 5, "crop": "Collard greens", "type": "Vegetable", "lbs": 6,
         "site": "Riverside Plots", "plot": "Plot 11", "date": "Mar 20", "status": "pending"},
    ]

def request_pickup(listing_id, org_id, preferred_date):
    try:
        r = req.post(
            f"{API_BASE}/surplus/requests",
            json={"org_id": org_id, "listing_id": listing_id, "preferred_pickup_date": preferred_date}
        )
        if r.status_code in (200, 201):
            return True, r.json().get("request_id")
        return False, None
    except Exception:
        return False, None

def cancel_request(request_id):
    try:
        r = req.delete(f"{API_BASE}/surplus/requests/{request_id}")
        return r.status_code in (200, 204)
    except Exception:
        return False

st.set_page_config(page_title="Browse Surplus - Sprouted", layout="wide")
SideBarLinks()

st.markdown("""
<style>
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
org_id = user.get("id", 1)

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
    st.button("Filter")

listings = get_surplus_listings()

if search:
    listings = [l for l in listings if search.lower() in l["crop"].lower()]
if crop_type != "All types":
    listings = [l for l in listings if l.get("type") == crop_type]
if min_qty > 0:
    listings = [l for l in listings if l.get("lbs", 0) >= min_qty]

st.caption(f"Showing {len(listings)} available listings")

requested = st.session_state.get("requested_surplus", {})

for listing in listings:
    col_main, col_action = st.columns([4, 1])

    tag_class = "tag-herb" if listing.get("type") == "Herb" else "tag-veg"
    pending_tag = '<span class="tag tag-pending">Pickup pending</span>' if listing.get("status") == "pending" else ""

    with col_main:
        st.markdown(f"""
        <div style="margin-bottom:4px;">
            <span class="crop-title">{listing['crop']}</span>
            <span class="tag {tag_class}">{listing.get('type', 'Produce')}</span>
            {pending_tag}
        </div>
        <div class="crop-sub">{listing['site']} · {listing['plot']} · {listing['date']}</div>
        """, unsafe_allow_html=True)

    with col_action:
        st.markdown(f'<div class="lbs-label">{listing["lbs"]} lbs</div>', unsafe_allow_html=True)
        listing_id = listing["id"]
        if listing.get("status") == "pending" or listing_id in requested:
            req_id = requested.get(listing_id)
            if st.button("Cancel request", key=f"cancel_{listing_id}", type="secondary"):
                ok = cancel_request(req_id) if req_id else False
                if ok:
                    del requested[listing_id]
                    st.session_state["requested_surplus"] = requested
                    st.success("Request cancelled.")
                    st.rerun()
                else:
                    st.error("Could not cancel.")
        else:
            if st.button("Request pickup", key=f"request_{listing_id}"):
                ok, req_id = request_pickup(listing_id, org_id, "2026-05-01")
                if ok:
                    requested[listing_id] = req_id
                    st.session_state["requested_surplus"] = requested
                    st.success(f"Pickup requested for {listing['crop']}!")
                    st.rerun()
                else:
                    st.error("Request failed.")

    st.divider()

st.caption(f"1-{len(listings)} of {len(listings)} listings")
