import logging
logger = logging.getLogger(__name__)

import streamlit as st
from modules.nav import SideBarLinks

st.set_page_config(layout='wide')

SideBarLinks()

st.title('Garden Admin Home Page')
st.write('### What would you like to do today?')

if st.button('Go to Garden Admin Dashboard',
             type='primary',
             use_container_width=True):
    st.switch_page('pages/01_Admin_Dashboard.py')

if st.button('Go to Plot Management Page',
             type='primary',
             use_container_width=True):
    st.switch_page('pages/02_Admin_Plots.py')

if st.button('Go to Workdays Management Page',
             type='primary',
             use_container_width=True):
    st.switch_page('pages/03_Admin_Workdays.py')
