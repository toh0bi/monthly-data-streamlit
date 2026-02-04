import streamlit as st
from src.data.db_handler import DBHandler
from src.ui.auth import auth_flow
from src.ui.dashboard import dashboard_page
from src.ui.data_entry import data_entry_page
from src.ui.settings import settings_page
from src.ui.ai_analytics import ai_analytics_page

import os

# Page config must be the first Streamlit command
st.set_page_config(page_title="Monthly Data Bot", layout="wide", page_icon="📊")

def main():
    db = DBHandler()
    
    user = auth_flow(db)
    
    if user:
        # Initialize page state if not exists
        if "current_page" not in st.session_state:
            st.session_state.current_page = "Dashboard"

        with st.sidebar:
            # Logo & Title
            if os.path.exists("logo.png"):
                st.image("logo.png", width="stretch")
            
            st.title("Monthly Data Bot")
            st.caption(f"Logged in as **{user.username}**")
            st.divider()
            
            # Navigation Buttons
            if st.button("📊 Dashboard", width="stretch", type="primary" if st.session_state.current_page == "Dashboard" else "secondary"):
                st.session_state.current_page = "Dashboard"
                st.rerun()
                
            if st.button("📝 Data Entry", width="stretch", type="primary" if st.session_state.current_page == "Data Entry" else "secondary"):
                st.session_state.current_page = "Data Entry"
                st.rerun()
                
            if st.button("🤖 AI Analysis", width="stretch", type="primary" if st.session_state.current_page == "AI Analysis" else "secondary"):
                st.session_state.current_page = "AI Analysis"
                st.rerun()

            if st.button("⚙️ Define Meter Types", width="stretch", type="primary" if st.session_state.current_page == "Define Meter Types" else "secondary"):
                st.session_state.current_page = "Define Meter Types"
                st.rerun()
            
            st.divider()
            if st.button("Logout"):
                del st.session_state['user']
                st.rerun()
        
        # Routing
        if st.session_state.current_page == "Dashboard":
            dashboard_page(db, user)
        elif st.session_state.current_page == "Data Entry":
            data_entry_page(db, user)
        elif st.session_state.current_page == "AI Analysis":
            ai_analytics_page(db, user)
        elif st.session_state.current_page == "Define Meter Types":
            settings_page(db, user)

if __name__ == "__main__":
    main()
