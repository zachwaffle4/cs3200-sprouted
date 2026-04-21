import logging
logger = logging.getLogger(__name__)

import streamlit as st
from modules.nav import SideBarLinks

st.set_page_config(layout='wide')

SideBarLinks()

st.title('Plot Owner Home Page')
st.write('### What would you like to do today?')

if st.button('View My Plot Summary',
             type='primary',
             use_container_width=True):
    st.switch_page('pages/11_Maria_My_Plot.py')

if st.button('Log a Planting or Harvest',
             type='primary',
             use_container_width=True):
    st.switch_page('pages/12_Maria_Log_Activity.py')

if st.button('Report a Pest or Disease',
             type='primary',
             use_container_width=True):
    st.switch_page('pages/13_Maria_Report_Pest.py')

if st.button('List Surplus Produce',
             type='primary',
             use_container_width=True):
    st.switch_page('pages/14_Maria_List_Surplus.py')