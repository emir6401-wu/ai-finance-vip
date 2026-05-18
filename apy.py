import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime, timedelta
import pytz
import plotly.graph_objects as go
import time
import json 

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

# 🎯 核心升級 1：將亞洲戰區快取極速縮短至 15 秒，配合網頁的高頻自動刷新率
@st.cache_data(ttl=15)
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
# ⚡ ⚡ 第六分頁專用：光速資料提領引擎
# ==========================================
@st.cache_data(ttl=15)
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
# 🌏 第一分頁：亞洲戰區 (📱 鋼鐵定格防誤觸 + 交易所時間軸動態稀釋版)
# ------------------------------------------
with tab_asia:
    records = load_daily_data()
    if records:
        try:
            latest_record = records[0]
            data_package = None
            try:
                data_package = json.loads(latest_record['ai_strategy'])
            except (json.JSONDecodeError, TypeError):
                data_package = None
            
            if data_package and "trends" in data_package:
                st.info(f"⏰ **雲端大數據最新同步時間：{data_package['latest_update']}** (每 5 分鐘高頻率自動刷新 ｜ 虛線橫線為【昨收價 0%】基準線，時間軸已對齊【交易所當地開盤時間】)")
                st.markdown("---")
                
                def draw_matrix_chart(group_name, country_name, trends_data):
                    fig = go.Figure()
                    has_line = False
                    
                    for ticker, info in trends_data.items():
                        if info.get('group') == group_name and info.get('country') == country_name:
                            if info.get('times') and len(info['times']) > 0:
                                has_line = True
                                fig.add_trace(go.Scatter(
                                    x=info['times'],
                                    y=info['pcts'],
                                    mode='lines+markers',
                                    marker=dict(size=4),
                                    name=info['name'],
                                    line=dict(width=2.2),
                                    customdata=info['closes'],
                                    hovertemplate='<b>%{text}</b><br>昨收相對變動: %{y:+.2f}%<br>最新報價: %{customdata:,}<extra></extra>',
                                    text=[info['name']]*len(info['times'])
                                ))
                                
                    if not has_line: return None
                    
                    all_times = info['times']
                    if len(all_times) > 0:
                        step = max(1, len(all_times) // 5)
                        tick_vals = [all_times[idx] for idx in range(0, len(all_times), step)]
                        if all_times[-1] not in tick_vals:
                            tick_vals.append(all_times[-1])
                    else:
                        tick_vals = []

                    fig.update_layout(
                        title=dict(
                            text=f"<b>{'🇯🇵 日本' if country_name=='日本' else '🇰🇷 韓國'} - {group_name[3:]}</b>",
                            font=dict(size=14, color='#2c3e50')
                        ),
                        height=350, 
                        margin=dict(l=45, r=15, t=55, b=55), 
                        xaxis=dict(
                            type='category',
                            tickmode='array',
                            tickvals=tick_vals, 
                            gridcolor='#f5f5f5', 
                            showline=True, 
                            linecolor='#bdc3c7', 
                            tickangle=0, 
                            automargin=True,
                            fixedrange=True 
                        ),
                        yaxis=dict(
                            title="昨收相對漲跌 (%)", 
                            gridcolor='#f5f5f5', 
                            showline=True, 
                            linecolor='#bdc3c7', 
                            automargin=True,
                            fixedrange=True 
                        ),
                        plot_bgcolor='white',
                        paper_bgcolor='white',
                        legend=dict(
                            orientation="h", 
                            yanchor="top", 
                            y=-0.18, 
                            xanchor="left", 
                            x=0, 
                            font=dict(size=9.5)
                        ),
                        showlegend=True
                    )
                    fig.add_shape(type="line", x0=0, y0=0, x1=1, y1=0, xref='paper', yref='y', line=dict(color="#95a5a6", width=1.2, dash="dash"))
                    return fig

                GRID_GROUPS = ["1. 核心設備區", "2. 材料與晶圓片", "3. 封裝基板與電容", "4. 晶片與記憶體代工"]
                
                for group_title in GRID_GROUPS:
                    col_ja, col_ko = st.columns(2)
                    
                    with col_ja:
                        fig_ja = draw_matrix_chart(group_title, "日本", data_package['trends'])
                        if fig_ja: 
                            st.plotly_chart(fig_ja, use_container_width=True, key=f"web_ja_{group_title}", config={'scrollZoom': False, 'displayModeBar': False, 'responsive': True})
                        else: st.info(f"日本 - {group_title[3:]} 盤中暫無有效波動線")
                        
                    with col_ko:
                        fig_ko = draw_matrix_chart(group_title, "韓國", data_package['trends'])
                        if fig_ko: 
                            st.plotly_chart(fig_ko, use_container_width=True, key=f"web_ko_{group_title}", config={'scrollZoom': False, 'displayModeBar': False, 'responsive': True})
                        else: st.info(f"韓國 - {group_title[3:]} 盤中暫無有效波動線")
                    st.markdown("<br>", unsafe_allow_html=True)
            else:
                st.warning("🔄 網頁端框架已成功升級！目前資料庫中皆為週末休市前的舊版文字紀錄。")
                st.info("💡 **下一輪開盤提示**：當您的 Mac 端發射站重啟並發射今日第一根 5 分鐘 K 線 JSON 數據後，這張紅色的報報就會消失，4x2 矩陣大畫布會立刻自動成型！")
        except Exception as e:
            st.error(f"❌ 矩陣畫布渲染受阻: {e}")
    else:
        st.info("🕒 報告區塊已於 06:00 淨空。正在等待今日的第一筆亞洲戰報上傳...")

# ------------------------------------------
# 🇹🇼 第二分頁：台股主力動向 (保持原樣，絕不變動)
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
# 🦅 第三分頁：美股常規戰區 (保持原樣，絕不變動)
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
# 🌙 第四分頁：美股盤後戰區 (保持原樣，絕不變動)
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
# 🐉 第五分頁：港陸戰區 (保持原樣，絕不變動)
# ------------------------------------------
with tab_hk:
    st.error("🐉 **港陸股熱錢追蹤系統規劃中**") 

# ------------------------------------------
# ⚡ ⚡ 第六分頁：5分即時監控 (保持原樣，絕不變動)
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
        st.info(f"最後同步時間：{datetime.now(pytz.timezone('Asia/Taipei')).strftime('%H:%M:%S')}")
    else:
        st.warning("🔄 正在等待本地雷達站上傳首次數據，請確保您的 RAD.py 正在執行中...")

# ==========================================
# ⚖️ 網頁最底部：免責聲明與版權 (保持原樣，絕不變動)
# ==========================================
st.markdown("<br><br><br>", unsafe_allow_html=True)
st.divider()
disclaimer_html = """
<div style='background-color: #f8f9fa; padding: 15px; border-radius: 8px; border-left: 5px solid #d9534f; color: #555; font-size: 13px; line-height: 1.6;'>
    <strong>⚖️ 法律免責聲明 (Disclaimer)：</strong><br>
    本平台所提供之全球金融市場、日韓半導體板塊及各類期貨、加密貨幣之 5 分鐘與盤後量化大數據，純屬程式 automatic 自動化運算與邏輯推演之歷史軌跡呈現。文內所有數據、圖表及自動化分析摘要，僅供學術探討與量化研究參考，絕不構成任何形式的個股推薦、買賣邀約或投資建議。金融市場交易具備極高風險，大數據與過去走勢不代表未來獲利保證。資訊提供者不對 any 讀者之交易決策負擔 any 法律責任，亦不承擔因系統延遲、數據誤差或交易所突發中斷所引發的任何交易損失。
</div>
<p style='text-align: center; color: gray; font-size: 12px; margin-top: 15px;'>© 2026 AI 戰略總部 | 全球熱錢羅盤 SaaS</p>
"""
st.markdown(disclaimer_html, unsafe_allow_html=True)

# ==============================================================================
# 🎯 核心升級 2：全自動自發性網頁刷新心臟 (部署於程式碼最末端，外部獨立運作)
# ==============================================================================
REFRESH_INTERVAL = 30  # 🎯 設定網頁每 30 秒自動大重整一次，秒刷最新盤中 K 線
countdown_placeholder = st.sidebar.empty()

for remaining in range(REFRESH_INTERVAL, 0, -1):
    countdown_placeholder.markdown(f"🔄 **雷達自動更新倒數：{remaining:2d} 秒**")
    time.sleep(1)

st.rerun()
