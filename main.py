import streamlit as st
import pandas as pd
import data_loader
import logic
import red
from qingx import qingxu

# --- Page Configuration ---
st.set_page_config(
    page_title="Sector Alpha Hunter",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed" # Collapsed to save space for "one page" feel
)

# --- Custom CSS (The "Linear" Look) ---
st.markdown("""
<style>
    /* Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
    
    .stApp { background-color: #FFFFFF; }
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        color: #1F2937;
    }

    /* Layout */
    .block-container {
        padding-top: 3rem !important;
        padding-bottom: 5rem !important;
        max-width: 1200px;
    }
    
    /* Typography */
    h1, h2, h3 {
        font-weight: 600 !important;
        color: #0F172A !important;
        letter-spacing: -0.025em;
    }
    h1 { font-size: 1.875rem !important; margin-bottom: 0.75rem !important; }
    h2 { font-size: 1.25rem !important; margin-top: 2rem !important; }
    h3 { font-size: 1.125rem !important; }
    
    /* Metric Cards */
    div[data-testid="metric-container"] {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 16px;
        padding: 1.5rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08);
        transition: all 0.25s ease;
    }
    div[data-testid="metric-container"]:hover {
        border-color: #EF4444;
        box-shadow: 0 4px 12px rgba(239, 68, 68, 0.15);
        transform: translateY(-2px);
    }
    div[data-testid="stMetricLabel"] { 
        font-size: 0.875rem; 
        color: #64748B; 
        font-weight: 500; 
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    div[data-testid="stMetricValue"] { 
        font-size: 2rem; 
        font-weight: 700; 
        color: #EF4444 !important;
    }

    /* Tables */
    div[data-testid="stDataFrame"] {
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        background: #FFFFFF;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2.5rem;
        border-bottom: 1px solid #E2E8F0;
    }
    .stTabs [data-baseweb="tab"] {
        height: 48px;
        color: #94A3B8;
        font-weight: 500;
        transition: color 0.2s ease;
    }
    .stTabs [data-baseweb="tab"]:hover { color: #64748B; }
    .stTabs [aria-selected="true"] {
        color: #EF4444 !important;
        border-bottom: 2px solid #EF4444 !important;
    }

    /* All Buttons - Base Style */
    .stButton > button,
    div.stDownloadButton > button {
        border-radius: 12px !important;
        padding: 0.625rem 1.5rem !important;
        font-weight: 500 !important;
        font-size: 0.9375rem !important;
        transition: all 0.2s ease !important;
        min-height: 42px !important;
    }

    /* Red Buttons (Primary + Download) */
    button[kind="primary"],
    div.stDownloadButton > button {
        background-color: #EF4444 !important;
        border: 1px solid #EF4444 !important;
        color: #FFFFFF !important;
    }
    button[kind="primary"]:hover,
    div.stDownloadButton > button:hover {
        background-color: #DC2626 !important;
        border-color: #DC2626 !important;
        box-shadow: 0 4px 12px rgba(239, 68, 68, 0.25) !important;
        transform: translateY(-1px);
    }
    
    /* Force white text on all red button children */
    button[kind="primary"] *,
    div.stDownloadButton > button * {
        color: #FFFFFF !important;
    }

    /* Secondary Buttons */
    button[kind="secondary"] {
        background-color: #F8FAFC !important;
        border: 1px solid #E2E8F0 !important;
        color: #475569 !important;
    }
    button[kind="secondary"]:hover {
        background-color: #F1F5F9 !important;
        border-color: #CBD5E1 !important;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #FAFAFA;
        border-right: 1px solid #E2E8F0;
    }

    /* Utils */
    .text-red { color: #EF4444; font-weight: 600; }
    .text-subtle { color: #94A3B8; font-size: 0.8125rem; }
</style>
""", unsafe_allow_html=True)

def main():
    # --- Header (Compact) ---
    col_title, col_settings = st.columns([6, 1])
    with col_title:
        st.markdown("<h1>📈 A股板块轮动猎手</h1>", unsafe_allow_html=True)
        st.markdown("<h3>追踪A股最强风口，锁定龙头与补涨机会</h3>", unsafe_allow_html=True)
    with col_settings:
        if st.button("刷新数据", type="primary", use_container_width=True):
            st.cache_data.clear()
            st.rerun()


    # --- Sidebar (Hidden by default, clean params) ---
    with st.sidebar:
        st.subheader("功能")
        
        # --- Export Feature ---
        if st.toggle("使用历史日期"):
             selected_date = st.date_input(
                "选择日期",
                value=pd.Timestamp.now().date(),
                max_value=pd.Timestamp.now().date()
            )
             date_str = selected_date.strftime("%Y%m%d")
             export_label = f"⬇️ 导出 {selected_date} 涨停数据"
        else:
             date_str = None # Defaults to "latest" in data_loader
             export_label = "⬇️ 导出今日涨停数据"

        if st.button(export_label, type="primary", use_container_width=True):
             with st.spinner("正在获取涨停数据..."):
                zt_df = data_loader.get_limit_up_pool(date=date_str)
                if not zt_df.empty:
                    export_df = logic.format_limit_up_export(zt_df)
                    
                    # Generate filename
                    final_date_str = date_str if date_str else pd.Timestamp.now().strftime('%Y%m%d')
                    
                    csv = export_df.to_csv(index=False).encode('gbk', errors='ignore') # GBK for Excel/WPS
                    st.download_button(
                        label="点击下载 CSV",
                        data=csv,
                        file_name=f"limit_up_{final_date_str}.csv",
                        mime='text/csv',
                        type='primary' 
                    )
                else:
                    st.error(f"暂无数据 ({date_str if date_str else '今日'}), 可能是非交易日")
        st.divider()
        st.subheader("设置")
        top_n = st.slider("展现板块数", 1, 10,9)
        max_mkt_cap_yi = st.number_input("补涨市值上限 (亿)", 10, 500, 200, 10)
        
        # --- Signal Lab ---
        with st.expander("🎯 信号工坊 (Signal Lab)", expanded=True):
            st.caption("选择叠加因子 (严格与逻辑)")
            
            # Dynamic Checkboxes based on Registry
            # Hardcoded for now based on known Phase 1 signals to ensure order/naming
            # In future, can iterate logic.SIGNAL_REGISTRY
            
            sig_vol = st.checkbox("量比爆发 (>1.5)", value=True, key="sig_vol_ratio")
            sig_div = st.checkbox("板块背离 (滞涨)", value=False, key="sig_sector_divergence")
            sig_cap = st.checkbox("市值下沉 (Bottom 20%)", value=False, key="sig_small_cap")
            
            selected_signal_ids = []
            if sig_vol: selected_signal_ids.append('vol_ratio')
            if sig_div: selected_signal_ids.append('sector_divergence')
            if sig_cap: selected_signal_ids.append('small_cap')
       # 创建主容器
    with st.empty():
        # 创建三个标签页
        tab1= st.tabs([ "🏢 龙头股分析"])
        # --- Step 1: Metrics Row (The "Market Heat" Bar) ---
        # Fetch Data

        with st.spinner("Analyzing Market..."):
            # 1. Get Ranking
            k1 = data_loader.get_sector_ranking(top_n=top_n)

            if k1.empty:
                st.error("无法获取板块排名，请稍后重试")
                return

            # 2. Parallel Fetching: Global Data + Sector Constituents
            # We do this here so the user waits once, then interactions are instant
            status_text = st.empty()
            status_text.text("正在拉取全市场实时数据...")
            k2 = data_loader.get_all_market_spot_data()
            status_text.text(f"正在并行扫描 Top {top_n} 板块成分股...")
            k3 = k1['板块名称'].tolist()
            k4 = data_loader.get_multiple_sector_cons(k3)
            status_text.empty() # Clear status

        # Display Top Sectors as a horizontal bar of cards
        cols = st.columns(top_n)
        for i, (index, row) in enumerate(k1.iterrows()):
            with cols[i]:
                st.metric(
                    label=row['板块名称'],
                    value=f"{row['涨跌幅']:.2f}%",
                    delta=None # Custom red color handled by CSS
                )

        st.markdown("<div style='margin-bottom: 1.5rem;'></div>", unsafe_allow_html=True)

        # --- Step 2: Main Content (Tabs) ---
        # Use tabs to keep it single-page, no scrolling down for other sectors
        k5 = [f"{row['板块名称']}" for _, row in k1.iterrows()]
        k6 = st.tabs(k5)

        for i, tab in enumerate(k6):
            k7 = k1.iloc[i]['板块名称']
            k8 = k1.iloc[i]['涨跌幅'] # Grab Sector Gain

            with tab:
                # Data Processing: Merge On-Demand (Fast in-memory)
                # Retrieve cons from map
                k9 = k4.get(k7, None)

                if k9 is None or k2.empty:
                    st.warning("暂无数据 (可能是API限制或网络波动)")
                    continue

                # Inject Sector Gain
                k10 = data_loader.merge_stock_data(k9, k2, sector_gain=k8)

                k11 = logic.clean_data(k10)
                    # 2-Column Layout for "Dragons" vs "Laggards"
                    # This allows seeing Leaders and Followers side-by-side (One Page concept)
                c1,c2,c3= st.columns([1,1.4,1])
                # --- Column 1: Leaders ---
                with c1:
                    st.markdown("### 🐲龙头梯队")
                    st.markdown("<p class='text-subtle'>高标 / 涨停</p>", unsafe_allow_html=True)

                    k13 = logic.filter_dragons(k11)
                    if not k13.empty:
                        dragons_disp = k13.copy()
                        dragons_disp['总市值'] = dragons_disp['总市值'] / 100_000_000

                        st.dataframe(
                            dragons_disp[['名称', '最新价', '涨跌幅', '总市值']],
                            height=400,  # Fixed height to align
                            use_container_width=True,
                            hide_index=True,
                            column_config={
                                "涨跌幅": st.column_config.NumberColumn(format="%.2f%%"),
                                "总市值": st.column_config.NumberColumn(label="市值(亿)", format="%.1f"),
                                "最新价": st.column_config.NumberColumn(format="%.2f"),
                            }
                        )
                    else:
                        st.caption("无")


if __name__ == "__main__":
    main()
