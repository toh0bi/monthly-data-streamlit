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

@st.cache_resource
def get_db() -> DBHandler:
    return DBHandler()

def main():
    # Initialize language
    if 'language' not in st.session_state:
        st.session_state.language = 'en'

    db = get_db()
    
    user = auth_flow(db)
    
    if not user:
        return

    # Page wrappers (st.Page callables take no arguments)
    def _data_entry():
        data_entry_page(db, user)

    def _dashboard():
        dashboard_page(db, user)

    def _ai_import():
        ai_data_entry_page(db, user)

    def _ai_analysis():
        ai_analytics_page(db, user)

    def _settings():
        settings_page(db, user)

    pages = [
        st.Page(_data_entry, title=t("Data Entry"), icon="📝", url_path="data-entry", default=True),
        st.Page(_dashboard, title=t("Dashboard"), icon="📊", url_path="dashboard"),
        st.Page(_ai_import, title=t("AI Data Import"), icon="🤖", url_path="ai-import"),
        st.Page(_ai_analysis, title=t("AI Analysis"), icon="🤖", url_path="ai-analysis"),
        st.Page(_settings, title=t("Define Data Series"), icon="⚙️", url_path="settings"),
    ]

    # Top navigation: all pages reachable without opening the sidebar (mobile friendly)
    nav = st.navigation(pages, position="top")

    # Sidebar holds only optional extras (account info, language, logout)
    with st.sidebar:
        if os.path.exists("logo.png"):
            st.image("logo.png", width="stretch")
        
        st.title(t("Monthly Data Bot"))
        st.caption(f"{t('Logged in as')} **{user.username}**")
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

        st.divider()
        if st.button(t("Logout")):
            del st.session_state['user']
            st.rerun()

    nav.run()

if __name__ == "__main__":
    main()
