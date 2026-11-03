import streamlit as st
import json
import pandas as pd
from datetime import datetime
from src.data.db_handler import DBHandler
from src.data.models import User, MeterReading
from src.logic.llm_client import LLMClient
from src.ui.ai_analytics import QUOTA_LIMIT
from src.ui.i18n import t

def ai_data_entry_page(db: DBHandler, user: User):
    st.header(t("🤖 AI Data Import"))
    st.caption(t("Paste chaotic data simply via Copy & Paste. The AI structures it for you."))

    # --- Quota Check ---
    current_month_str = datetime.now().strftime("%Y-%m")
    if user.quota_month != current_month_str:
        user_quota_used = 0
    else:
        user_quota_used = user.ai_quota_used

    st.progress(min(user_quota_used / QUOTA_LIMIT, 1.0),
                text=t("Monthly Quota: {}/{} requests", user_quota_used, QUOTA_LIMIT))

    if user_quota_used >= QUOTA_LIMIT:
        st.error(t("You have reached your monthly limit of {} requests. Come back next month!", QUOTA_LIMIT))
        return
    # -------------------

    # Initialize LLM
    if "llm_client" not in st.session_state:
        st.session_state.llm_client = LLMClient(region_name="eu-central-1")

    col1, col2 = st.columns(2)
    
    with col1:
        # Input Area - Text
        raw_text = st.text_area(t("Paste data here (Excel, CSV, Notes...)"), height=200, 
                                placeholder=t("Example:\nJan 2023: Electricity 1050, Water 50\nFeb 2023: Electricity 1120, Water 52\n..."))
    
    with col2:
        # Input Area - Image
        uploaded_file = st.file_uploader(t("Or upload an image (Photo, Scan)"), type=['png', 'jpg', 'jpeg'])

    if st.button(t("Start AI Analysis"), type="primary"):
        if not raw_text.strip() and not uploaded_file:
            st.warning(t("Please enter text or upload an image."))
        else:
            with st.spinner(t("Analyzing data...")):
                metadata = db.get_user_metadata(user.user_id)
                configs = metadata['configs']
                meter_types = [
                    mt for mt in metadata['meter_types']
                    if configs.get(mt, {}).get('eval_mode') != 'formula'
                ]
                
                image_bytes = None
                media_type = "image/jpeg"
                
                if uploaded_file:
                    image_bytes = uploaded_file.getvalue()
                    media_type = uploaded_file.type
                
                json_str = st.session_state.llm_client.parse_smart_import(
                    raw_text, 
                    meter_types, 
                    image_data=image_bytes, 
                    media_type=media_type
                )
                
                try:
                    data = json.loads(json_str)
                    
                    # Check for explicit error from backend
                    if isinstance(data, dict) and "error" in data:
                        st.error(t("AI Error: {}", data['error']))
                    elif not data:
                        st.error(t("Could not find valid data."))
                    else:
                        if user.quota_month != current_month_str:
                            db.reset_ai_quota(user.username, current_month_str)
                            user.quota_month = current_month_str
                            user.ai_quota_used = 1
                        else:
                            db.increment_ai_quota(user.username, current_month_str)
                            user.ai_quota_used += 1

                        st.session_state.import_preview_data = data
                        st.success(t("{} records found!", len(data)))
                        
                except json.JSONDecodeError:
                    st.error(t("Error processing response: {}...", json_str[:100]))

    # Preview & Save Area
    if "import_preview_data" in st.session_state and st.session_state.import_preview_data:
        st.divider()
        st.subheader(t("Preview"))
        
        # Edit Dataframe allow
        df = pd.DataFrame(st.session_state.import_preview_data)
        edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True)
        
        col1, col2 = st.columns(2)
        with col1:
             if st.button(t("💾 Save All"), type="primary"):
                saved_count = 0
                current_types = db.get_meter_types(user.user_id)
                types_updated = False

                for _, row in edited_df.iterrows():
                    try:
                        m_type = str(row.get('meter_type', '')).strip()
                        val_raw = row.get('value')
                        date_raw = str(row.get('date', '')).strip()

                        if not m_type or val_raw is None or pd.isna(val_raw) or not date_raw:
                            continue

                        # Validate ISO date format
                        parsed_date = datetime.strptime(date_raw, "%Y-%m-%d").strftime("%Y-%m-%d")

                        reading = MeterReading(
                            meter_type=m_type,
                            meter_reading=float(val_raw),
                            reading_date=parsed_date
                        )
                        if db.add_reading(user.user_id, reading):
                            saved_count += 1
                            if m_type not in current_types:
                                current_types.append(m_type)
                                types_updated = True
                    except Exception as e:
                        st.error(t("Error at row {}: {}", row.to_dict(), e))
                
                if types_updated:
                    db.update_meter_types(user.user_id, current_types)

                st.success(t("{} records successfully saved!", saved_count))
                del st.session_state.import_preview_data # Clear
        
        with col2:
            if st.button(t("Cancel")):
                del st.session_state.import_preview_data
                st.rerun()
