import streamlit as st
import altair as alt
from src.data.db_handler import DBHandler
from src.data.models import User
from src.logic.analytics import calculate_monthly_consumption, calculate_yearly_stats

def dashboard_page(db: DBHandler, user: User):
    st.header("Dashboard")
    
    meter_types = db.get_meter_types(user.user_id)
    if not meter_types:
        st.warning("No data.")
        return
        
    # Tabs for each meter type
    tabs = st.tabs(meter_types)
    
    for i, m_type in enumerate(meter_types):
        with tabs[i]:
            readings = db.get_readings(user.user_id, m_type)
            if not readings:
                st.info("No readings.")
                continue
            
            # Get config
            eval_mode = db.get_meter_config(user.user_id, m_type, 'eval_mode') or 'difference'
            unit = db.get_meter_config(user.user_id, m_type, 'unit') or "Units"
            
            monthly_df = calculate_monthly_consumption(readings, eval_mode)
            
            if monthly_df.empty:
                st.info("Not enough data to calculate consumption.")
                continue
                
            # Dynamic Title based on mode
            value_label = "Consumption" if eval_mode == 'difference' else "Average Value"
            
            # --- 1. Multi-Year Line Chart ---
            st.subheader(f"Monthly {value_label} ({unit})")
            
            # We want X=Month (Jan, Feb...), Y=Consumption, Color=Year
            # Ensure month_index is sorted correctly
            line_chart = alt.Chart(monthly_df).mark_line(point=True).encode(
                x=alt.X('month_name', sort=['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'], title='Month'),
                y=alt.Y('consumption', title=f'{value_label} ({unit})'),
                color=alt.Color('year:O', title='Year', scale=alt.Scale(scheme='category10')), # High contrast colors
                tooltip=['year', 'month_name', 'consumption']
            ).interactive()
            
            st.altair_chart(line_chart, width="stretch")
            
            # --- 2. Yearly Stats ---
            st.subheader("Yearly Statistics")
            stats_df = calculate_yearly_stats(readings, monthly_df)
            
            if not stats_df.empty:
                for _, row in stats_df.iterrows():
                    year = int(row['year'])
                    with st.expander(f"Year {year}", expanded=True):
                        # Use 2x2 grid for better mobile responsiveness
                        c1, c2 = st.columns(2)
                        c1.metric("Data Points", int(row['data_points']))
                        c2.metric("Total", f"{row['total_consumption']:.1f} {unit}")
                        
                        c3, c4 = st.columns(2)
                        c3.metric("Avg Monthly", f"{row['avg_monthly']:.1f} {unit}")
                        c4.metric("Avg Daily", f"{row['avg_daily']:.1f} {unit}")

