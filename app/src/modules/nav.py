# Idea borrowed from https://github.com/fsmosca/sample-streamlit-authenticator

# This file has functions to add links to the left sidebar based on the user's role.
import streamlit as st

# ---- General ----------------------------------------------------------------

def home_nav():
    st.sidebar.page_link("Home.py", label="Home", icon="🏠")

def about_page_nav():
    st.sidebar.page_link("pages/30_About.py", label="About", icon="🧠")


# ---- Role: garden_admin ------------------------------------------------

def garden_admin_home_nav():
    st.sidebar.page_link(
        "pages/00_Admin_Home.py", label="Garden Admin Home", icon="🏠"
    )

def admin_dashboard_nav():
    st.sidebar.page_link(
        "pages/01_Admin_Dashboard.py", label="Dashboard", icon="📊"
    )

def admin_plots_nav():
    st.sidebar.page_link(
        "pages/02_Admin_Plots.py", label="Plot Manager", icon="🌱"
    )

def admin_workdays_nav():
    st.sidebar.page_link(
        "pages/03_Admin_Workdays.py", label="Workdays Manager", icon="📅"
    )


# ---- Role: plot_owner -----------------------------------------------------

def plot_owner_home_nav():
    st.sidebar.page_link(
        "pages/10_Plot_Owner_Home.py", label="Plot Owner Home", icon="🏠"
    )

def maria_my_plot_nav():
    st.sidebar.page_link(
        "pages/11_Maria_My_Plot.py", label="My Plot", icon="🌿"
    )

def maria_log_activity_nav():
    st.sidebar.page_link(
        "pages/12_Maria_Log_Activity.py", label="Log Activity", icon="📝"
    )

def maria_report_pest_nav():
    st.sidebar.page_link(
        "pages/13_Maria_Report_Pest.py", label="Report Pest", icon="🐛"
    )

def maria_list_surplus_nav():
    st.sidebar.page_link(
        "pages/14_Maria_List_Surplus.py", label="List Surplus", icon="🥕"
    )


# ---- Role: volunteer ----------------------------------------------------
def volunteer_home_nav():
    st.sidebar.page_link(
        "pages/40_Clark_Home.py", label="Volunteer Home", icon="🏠"
    )

def volunteer_open_tasks_nav():
    st.sidebar.page_link(
        "pages/41_Clark_Open_Tasks.py", label="Open Tasks", icon="📋"
    )

def volunteer_my_hours_nav():
    st.sidebar.page_link(
        "pages/42_Clark_My_Hours.py", label="My Hours", icon="⏱️"
    )

def volunteer_event_detail_nav():
    st.sidebar.page_link(
        "pages/43_Clark_Event_Detail.py", label="Event Detail", icon="📍"
    )


# ---- Role: food_bank_coordinator ----------------------------------------------------

def lucia_dashboard_nav():
    st.sidebar.page_link("pages/50_Lucia_Dashboard.py", label="Dashboard", icon="📊")


def lucia_browse_nav():
    st.sidebar.page_link("pages/51_Lucia_Browse_Surplus.py", label="Browse Surplus", icon="🥦")


def lucia_requests_nav():
    st.sidebar.page_link("pages/52_Lucia_My_Requests.py", label="My Requests", icon="📋")


# ---- Sidebar assembly -------------------------------------------------------

def SideBarLinks(show_home=False):
    """
    Renders sidebar navigation links based on the logged-in user's role.
    The role is stored in st.session_state when the user logs in on Home.py.
    """

    # Logo appears at the top of the sidebar on every page
    st.sidebar.image("assets/logo.png", width=150)

    # If no one is logged in, send them to the Home (login) page
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
        st.switch_page("Home.py")

    if show_home:
        home_nav()

    if st.session_state["authenticated"]:

        if st.session_state["role"] == "garden_admin":
            garden_admin_home_nav()
            admin_dashboard_nav()
            admin_plots_nav()
            admin_workdays_nav()

        if st.session_state["role"] == "plot_owner":
            plot_owner_home_nav()
            maria_my_plot_nav()
            maria_log_activity_nav()
            maria_report_pest_nav()
            maria_list_surplus_nav()

        if st.session_state["role"] == "volunteer":
            volunteer_home_nav()
            volunteer_open_tasks_nav()
            volunteer_my_hours_nav()
            volunteer_event_detail_nav()

        if st.session_state["role"] == "food_bank_coordinator":
            lucia_dashboard_nav()
            lucia_browse_nav()
            lucia_requests_nav()

    # About link appears at the bottom for all roles
    about_page_nav()

    if st.session_state["authenticated"]:
        if st.sidebar.button("Logout"):
            del st.session_state["role"]
            del st.session_state["authenticated"]
            st.switch_page("Home.py")