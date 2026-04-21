import streamlit as st
import requests
from modules.nav import SideBarLinks
 
API_BASE = "http://api:4000"
 
def get_dashboard_data(food_bank_id, season="2026", compare_to="2025"):
    try:
        # Fetch actual analytics data from backend
        r_months = requests.get(f"{API_BASE}/analytics/donations-by-month", params={"org_id": food_bank_id})
        r_sites = requests.get(f"{API_BASE}/analytics/top-sites", params={"org_id": food_bank_id})
        
        monthly_raw = r_months.json() if r_months.status_code == 200 else []
        sites_raw = r_sites.json() if r_sites.status_code == 200 else []
        
        # Transform monthly data
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        current_vals = [0.0] * 12
        for entry in monthly_raw:
            try:
                m_idx = int(entry['month'].split('-')[1]) - 1
                current_vals[m_idx] += float(entry['total_lbs'])
            except: continue
            
        total_lbs = sum(current_vals)
        
        # Transform sites data
        top_sites = []
        for s in sites_raw[:5]:
            top_sites.append({
                "name": s.get('site_name'),
                "lbs": s.get('total_contributed_lbs'),
                "pickups": "N/A" # Backend doesn't count pickups yet
            })
            
        return {
            "total_received_lbs": total_lbs,
            "total_received_change": 0,
            "pickups_completed": len(monthly_raw),
            "pickups_change": 0,
            "garden_partners": len(sites_raw),
            "garden_partners_change": 0,
            "crop_varieties": len(set(e.get('crop_type') for e in monthly_raw)),
            "crop_varieties_change": 0,
            "monthly_data": {
                "months": months,
                "current": current_vals,
                "previous": [0.0] * 12,
            },
            "top_sites": top_sites,
            "crop_breakdown": [], # Can be derived from monthly_raw if needed
        }
    except Exception as e:
        print(f"Error: {e}")
    
    # Fallback to mock data if API fails or returns empty
    return {
        "total_received_lbs": 847,
        "total_received_change": 12,
        "pickups_completed": 38,
        "pickups_change": 5,
        "garden_partners": 3,
        "garden_partners_change": 0,
        "crop_varieties": 14,
        "crop_varieties_change": 3,
        "monthly_data": {
            "months": ["Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov"],
            "current": [20, 85, 120, 160, 175, 140, 95, 52],
            "previous": [15, 70, 100, 130, 150, 120, 80, 40],
        },
        "top_sites": [
            {"name": "Elm Street Garden", "lbs": 412, "pickups": 19},
            {"name": "Riverside Plots", "lbs": 268, "pickups": 12},
            {"name": "MLK Community Farm", "lbs": 167, "pickups": 8},
        ],
        "crop_breakdown": [
            {"crop": "Tomatoes", "lbs": 214, "pct": 25},
            {"crop": "Zucchini", "lbs": 178, "pct": 21},
            {"crop": "Peppers", "lbs": 136, "pct": 16},
            {"crop": "Collard greens", "lbs": 102, "pct": 12},
            {"crop": "Other (10 types)", "lbs": 217, "pct": 26},
        ],
    }
 
st.set_page_config(page_title="Dashboard – Sprouted", layout="wide")
 
SideBarLinks()
 
st.markdown("""
<style>
    .metric-card {
        background: #f9f9f9;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 14px 16px;
        text-align: center;
    }
    .metric-label { font-size: 0.75rem; color: #888; margin-bottom: 4px; }
    .metric-value { font-size: 1.8rem; font-weight: 700; color: #1a3a1a; }
    .metric-change-pos { font-size: 0.75rem; color: #2d6a2d; margin-top: 2px; }
    .metric-change-neu { font-size: 0.75rem; color: #888; margin-top: 2px; }
    .site-row {
        display: flex; justify-content: space-between; align-items: center;
        padding: 10px 0; border-bottom: 1px solid #f0f0f0;
    }
    .site-name { font-weight: 500; font-size: 13px; }
    .site-sub { font-size: 11px; color: #888; }
    .site-lbs { font-size: 15px; font-weight: 700; color: #1a3a1a; }
    .crop-row { display: flex; align-items: center; gap: 10px; margin-bottom: 8px; }
    .crop-name { font-size: 12px; width: 120px; }
    .crop-bar-bg { flex: 1; background: #eee; border-radius: 3px; height: 8px; }
    .crop-pct { font-size: 11px; color: #888; width: 60px; text-align: right; }
</style>
""", unsafe_allow_html=True)
 
user = st.session_state.get("user", {"id": 1, "name": "Lucia Tran"})
food_bank_id = user.get("id", 1)
 
st.title("Dashboard")
st.caption("Donation tracking and seasonal reporting")
 
col1, col2 = st.columns(2)
with col1:
    season = st.selectbox("Time range", ["Current season (2026)", "Last 6 months", "Last 12 months"], label_visibility="visible")
with col2:
    compare_to = st.selectbox("Compare to", ["Previous season (2025)", "Two seasons ago (2024)"], label_visibility="visible")
 
season_val = "2026" if "2026" in season else "2025"
compare_val = "2025" if "2025" in compare_to else "2024"
 
data = get_dashboard_data(food_bank_id, season_val, compare_val)
 
st.markdown("")
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Total received</div>
        <div class="metric-value">{data['total_received_lbs']} lbs</div>
        <div class="metric-change-pos">+{data['total_received_change']}% vs {compare_val}</div>
    </div>""", unsafe_allow_html=True)
with c2:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Pickups completed</div>
        <div class="metric-value">{data['pickups_completed']}</div>
        <div class="metric-change-pos">+{data['pickups_change']} vs {compare_val}</div>
    </div>""", unsafe_allow_html=True)
with c3:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Garden partners</div>
        <div class="metric-value">{data['garden_partners']}</div>
        <div class="metric-change-neu">Same as {compare_val}</div>
    </div>""", unsafe_allow_html=True)
with c4:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Crop varieties</div>
        <div class="metric-value">{data['crop_varieties']}</div>
        <div class="metric-change-pos">+{data['crop_varieties_change']} vs {compare_val}</div>
    </div>""", unsafe_allow_html=True)
 
st.markdown("")
st.subheader("Monthly produce received (lbs)")
 
months = data["monthly_data"]["months"]
current = data["monthly_data"]["current"]
previous = data["monthly_data"]["previous"]
 
import pandas as pd
chart_data = pd.DataFrame({
    str(season_val): current,
    str(compare_val): previous,
}, index=months)
st.bar_chart(chart_data, height=250)
 
st.markdown("")
col_left, col_right = st.columns(2)
 
with col_left:
    st.subheader("Top contributing sites")
    for site in data["top_sites"]:
        st.markdown(f"""
        <div class="site-row">
            <div>
                <div class="site-name">{site['name']}</div>
                <div class="site-sub">{site['pickups']} pickups</div>
            </div>
            <div class="site-lbs">{site['lbs']} lbs</div>
        </div>""", unsafe_allow_html=True)
 
with col_right:
    st.subheader("Breakdown by crop type")
    for crop in data["crop_breakdown"]:
        bar_width = crop["pct"]
        st.markdown(f"""
        <div class="crop-row">
            <div class="crop-name">{crop['crop']}</div>
            <div class="crop-bar-bg">
                <div style="width:{bar_width}%;background:#4a7c4a;height:8px;border-radius:3px;"></div>
            </div>
            <div class="crop-pct">{crop['lbs']} lbs ({crop['pct']}%)</div>
        </div>""", unsafe_allow_html=True)
