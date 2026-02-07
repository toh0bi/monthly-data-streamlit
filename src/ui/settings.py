import streamlit as st
from src.data.db_handler import DBHandler
from src.data.models import User

def settings_page(db: DBHandler, user: User):
    st.header("Define Data Categories")
    st.caption("Here you can define what kind of data you want to track. This can be utility meters (electricity, water) or personal metrics (weight, rainfall, etc.).")
    
    st.subheader("Add New Category")
    
    # Tooltip for the mode
    mode_help = """
    **Counter / Accumulating**: 
    Use this for meters that simply count up (like Electricity, Gas, Water meters). 
    The app will calculate the monthly usage by subtracting the previous month's value from the current reading.

    **Direct Value / Measurement**: 
    Use this for data where the value itself is what you want to track for that month.
    Examples: Body Weight (kg), Rainfall (mm), Average Temperature (°C), Bank Account Balance (€).
    """

    mode_options = {
        'difference': 'Counter / Accumulating (Calculates Difference)', 
        'absolute': 'Direct Value (Takes Value as is)'
    }

    # Add new type with config
    with st.form("add_type_form"):
        col1, col2, col3 = st.columns(3)
        new_type = col1.text_input("Name (e.g. 'Weight', 'Electricity')")
        new_unit = col2.text_input("Unit (e.g. 'kg', 'kWh')")
        
        new_mode_display = col3.selectbox(
            "Type", 
            list(mode_options.values()),
            help=mode_help
        )
        new_mode = [k for k, v in mode_options.items() if v == new_mode_display][0]
        
        if st.form_submit_button("Add Category"):
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
                st.error("Category already exists")
            
    # Configure existing types
    st.divider()
    st.subheader("Manage Existing Categories")
    
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
            
            # Re-using the options defined above for consistency
            mode_options = {
                'difference': 'Counter / Accumulating (Calculates Difference)', 
                'absolute': 'Direct Value (Takes Value as is)'
            }
            display_options = list(mode_options.values())
            current_display = mode_options.get(current_mode, mode_options['difference'])
            
            new_display = col1.selectbox(
                f"Evaluation Mode", 
                display_options, 
                index=display_options.index(current_display),
                key=f"mode_{m_type}",
                help="Select 'Counter' for increasing meters (utilities) or 'Direct Value' for measurements (weight, temp)."
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

    # System / Usage Stats
    st.divider()
    st.subheader("System & Quota")
    st.caption(f"Logged in as: {user.username}")
    
    col_q1, col_q2 = st.columns(2)
    col_q1.metric("AI Requests Used (Month)", f"{user.ai_quota_used} / 50")
    col_q2.metric("Data Categories", len(current_types))
