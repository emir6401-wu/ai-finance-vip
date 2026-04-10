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
    
    # 👈 左側區塊：結合雲端計數器的淺色系看板
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

    # 🎯 中間區塊：登入主畫面
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
                
    st.stop() # 🛑 阻擋未登入者往下看

# 登入成功後，在側邊欄也顯示一下尊榮的計數器
st.sidebar.metric(label="🔥 總監專屬：累積訪問人次", value=f"{new_visits} 次")

# ==========================================
# ⏳ 資料庫讀取邏輯區
# ==========================================
# 🌏 亞洲戰區：計算時間區間
def get_time_window():
    tz = pytz.timezone('Asia/Taipei')
    now = datetime.now(tz)
    if now.hour >= 6:
        start_time = now.replace(hour=6, minute=0, second=0, microsecond=0)
    else:
        start_time = (now - timedelta(days=1)).replace(hour=6, minute=0, second=0, microsecond=0)
    end_time = start_time + timedelta(days=1)
    return start_time.isoformat(), end_time.isoformat()

# 🌏 亞洲戰區讀取
@st.cache_data(ttl=60)
def load_daily_data():
    start_iso, end_iso = get_time_window()
    try:
        response = supabase.table("daily_reports").select("*").gte("created_at", start_iso).lt("created_at", end_iso).order("created_at", desc=True).execute()
        return response.data
    except: return []

# 🇹🇼 台股戰區讀取
@st.cache_data(ttl=60)
def load_tw_data():
    try:
        response = supabase.table("tw_daily_reports").select("*").order("report_date", desc=True).limit(5).execute()
        return response.data
    except: return []

# 🦅 美股戰區讀取
@st.cache_data(ttl=60)
def load_us_data():
    try:
        response = supabase.table("us_market_reports").select("*").order("report_date", desc=True).limit(5).execute()
        return response.data
    except Exception as e:
        st.error(f"連線美股資料庫失敗: {e}")
        return []

# 🛢️ 原物料戰區讀取
@st.cache_data(ttl=60)
def load_commodities_data():
    try:
        response = supabase.table("commodities_reports").select("*").order("report_date", desc=True).limit(5).execute()
        return response.data
    except Exception as e:
        st.error(f"連線原物料資料庫失敗: {e}")
        return []


# ==========================================
# 🎨 網頁主介面：六大戰略分頁
# ==========================================
st.title("🧭 全球熱錢羅盤 - 戰略決策室")
st.markdown("歡迎回來，總監。請選擇您要查看的資金戰區。")

# 🗂️ 建立六大戰區分頁
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
# 🇹🇼 第二分頁：台股主力動向
# ------------------------------------------
with tab_tw:
    tw_records = load_tw_data()
    if tw_records:
        st.markdown("### 🇹🇼 台股籌碼雷達觀測")
        
        def format_tw_time(record):
            date_str = record['report_date']
            if len(date_str) == 8: return f"{date_str[:4]}/{date_str[4:6]}/{date_str[6:]} 戰報"
            return f"{date_str} 戰報"

        selected_tw_record = st.selectbox("📖 請選擇台股戰報日期：", options=tw_records, format_func=format_tw_time, key="tw_selectbox")
        st.markdown("<br>", unsafe_allow_html=True)
        
        df_surge = pd.DataFrame(selected_tw_record.get('surge_data', []))
        df_synergy = pd.DataFrame(selected_tw_record.get('synergy_data', []))
        
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
        st.info("🕒 目前雲端尚無台股戰報資料，請等待後台爬蟲執行與上傳...")

# ------------------------------------------
# 🦅 第三分頁：美股常規戰區 (🚀全新上線)
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
        st.info("🕒 目前雲端尚無美股戰報資料，請等待後台爬蟲執行與上傳...")

# ------------------------------------------
# 🌙 第四分頁：美股盤後戰區 (準備中)
# ------------------------------------------
with tab_us_after:
    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.info("🌙 **美股盤後突發監測站建置中**")
        st.write("專注捕捉財報發布、重要經濟數據出爐後的盤後劇烈波動，提早預判隔日台股開盤風向。")
        st.progress(20, text="API 盤後數據源串接測試中 20%")

# ------------------------------------------
# 🐉 第五分頁：港陸戰區 (準備中)
# ------------------------------------------
with tab_hk:
    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.error("🐉 **港陸股熱錢追蹤系統規劃中**") 
        st.write("預計串接恆生指數與滬深 300 重點標的，掌握外資與北水南下的資金博弈。")
        st.progress(10, text="資料庫串接進度 10%")

# ------------------------------------------
# 🛢️ 第六分頁：原物料與期貨戰區 (🚀全新上線)
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
            # 讓原物料置中並稍微限制寬度，看起來比較精緻
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
