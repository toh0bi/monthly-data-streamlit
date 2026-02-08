import streamlit as st
import pandas as pd
from src.data.db_handler import DBHandler
from src.data.models import User, MeterReading
from src.ui.i18n import t
from datetime import date

def data_entry_page(db: DBHandler, user: User):
    st.header(t("Data Entry"))
    
    meter_types = db.get_meter_types(user.user_id)
    if not meter_types:
        st.warning(t("No meter types defined. Go to Settings to add one."))
        return

    # Use Tabs for navigation
    tabs = st.tabs(meter_types)
    
    for i, selected_type in enumerate(meter_types):
        with tabs[i]:
            # Fetch readings for this type
            readings = db.get_readings(user.user_id, selected_type)
            
            # Determine default value (last reading)
            default_value = 0.0
            if readings:
                # Sort by date descending
                sorted_readings = sorted(readings, key=lambda x: x.reading_date, reverse=True)
                default_value = sorted_readings[0].meter_reading

            # Add New Reading Form
            st.subheader(t("Add New Reading"))
            with st.form(f"add_reading_form_{selected_type}"):
                col1, col2 = st.columns(2)
                with col1:
                    reading_date = st.date_input(t("Date"), value=date.today(), format="DD.MM.YYYY", key=f"date_{selected_type}")
                with col2:
                    reading_value = st.number_input(t("Counter Value"), min_value=0.0, step=0.1, format="%.2f", value=default_value, key=f"val_{selected_type}")
                
                submit = st.form_submit_button(t("Add Reading"))
                
                if submit:
                    new_reading = MeterReading(
                        meter_type=selected_type,
                        meter_reading=reading_value,
                        reading_date=reading_date.strftime("%Y-%m-%d")
                    )
                    if db.add_reading(user.user_id, new_reading):
                        st.success(t("Reading added!"))
                        st.rerun()
                    else:
                        st.error(t("Failed to add reading."))

            # View & Manage Data
            st.subheader(t("History: {}", selected_type))
            
            if readings:
                # Convert to DataFrame for display
                df = pd.DataFrame([r.__dict__ for r in readings])
                df = df.sort_values('reading_date', ascending=False)
                
                # Display table with selection
                event = st.dataframe(
                    df,
                    column_config={
                        "meter_type": None, # Hide
                        "reading_date": t("Date"),
                        "meter_reading": t("Value")
                    },
                    width="stretch",
                    hide_index=True,
                    on_select="rerun",
                    selection_mode="multi-row",
                    key=f"history_{selected_type}"
                )
                
                # CSV Download Button
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label=t("📥 Download {} History (CSV)", selected_type),
                    data=csv,
                    file_name=f"{selected_type}_history.csv",
                    mime="text/csv",
                    key=f"dl_{selected_type}"
                )
                
                # Handle deletion of selected rows
                if len(event.selection.rows) > 0:
                    st.caption(t("{} readings selected", len(event.selection.rows)))
                    if st.button(t("🗑️ Delete Selected"), key=f"del_btn_{selected_type}", type="primary"):
                        # Get data to delete using iloc with the selected indices
                        rows_to_delete = df.iloc[event.selection.rows]
                        
                        for _, row in rows_to_delete.iterrows():
                            db.delete_reading(user.user_id, row['meter_type'], row['reading_date'])
                        
                        st.success(t("Deleted!"))
                        st.rerun()
                        
            else:
                st.info(t("No readings found."))
