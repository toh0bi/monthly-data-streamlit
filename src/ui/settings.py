import streamlit as st
from src.data.db_handler import DBHandler
from src.data.models import User
from src.logic.analytics import validate_formula
from src.ui.i18n import t

def _append_to_formula_state(state_key: str, token: str):
    current = st.session_state.get(state_key, "")
    if current and not current.endswith(" "):
        st.session_state[state_key] = f"{current} {token}"
    else:
        st.session_state[state_key] = f"{current}{token}"

def _render_formula_builder(state_key: str, available_series: list[str], key_prefix: str):
    if state_key not in st.session_state:
        st.session_state[state_key] = ""

    st.caption(t("Click to insert data series or operators into the formula:"))

    if available_series:
        cols = st.columns(min(len(available_series), 4))
        for idx, s_name in enumerate(available_series):
            with cols[idx % len(cols)]:
                st.button(
                    f"➕ [{s_name}]",
                    key=f"{key_prefix}_var_{s_name}",
                    use_container_width=True,
                    on_click=_append_to_formula_state,
                    args=(state_key, f"[{s_name}]")
                )
    else:
        st.info(t("Create at least one data series first to use in a formula."))

    op_cols = st.columns(6)
    operators = ["+", "-", "*", "/", "(", ")"]
    for idx, op in enumerate(operators):
        with op_cols[idx]:
            st.button(
                op,
                key=f"{key_prefix}_op_{idx}",
                use_container_width=True,
                on_click=_append_to_formula_state,
                args=(state_key, op)
            )

    st.text_input(
        t("Formula (e.g. [Main Meter] - [Sub Meter] + 2 * [Solar])"),
        key=state_key,
        placeholder="[Electricity] - [Heatpump]"
    )
    st.caption(t("FORMULA_HELP_TEXT"))

def settings_page(db: DBHandler, user: User):
    st.header(t("Define Data Series"))
    st.caption(t("Here you can define what kind of data you want to track. This can be utility meters (electricity, water), personal metrics (weight, rainfall) or calculated series based on formulas."))
    
    if st.session_state.pop("_clear_new_series_inputs", False):
        st.session_state["new_series_name"] = ""
        st.session_state["new_series_unit"] = ""
        st.session_state["new_series_formula"] = ""

    metadata = db.get_user_metadata(user.user_id)
    current_types = [mt for mt in metadata['meter_types'] if mt != 'none']
    configs = metadata['configs']

    st.subheader(t("Add New Data Series"))
    
    # Tooltip for the mode
    mode_help = f"""
    **{t("Counter / Accumulating")}**: 
    {t("MODE_HELP_COUNTER")}

    **{t("Direct Value / Measurement")}**: 
    {t("MODE_HELP_DIRECT")}

    **{t("Calculated (Formula)")}**: 
    {t("MODE_HELP_FORMULA")}
    """

    mode_options = {
        'difference': f"📈 {t('Counter / Accumulating')}",
        'absolute': f"📏 {t('Direct Value')}",
        'formula': f"🧮 {t('Calculated (Formula)')}"
    }

    selected_mode = st.pills(
        t("Type"),
        options=list(mode_options.keys()),
        default='difference',
        format_func=lambda k: mode_options[k],
        help=mode_help,
        key="new_series_mode_pills"
    ) or 'difference'

    col1, col2 = st.columns(2)
    new_type = col1.text_input(t("Name (e.g. 'Weight', 'Electricity')"), key="new_series_name").strip()
    new_unit = col2.text_input(t("Unit (e.g. 'kg', 'kWh')"), key="new_series_unit").strip()

    if selected_mode == 'formula':
        _render_formula_builder("new_series_formula", current_types, "add_builder")

    if st.button(t("Add Data Series"), type="primary"):
        if not new_type:
            st.error(t("Please enter a name."))
        elif new_type in current_types:
            st.error(t("Data series already exists"))
        else:
            formula_str = st.session_state.get("new_series_formula", "").strip() if selected_mode == 'formula' else ""
            if selected_mode == 'formula':
                is_valid, err_msg = validate_formula(formula_str, current_types, self_name=new_type)
                if not is_valid:
                    st.error(t(err_msg))
                    st.stop()

            current_types.append(new_type)
            db.update_meter_types(user.user_id, current_types)

            if new_unit:
                db.update_meter_config(user.user_id, new_type, 'unit', new_unit)
            db.update_meter_config(user.user_id, new_type, 'eval_mode', selected_mode)
            if selected_mode == 'formula':
                db.update_meter_config(user.user_id, new_type, 'formula', formula_str)

            st.session_state["_clear_new_series_inputs"] = True
            st.success(t("Added {}", new_type))
            st.rerun()
            
    # Configure existing types
    st.divider()
    st.subheader(t("Manage Existing Data Series"))
    
    for i, m_type in enumerate(current_types):
        if m_type == 'none':
            continue
        
        m_cfg = configs.get(m_type, {})
        current_mode = m_cfg.get('eval_mode') or 'difference'
        badge = "🧮 " if current_mode == 'formula' else ""

        with st.expander(f"**{badge}{m_type}**", expanded=False):
            # 1. Reordering Controls
            c_up, c_down, _ = st.columns([1, 1, 2])
            with c_up:
                if i > 0:
                    if st.button(t("⬆️ Up"), key=f"up_{m_type}", use_container_width=True):
                        current_types[i], current_types[i-1] = current_types[i-1], current_types[i]
                        db.update_meter_types(user.user_id, current_types)
                        st.rerun()
            with c_down:
                if i < len(current_types) - 1:
                    if st.button(t("⬇️ Down"), key=f"down_{m_type}", use_container_width=True):
                        current_types[i], current_types[i+1] = current_types[i+1], current_types[i]
                        db.update_meter_types(user.user_id, current_types)
                        st.rerun()
            
            st.divider()

            # 2. Configuration
            new_mode = st.pills(
                t("Evaluation Mode"),
                options=list(mode_options.keys()),
                default=current_mode if current_mode in mode_options else 'difference',
                format_func=lambda k: mode_options[k],
                key=f"mode_pills_{m_type}",
                help=mode_help
            ) or current_mode

            col1, col2 = st.columns(2)
            current_unit = m_cfg.get('unit') or ''
            new_unit = col1.text_input(t("Unit"), value=current_unit, key=f"unit_{m_type}").strip()

            formula_state_key = f"formula_edit_{m_type}"
            if formula_state_key not in st.session_state:
                st.session_state[formula_state_key] = m_cfg.get('formula') or ''

            if new_mode == 'formula':
                other_series = [s for s in current_types if s != m_type]
                _render_formula_builder(formula_state_key, other_series, f"edit_builder_{m_type}")

            btn_col1, btn_col2 = st.columns(2)
            if btn_col1.button(t("Save Configuration"), key=f"save_{m_type}"):
                if new_mode == 'formula':
                    edited_formula = st.session_state.get(formula_state_key, "").strip()
                    other_series = [s for s in current_types if s != m_type]
                    is_valid, err_msg = validate_formula(edited_formula, other_series, self_name=m_type)
                    if not is_valid:
                        st.error(t(err_msg))
                        st.stop()
                    db.update_meter_config(user.user_id, m_type, 'formula', edited_formula)

                db.update_meter_config(user.user_id, m_type, 'unit', new_unit)
                db.update_meter_config(user.user_id, m_type, 'eval_mode', new_mode)
                st.success(t("Saved"))
                st.rerun()
                
            # Delete Type
            if btn_col2.button(t("Delete {}", m_type), type="primary", key=f"del_{m_type}"):
                current_types.remove(m_type)
                db.delete_meter_category(user.user_id, m_type, current_types)
                st.warning(t("Deleted {}", m_type))
                st.rerun()

    # System / Usage Stats
    st.divider()
    st.subheader(t("System & Quota"))
    st.caption(f"{t('Logged in as')}: {user.username}")
    
    col_q1, col_q2 = st.columns(2)
    col_q1.metric(t("AI Requests Used (Month)"), f"{user.ai_quota_used} / 50")
    col_q2.metric(t("Data Series"), len(current_types))
