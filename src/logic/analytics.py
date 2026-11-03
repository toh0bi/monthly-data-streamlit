import ast
import calendar
import operator
import re
import pandas as pd
from src.data.models import MeterReading

def process_readings(readings: list[MeterReading]) -> pd.DataFrame:
    if not readings:
        return pd.DataFrame()
    
    df = pd.DataFrame([r.__dict__ for r in readings])
    df['reading_date'] = pd.to_datetime(df['reading_date'])
    # Deduplicate same-day readings (keep latest entry) and sort chronologically
    df = df.sort_values('reading_date').drop_duplicates(subset=['reading_date'], keep='last').reset_index(drop=True)
    
    # Calculate consumption
    df['prev_date'] = df['reading_date'].shift(1)
    df['prev_reading'] = df['meter_reading'].shift(1)
    df['days_diff'] = (df['reading_date'] - df['prev_date']).dt.days
    df['reading_diff'] = df['meter_reading'] - df['prev_reading']
    
    # Handle resets (negative diff) - simplified
    mask_reset = df['reading_diff'] < 0
    df.loc[mask_reset, 'reading_diff'] = 0 
    
    df['daily_avg'] = df['reading_diff'] / df['days_diff'].replace(0, pd.NA)
    
    return df

MIN_COVERED_DAYS_PER_MONTH = 20

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
        covered_series = pd.Series(False, index=daily_idx)
        
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
            covered_series.loc[mask] = True
            
        # Resample to Month End: take SUM of consumption and count of covered days
        monthly = daily_series.resample('ME').sum()
        covered_days = covered_series.resample('ME').sum()
        # Only include months with at least MIN_COVERED_DAYS_PER_MONTH (20) covered days
        monthly = monthly[covered_days >= MIN_COVERED_DAYS_PER_MONTH]

    if monthly.empty:
        return pd.DataFrame(columns=['date', 'consumption', 'month_str'])
    
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

def calculate_yearly_stats(readings: list[MeterReading], monthly_df: pd.DataFrame, eval_mode: str = 'difference') -> pd.DataFrame:
    if not readings or monthly_df.empty:
        return pd.DataFrame()

    # 1. Data Points per year
    readings_df = pd.DataFrame([r.__dict__ for r in readings])
    readings_df['reading_date'] = pd.to_datetime(readings_df['reading_date'])
    readings_df['year'] = readings_df['reading_date'].dt.year
    
    # Get intervals for accurate daily avg calculation
    intervals_df = process_readings(readings)
    if not intervals_df.empty:
        min_d = intervals_df['reading_date'].min()
        max_d = intervals_df['reading_date'].max()
        daily_idx = pd.date_range(start=min_d, end=max_d, freq='D')
        covered_series = pd.Series(False, index=daily_idx)
        for _, row in intervals_df.iterrows():
            if pd.isna(row['prev_date']) or pd.isna(row['daily_avg']):
                continue
            mask = (covered_series.index > row['prev_date']) & (covered_series.index <= row['reading_date'])
            covered_series.loc[mask] = True
        monthly_covered_days = covered_series.resample('ME').sum()
        covered_by_month = {dt.strftime('%Y-%m'): int(days) for dt, days in monthly_covered_days.items()}
    else:
        covered_by_month = {}
    
    stats = []
    # Sort years descending
    years = sorted(monthly_df['year'].unique(), reverse=True)
    
    for year in years:
        # Filter readings for this year
        year_readings = readings_df[readings_df['year'] == year]
        data_points = len(year_readings)
        
        # Filter monthly values for this year
        year_monthly = monthly_df[monthly_df['year'] == year]
        if year_monthly.empty:
            continue

        if eval_mode == 'absolute':
            # For direct measurements (e.g., weight, temperature), compute mean/min/max instead of sum
            avg_monthly = float(year_monthly['consumption'].mean())
            min_val = float(year_readings['meter_reading'].min()) if not year_readings.empty else float(year_monthly['consumption'].min())
            max_val = float(year_readings['meter_reading'].max()) if not year_readings.empty else float(year_monthly['consumption'].max())
            stats.append({
                'year': year,
                'data_points': data_points,
                'total_consumption': avg_monthly,
                'avg_monthly': avg_monthly,
                'avg_daily': avg_monthly,
                'min_value': min_val,
                'max_value': max_val
            })
            continue

        total_consumption = year_monthly['consumption'].sum()
        
        # Avg Monthly
        active_months = len(year_monthly[year_monthly['consumption'] > 0])
        avg_monthly = total_consumption / active_months if active_months > 0 else 0
        
        # Avg Daily - sum the covered days of the included months so numerator & denominator match
        active_days = sum(covered_by_month.get(m_str, 0) for m_str in year_monthly['month_str'])
        if active_days == 0:
            active_days = 1  # Avoid division by zero
        
        avg_daily = total_consumption / active_days if active_days > 0 else 0
        
        stats.append({
            'year': year,
            'data_points': data_points,
            'total_consumption': total_consumption,
            'avg_monthly': avg_monthly,
            'avg_daily': avg_daily,
            'min_value': float(year_monthly['consumption'].min()),
            'max_value': float(year_monthly['consumption'].max())
        })
        
    return pd.DataFrame(stats)


# --- Formula / Calculated Series Support ---

_VAR_PATTERN = re.compile(r'\[([^\[\]]+)\]')

def extract_formula_variables(formula: str) -> list[str]:
    """Extracts all variable names enclosed in [brackets] in order of appearance (deduplicated)."""
    seen = []
    for match in _VAR_PATTERN.finditer(formula or ""):
        name = match.group(1).strip()
        if name and name not in seen:
            seen.append(name)
    return seen

def _prepare_formula_expr(formula: str, var_map: dict[str, str]) -> str:
    """
    Replaces [Series Name] tokens with safe Python identifiers (__v0, __v1, ...)
    and normalizes implicit multiplication like `2[x]` or `) [x]` or `2(x)`.
    """
    expr = (formula or "").strip()
    # Replace decimal commas in numbers (e.g. 1,5 -> 1.5)
    expr = re.sub(r'(\d),(\d)', r'\1.\2', expr)

    def replacer(match: re.Match) -> str:
        name = match.group(1).strip()
        return var_map.get(name, "__missing__")

    expr = _VAR_PATTERN.sub(replacer, expr)
    # Implicit multiplication: number or closing paren followed by variable or opening paren
    expr = re.sub(r'(\d|\))\s*(__v\d+|\()', r'\1 * \2', expr)
    expr = re.sub(r'(__v\d+)\s*(\d|\(|__v\d+)', r'\1 * \2', expr)
    return expr

_ALLOWED_BIN_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
}

_ALLOWED_UNARY_OPS = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}

def _eval_ast_node(node: ast.AST, env: dict[str, pd.Series | float]):
    if isinstance(node, ast.Expression):
        return _eval_ast_node(node.body, env)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return float(node.value)
    if isinstance(node, ast.Name):
        if node.id in env:
            return env[node.id]
        raise ValueError(f"Unknown variable: {node.id}")
    if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED_BIN_OPS:
        left = _eval_ast_node(node.left, env)
        right = _eval_ast_node(node.right, env)
        return _ALLOWED_BIN_OPS[type(node.op)](left, right)
    if isinstance(node, ast.UnaryOp) and type(node.op) in _ALLOWED_UNARY_OPS:
        operand = _eval_ast_node(node.operand, env)
        return _ALLOWED_UNARY_OPS[type(node.op)](operand)
    raise ValueError("Unsupported formula syntax")

def validate_formula(formula: str, available_series: list[str], self_name: str = "") -> tuple[bool, str]:
    """
    Validates a user formula string.
    Returns (is_valid, error_key_or_message).
    """
    if not formula or not formula.strip():
        return False, "Please enter a formula."

    variables = extract_formula_variables(formula)
    if not variables:
        return False, "Formula must reference at least one data series in [brackets]."

    for v in variables:
        if self_name and v == self_name:
            return False, f"Formula cannot reference itself ([{v}])."
        if v not in available_series:
            return False, f"Unknown data series: [{v}]"

    var_map = {v: f"__v{i}" for i, v in enumerate(variables)}
    expr = _prepare_formula_expr(formula, var_map)

    # Check for stray brackets or invalid characters outside variables
    if '[' in expr or ']' in expr:
        return False, "Unmatched brackets in formula."

    try:
        tree = ast.parse(expr, mode='eval')
        dummy_env = {placeholder: 1.0 for placeholder in var_map.values()}
        _eval_ast_node(tree, dummy_env)
    except ZeroDivisionError:
        pass
    except Exception:
        return False, "Invalid mathematical expression."

    return True, ""

def calculate_formula_monthly(
    formula: str,
    source_monthly_dfs: dict[str, pd.DataFrame]
) -> pd.DataFrame:
    """
    Computes monthly values for a calculated series based on already processed monthly DataFrames.
    Only months where ALL referenced variables have a known value (including 0.0) are included.
    Months where any referenced variable is missing/unknown are omitted.
    """
    empty_df = pd.DataFrame(columns=['date', 'consumption', 'month_str', 'year', 'month_index', 'month_name'])
    variables = extract_formula_variables(formula)
    if not variables:
        return empty_df

    # Ensure all required series exist and are non-empty
    series_by_placeholder: dict[str, pd.Series] = {}
    var_map = {v: f"__v{i}" for i, v in enumerate(variables)}

    common_months = None
    month_to_date = {}

    for v in variables:
        df = source_monthly_dfs.get(v)
        if df is None or df.empty:
            return empty_df
        # Drop NA consumption rows if any exist, keep valid 0.0 values
        valid_df = df.dropna(subset=['consumption'])
        if valid_df.empty:
            return empty_df

        for _, r in valid_df.iterrows():
            month_to_date[r['month_str']] = r['date']

        s = valid_df.set_index('month_str')['consumption'].astype(float)
        series_by_placeholder[var_map[v]] = s
        months_set = set(s.index)
        common_months = months_set if common_months is None else (common_months & months_set)

    if not common_months:
        return empty_df

    sorted_months = sorted(common_months)
    aligned_env = {
        ph: s.reindex(sorted_months) for ph, s in series_by_placeholder.items()
    }

    expr = _prepare_formula_expr(formula, var_map)
    try:
        tree = ast.parse(expr, mode='eval')
        computed = _eval_ast_node(tree, aligned_env)
        if isinstance(computed, (int, float)):
            computed = pd.Series(float(computed), index=sorted_months)
    except Exception:
        return empty_df

    # Drop NaN / inf (e.g. division by zero in a month)
    computed = pd.Series(computed, index=sorted_months).replace([float('inf'), float('-inf')], pd.NA).dropna()
    if computed.empty:
        return empty_df

    english_months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    rows = []
    for m_str, val in computed.items():
        dt = pd.to_datetime(month_to_date.get(m_str, f"{m_str}-01"))
        rows.append({
            'date': dt,
            'consumption': float(val),
            'month_str': m_str,
            'year': dt.year,
            'month_index': dt.month,
            'month_name': english_months[dt.month - 1]
        })

    return pd.DataFrame(rows)

def calculate_formula_yearly_stats(monthly_df: pd.DataFrame) -> pd.DataFrame:
    """Calculates yearly statistics directly from a calculated monthly DataFrame."""
    if monthly_df is None or monthly_df.empty:
        return pd.DataFrame()

    stats = []
    years = sorted(monthly_df['year'].unique(), reverse=True)

    for year in years:
        year_monthly = monthly_df[monthly_df['year'] == year]
        if year_monthly.empty:
            continue

        months_count = len(year_monthly)
        total_consumption = float(year_monthly['consumption'].sum())
        avg_monthly = total_consumption / months_count if months_count > 0 else 0.0

        total_days = sum(
            calendar.monthrange(int(r['year']), int(r['month_index']))[1]
            for _, r in year_monthly.iterrows()
        )
        avg_daily = total_consumption / total_days if total_days > 0 else 0.0

        stats.append({
            'year': year,
            'data_points': months_count,
            'total_consumption': total_consumption,
            'avg_monthly': avg_monthly,
            'avg_daily': avg_daily,
            'min_value': float(year_monthly['consumption'].min()),
            'max_value': float(year_monthly['consumption'].max())
        })

    return pd.DataFrame(stats)

def calculate_all_monthly_series(
    db,
    user_id: str,
    meter_types: list[str],
    configs: dict[str, dict[str, str]]
) -> dict[str, pd.DataFrame]:
    """
    Resolves monthly DataFrames for all series (standard and formula-based).
    Supports multi-pass resolution so calculated series can reference other calculated series.
    """
    monthly_dfs: dict[str, pd.DataFrame] = {}
    formula_types: list[str] = []

    for mt in meter_types:
        m_cfg = configs.get(mt, {})
        eval_mode = m_cfg.get('eval_mode') or 'difference'
        if eval_mode == 'formula':
            formula_types.append(mt)
        else:
            readings = db.get_readings(user_id, mt)
            monthly_dfs[mt] = calculate_monthly_consumption(readings, eval_mode) if readings else pd.DataFrame()

    # Resolve formulas in up to len(formula_types) passes
    remaining = list(formula_types)
    for _ in range(len(formula_types) + 1):
        if not remaining:
            break
        progressed = False
        next_remaining = []
        for mt in remaining:
            formula = configs.get(mt, {}).get('formula', '')
            vars_needed = extract_formula_variables(formula)
            if all(v in monthly_dfs for v in vars_needed):
                monthly_dfs[mt] = calculate_formula_monthly(formula, monthly_dfs)
                progressed = True
            else:
                next_remaining.append(mt)
        remaining = next_remaining
        if not progressed:
            break

    for mt in remaining:
        formula = configs.get(mt, {}).get('formula', '')
        monthly_dfs[mt] = calculate_formula_monthly(formula, monthly_dfs)

    return monthly_dfs
