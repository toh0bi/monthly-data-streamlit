import pandas as pd
from src.data.models import MeterReading

def process_readings(readings: list[MeterReading]) -> pd.DataFrame:
    if not readings:
        return pd.DataFrame()
    
    df = pd.DataFrame([r.__dict__ for r in readings])
    df['reading_date'] = pd.to_datetime(df['reading_date'])
    df = df.sort_values('reading_date')
    
    # Calculate consumption
    df['prev_date'] = df['reading_date'].shift(1)
    df['prev_reading'] = df['meter_reading'].shift(1)
    df['days_diff'] = (df['reading_date'] - df['prev_date']).dt.days
    df['reading_diff'] = df['meter_reading'] - df['prev_reading']
    
    # Handle resets (negative diff) - simplified
    mask_reset = df['reading_diff'] < 0
    df.loc[mask_reset, 'reading_diff'] = 0 
    
    df['daily_avg'] = df['reading_diff'] / df['days_diff']
    
    return df

def calculate_monthly_consumption(readings: list[MeterReading], eval_mode: str = 'difference') -> pd.DataFrame:
    if not readings:
        return pd.DataFrame()
        
    df = process_readings(readings)
    if df.empty:
        return pd.DataFrame(columns=['date', 'consumption', 'month_str'])

    # Create a daily range from min to max date
    min_date = df['reading_date'].min()
    max_date = df['reading_date'].max()
    
    daily_idx = pd.date_range(start=min_date, end=max_date, freq='D')
    
    if eval_mode == 'absolute':
        # Absolute Mode: Interpolate values between readings
        # 1. Create a Series with known values at known dates
        known_series = df.set_index('reading_date')['meter_reading']
        # 2. Reindex to daily (this introduces NaNs)
        daily_series = known_series.reindex(daily_idx)
        # 3. Interpolate to fill NaNs
        daily_series = daily_series.interpolate(method='linear')
        # 4. Resample to Month End and take MEAN
        monthly = daily_series.resample('ME').mean()
        
    else:
        # Difference Mode: Spread consumption over days
        if len(df) < 2:
             return pd.DataFrame(columns=['date', 'consumption', 'month_str'])
             
        daily_series = pd.Series(0.0, index=daily_idx)
        
        for _, row in df.iterrows():
            if pd.isna(row['prev_date']):
                continue
                
            start_date = row['prev_date']
            end_date = row['reading_date']
            daily_rate = row['daily_avg']
            
            if pd.isna(daily_rate):
                continue

            # Assign rate to days > start_date and <= end_date
            mask = (daily_series.index > start_date) & (daily_series.index <= end_date)
            daily_series.loc[mask] = daily_rate
            
        # Resample to Month End and take SUM
        monthly = daily_series.resample('ME').sum()
    
    # Format for chart
    result = monthly.reset_index()
    result.columns = ['date', 'consumption']
    result['month_str'] = result['date'].dt.strftime('%Y-%m')
    result['year'] = result['date'].dt.year
    
    # Ensure English month names regardless of system locale
    english_months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    result['month_index'] = result['date'].dt.month
    # dt.month is 1-based (Jan=1), list is 0-based
    result['month_name'] = result['month_index'].apply(lambda x: english_months[x-1])
    
    return result

def calculate_yearly_stats(readings: list[MeterReading], monthly_df: pd.DataFrame) -> pd.DataFrame:
    if not readings or monthly_df.empty:
        return pd.DataFrame()

    # 1. Data Points per year
    readings_df = pd.DataFrame([r.__dict__ for r in readings])
    readings_df['reading_date'] = pd.to_datetime(readings_df['reading_date'])
    readings_df['year'] = readings_df['reading_date'].dt.year
    
    # Get intervals for accurate daily avg calculation
    intervals_df = process_readings(readings)
    
    stats = []
    # Sort years descending
    years = sorted(readings_df['year'].unique(), reverse=True)
    
    for year in years:
        # Filter readings for this year
        year_readings = readings_df[readings_df['year'] == year]
        data_points = len(year_readings)
        
        # Filter monthly consumption for this year
        year_monthly = monthly_df[monthly_df['year'] == year]
        total_consumption = year_monthly['consumption'].sum()
        
        # Avg Monthly
        active_months = len(year_monthly[year_monthly['consumption'] > 0])
        avg_monthly = total_consumption / active_months if active_months > 0 else 0
        
        # Avg Daily - calculate active days allocated to this year
        active_days = 0
        year_start = pd.Timestamp(year=year, month=1, day=1)
        year_end = pd.Timestamp(year=year, month=12, day=31)
        # We start counting from (year_start - 1 day) effectively for the interval logic
        # Interval (D0, D1]. Days = D1 - D0.
        # Intersect with [Jan 1, Dec 31].
        # Is equivalent to Intersect (D0, D1] with (Dec 31 Prev, Dec 31 Curr].
        year_start_limit = year_start - pd.Timedelta(days=1)
        
        if not intervals_df.empty:
            for _, row in intervals_df.iterrows():
                if pd.isna(row['prev_date']):
                    continue
                
                # Interval: (prev_date, reading_date]
                p_date = row['prev_date']
                r_date = row['reading_date']
                
                # Check for overlap
                if r_date <= year_start_limit or p_date >= year_end:
                    continue
                
                # Calculate overlap
                eff_start = max(p_date, year_start_limit)
                eff_end = min(r_date, year_end)
                
                days = (eff_end - eff_start).days
                if days > 0:
                    active_days += days
        
        if active_days == 0:
             active_days = 1 # Avoid division by zero
        
        avg_daily = total_consumption / active_days if active_days > 0 else 0
        
        stats.append({
            'year': year,
            'data_points': data_points,
            'total_consumption': total_consumption,
            'avg_monthly': avg_monthly,
            'avg_daily': avg_daily
        })
        
    return pd.DataFrame(stats)
