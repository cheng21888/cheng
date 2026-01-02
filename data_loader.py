import akshare as ak
import pandas as pd
import streamlit as st

# Use Streamlit's caching to avoid frequent API calls
@st.cache_data(ttl=300)
def get_sector_ranking(top_n=5):
    """
    Fetch the ranking of concept boards.
    Returns:
        pd.DataFrame: Columns ['板块名称', '板块代码', '涨跌幅']
    """
    try:
        # Fetch Concept Board Name and Change
        # Interface: stock_board_concept_name_em
        df = ak.stock_board_concept_name_em()
        
        # Ensure '涨跌幅' works as numeric
        df['涨跌幅'] = pd.to_numeric(df['涨跌幅'], errors='coerce')
        
        # Sort by Change % Descending
        df_sorted = df.sort_values(by='涨跌幅', ascending=False)
        
        # Select top N and relevant columns
        result = df_sorted[['板块名称', '板块代码', '涨跌幅']].head(top_n)
        return result
    except Exception as e:
        print(f"Error fetching sector ranking: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=60)
def get_all_market_spot_data():
    """
    Fetch global spot data for the entire market ONCE.
    Contains Volume Ratio, Market Cap, etc.
    """
    try:
        return ak.stock_zh_a_spot_em()
    except Exception as e:
        print(f"Error fetching global spot data: {e}")
        return pd.DataFrame()

def get_sector_cons_single(sector_name):
    """
    Fetch constituents for a single sector (Uncached helper for threading).
    """
    try:
        df = ak.stock_board_concept_cons_em(symbol=sector_name)
        if df.empty:
            return None
        return df[['代码']] # Minimal columns
    except Exception as e:
        print(f"Error fetching cons for {sector_name}: {e}")
        return None

@st.cache_data(ttl=60)
def get_multiple_sector_cons(sector_names):
    """
    Fetch constituents for multiple sectors in PARALLEL.
    Returns:
        dict: {sector_name: cons_dataframe}
    """
    import concurrent.futures
    
    results = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        # Map sector name to future
        future_to_sector = {executor.submit(get_sector_cons_single, name): name for name in sector_names}
        
        for future in concurrent.futures.as_completed(future_to_sector):
            sector_name = future_to_sector[future]
            try:
                data = future.result()
                if data is not None:
                    results[sector_name] = data
            except Exception as e:
                print(f"Exception for {sector_name}: {e}")
                
    return results

def merge_stock_data(sector_cons_df, global_spot_df, sector_gain=None):
    """
    Merge sector constituents with pre-fetched global spot data.
    Args:
        sector_cons_df: DataFrame of sector constituents.
        global_spot_df: DataFrame of all market spot data.
        sector_gain: Optional float, sector change %.
    """
    if sector_cons_df is None or sector_cons_df.empty or global_spot_df.empty:
        return pd.DataFrame()
        
    try:
        # Inner merge
        merged_df = pd.merge(sector_cons_df, global_spot_df, on='代码', how='inner')
        
        target_cols = ['代码', '名称', '最新价', '涨跌幅', '总市值', '量比', '换手率']
        available_cols = [c for c in target_cols if c in merged_df.columns]
        
        result = merged_df[available_cols].copy()
        
        # Inject Sector Gain if provided (BROADCAST)
        if sector_gain is not None:
            result['sector_pct_chg'] = float(sector_gain)
            
        return result
    except Exception as e:
        print(f"Error merging data: {e}")
        return pd.DataFrame()
@st.cache_data(ttl=60)
def get_limit_up_pool(date=None):
    """
    Fetch the Daily Limit-Up (ZhangTing) pool.
    Args:
        date (str): YYYYMMDD. If None, uses latest trading day.
    """
    import datetime
    
    if date is None:
        # Simple fallback to today's string in YYYYMMDD
        date = datetime.date.today().strftime("%Y%m%d")
        
    try:
        # stock_zt_pool_em: Eastmoney Limit Up Pool
        df = ak.stock_zt_pool_em(date=date)
        return df
    except Exception as e:
        print(f"Error fetching limit up pool: {e}")
        return pd.DataFrame()

if __name__ == "__main__":
    # 测试上证股票（600118）
    print(get_sector_ranking(top_n=5))