import streamlit as st
import json
import pandas as pd
from src.data.db_handler import DBHandler
from src.data.models import User, MeterReading
from src.logic.llm_client import LLMClient

def ai_data_entry_page(db: DBHandler, user: User):
    st.header("🤖 AI Data Import")
    st.caption("Füge chaotische Daten einfach per Copy & Paste ein. Die KI strukturiert sie für dich.")

    # Initialize LLM
    if "llm_client" not in st.session_state:
        st.session_state.llm_client = LLMClient(region_name="eu-central-1")

    # Input Area
    raw_text = st.text_area("Daten hier einfügen (Excel, CSV, Notizen...)", height=200, 
                            placeholder="Beispiel:\nJan 2023: Strom 1050, Wasser 50\nFeb 2023: Strom 1120, Wasser 52\n...")

    if st.button("KI-Analyse starten", type="primary"):
        if not raw_text.strip():
            st.warning("Bitte gib erst Text ein.")
        else:
            with st.spinner("Analysiere Struktur..."):
                meter_types = db.get_meter_types(user.user_id)
                json_str = st.session_state.llm_client.parse_smart_import(raw_text, meter_types)
                
                try:
                    data = json.loads(json_str)
                    if not data:
                        st.error("Konnte keine gültigen Daten finden.")
                    else:
                        st.session_state.import_preview_data = data
                        st.success(f"{len(data)} Datensätze gefunden!")
                except json.JSONDecodeError:
                    st.error("Fehler beim Verarbeiten der KI-Antwort.")

    # Preview & Save Area
    if "import_preview_data" in st.session_state and st.session_state.import_preview_data:
        st.divider()
        st.subheader("Vorschau")
        
        # Edit Dataframe allow
        df = pd.DataFrame(st.session_state.import_preview_data)
        edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True)
        
        col1, col2 = st.columns(2)
        with col1:
             if st.button("💾 Alle speichern", type="primary"):
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
                        st.error(f"Fehler bei Zeile {row}: {e}")
                
                st.success(f"{saved_count} Einträge erfolgreich gespeichert!")
                del st.session_state.import_preview_data # Clear
                # Refresh meter types if new ones appeared (optional logic)
        
        with col2:
            if st.button("Abbrechen"):
                del st.session_state.import_preview_data
                st.rerun()
