import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime, timedelta
import pytz
import plotly.graph_objects as go
import time

# ==========================================
# 🔑 雲端金鑰區 (讀取 Streamlit Secrets)
# ==========================================
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
VIP_PASSWORD = st.secrets["VIP_PASSWORD"]

# 網頁基本設定 (設定為寬螢幕)
st.set_page_config(page_title="AI 股市戰略總部", page_icon="🧭", layout="wide")

# 🎨 【專業化升級】隱藏 Streamlit 預設的選單與浮水印
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

# ==========================================
# 🔌 初始化雲端資料庫連線
# ==========================================
@st.cache_resource
def init_connection():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_connection()

# ==========================================
# 🚀 雲端訪客計數引擎
# ==========================================
if 'has_counted' not in st.session_state:
    st.session_state['has_counted'] = True
    try:
        res = supabase.table("visit_counter").select("visits").eq("id", 1).execute()
        current_visits = res.data[0]['visits']
        new_visits = current_visits + 1
        supabase.table("visit_counter").update({"visits": new_visits}).eq("id", 1).execute()
    except:
        new_visits = "系統讀取中"
else:
    try:
        res = supabase.table("visit_counter").select("visits").eq("id", 1).execute()
        new_visits = res.data[0]['visits']
    except:
        new_visits = "系統讀取中"

# ==========================================
# 🔒 大門警衛系統 (高質感登入介面)
# ==========================================
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        st.markdown(f"""
            <div style='background-color: #F5F5F5; padding: 25px; border-radius: 15px; text-align: center; border: 1px solid #E0E0E0; box-shadow: 0 6px 10px rgba(0,0,0,0.05);'>
                <p style='font-size: 30px; margin: 0;'>🧭</p>
                <p style='color: #888888; margin-top: 10px; margin-bottom: 5px; font-size: 14px;'>系統穩定運行</p>
                <p style='color: #555555; margin-bottom: 0px; font-size: 16px;'>歷史累計登入人次</p>
                <h1 style='color: #FFD700; margin: 5px 0 0 0; font-size: 48px;'>{new_visits}</h1>
            </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("<h2 style='text-align: center;'>🔒 戰略總部 VIP 登入</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: gray;'>請輸入總監專屬通關密碼以解鎖今日戰報</p>", unsafe_allow_html=True)
        pwd = st.text_input("通關密碼", type="password", label_visibility="collapsed", placeholder="請輸入密碼...")
        if st.button("解鎖進入", use_container_width=True):
            if pwd == VIP_PASSWORD:
                st.session_state['logged_in'] = True
                st.rerun()
            else:
                st.error("❌ 密碼錯誤，請重新輸入！")
    st.stop() 

st.sidebar.metric(label="🔥 總監專屬：累積訪問人次", value=f"{new_visits} 次")

# ==========================================
# ⏳ 資料庫讀取邏輯區 (前五分頁使用)
# ==========================================
def get_time_window():
    tz = pytz.timezone('Asia/Taipei')
    now = datetime.now(tz)
    if now.hour >= 6:
        start_time = now.replace(hour=6, minute=0, second=0, microsecond=0)
    else:
        start_time = (now - timedelta(days=1)).replace(hour=6, minute=0, second=0, microsecond=0)
    end_time = start_time + timedelta(days=1)
    return start_time.isoformat(), end_time.isoformat()

@st.cache_data(ttl=60)
def load_daily_data():
    start_iso, end_iso = get_time_window()
    try:
        response = supabase.table("daily_reports").select("*").gte("created_at", start_iso).lt("created_at", end_iso).order("created_at", desc=True).execute()
        return response.data
    except: return []

@st.cache_data(ttl=60)
def load_tw_data():
    try:
        response = supabase.table("tw_daily_reports").select("*").order("report_date", desc=True).limit(5).execute()
        return response.data
    except: return []

@st.cache_data(ttl=30) 
def load_bidask_data():
    try:
        response = supabase.table("tw_bidask_reports").select("*").order("created_at", desc=True).limit(1).execute()
        return response.data
    except: return []

@st.cache_data(ttl=60)
def load_us_data():
    try:
        response = supabase.table("us_market_reports").select("*").order("report_date", desc=True).limit(5).execute()
        return response.data
    except: return []

@st.cache_data(ttl=60)
def load_us_after_data():
    try:
        response = supabase.table("us_after_hours_reports").select("*").order("report_time", desc=True).limit(5).execute()
        return response.data
    except: return []

# ==========================================
# ⚡ ⚡ 第六分頁專用：光速資料提領引擎 (讀取本地 RAD.py 傳送的數據)
# ==========================================
@st.cache_data(ttl=60)
def fetch_realtime_payload():
    try:
        response = supabase.table("macro_5m_data").select("payload").eq("id", 1).execute()
        if response.data and len(response.data) > 0:
            return response.data[0]['payload']
        return None
    except:
        return None

def draw_realtime_chart(df):
    o = 'Open' if 'Open' in df.columns else 'open'
    h = 'High' if 'High' in df.columns else 'high'
    l = 'Low' if 'Low' in df.columns else 'low'
    c = 'Close' if 'Close' in df.columns else 'close'
    fig = go.Figure(data=[go.Candlestick(
        x=df['TimeStr'], open=df[o], high=df[h],
        low=df[l], close=df[c],
        increasing_line_color='red', decreasing_line_color='green' 
    )])
    fig.update_layout(height=250, margin=dict(l=10, r=10, t=10, b=10), xaxis_rangeslider_visible=False)
    return fig

def render_realtime_panel(col_obj, data_info, title, unit=""):
    with col_obj:
        if data_info and data_info.get('df'):
            df = pd.DataFrame(data_info['df'])
            prev_close = data_info['prev_close']
            if not df.empty:
                c_col = 'Close' if 'Close' in df.columns else 'close'
                latest_price = float(df[c_col].iloc[-1])
                diff = latest_price - prev_close
                pct_change = (diff / prev_close) * 100 if prev_close != 0 else 0
                sign = "+" if diff > 0 else ""
                delta_str = f"{sign}{diff:,.2f} ({sign}{pct_change:.2f}%)"
                st.metric(label=title, value=f"{latest_price:,.2f} {unit}", delta=delta_str, delta_color="inverse")
                st.plotly_chart(draw_realtime_chart(df), use_container_width=True)
            else: st.info(f"{title} 今日無效數據")
        else: st.info(f"{title} 雲端無數據")

# ==========================================
# 🎨 網頁主介面：六大戰略分頁
# ==========================================
st.title("🧭 全球熱錢羅盤 - 戰略決策室")
st.markdown("歡迎回來，總監。請選擇您要查看的資金戰區。")

tab_asia, tab_tw, tab_us_reg, tab_us_after, tab_hk, tab_realtime = st.tabs([
    "🌏 亞洲戰區 (日韓)", 
    "🇹🇼 台股主力動向", 
    "🦅 美股常規盤", 
    "🌙 美股盤後動向", 
    "🐉 港陸戰區", 
    "⚡ 5分即時監控"
])

# ------------------------------------------
# 🌏 第一分頁：亞洲戰區 (保持原樣)
# ------------------------------------------
with tab_asia:
    records = load_daily_data()
    if records:
        tz = pytz.timezone('Asia/Taipei')
        def format_time(record):
            dt = datetime.fromisoformat(record['created_at']).astimezone(tz)
            return dt.strftime("%Y/%m/%d - %H:%M")
        st.markdown("### 📊 亞洲熱錢觀測")
        selected_record = st.selectbox("📖 請選擇戰報時間：", options=records, format_func=format_time, key="asia_selectbox")
        st.success("**🤖 AI 戰略分析與狙擊暗示**")
        st.write(selected_record['ai_strategy'])
        df_gainers = pd.DataFrame(selected_record['gainers_data'])
        df_losers = pd.DataFrame(selected_record['losers_data'])
        col1, col2 = st.columns(2)
        with col1: st.dataframe(df_gainers, use_container_width=True, height=400)
        with col2: st.dataframe(df_losers, use_container_width=True, height=400)
    else:
        st.info("🕒 報告區塊已於 06:00 淨空。正在等待今日的第一筆亞洲戰報上傳...")

# ------------------------------------------
# 🇹🇼 第二分頁：台股主力動向 (保持原樣)
# ------------------------------------------
with tab_tw:
    bidask_data = load_bidask_data()
    if bidask_data:
        latest_bidask = bidask_data[0]
        st.markdown(f"### ⚡ 巨頭氣勢比狙擊 (熱門250大 | 報告時間: {latest_bidask['report_time']})")
        df_top30 = pd.DataFrame(latest_bidask.get('top_30', []))
        df_bot30 = pd.DataFrame(latest_bidask.get('bottom_30', []))
        col_ba1, col_ba2 = st.columns(2)
        with col_ba1:
            st.success("🔥 買氣碾壓 (氣勢比 > 50%)")
            if not df_top30.empty: st.dataframe(df_top30, use_container_width=True, height=350)
        with col_ba2:
            st.error("🧊 倒貨碾壓 (氣勢比 < -50%)")
            if not df_bot30.empty: st.dataframe(df_bot30, use_container_width=True, height=350)
    st.divider() 
    tw_records = load_tw_data()
    if tw_records:
        st.markdown("### 🇹🇼 台股籌碼雷達觀測 (盤後)")
        selected_tw_record = st.selectbox("📖 請選擇台股戰報日期：", options=tw_records, format_func=lambda x: f"{x['report_date']} 戰報", key="tw_selectbox")
        df_synergy = pd.DataFrame(selected_tw_record.get('synergy_data', []))
        st.markdown("#### 🎯 主力分點共振雷達")
        st.dataframe(df_synergy, use_container_width=True, height=350)

# ------------------------------------------
# 🦅 第三分頁：美股常規戰區 (保持原樣)
# ------------------------------------------
with tab_us_reg:
    us_records = load_us_data()
    if us_records:
        st.markdown("### 🦅 美股板塊與領頭羊觀測")
        selected_us_record = st.selectbox("📖 請選擇美股戰報日期：", options=us_records, format_func=lambda x: f"{x['report_date']} 美股戰報", key="us_selectbox")
        st.success("**🤖 華爾街 AI 戰略推演**")
        st.write(selected_us_record.get('ai_strategy', '無 AI 分析資料'))
        df_overview = pd.DataFrame(selected_us_record.get('overview_data', []))
        df_leaders = pd.DataFrame(selected_us_record.get('leaders_data', []))
        c1, c2 = st.columns([1, 2])
        with c1: st.dataframe(df_overview, use_container_width=True, height=500)
        with c2: st.dataframe(df_leaders, use_container_width=True, height=500)

# ------------------------------------------
# 🌙 第四分頁：美股盤後戰區 (保持原樣)
# ------------------------------------------
with tab_us_after:
    after_records = load_us_after_data()
    if after_records:
        selected_after = st.selectbox("📖 選擇盤後戰報時段：", options=after_records, format_func=lambda x: x['report_time'], key="us_after_selectbox")
        st.markdown(f"### 🌙 美股盤後異動監控")
        st.success("**🤖 AI 盤後概念連動分析**")
        st.write(selected_after.get('ai_analysis', '無數據'))
        df_after = pd.DataFrame(selected_after.get('top_movers', []))
        st.dataframe(df_after, use_container_width=True, height=450)

# ------------------------------------------
# 🐉 第五分頁：港陸戰區 (保持原樣)
# ------------------------------------------
with tab_hk:
    st.error("🐉 **港陸股熱錢追蹤系統規劃中**") 

# ------------------------------------------
# ⚡ ⚡ 第六分頁：5分即時監控 (⚡ 改寫為光速讀取模式)
# ------------------------------------------
with tab_realtime:
    st.markdown("### ⚡ 全球資產 5 分鐘即時監控 (雲端讀取模式)")
    st.caption("數據來源：本地電腦 RAD.py 每 5 分鐘自動覆蓋更新")
    
    payload = fetch_realtime_payload()
    
    if payload:
        r1 = st.columns(4)
        r2 = st.columns(4)
        render_realtime_panel(r1[0], payload.get('EC'), "🚢 歐線集運主連 (EC)")
        render_realtime_panel(r1[1], payload.get('PVC'), "🛢️ 塑化主連 (PVC)")
        render_realtime_panel(r1[2], payload.get('Bond_10Y'), "🏦 10Y 美債殖利率", "%")
        render_realtime_panel(r1[3], payload.get('Gold'), "✨ 黃金期貨", "USD")
        render_realtime_panel(r2[0], payload.get('Copper'), "🏗️ 銅價期貨", "USD")
        render_realtime_panel(r2[1], payload.get('Brent'), "🛢️ 布蘭特原油", "USD")
        render_realtime_panel(r2[2], payload.get('BTC'), "🪙 比特幣 (BTC)", "USD")
        render_realtime_panel(r2[3], payload.get('DXY'), "💵 美元指數 (DXY)")
        
        st.markdown("---")
        # 增加網頁自動刷新倒數
        refresh_timer = st.empty()
        # 這裡不使用 sleep 迴圈以免卡住其他分頁切換，僅顯示最後更新時間
        st.info(f"最後同步時間：{datetime.now(pytz.timezone('Asia/Taipei')).strftime('%H:%M:%S')}")
    else:
        st.warning("🔄 正在等待本地雷達站上傳首次數據，請確保您的 RAD.py 正在執行中...")

# ==========================================
# ⚖️ 網頁最底部：免責聲明與版權 (保持原樣)
# ==========================================
st.markdown("<br><br><br>", unsafe_allow_html=True)
st.divider()
disclaimer_html = """
<div style='background-color: #f8f9fa; padding: 15px; border-radius: 8px; border-left: 5px solid #d9534f; color: #555; font-size: 13px; line-height: 1.6;'>
    <strong>⚖️ 法律免責聲明 (Disclaimer)：</strong><br>
    ... (內容保持原樣) ...
</div>
<p style='text-align: center; color: gray; font-size: 12px; margin-top: 15px;'>© 2026 AI 戰略總部 | 全球熱錢羅盤 SaaS</p>
"""
st.markdown(disclaimer_html, unsafe_allow_html=True)
