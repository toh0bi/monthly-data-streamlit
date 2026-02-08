import streamlit as st
import json
import pandas as pd
from src.data.db_handler import DBHandler
from src.data.models import User, MeterReading
from src.logic.llm_client import LLMClient
from src.ui.i18n import t

def ai_data_entry_page(db: DBHandler, user: User):
    st.header(t("🤖 AI Data Import"))
    st.caption(t("Paste chaotic data simply via Copy & Paste. The AI structures it for you."))

    # Initialize LLM
    if "llm_client" not in st.session_state:
        st.session_state.llm_client = LLMClient(region_name="eu-central-1")

    # Input Area
    raw_text = st.text_area(t("Paste data here (Excel, CSV, Notes...)"), height=200, 
                            placeholder=t("Example:\nJan 2023: Electricity 1050, Water 50\nFeb 2023: Electricity 1120, Water 52\n..."))

    if st.button(t("Start AI Analysis"), type="primary"):
        if not raw_text.strip():
            st.warning(t("Please enter text first."))
        else:
            with st.spinner(t("Analyzing structure...")):
                meter_types = db.get_meter_types(user.user_id)
                json_str = st.session_state.llm_client.parse_smart_import(raw_text, meter_types)
                
                try:
                    data = json.loads(json_str)
                    
                    # Check for explicit error from backend
                    if isinstance(data, dict) and "error" in data:
                        st.error(t("AI Error: {}", data['error']))
                    elif not data:
                        st.error(t("Could not find valid data."))
                    else:
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
                for _, row in edited_df.iterrows():
                    # Create Reading Object
                    try:
                        reading = MeterReading(
                            meter_type=str(row['meter_type']),
                            meter_reading=float(row['value']),
                            reading_date=str(row['date'])
                        )
                        # Save to DB
                        if db.add_reading(user.user_id, reading):
                            saved_count += 1
                    except Exception as e:
                        st.error(t("Error at row {}: {}", row, e))
                
                st.success(t("{} records successfully saved!", saved_count))
                del st.session_state.import_preview_data # Clear
                # Refresh meter types if new ones appeared (optional logic)
        
        with col2:
            if st.button(t("Cancel")):
                del st.session_state.import_preview_data
                st.rerun()
