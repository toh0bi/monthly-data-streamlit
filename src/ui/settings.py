import streamlit as st
from src.data.db_handler import DBHandler
from src.data.models import User

def settings_page(db: DBHandler, user: User):
    st.header("Define Meter Types")
    
    st.subheader("Meter Types")
    current_types = db.get_meter_types(user.user_id)
    
    # Add new type
    with st.form("add_type_form"):
        new_type = st.text_input("Add new meter type (e.g. 'water', 'gas')")
        if st.form_submit_button("Add Type"):
            if new_type and new_type not in current_types:
                current_types.append(new_type)
                db.update_meter_types(user.user_id, current_types)
                st.success(f"Added {new_type}")
                st.rerun()
            
    # Configure existing types
    st.divider()
    st.write("Configure Existing Types")
    
    for m_type in current_types:
        if m_type == 'none': continue
        
        with st.expander(f"Configure: {m_type}"):
            col1, col2 = st.columns(2)
            
            # Unit
            current_unit = db.get_meter_config(user.user_id, m_type, 'unit') or ''
            new_unit = col1.text_input(f"Unit for {m_type}", value=current_unit, key=f"unit_{m_type}")
            
            # Evaluation Mode
            current_mode = db.get_meter_config(user.user_id, m_type, 'eval_mode') or 'difference'
            mode_options = {'difference': 'Cumulative (Difference)', 'absolute': 'Absolute (Average)'}
            # Reverse lookup for display
            display_options = list(mode_options.values())
            current_display = mode_options.get(current_mode, 'Cumulative (Difference)')
            
            new_display = col1.selectbox(
                f"Evaluation Mode for {m_type}", 
                display_options, 
                index=display_options.index(current_display),
                key=f"mode_{m_type}",
                help="Cumulative: Calculates consumption (e.g. Electricity). Absolute: Calculates average value (e.g. Temperature)."
            )
            
            # Map back to key
            new_mode = [k for k, v in mode_options.items() if v == new_display][0]

            if col1.button(f"Save Configuration", key=f"save_{m_type}"):
                db.update_meter_config(user.user_id, m_type, 'unit', new_unit)
                db.update_meter_config(user.user_id, m_type, 'eval_mode', new_mode)
                st.success("Saved")
                
            # Delete Type
            if col2.button(f"Delete {m_type}", type="primary", key=f"del_{m_type}"):
                current_types.remove(m_type)
                db.update_meter_types(user.user_id, current_types)
                st.warning(f"Deleted {m_type}")
                st.rerun()
