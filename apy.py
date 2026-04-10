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
# 🌏 亞洲戰區：計算「當日早上 6:00」到「隔天早上 6:00」的時間區間
def get_time_window():
    tz = pytz.timezone('Asia/Taipei')
    now = datetime.now(tz)
    if now.hour >= 6:
        start_time = now.replace(hour=6, minute=0, second=0, microsecond=0)
    else:
        start_time = (now - timedelta(days=1)).replace(hour=6, minute=0, second=0, microsecond=0)
    end_time = start_time + timedelta(days=1)
    return start_time.isoformat(), end_time.isoformat()

# 🌏 亞洲戰區：讀取快取資料
@st.cache_data(ttl=60)
def load_daily_data():
    start_iso, end_iso = get_time_window()
    try:
        response = supabase.table("daily_reports") \
            .select("*") \
            .gte("created_at", start_iso) \
            .lt("created_at", end_iso) \
            .order("created_at", desc=True) \
            .execute()
        return response.data
    except Exception as e:
        st.error(f"連線雲端資料庫失敗: {e}")
        return []

# 🇹🇼 台股戰區：讀取最新 5 筆戰報
@st.cache_data(ttl=60)
def load_tw_data():
    try:
        response = supabase.table("tw_daily_reports") \
            .select("*") \
            .order("report_date", desc=True) \
            .limit(5) \
            .execute()
        return response.data
    except Exception as e:
        st.error(f"連線台股雲端資料庫失敗: {e}")
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
        selected_record = st.selectbox(
            "📖 請選擇戰報時間 (點擊展開歷史紀錄)：", 
            options=records, 
            format_func=format_time,
            key="asia_selectbox" 
        )
        
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
            if len(date_str) == 8:
                return f"{date_str[:4]}/{date_str[4:6]}/{date_str[6:]} 戰報"
            return f"{date_str} 戰報"

        selected_tw_record = st.selectbox(
            "📖 請選擇台股戰報日期 (保留最近五日)：", 
            options=tw_records, 
            format_func=format_tw_time,
            key="tw_selectbox" 
        )
        
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
# 🦅 第三分頁：美股常規戰區
# ------------------------------------------
with tab_us_reg:
    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.warning("🦅 **美股常規盤 AI 分析管線建置中**")
        st.write("準備對接 S&P 500、納斯達克及費半重點標的，為您總結昨夜華爾街主力的最終籌碼分佈。")
        st.progress(35, text="資料庫表單規劃進度 35%")

# ------------------------------------------
# 🌙 第四分頁：美股盤後戰區
# ------------------------------------------
with tab_us_after:
    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.info("🌙 **美股盤後突發監測站建置中**")
        st.write("專注捕捉財報發布、重要經濟數據出爐後的盤後劇烈波動，提早預判隔日台股開盤風向。")
        st.progress(20, text="API 盤後數據源串接測試中 20%")

# ------------------------------------------
# 🐉 第五分頁：港陸戰區
# ------------------------------------------
with tab_hk:
    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.error("🐉 **港陸股熱錢追蹤系統規劃中**") 
        st.write("預計串接恆生指數與滬深 300 重點標的，掌握外資與北水南下的資金博弈。")
        st.progress(10, text="資料庫串接進度 10%")

# ------------------------------------------
# 🛢️ 第六分頁：原物料與期貨戰區
# ------------------------------------------
with tab_commodities:
    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.success("🛢️ **原物料與期貨報價中心建置中**")
        st.write("黃金、原油、銅等避險與工業金屬即時行情分離監測，協助您判斷全球通膨與避險情緒。")
        st.progress(45, text="後端腳本抽離與格式化進度 45%")

# ==========================================
# 網頁最底部版權宣告
# ==========================================
st.divider()
st.markdown("<p style='text-align: center; color: gray; font-size: 12px;'>© 2026 AI 戰略總部 | 資訊僅供決策參考，不構成實質交易建議。</p>", unsafe_allow_html=True)
