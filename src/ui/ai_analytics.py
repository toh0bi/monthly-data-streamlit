import streamlit as st
from datetime import datetime
from src.data.db_handler import DBHandler
from src.data.models import User
from src.logic.llm_client import LLMClient
from src.logic.analytics import calculate_all_monthly_series
from src.ui.i18n import t

QUOTA_LIMIT = 20  # Hard limit per user per month

def ai_analytics_page(db: DBHandler, user: User):
    st.header(t("🤖 Talk to your Data"))
    st.caption(t("Analyze your monthly data with AI support (Powered by AWS Bedrock / Claude Haiku 5.5)"))

    # --- Quota Check ---
    current_month_str = datetime.now().strftime("%Y-%m")
    
    # Check if we need to reset quota view for new month logic
    if user.quota_month != current_month_str:
        user_quota_used = 0 # Will be reset in DB on next write
    else:
        user_quota_used = user.ai_quota_used
        
    st.progress(min(user_quota_used / QUOTA_LIMIT, 1.0), 
                text=t("Monthly Quota: {}/{} requests", user_quota_used, QUOTA_LIMIT))

    if user_quota_used >= QUOTA_LIMIT:
        st.error(t("You have reached your monthly limit of {} requests. Come back next month!", QUOTA_LIMIT))
        return
    # -------------------

    # Reset Button
    if st.button(t("🗑️ Start new chat"), type="secondary", help=t("Clears the current chat history")):
        st.session_state.messages = []
        st.rerun()

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
        # Add an initial greeting
        st.session_state.messages.append({
            "role": "assistant", 
            "content": t("CHAT_GREETING")
        })

    # Initialize LLM Client (cached to avoid re-init per rerun)
    if "llm_client" not in st.session_state:
        # You might want to let the user configure the region in settings, but for now we default here
        st.session_state.llm_client = LLMClient(region_name="eu-central-1")

    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # React to user input
    if prompt := st.chat_input(t("Ask a question about your data...")):
        # Display user message in chat message container
        st.chat_message("user").markdown(prompt)
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Display assistant response in chat message container
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            message_placeholder.markdown(t("⏳ *Analyzing data...*"))
            
            try:
                # 1. Fetch Data
                metadata = db.get_user_metadata(user.user_id)
                meter_types = metadata['meter_types']
                configs = metadata['configs']
                data_summary = {}
                
                if not meter_types:
                    response_text = t("Unfortunately, I cannot find any meter data in your profile. Please add data in the dashboard first.")
                else:
                    all_monthly_dfs = calculate_all_monthly_series(db, user.user_id, meter_types, configs)
                    for mt in meter_types:
                        m_cfg = configs.get(mt, {})
                        unit = m_cfg.get('unit') or "Units"
                        eval_mode = m_cfg.get('eval_mode') or 'difference'
                        monthly_df = all_monthly_dfs.get(mt)
                        
                        if monthly_df is not None and not monthly_df.empty:
                            data_summary[mt] = {
                                "unit": unit,
                                "mode": eval_mode,
                                "df": monthly_df
                            }
                    
                    if not data_summary:
                        st.warning(t("Insufficient data available for analysis."))
                        st.stop()
                    
                    # 2. Format Data
                    context_data = st.session_state.llm_client.format_readings(data_summary)
                    
                    # 3. Call LLM with History
                    response_text = st.session_state.llm_client.query(st.session_state.messages, context_data)
                    
                    # 4. Update Quota
                    if user.quota_month != current_month_str:
                        db.reset_ai_quota(user.username, current_month_str)
                        user.quota_month = current_month_str
                        user.ai_quota_used = 1
                    else:
                        db.increment_ai_quota(user.username, current_month_str)
                        user.ai_quota_used += 1

                # Show result
                message_placeholder.markdown(response_text)
                st.session_state.messages.append({"role": "assistant", "content": response_text})
                
            except Exception as e:
                error_msg = f"Ein unerwarteter Fehler ist aufgetreten: {str(e)}"
                message_placeholder.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
