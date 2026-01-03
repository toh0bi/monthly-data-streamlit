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
    result['month_name'] = result['date'].dt.strftime('%b') # Jan, Feb...
    result['month_index'] = result['date'].dt.month
    
    return result

def calculate_yearly_stats(readings: list[MeterReading], monthly_df: pd.DataFrame) -> pd.DataFrame:
    if not readings or monthly_df.empty:
        return pd.DataFrame()

    # 1. Data Points per year
    readings_df = pd.DataFrame([r.__dict__ for r in readings])
    readings_df['reading_date'] = pd.to_datetime(readings_df['reading_date'])
    readings_df['year'] = readings_df['reading_date'].dt.year
    
    stats = []
    years = sorted(readings_df['year'].unique())
    
    for year in years:
        # Filter readings for this year
        year_readings = readings_df[readings_df['year'] == year]
        data_points = len(year_readings)
        
        # Filter monthly consumption for this year
        year_monthly = monthly_df[monthly_df['year'] == year]
        total_consumption = year_monthly['consumption'].sum()
        
        # Avg Monthly (only count months that have data > 0 or exist in the range)
        # Using len(year_monthly) assumes we have rows for months. 
        # Note: resample('ME') creates rows for all months in range.
        # We should probably only count months that actually have consumption > 0 or are within the reading range.
        # Let's use the count of months where consumption > 0 for now, or just 12 if full year?
        # Legacy logic: months_with_data = len(monthly_data). 
        # In our case, year_monthly contains all months in the range.
        # Let's count months where consumption > 0.001 to avoid empty padding months if any
        active_months = len(year_monthly[year_monthly['consumption'] > 0])
        avg_monthly = total_consumption / active_months if active_months > 0 else 0
        
        # Avg Daily
        # Span = last reading of year - first reading of year (or Jan 1st?)
        # Legacy used: (last_date - first_date).days
        first_date = year_readings['reading_date'].min()
        last_date = year_readings['reading_date'].max()
        day_span = (last_date - first_date).days
        if day_span == 0: day_span = 1 # Avoid division by zero for single reading
        
        avg_daily = total_consumption / day_span if day_span > 0 else 0
        
        stats.append({
            'year': year,
            'data_points': data_points,
            'total_consumption': total_consumption,
            'avg_monthly': avg_monthly,
            'avg_daily': avg_daily
        })
        
    return pd.DataFrame(stats)
