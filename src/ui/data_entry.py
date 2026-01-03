import streamlit as st
import pandas as pd
from src.data.db_handler import DBHandler
from src.data.models import User, MeterReading
from datetime import date

def data_entry_page(db: DBHandler, user: User):
    st.header("Data Entry")
    
    meter_types = db.get_meter_types(user.user_id)
    if not meter_types:
        st.warning("No meter types defined. Go to Settings to add one.")
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
            with st.expander("Add New Reading", expanded=True):
                with st.form(f"add_reading_form_{selected_type}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        reading_date = st.date_input("Date", value=date.today(), format="DD.MM.YYYY", key=f"date_{selected_type}")
                    with col2:
                        reading_value = st.number_input("Counter Value", min_value=0.0, step=0.1, format="%.2f", value=default_value, key=f"val_{selected_type}")
                    
                    submit = st.form_submit_button("Add Reading")
                    
                    if submit:
                        new_reading = MeterReading(
                            meter_type=selected_type,
                            meter_reading=reading_value,
                            reading_date=reading_date.strftime("%Y-%m-%d")
                        )
                        if db.add_reading(user.user_id, new_reading):
                            st.success("Reading added!")
                            st.rerun()
                        else:
                            st.error("Failed to add reading.")

            # View & Manage Data
            st.subheader(f"History: {selected_type}")
            
            if readings:
                # Convert to DataFrame for display
                df = pd.DataFrame([r.__dict__ for r in readings])
                df = df.sort_values('reading_date', ascending=False)
                
                # Display table
                st.dataframe(
                    df,
                    column_config={
                        "meter_type": None, # Hide
                        "reading_date": "Date",
                        "meter_reading": "Value"
                    },
                    use_container_width=True,
                    hide_index=True
                )
                
                st.divider()
                st.write("Delete Readings")
                
                # Multi-select for deletion
                options = {f"{r.reading_date}: {r.meter_reading}": r for r in readings}
                to_delete = st.multiselect("Select readings to delete", options.keys(), key=f"del_sel_{selected_type}")
                
                if to_delete:
                    if st.button("Delete Selected", key=f"del_btn_{selected_type}"):
                        for key in to_delete:
                            reading = options[key]
                            db.delete_reading(user.user_id, reading.meter_type, reading.reading_date)
                        st.success("Deleted!")
                        st.rerun()
                        
            else:
                st.info("No readings found.")
