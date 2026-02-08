import streamlit as st
from src.data.db_handler import DBHandler
from src.ui.auth import auth_flow
from src.ui.dashboard import dashboard_page
from src.ui.data_entry import data_entry_page
from src.ui.settings import settings_page
from src.ui.ai_analytics import ai_analytics_page
from src.ui.ai_data_entry import ai_data_entry_page
from src.ui.i18n import t

import os

# Page config must be the first Streamlit command
st.set_page_config(page_title="Monthly Data Bot", layout="wide", page_icon="📊")

def main():
    # Initialize language
    if 'language' not in st.session_state:
        st.session_state.language = 'en'

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
            
            st.title(t("Monthly Data Bot"))
            st.caption(f"{t('Logged in as')} **{user.username}**")
            st.divider()
            
            # Navigation Buttons
            if st.button(f"📊 {t('Dashboard')}", width="stretch", type="primary" if st.session_state.current_page == "Dashboard" else "secondary"):
                st.session_state.current_page = "Dashboard"
                st.rerun()
                
            if st.button(f"📝 {t('Data Entry')}", width="stretch", type="primary" if st.session_state.current_page == "Data Entry" else "secondary"):
                st.session_state.current_page = "Data Entry"
                st.rerun()

            if st.button(f"🤖 {t('AI Data Import')}", width="stretch", type="primary" if st.session_state.current_page == "AI Data Import" else "secondary"):
                st.session_state.current_page = "AI Data Import"
                st.rerun()
                
            if st.button(f"🤖 {t('AI Analysis')}", width="stretch", type="primary" if st.session_state.current_page == "AI Analysis" else "secondary"):
                st.session_state.current_page = "AI Analysis"
                st.rerun()

            st.divider()
            
            # Language Selector
            lang_options = {"en": "🇬🇧 English", "de": "🇩🇪 Deutsch"}
            selected_lang = st.selectbox(
                "Language / Sprache", 
                options=list(lang_options.keys()), 
                format_func=lambda x: lang_options[x],
                index=0 if st.session_state.language == 'en' else 1
            )
            
            if selected_lang != st.session_state.language:
                st.session_state.language = selected_lang
                st.rerun()

            if st.button("⚙️ Define Data Categories", width="stretch", type="primary" if st.session_state.current_page == "Define Data Categories" else "secondary"):
                st.session_state.current_page = "Define Data Categories"
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
        elif st.session_state.current_page == "AI Data Import":
            ai_data_entry_page(db, user)
        elif st.session_state.current_page == "AI Analysis":
            ai_analytics_page(db, user)
        elif st.session_state.current_page == "Define Data Categories":
            settings_page(db, user)

if __name__ == "__main__":
    main()
