import logging
logger = logging.getLogger(__name__)

import streamlit as st
from modules.nav import SideBarLinks

st.set_page_config(layout='wide')

SideBarLinks()

st.title('Volunteer Page')
st.write('### What would you like to do today?')

if st.button('Go to Open Tasks Dashboard',
             type='primary',
             use_container_width=True):
    st.switch_page('pages/41_Clark_Open_Tasks.py')

if st.button('Go to My Hours Page',
             type='primary',
             use_container_width=True):
    st.switch_page('pages/42_Clark_My_Hours.py')

if st.button('Go to My Events Page',
             type='primary',
             use_container_width=True):
    st.switch_page('pages/43_Clark_Event_Detail.py')
