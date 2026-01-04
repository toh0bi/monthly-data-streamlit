import streamlit as st
from src.data.db_handler import DBHandler
from src.data.models import User

def settings_page(db: DBHandler, user: User):
    st.header("Define Meter Types")
    
    st.subheader("Add New Meter Type")
    
    # Add new type with config
    with st.form("add_type_form"):
        col1, col2, col3 = st.columns(3)
        new_type = col1.text_input("Name (e.g. 'water')")
        new_unit = col2.text_input("Unit (e.g. 'm³')")
        
        mode_options = {'difference': 'Cumulative (Difference)', 'absolute': 'Absolute (Average)'}
        new_mode_display = col3.selectbox("Type", list(mode_options.values()))
        new_mode = [k for k, v in mode_options.items() if v == new_mode_display][0]
        
        if st.form_submit_button("Add Type"):
            current_types = db.get_meter_types(user.user_id)
            if new_type and new_type not in current_types:
                # Add to list
                current_types.append(new_type)
                db.update_meter_types(user.user_id, current_types)
                
                # Save config
                if new_unit:
                    db.update_meter_config(user.user_id, new_type, 'unit', new_unit)
                db.update_meter_config(user.user_id, new_type, 'eval_mode', new_mode)
                
                st.success(f"Added {new_type}")
                st.rerun()
            elif new_type in current_types:
                st.error("Type already exists")
            
    # Configure existing types
    st.divider()
    st.subheader("Manage Existing Types")
    
    current_types = db.get_meter_types(user.user_id)
    
    for i, m_type in enumerate(current_types):
        if m_type == 'none': continue
        
        with st.expander(f"**{m_type}**", expanded=False):
            # 1. Reordering Controls
            c_up, c_down, c_fill = st.columns([1, 1, 2])
            with c_up:
                if i > 0:
                    if st.button("⬆️ Up", key=f"up_{m_type}", use_container_width=True):
                        current_types[i], current_types[i-1] = current_types[i-1], current_types[i]
                        db.update_meter_types(user.user_id, current_types)
                        st.rerun()
            with c_down:
                if i < len(current_types) - 1:
                    if st.button("⬇️ Down", key=f"down_{m_type}", use_container_width=True):
                        current_types[i], current_types[i+1] = current_types[i+1], current_types[i]
                        db.update_meter_types(user.user_id, current_types)
                        st.rerun()
            
            st.divider()

            # 2. Configuration
            col1, col2 = st.columns(2)
            
            # Unit
            current_unit = db.get_meter_config(user.user_id, m_type, 'unit') or ''
            new_unit = col1.text_input(f"Unit", value=current_unit, key=f"unit_{m_type}")
            
            # Evaluation Mode
            current_mode = db.get_meter_config(user.user_id, m_type, 'eval_mode') or 'difference'
            mode_options = {'difference': 'Cumulative (Difference)', 'absolute': 'Absolute (Average)'}
            display_options = list(mode_options.values())
            current_display = mode_options.get(current_mode, 'Cumulative (Difference)')
            
            new_display = col1.selectbox(
                f"Evaluation Mode", 
                display_options, 
                index=display_options.index(current_display),
                key=f"mode_{m_type}"
            )
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
