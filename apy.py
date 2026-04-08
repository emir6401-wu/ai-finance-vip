import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime, timedelta
import pytz # 👈 新增：專門對付跨國伺服器的時區套件

# ==========================================
# 🔑 雲端金鑰區 (記得填入你的真實金鑰)
# ==========================================
SUPABASE_URL = 'https://qdduovihbjzozlbuppsj.supabase.co'
SUPABASE_KEY = 'sb_publishable_EZoRnAwbrZIAmdWuUwPm-A_1sZZkMnB'
VIP_PASSWORD = 'VIP888'

st.set_page_config(page_title="AI 股市戰略總部", page_icon="📈", layout="wide")

# 大門警衛系統
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    st.title("🔒 亞洲熱錢羅盤 - VIP 登入")
    st.markdown("請輸入總監專屬通關密碼以解鎖今日戰報。")
    pwd = st.text_input("通關密碼", type="password")
    if st.button("解鎖進入"):
        if pwd == VIP_PASSWORD:
            st.session_state['logged_in'] = True
            st.rerun()
        else:
            st.error("❌ 密碼錯誤，請重新輸入或聯繫管理員！")
    st.stop()

@st.cache_resource
def init_connection():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_connection()

# ==========================================
# ⏳ 核心邏輯：計算「當日早上 6:00」到「隔天早上 6:00」的時間區間
# ==========================================
def get_time_window():
    # 強制鎖定台灣時間
    tz = pytz.timezone('Asia/Taipei')
    now = datetime.now(tz)
    
    # 如果現在時間大於早上 6 點，起點就是今天的 6:00
    if now.hour >= 6:
        start_time = now.replace(hour=6, minute=0, second=0, microsecond=0)
    # 如果現在是凌晨 1 點~5點，起點其實是「昨天」的 6:00
    else:
        start_time = (now - timedelta(days=1)).replace(hour=6, minute=0, second=0, microsecond=0)
        
    # 終點就是起點加 24 小時
    end_time = start_time + timedelta(days=1)
    return start_time.isoformat(), end_time.isoformat()

# 從雲端冰箱拿取「這個時間區間內」的所有資料
@st.cache_data(ttl=60) # 縮短快取時間到1分鐘，讓新戰報更快出現
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

# ==========================================
# 🎨 網頁介面
# ==========================================
st.title("🧭 亞洲熱錢羅盤 - VIP 專屬戰略室")
st.markdown("歡迎回來，總監。以下是最新出爐的 AI 資金流向觀測。")
st.divider() 

# 取得 6:00 至今的所有報告
records = load_daily_data()

if records:
    # 建立一個時間格式化的函數，讓選單顯示漂亮的台灣時間
    tz = pytz.timezone('Asia/Taipei')
    def format_time(record):
        # 將 Supabase 的 UTC 時間轉換為台灣時間
        dt = datetime.fromisoformat(record['created_at']).astimezone(tz)
        return dt.strftime("%Y/%m/%d - %H:%M")

    # 📖 翻書功能：建立下拉選單讓總監選擇不同時間的報告
    selected_record = st.selectbox(
        "📖 請選擇戰報時間 (點擊展開歷史紀錄)：", 
        options=records, 
        format_func=format_time
    )
    
    st.markdown("<br>", unsafe_allow_html=True) 
    
    # 以下顯示的資料，全部對應到 selected_record (被選中的那一筆)
    st.subheader("🤖 AI 戰略分析與狙擊暗示")
    st.info(selected_record['ai_strategy'])
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    df_gainers = pd.DataFrame(selected_record['gainers_data'])
    df_losers = pd.DataFrame(selected_record['losers_data'])
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🚀 資金狂潮 (漲幅榜)")
        st.dataframe(df_gainers, use_container_width=True, height=400)
    with col2:
        st.subheader("⚠️ 避險雷區 (跌幅榜)")
        st.dataframe(df_losers, use_container_width=True, height=400)
else:
    # 每天早上 6:00 一到，只要還沒傳新資料，這裡就會自動淨空
    st.warning("📊 報告區塊已於 06:00 淨空。正在等待今日的第一筆戰報上傳...")