import streamlit as st
import pandas as pd
from supabase import create_client, Client

# ==========================================
# 🔑 雲端金鑰區 
# ==========================================
SUPABASE_URL = 'https://qdduovihbjzozlbuppsj.supabase.co'
SUPABASE_KEY = 'sb_publishable_EZoRnAwbrZIAmdWuUwPm-A_1sZZkMnB'
VIP_PASSWORD = 'VIP888'  # 👈 新增：總監專屬通關密碼 (你可以隨意修改)

# 網頁基本設定
st.set_page_config(page_title="AI 股市戰略總部", page_icon="📈", layout="wide")

# ==========================================
# 🛡️ 大門警衛系統 (登入驗證)
# ==========================================
# 初始化登入狀態
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

# 如果還沒登入，就顯示輸入密碼的畫面
if not st.session_state['logged_in']:
    st.title("🔒 亞洲熱錢羅盤 - VIP 登入")
    st.markdown("請輸入總監專屬通關密碼以解鎖今日戰報。")
    
    # 建立一個輸入框，type="password" 會讓輸入的字變成黑點
    pwd = st.text_input("通關密碼", type="password")
    
    if st.button("解鎖進入"):
        if pwd == VIP_PASSWORD:
            st.session_state['logged_in'] = True
            st.rerun() # 密碼正確，重新整理頁面以進入大廳
        else:
            st.error("❌ 密碼錯誤，請重新輸入或聯繫管理員！")
            
    st.stop() # 🛑 關鍵指令：只要沒登入，程式就在這裡停止，絕對不載入後面的資料！

# ==========================================
# 🎨 成功登入後：開始繪製網頁介面 (跟原本一樣)
# ==========================================
@st.cache_resource
def init_connection():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_connection()

@st.cache_data(ttl=600)
def load_latest_data():
    try:
        response = supabase.table("daily_reports").select("*").order("created_at", desc=True).limit(1).execute()
        if response.data:
            return response.data[0]
        return None
    except Exception as e:
        st.error(f"連線雲端資料庫失敗: {e}")
        return None

st.title("🧭 亞洲熱錢羅盤 - VIP 專屬戰略室")
st.markdown("歡迎回來，總監。以下是最新出爐的 AI 資金流向觀測。")
st.divider() 

data = load_latest_data()

if data:
    st.header(f"📅 戰報日期：{data['report_date']}")
    st.markdown("<br>", unsafe_allow_html=True) 
    
    st.subheader("🤖 AI 戰略分析與狙擊暗示")
    st.info(data['ai_strategy'])
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    df_gainers = pd.DataFrame(data['gainers_data'])
    df_losers = pd.DataFrame(data['losers_data'])
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🚀 資金狂潮 (漲幅榜)")
        st.dataframe(df_gainers, use_container_width=True, height=400)
        
    with col2:
        st.subheader("⚠️ 避險雷區 (跌幅榜)")
        st.dataframe(df_losers, use_container_width=True, height=400)
else:
    st.warning("目前雲端資料庫沒有資料喔！請先執行 test.py 上傳今日戰報。")