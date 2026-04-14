import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime, timedelta
import pytz

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
# ⏳ 資料庫讀取邏輯區
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

# ⚡ 新增：盤差報告讀取 (高頻更新)
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

# ⚡ 新增：美股盤後專屬讀取
@st.cache_data(ttl=60)
def load_us_after_data():
    try:
        response = supabase.table("us_after_hours_reports").select("*").order("report_time", desc=True).limit(5).execute()
        return response.data
    except: return []

@st.cache_data(ttl=60)
def load_commodities_data():
    try:
        response = supabase.table("commodities_reports").select("*").order("report_date", desc=True).limit(5).execute()
        return response.data
    except: return []


# ==========================================
# 🎨 網頁主介面：六大戰略分頁
# ==========================================
st.title("🧭 全球熱錢羅盤 - 戰略決策室")
st.markdown("歡迎回來，總監。請選擇您要查看的資金戰區。")

tab_asia, tab_tw, tab_us_reg, tab_us_after, tab_hk, tab_commodities = st.tabs([
    "🌏 亞洲戰區 (日韓)", 
    "🇹🇼 台股主力動向", 
    "🦅 美股常規盤", 
    "🌙 美股盤後動向", 
    "🐉 港陸戰區", 
    "🛢️ 原物料與期貨"
])

# ------------------------------------------
# 🌏 第一分頁：亞洲戰區
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
        st.markdown("<br>", unsafe_allow_html=True) 
        
        st.success("**🤖 AI 戰略分析與狙擊暗示**")
        st.write(selected_record['ai_strategy'])
        st.markdown("<br>", unsafe_allow_html=True)
        
        df_gainers = pd.DataFrame(selected_record['gainers_data'])
        df_losers = pd.DataFrame(selected_record['losers_data'])
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### 🚀 資金狂潮 (漲幅榜)")
            st.dataframe(df_gainers, use_container_width=True, height=400)
        with col2:
            st.markdown("#### ⚠️ 避險雷區 (跌幅榜)")
            st.dataframe(df_losers, use_container_width=True, height=400)
    else:
        st.info("🕒 報告區塊已於 06:00 淨空。正在等待今日的第一筆亞洲戰報上傳...")

# ------------------------------------------
# 🇹🇼 第二分頁：台股主力動向 (含盤差與籌碼)
# ------------------------------------------
with tab_tw:
    # --- ⚡ 區塊 1：即時內外盤差 ---
    bidask_data = load_bidask_data()
    if bidask_data:
        latest_bidask = bidask_data[0]
        st.markdown(f"### ⚡ 巨頭氣勢比狙擊 (熱門250大 | 報告時間: {latest_bidask['report_time']})")
        st.caption("公式：(外盤-內盤)/(外盤+內盤)。比例 > 50% 代表買方不計代價掃貨；< -50% 代表賣方恐慌殺出。每日自動清除舊檔。")
        
        df_top30 = pd.DataFrame(latest_bidask.get('top_30', []))
        df_bot30 = pd.DataFrame(latest_bidask.get('bottom_30', []))
        
        col_ba1, col_ba2 = st.columns(2)
        with col_ba1:
            st.success("🔥 買氣碾壓 (氣勢比 > 50%)")
            if not df_top30.empty:
                display_cols = ['狀態', '證券代號', '證券名稱', '氣勢比(%)', '內外盤差(張)', '外盤量(張)', '內盤量(張)']
                df_top30 = df_top30[[c for c in display_cols if c in df_top30.columns]]
                st.dataframe(df_top30, use_container_width=True, height=350)
            else:
                st.info("目前無任何熱門股達到買氣 > 50% 門檻。")
                
        with col_ba2:
            st.error("🧊 倒貨碾壓 (氣勢比 < -50%)")
            if not df_bot30.empty:
                display_cols = ['狀態', '證券代號', '證券名稱', '氣勢比(%)', '內外盤差(張)', '外盤量(張)', '內盤量(張)']
                df_bot30 = df_bot30[[c for c in display_cols if c in df_bot30.columns]]
                st.dataframe(df_bot30, use_container_width=True, height=350)
            else:
                st.info("目前無任何熱門股達到賣壓 < -50% 門檻。")
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.divider() 

    # --- 📊 區塊 2：盤後籌碼雷達 ---
    tw_records = load_tw_data()
    if tw_records:
        st.markdown("### 🇹🇼 台股籌碼雷達觀測 (盤後)")
        
        def format_tw_time(record):
            date_str = record['report_date']
            if len(date_str) == 8: return f"{date_str[:4]}/{date_str[4:6]}/{date_str[6:]} 戰報"
            return f"{date_str} 戰報"

        selected_tw_record = st.selectbox("📖 請選擇台股戰報日期：", options=tw_records, format_func=format_tw_time, key="tw_selectbox")
        st.markdown("<br>", unsafe_allow_html=True)
        
        df_surge = pd.DataFrame(selected_tw_record.get('surge_data', []))
        df_synergy = pd.DataFrame(selected_tw_record.get('synergy_data', []))
        
        # 🛡️ 欄位強制排序防呆
        if not df_surge.empty:
            surge_cols = ['觸發訊號', '證券代號', '證券名稱', '產業類別', '當日收盤價', '漲跌幅(%)', 'EMA20', '本益比(PE)', '淨值比(PB)', '本日成交量(張)', '外資買超(張)', '投信買超(張)']
            df_surge = df_surge[[c for c in surge_cols if c in df_surge.columns]]
            
        if not df_synergy.empty:
            base_syn_cols = ['觸發訊號', '證券代號', '證券名稱', '產業類別', '同買分點名單', '同賣分點名單', '主力總淨買賣(張)', '最新收盤價', 'EMA20(月線)', '本益比(PE)', '淨值比(PB)']
            extra_cols = [c for c in df_synergy.columns if c not in base_syn_cols]
            df_synergy = df_synergy[[c for c in base_syn_cols if c in df_synergy.columns] + extra_cols]

        st.markdown("#### 🎯 主力分點共振雷達")
        if not df_synergy.empty:
            st.dataframe(df_synergy, use_container_width=True, height=350)
        else:
            st.info("本日無主力共振訊號，主力資金呈現觀望。")
            
        st.markdown("<br>", unsafe_allow_html=True)
            
        st.markdown("#### 🚨 飆股起漲雷達 (爆量/布林/土洋)")
        if not df_surge.empty:
            st.dataframe(df_surge, use_container_width=True, height=350)
        else:
            st.info("本日市場量能萎縮，無符合技術面起漲之飆股訊號。")
    else:
        st.info("🕒 目前雲端尚無台股籌碼戰報資料...")

# ------------------------------------------
# 🦅 第三分頁：美股常規戰區
# ------------------------------------------
with tab_us_reg:
    us_records = load_us_data()
    if us_records:
        st.markdown("### 🦅 美股板塊與領頭羊觀測")
        
        def format_us_time(record):
            date_str = record['report_date']
            if len(date_str) == 8: return f"{date_str[:4]}/{date_str[4:6]}/{date_str[6:]} 美股戰報"
            return f"{date_str} 戰報"

        selected_us_record = st.selectbox("📖 請選擇美股戰報日期：", options=us_records, format_func=format_us_time, key="us_selectbox")
        st.markdown("<br>", unsafe_allow_html=True)
        
        st.success("**🤖 華爾街 AI 戰略推演**")
        st.write(selected_us_record.get('ai_strategy', '無 AI 分析資料'))
        st.markdown("<br>", unsafe_allow_html=True)
        
        df_overview = pd.DataFrame(selected_us_record.get('overview_data', []))
        df_leaders = pd.DataFrame(selected_us_record.get('leaders_data', []))
        
        col1, col2 = st.columns([1, 2])
        with col1:
            st.markdown("#### 📊 12大板塊資金流向")
            st.dataframe(df_overview, use_container_width=True, height=500)
        with col2:
            st.markdown("#### 🎯 強弱勢領頭羊解析")
            st.dataframe(df_leaders, use_container_width=True, height=500)
    else:
        st.info("🕒 目前雲端尚無美股戰報資料...")

# ------------------------------------------
# 🌙 第四分頁：美股盤後戰區 (精準對接修復版)
# ------------------------------------------
with tab_us_after:
    after_records = load_us_after_data()
    
    if after_records:
        # 轉換時間格式以便美化顯示
        def format_after_time(record):
            raw_time = record['report_time']
            try:
                dt = datetime.strptime(raw_time, '%Y-%m-%d %H:%M:%S')
                return dt.strftime("%m/%d %H:%M 戰報")
            except:
                return raw_time

        selected_after = st.selectbox("📖 選擇盤後戰報時段：", options=after_records, format_func=format_after_time, key="us_after_selectbox")
        
        try:
            display_time = datetime.strptime(selected_after['report_time'], '%Y-%m-%d %H:%M:%S').strftime("%Y/%m/%d %H:%M")
        except:
            display_time = selected_after['report_time']

        st.markdown(f"### 🌙 美股盤後異動監控")
        st.caption(f"報告生成時間：{display_time}")
        
        # 🤖 AI 評論防呆顯示
        st.success("**🤖 AI 盤後概念連動分析**")
        ai_text = selected_after.get('ai_analysis')
        if not ai_text or str(ai_text).strip() == "":
            st.warning("⚠️ 本次戰報未捕捉到 AI 評論 (可能因 API 連線超時或未設定金鑰)。")
        else:
            st.write(ai_text)
        
        # 📊 數據表格顯示 (已修復欄位對接)
        df_after = pd.DataFrame(selected_after.get('top_movers', []))
        if not df_after.empty:
            # 🎯 這裡的名稱已經完全對齊您爬蟲程式的輸出！
            cols = ['板塊', '代號', '名稱', '盤後漲幅(%)', '最新盤後價', '連動族群']
            df_after = df_after[[c for c in cols if c in df_after.columns]]
            
            st.markdown("#### 🚀 盤後重點異動名單")
            st.dataframe(df_after, use_container_width=True, height=450)
    else:
        st.markdown("<br><br>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.info("🌙 正在監控盤後交易中，目前尚無顯著波動戰報上傳。")
# ------------------------------------------
# 🐉 第五分頁：港陸戰區
# ------------------------------------------
with tab_hk:
    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.error("🐉 **港陸股熱錢追蹤系統規劃中**") 
        st.write("預計串接恆生指數與滬深 300 重點標的，掌握外資與北水南下的資金博弈。")

# ------------------------------------------
# 🛢️ 第六分頁：原物料與期貨戰區
# ------------------------------------------
with tab_commodities:
    comm_records = load_commodities_data()
    if comm_records:
        st.markdown("### 🛢️ 國際原物料純正期貨報價")
        
        def format_comm_time(record):
            date_str = record['report_date']
            if len(date_str) == 8: return f"{date_str[:4]}/{date_str[4:6]}/{date_str[6:]} 原物料報價"
            return f"{date_str} 報價"

        selected_comm_record = st.selectbox("📖 請選擇報價日期：", options=comm_records, format_func=format_comm_time, key="comm_selectbox")
        st.markdown("<br>", unsafe_allow_html=True)
        
        df_commodities = pd.DataFrame(selected_comm_record.get('commodities_data', []))
        if not df_commodities.empty:
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.dataframe(df_commodities, use_container_width=True)
        else:
            st.info("無原物料數據。")
    else:
        st.info("🕒 目前雲端尚無原物料戰報資料...")

# ==========================================
# ⚖️ 網頁最底部：免責聲明與版權 (法律壁壘)
# ==========================================
st.markdown("<br><br><br>", unsafe_allow_html=True)
st.divider()

disclaimer_html = """
<div style='background-color: #f8f9fa; padding: 15px; border-radius: 8px; border-left: 5px solid #d9534f; color: #555; font-size: 13px; line-height: 1.6;'>
    <strong>⚖️ 法律免責聲明 (Disclaimer)：</strong><br>
    1. <strong>資料來源：</strong> 本系統之所有盤後籌碼與報價數據，均來自於公開網路資訊（包含且不限於 台灣證券交易所、櫃買中心、Yahoo Finance 等公開 API）。<br>
    2. <strong>個人與學術用途：</strong> 本平台僅作為開發者個人之「程式自動化爬蟲測試」與「數據整合視覺化」之學術與研究用途，絕無任何營利行為。<br>
    3. <strong>無投資建議：</strong> 本平台所顯示之任何包含「飆股」、「強勢」、「避險」、「AI 預判」等字眼，純屬演算法與語言模型之自動生成結果，<strong>絕不構成任何實質之投資建議、邀約、推薦或買賣指示</strong>。<br>
    4. <strong>風險自負：</strong> 系統抓取之數據與報價可能有延遲、遺漏或系統運算錯誤。使用者應自行查核真實資訊，並自行承擔所有投資風險。本平台及開發者對任何基於本系統資訊而做出的交易決策與損失，概不負任何法律責任。
</div>
<p style='text-align: center; color: gray; font-size: 12px; margin-top: 15px;'>© 2026 AI 戰略總部 | 全球熱錢羅盤 SaaS</p>
"""
st.markdown(disclaimer_html, unsafe_allow_html=True)

