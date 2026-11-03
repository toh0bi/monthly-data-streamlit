import streamlit as st
import pandas as pd
import altair as alt
from src.data.db_handler import DBHandler
from src.data.models import User
from src.logic.analytics import (
    calculate_all_monthly_series,
    calculate_yearly_stats,
    calculate_formula_yearly_stats
)
from src.ui.i18n import t

def dashboard_page(db: DBHandler, user: User):
    st.header(t("Dashboard"))
    
    metadata = db.get_user_metadata(user.user_id)
    meter_types = metadata['meter_types']
    configs = metadata['configs']

    if not meter_types:
        st.warning(t("No data."))
        return

    all_monthly_dfs = calculate_all_monthly_series(db, user.user_id, meter_types, configs)
        
    # Tabs for each meter type
    tabs = st.tabs(meter_types)
    
    for i, m_type in enumerate(meter_types):
        with tabs[i]:
            # Get config from prefetched metadata
            m_cfg = configs.get(m_type, {})
            eval_mode = m_cfg.get('eval_mode') or 'difference'
            unit = m_cfg.get('unit') or "Units"
            formula = m_cfg.get('formula') or ""

            if eval_mode == 'formula':
                if formula:
                    st.caption(f"🧮 {t('Formula')}: `{formula}`")
                readings = []
                monthly_df = all_monthly_dfs.get(m_type, pd.DataFrame())
            else:
                readings = db.get_readings(user.user_id, m_type)
                if not readings:
                    st.info(t("No readings."))
                    continue
                monthly_df = all_monthly_dfs.get(m_type, pd.DataFrame())
            
            if monthly_df.empty:
                st.info(t("Not enough data to calculate consumption."))
                continue

            # Year Slider Filter
            min_year = int(monthly_df['year'].min())
            max_year = int(monthly_df['year'].max())
            
            selected_years = (min_year, max_year)
            if min_year < max_year:
                selected_years = st.slider(
                    t("Filter Years"),
                    min_value=min_year,
                    max_value=max_year,
                    value=(min_year, max_year),
                    key=f"year_slider_{m_type}"
                )
            
            # Filter monthly_df based on selection (use .copy() to avoid SettingWithCopyWarning)
            monthly_df = pd.DataFrame(monthly_df[
                (monthly_df['year'] >= selected_years[0]) & 
                (monthly_df['year'] <= selected_years[1])
            ]).copy()
            
            if monthly_df.empty:
                st.info(t("No data in selected range."))
                continue
                
            # Dynamic Title based on mode
            # "Consumption" generalized to "Monthly Total" (for diffs/formulas) and "Value" (for absolute)
            value_label = "Value" if eval_mode == 'absolute' else "Monthly Total"
            
            # --- 1. Charts ---
            st.subheader(f"{t('Monthly')} {t(value_label)} ({unit})")
            
            # View Selection
            view_mode = st.radio(
                t("View Mode"), 
                ["Year-over-Year", "Linear Trend"], 
                horizontal=True, 
                key=f"view_{m_type}", 
                label_visibility="collapsed",
                format_func=lambda x: t(x)
            )

            # Translate Data for Chart
            monthly_df['month_name'] = monthly_df['month_name'].apply(lambda x: t(x))
            # Tooltip Date Format
            monthly_df['month_str_pretty'] = monthly_df['date'].dt.strftime('%b %Y') # Still English here if locale is EN
            
            if view_mode == "Year-over-Year":
                # We want X=Month (Jan, Feb...), Y=Consumption, Color=Year
                # Ensure month_index is sorted correctly
                line_chart = alt.Chart(monthly_df).mark_line(point=True).encode(
                    x=alt.X('month_name', sort=alt.EncodingSortField(field="month_index", order="ascending"), title=t('Month')),
                    y=alt.Y('consumption', title=f'{t(value_label)} ({unit})'),
                    color=alt.Color('year:O', title=t('Year'), scale=alt.Scale(scheme='category10')), # High contrast colors
                    tooltip=[alt.Tooltip('year', title=t('Year')), alt.Tooltip('month_name', title=t('Month')), alt.Tooltip('consumption', title=t(value_label))]
                ).interactive()
                
                st.altair_chart(line_chart, use_container_width=True)
                
            else:
                # Linear Trend with Regression
                base = alt.Chart(monthly_df).encode(
                    x=alt.X('date:T', title=t('Date'), axis=alt.Axis(format='%b %Y', labelAngle=-45)),
                    y=alt.Y('consumption', title=f'{t(value_label)} ({unit})'),
                    tooltip=[alt.Tooltip('month_str', title=t('Month')), alt.Tooltip('consumption', title=t(value_label))]
                )
                
                line = base.mark_line(point=True)
                
                # Regression Line
                trend = base.transform_regression(
                    'date', 'consumption', method="linear"
                ).mark_line(
                    color='red', 
                    strokeDash=[5, 5],
                    strokeWidth=2
                )
                
                st.altair_chart((line + trend).interactive(), use_container_width=True)
            
            # --- 2. Yearly Stats ---
            st.subheader(t("Yearly Statistics"))
            if eval_mode == 'formula':
                stats_df = calculate_formula_yearly_stats(monthly_df)
            else:
                stats_df = calculate_yearly_stats(readings, monthly_df, eval_mode)
            
            if not stats_df.empty:
                # Apply filter to stats as well
                stats_df = stats_df.loc[
                    (stats_df['year'] >= selected_years[0]) & 
                    (stats_df['year'] <= selected_years[1])
                ]

                for _, row in stats_df.iterrows():
                    year = int(row['year'])
                    with st.expander(t("Year {}", year), expanded=False):
                        if eval_mode == 'absolute':
                            c1, c2 = st.columns(2)
                            c1.metric(t("Data Points"), int(row['data_points']))
                            c2.metric(t("Avg Monthly"), f"{row['avg_monthly']:.1f} {unit}")
                            
                            c3, c4 = st.columns(2)
                            c3.metric(t("Min"), f"{row['min_value']:.1f} {unit}")
                            c4.metric(t("Max"), f"{row['max_value']:.1f} {unit}")
                        else:
                            # Use 2x2 grid for better mobile responsiveness
                            c1, c2 = st.columns(2)
                            c1.metric(t("Data Points"), int(row['data_points']))
                            c2.metric(t("Total"), f"{row['total_consumption']:.1f} {unit}")
                            
                            c3, c4 = st.columns(2)
                            c3.metric(t("Avg Monthly"), f"{row['avg_monthly']:.1f} {unit}")
                            c4.metric(t("Avg Daily"), f"{row['avg_daily']:.1f} {unit}")

