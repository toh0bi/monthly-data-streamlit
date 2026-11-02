import streamlit as st
import bcrypt
import os
from src.data.db_handler import DBHandler
from src.data.models import User
from src.ui.i18n import t
from datetime import datetime
import uuid

def hash_password(password: str) -> str:
    pw_bytes = password.encode('utf-8')[:72]
    return bcrypt.hashpw(pw_bytes, bcrypt.gensalt()).decode('utf-8')

def check_password(password: str, hashed: str) -> bool:
    pw_bytes = password.encode('utf-8')[:72]
    return bcrypt.checkpw(pw_bytes, hashed.encode('utf-8'))

def login_form(db: DBHandler):
    with st.form("login_form"):
        username = st.text_input(t("Username"))
        password = st.text_input(t("Password"), type="password")
        submit = st.form_submit_button(t("Login"))
        
        if submit:
            # Clean input
            username = username.strip()
            password = password.strip()
            
            if not username or not password:
                st.error(t("Invalid username or password"))
                return

            user = db.get_user(username)
            if user and check_password(password, user.password_hash):
                db.update_user_stats(user.username)
                st.session_state['user'] = user
                st.success(t("Welcome back, {}!", user.username))
                st.rerun()
            else:
                st.error(t("Invalid username or password"))

def register_form(db: DBHandler):
    with st.form("register_form"):
        username = st.text_input(t("Username"))
        password = st.text_input(t("Password"), type="password")
        password_confirm = st.text_input(t("Confirm Password"), type="password")
        # Optional: Allow linking to old chat_id for migration
        old_chat_id = st.text_input(
            t("Legacy Chat ID (Optional)"),
            help=t("Enter your numeric Telegram Chat ID to migrate your existing bot data. Each Chat ID can only be claimed once.")
        )
        
        submit = st.form_submit_button(t("Register"))
        
        if submit:
            # Clean input
            username = username.strip()
            password = password.strip()
            password_confirm = password_confirm.strip()
            old_chat_id = old_chat_id.strip()

            if not username or len(username) < 3:
                st.error(t("Username must be at least 3 characters long"))
                return

            if not password or len(password) < 6:
                st.error(t("Password must be at least 6 characters long"))
                return

            if password != password_confirm:
                st.error(t("Passwords do not match"))
                return
            
            if db.get_user(username):
                st.error(t("Username already exists"))
                return
            
            if old_chat_id:
                # 1. Must be a numeric Telegram chat ID ( prevents arbitrary UUID hijacking )
                if not old_chat_id.isdigit():
                    st.error(t("Invalid Legacy Chat ID format."))
                    return
                # 2. Optional whitelist via secrets (ALLOWED_LEGACY_CHAT_IDS = ["12345678"])
                allowed_ids = st.secrets.get("ALLOWED_LEGACY_CHAT_IDS", None) if hasattr(st, "secrets") else None
                if allowed_ids is not None and old_chat_id not in [str(x) for x in allowed_ids]:
                    st.error(t("This Legacy Chat ID is not authorized for migration."))
                    return
                # 3. Must actually exist in the database
                if not db.legacy_chat_id_exists(old_chat_id):
                    st.error(t("Legacy Chat ID not found."))
                    return
                # 4. Must not be claimed by any user yet (One-Time Claim protection)
                if db.is_user_id_claimed(old_chat_id):
                    st.error(t("This Legacy Chat ID is already linked to an account."))
                    return
                user_id = old_chat_id
            else:
                user_id = str(uuid.uuid4())
            
            new_user = User(
                username=username,
                user_id=user_id,
                password_hash=hash_password(password),
                created_at=datetime.now().isoformat()
            )
            
            if db.create_user(new_user):
                st.success(t("Registration successful! Please login."))
            else:
                st.error(t("Registration failed. Please try again."))

def auth_flow(db: DBHandler):
    if 'user' in st.session_state:
        return st.session_state['user']
    
    # Sidebar: Login & Register
    with st.sidebar:
        if os.path.exists("logo.png"):
            st.image("logo.png", width="stretch")
        st.title(t("Monthly Data Bot"))
        
        tab_login, tab_register = st.tabs([t("Login"), t("Register")])
        
        with tab_login:
            login_form(db)
        
        with tab_register:
            register_form(db)

    # Main Area: Description
    st.title(t("Welcome to Monthly Data Bot 📊"))
    
    st.markdown(t("HOME_PAGE_DESCRIPTION"))
    
    return None
