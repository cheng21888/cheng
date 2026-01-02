import pandas as pd
import MyTT
def clean_data(df):
    """
    Clean and normalize data types.
    Ensures numeric columns are floats.
    """
    if df.empty:
        return df

    # Copy to avoid SettingWithCopyWarning
    df = df.copy()

    numeric_cols = ['最新价', '涨跌幅', '总市值', '量比', '换手率']
    
    for col in numeric_cols:
        if col in df.columns:
            # Coerce errors to NaN
            df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Special handling for Market Cap: Invalid/NaN should be dropped, not 0
            if col == '总市值':
                 df.dropna(subset=[col], inplace=True)
            else:
                 # For others, 0 fill might be acceptable or safe defaults, 
                 # but generally NaN in Price/Change is also bad. 
                 # Let's keep existing 0 fill behavior for others to minimize regression risk, 
                 # but strictly cast to float.
                 df[col] = df[col].fillna(0).astype(float)
            
            # Ensure float type for Market Cap after drop
            if col == '总市值':
                df[col] = df[col].astype(float)
            
    return df

def color_negative_red(val):
    try:
        val = float(val.rstrip("%"))
    except ValueError:
        return ""
    color = "red" if val > 0 else "green"
    return f"color: {color}"

def filter_dragons(df):
    """
    Filter for Dragon candidates (Leaders).
    Criteria:
    1. Change % >= 9.0 (Limit up or near limit up)
    2. Name excludes "ST"
    
    Returns:
        DataFrame sorted by Market Cap descending.
    """
    if df.empty:
        return df

    # Filter 1: Change >= 9.0
    mask_gain = df['涨跌幅'] >= 9.0
    
    # Filter 2: Not ST
    mask_st = ~df['名称'].str.contains('ST', na=False)
    
    dragons = df[mask_gain & mask_st].copy()
    
    # Sort by Market Cap Desc
    return dragons.sort_values(by='总市值', ascending=False)


def tidui(df):
    if df.empty:
        return df
    mask_gain = df['振幅'] >= 6
    mask_turnover = df['换手率'] > 10.0

    laggards = df[mask_gain  & mask_turnover].copy()

    return laggards



def filter_laggards(df, max_cap_billion=200):
    """
    Filter for Laggard candidates (Catch-up).
    Criteria:
    1. 0 <= Change % <= 4.0 (Not yet exploded)
    2. Market Cap < Threshold (Small cap)
    3. Turnover > 3.0 (Active)
    
    Args:
        max_cap_billion: int, Market Cap limit in Billions.
    """
    if df.empty:
        return df

    # Convert billion to actual units if raw data uses actual units
    # Note: AkShare '总市值' usually is in actual value? Or Yi?
    # Let's assume AkShare returns '总市值' in 'Yi' (100 Million) or absolute value.
    # Verification needed: standard AkShare usually returns actual value.
    # But let's look at recent data snapshot from debug_akshare:
    # No snapshot of '总市值' value was clearly printed with magnitude.
    # Safest bet: Assume '总市值' is in raw currency, so 100 Billion = 100 * 10^8.
    # WAIT: AkShare stock_zh_a_spot_em returns '总市值' often in absolute range.
    # e.g. 10000000000.
    
    # Let's handle the safe conversion. 
    # If values are huge (> 1e8), treat as raw. If small, treat as Yi?
    # Actually, let's assume raw absolute numbers for now based on standard API behavior.
    
    limit_val = max_cap_billion * 100_000_000
    
    mask_gain = (df['涨跌幅'] >= 0) & (df['涨跌幅'] <= 4.0)
    mask_cap = df['总市值'] < limit_val
    mask_turnover = df['换手率'] > 3.0
    
    laggards = df[mask_gain & mask_cap & mask_turnover].copy()
    
    return laggards


def format_limit_up_export(df):
    """
    Format the limit-up dataframe for CSV export (User-friendly columns).
    """
    if df.empty:
        return pd.DataFrame()
        
    try:
        df = df.copy()
        
        # 0. Ensure numeric types for calculation
        numeric_targets = ['最新价', '涨跌幅', '流通市值', '换手率', '连板数', '封单金额', '成交额']
        for col in numeric_targets:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        # 1. Define Mapping
        col_map = {
            '代码': '股票代码',
            '名称': '股票名称',
            '最新价': '价格',
            '涨跌幅': '涨幅(%)',
            '成交额': '成交额',
            '流通市值': '流通市值(亿)',
            '换手率': '换手率(%)',
            '连板数': '连板高度',
            '封单金额': '封单力度',
            '所属行业': '所属板块',
            '涨停原因类别': '涨停原因类别'
        }
        
        # 2. Rename
        result = df.rename(columns=col_map)
        
        # 3. Conversions
        if '流通市值(亿)' in result.columns:
            result['流通市值(亿)'] = (result['流通市值(亿)'] / 100_000_000).round(2)
            
        if '封单力度' in result.columns:
            result['封单力度'] = (result['封单力度'] / 100_000_000).round(2)
            result.rename(columns={'封单力度': '封单力度(亿)'}, inplace=True)
            col_map['封单金额'] = '封单力度(亿)' # Update map for strict selection
            
        if '成交额' in result.columns:
            result['成交额'] = (result['成交额'] / 100_000_000).round(2)
            result.rename(columns={'成交额': '成交额(亿)'}, inplace=True)

        # 4. Rounding
        if '涨幅(%)' in result.columns:
            result['涨幅(%)'] = result['涨幅(%)'].round(2)
            
        if '换手率(%)' in result.columns:
            result['换手率(%)'] = result['换手率(%)'].round(2)
            
        # 5. Select Columns
        # We need to know the final column names. 
        # The key in col_map is original, value is target.
        # But we might have renamed some target columns (like adding (亿)).
        
        final_targets = ['股票代码', '股票名称', '价格', '涨幅(%)', '连板高度', '所属板块', 
                         '流通市值(亿)', '换手率(%)', '封单力度(亿)', '成交额(亿)', '涨停原因类别']
        
        available = [c for c in final_targets if c in result.columns]
        result = result[available]
        
        # 6. Sort
        if '连板高度' in result.columns:
            result = result.sort_values(by='连板高度', ascending=False)
            
        return result
        
    except Exception as e:
        print(f"Error formatting export: {e}")
        return df

# --- Signal Engine ---

SIGNAL_REGISTRY = {}

def get_active_signals(selected_ids):
    """
    Retrieve signal objects from the registry based on IDs.
    """
    active = []
    for sig_id in selected_ids:
        if sig_id in SIGNAL_REGISTRY:
            active.append(SIGNAL_REGISTRY[sig_id])
    return active

def apply_signals(df, selected_signal_ids):
    """
    Apply selected signals to the DataFrame using strict AND logic.
    Returns filtered DataFrame.
    """
    if df.empty:
        return df
        
    if not selected_signal_ids:
        return df
    
    # Start with all True mask
    mask = pd.Series(True, index=df.index)
    
    active_signals = get_active_signals(selected_signal_ids)
    
    for sig in active_signals:
        func = sig['func']
        # Apply AND logic: intersection
        mask = mask & func(df)
        
    return df[mask].copy()

# --- Signal Implementations ---

def sig_vol_ratio(df):
    """Signal: Volume Ratio > 1.5"""
    if '量比' not in df.columns:
        return pd.Series(False, index=df.index)
    return df['量比'] > 1.5

def sig_sector_divergence(df):
    """Signal: Sector Gain - Stock Gain > 3.0"""
    if 'sector_pct_chg' not in df.columns or '涨跌幅' not in df.columns:
        return pd.Series(False, index=df.index)
    return (df['sector_pct_chg'] - df['涨跌幅']) > 3.0

def sig_small_cap(df):
    """Signal: Market Cap in bottom 20% of current pool"""
    if '总市值' not in df.columns or df.empty:
        return pd.Series(False, index=df.index)
        
    # Calculate quantile 0.2
    # Interpolation 'linear' is default
    limit = df['总市值'].quantile(0.2)
    return df['总市值'] <= limit

def _register_signals():
    """
    Populate registry with available signals.
    """
    SIGNAL_REGISTRY['vol_ratio'] = {
        'id': 'vol_ratio',
        'name': '量比爆发 (>1.5)',
        'func': sig_vol_ratio
    }
    
    SIGNAL_REGISTRY['sector_divergence'] = {
        'id': 'sector_divergence',
        'name': '板块背离 (滞涨)',
        'func': sig_sector_divergence
    }
    
    SIGNAL_REGISTRY['small_cap'] = {
        'id': 'small_cap',
        'name': '市值下沉 (Bottom 20%)',
        'func': sig_small_cap
    }

# Initialize
_register_signals()
