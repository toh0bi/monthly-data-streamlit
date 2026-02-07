import streamlit as st
import bcrypt
import os
from src.data.db_handler import DBHandler
from src.data.models import User
from datetime import datetime
import uuid

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def login_form(db: DBHandler):
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")
        
        if submit:
            user = db.get_user(username)
            if user and check_password(password, user.password_hash):
                st.session_state['user'] = user
                st.success(f"Welcome back, {user.username}!")
                st.rerun()
            else:
                st.error("Invalid username or password")

def register_form(db: DBHandler):
    with st.form("register_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        password_confirm = st.text_input("Confirm Password", type="password")
        # Optional: Allow linking to old chat_id for migration
        old_chat_id = st.text_input("Legacy Chat ID (Optional)")
        
        submit = st.form_submit_button("Register")
        
        if submit:
            if password != password_confirm:
                st.error("Passwords do not match")
                return
            
            if db.get_user(username):
                st.error("Username already exists")
                return
            
            user_id = old_chat_id if old_chat_id else str(uuid.uuid4())
            
            new_user = User(
                username=username,
                user_id=user_id,
                password_hash=hash_password(password),
                created_at=datetime.now().isoformat()
            )
            
            if db.create_user(new_user):
                st.success("Registration successful! Please login.")
            else:
                st.error("Registration failed. Please try again.")

def auth_flow(db: DBHandler):
    if 'user' in st.session_state:
        return st.session_state['user']
    
    # Sidebar: Login & Register
    with st.sidebar:
        if os.path.exists("logo.png"):
            st.image("logo.png", width="stretch")
        st.title("Monthly Data Bot")
        
        tab_login, tab_register = st.tabs(["Login", "Register"])
        
        with tab_login:
            login_form(db)
        
        with tab_register:
            register_form(db)

    # Main Area: Description
    st.title("Welcome to Monthly Data Bot 📊")
    
    st.markdown("""
    ### Your Personal Data Tracker
    
    Keep track of any monthly data you care about:
    *   ⚡ **Utilities** (Electricity, Water, Gas, PV)
    *   💪 **Health** (Body Weight, Gym Visits)
    *   🌱 **Environment** (Rainfall, Temperature)
    *   💰 **Finance** (Savings, Expenses)
    
    **Features:**
    *   📅 **Easy Data Entry:** Smart forms adapt to your data types.
    *   📈 **Interactive Dashboards:** Visualize trends, seasonalities and compare years.
    *   🤖 **AI Analysis:** Chat with your data using advanced AI.
    *   📱 **Mobile Friendly:** Works great on your phone.
    
    👈 **Please log in or register in the sidebar to continue.**
    """)
    
    return None
