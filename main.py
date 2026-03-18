import streamlit as st
import pandas as pd
import altair as alt
import streamlit.components.v1 as components
import time
from datetime import datetime, date, timedelta, timezone
from streamlit_gsheets import GSheetsConnection

# ==========================================
# 1. ページ設定 & デザイン調整
# ==========================================
st.set_page_config(page_title="ぱいん成績管理", layout="wide", page_icon="🀄")

hide_style = """
    <style>
    /* ========== Google Fonts ========== */
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;500;700;900&family=Zen+Kaku+Gothic+New:wght@400;700;900&display=swap');

    /* ========== ベースリセット ========== */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}

    /* ========== カラーパレット ========== */
    :root {
        --bg-base:       #0f1117;
        --bg-card:       #1a1d2e;
        --bg-card2:      #222537;
        --bg-input:      #1e2132;
        --accent:        #f0c040;
        --accent2:       #e07b39;
        --accent-soft:   rgba(240,192,64,0.12);
        --accent2-soft:  rgba(224,123,57,0.12);
        --green:         #4caf87;
        --green-soft:    rgba(76,175,135,0.12);
        --red:           #e05c5c;
        --red-soft:      rgba(224,92,92,0.12);
        --blue:          #5b9cf6;
        --blue-soft:     rgba(91,156,246,0.12);
        --text-primary:  #e8e8f0;
        --text-muted:    #8890a8;
        --border:        rgba(255,255,255,0.07);
        --border-accent: rgba(240,192,64,0.3);
        --shadow:        0 4px 24px rgba(0,0,0,0.4);
        --radius:        12px;
        --radius-sm:     8px;
    }

    /* ========== 全体背景 ========== */
    .stApp {
        background-color: var(--bg-base);
        font-family: 'Noto Sans JP', sans-serif;
        color: var(--text-primary);
    }
    .main .block-container {
        padding: 1.5rem 2rem 3rem;
        max-width: 1100px;
    }

    /* ========== サイドバー非表示 ========== */
    [data-testid="stSidebar"] { display: none; }

    /* ========== ヘッダー / タイトル ========== */
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Zen Kaku Gothic New', sans-serif;
        color: var(--text-primary) !important;
    }
    h1 { 
        font-size: 1.8rem !important;
        font-weight: 900 !important;
        letter-spacing: 0.03em;
        border-bottom: 2px solid var(--border-accent);
        padding-bottom: 0.5rem;
        margin-bottom: 1.5rem !important;
    }
    h2 { font-size: 1.3rem !important; font-weight: 700 !important; }
    h3 { font-size: 1.1rem !important; font-weight: 700 !important; }

    /* ========== カード共通 ========== */
    .pine-card {
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: var(--radius);
        padding: 1.2rem 1.4rem;
        margin-bottom: 1rem;
        box-shadow: var(--shadow);
    }
    .pine-card-accent {
        background: linear-gradient(135deg, var(--bg-card) 0%, rgba(240,192,64,0.06) 100%);
        border-color: var(--border-accent);
    }

    /* ========== ホームボタングリッド ========== */
    .home-nav-btn {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: var(--radius);
        padding: 1.1rem 1.3rem;
        color: var(--text-primary);
        font-size: 1rem;
        font-weight: 700;
        font-family: 'Zen Kaku Gothic New', sans-serif;
        cursor: pointer;
        transition: all 0.18s ease;
        width: 100%;
        text-decoration: none;
        box-shadow: 0 2px 8px rgba(0,0,0,0.3);
    }
    .home-nav-btn:hover {
        border-color: var(--accent);
        background: var(--accent-soft);
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(240,192,64,0.15);
    }
    .home-nav-btn .icon {
        font-size: 1.5rem;
        min-width: 2rem;
        text-align: center;
    }

    /* ========== Streamlit ボタン ========== */
    .stButton > button {
        background: var(--bg-card2) !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius-sm) !important;
        font-family: 'Noto Sans JP', sans-serif !important;
        font-weight: 500 !important;
        padding: 0.5rem 1rem !important;
        transition: all 0.15s ease !important;
    }
    .stButton > button:hover {
        border-color: var(--accent) !important;
        background: var(--accent-soft) !important;
        color: var(--accent) !important;
    }
    .stButton > button[kind="primary"] {
        background: var(--accent) !important;
        color: #0f1117 !important;
        border-color: var(--accent) !important;
        font-weight: 700 !important;
    }
    .stButton > button[kind="primary"]:hover {
        background: #f5d060 !important;
        border-color: #f5d060 !important;
        color: #0f1117 !important;
    }

    /* 戻るボタン専用 */
    .back-btn > button {
        background: transparent !important;
        border-color: var(--border) !important;
        color: var(--text-muted) !important;
        font-size: 0.85rem !important;
        padding: 0.3rem 0.8rem !important;
    }
    .back-btn > button:hover {
        color: var(--text-primary) !important;
        border-color: var(--text-primary) !important;
        background: transparent !important;
    }

    /* ========== セレクトボックス / インプット ========== */
    .stSelectbox > div > div,
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stDateInput > div > div > input,
    .stTextArea > div > div > textarea {
        background-color: var(--bg-input) !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius-sm) !important;
        font-family: 'Noto Sans JP', sans-serif !important;
    }
    .stSelectbox > div > div:focus-within,
    .stTextInput > div > div:focus-within {
        border-color: var(--accent) !important;
        box-shadow: 0 0 0 2px var(--accent-soft) !important;
    }
    .stSelectbox label,
    .stTextInput label,
    .stNumberInput label,
    .stDateInput label,
    .stTextArea label,
    .stRadio label,
    .stCheckbox label {
        color: var(--text-muted) !important;
        font-size: 0.82rem !important;
        font-weight: 500 !important;
        letter-spacing: 0.05em !important;
        text-transform: uppercase !important;
    }

    /* ========== ラジオボタン ========== */
    .stRadio > div {
        gap: 0.5rem !important;
        flex-wrap: wrap !important;
    }
    .stRadio > div > label {
        background: var(--bg-card2) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius-sm) !important;
        padding: 0.35rem 0.8rem !important;
        color: var(--text-primary) !important;
        font-size: 0.9rem !important;
        text-transform: none !important;
        letter-spacing: 0 !important;
        cursor: pointer !important;
        transition: all 0.15s ease !important;
    }
    .stRadio > div > label:has(input:checked) {
        background: var(--accent-soft) !important;
        border-color: var(--accent) !important;
        color: var(--accent) !important;
        font-weight: 700 !important;
    }
    [data-baseweb="radio"] input { display: none !important; }
    [data-baseweb="radio"] > div { display: none !important; }

    /* ========== チェックボックス ========== */
    .stCheckbox > label {
        color: var(--text-primary) !important;
        font-size: 0.9rem !important;
        text-transform: none !important;
        letter-spacing: 0 !important;
    }

    /* ========== タブ ========== */
    .stTabs [data-baseweb="tab-list"] {
        background: var(--bg-card) !important;
        border-radius: var(--radius) var(--radius) 0 0 !important;
        border: 1px solid var(--border) !important;
        border-bottom: none !important;
        padding: 0.3rem 0.5rem !important;
        gap: 0.2rem !important;
    }
    .stTabs [data-baseweb="tab"] {
        background: transparent !important;
        color: var(--text-muted) !important;
        border-radius: var(--radius-sm) !important;
        font-family: 'Noto Sans JP', sans-serif !important;
        font-size: 0.85rem !important;
        font-weight: 500 !important;
        padding: 0.4rem 0.8rem !important;
        border: none !important;
        transition: all 0.15s ease !important;
    }
    .stTabs [aria-selected="true"] {
        background: var(--accent-soft) !important;
        color: var(--accent) !important;
        font-weight: 700 !important;
    }
    .stTabs [data-baseweb="tab-panel"] {
        background: var(--bg-card) !important;
        border: 1px solid var(--border) !important;
        border-top: none !important;
        border-radius: 0 0 var(--radius) var(--radius) !important;
        padding: 1.2rem !important;
    }

    /* ========== メトリクス ========== */
    [data-testid="stMetric"] {
        background: var(--bg-card) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius) !important;
        padding: 0.9rem 1.1rem !important;
        box-shadow: var(--shadow) !important;
    }
    [data-testid="stMetricLabel"] {
        color: var(--text-muted) !important;
        font-size: 0.78rem !important;
        font-weight: 600 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.06em !important;
    }
    [data-testid="stMetricValue"] {
        color: var(--accent) !important;
        font-size: 1.5rem !important;
        font-weight: 900 !important;
        font-family: 'Zen Kaku Gothic New', sans-serif !important;
    }
    [data-testid="stMetricDelta"] { font-size: 0.8rem !important; }

    /* ========== データフレーム ========== */
    .stDataFrame {
        border: 1px solid var(--border) !important;
        border-radius: var(--radius) !important;
        overflow: hidden !important;
    }
    [data-testid="stDataFrame"] table {
        background: var(--bg-card) !important;
        color: var(--text-primary) !important;
    }
    [data-testid="stDataFrame"] th {
        background: var(--bg-card2) !important;
        color: var(--text-muted) !important;
        font-size: 0.78rem !important;
        font-weight: 600 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05em !important;
        border-bottom: 1px solid var(--border) !important;
        padding: 0.6rem 0.8rem !important;
    }
    [data-testid="stDataFrame"] td {
        border-bottom: 1px solid var(--border) !important;
        padding: 0.55rem 0.8rem !important;
        font-size: 0.88rem !important;
    }
    [data-testid="stDataFrame"] tr:hover td {
        background: var(--accent-soft) !important;
        cursor: pointer;
    }

    /* ========== アラート / インフォ ========== */
    .stSuccess, .stInfo, .stWarning, .stError {
        border-radius: var(--radius) !important;
        border: 1px solid !important;
        font-size: 0.9rem !important;
    }
    .stSuccess { 
        background: var(--green-soft) !important; 
        border-color: var(--green) !important;
        color: var(--green) !important;
    }
    .stInfo { 
        background: var(--blue-soft) !important; 
        border-color: var(--blue) !important;
        color: var(--blue) !important;
    }
    .stWarning { 
        background: var(--accent2-soft) !important; 
        border-color: var(--accent2) !important;
        color: var(--accent2) !important;
    }
    .stError { 
        background: var(--red-soft) !important; 
        border-color: var(--red) !important;
        color: var(--red) !important;
    }

    /* ========== フォーム ========== */
    [data-testid="stForm"] {
        background: var(--bg-card) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius) !important;
        padding: 1.2rem !important;
    }

    /* ========== スライダー ========== */
    .stSlider > div > div > div > div {
        background: var(--accent) !important;
    }

    /* ========== 区切り線 ========== */
    hr {
        border-color: var(--border) !important;
        margin: 1.2rem 0 !important;
    }

    /* ========== スピナー ========== */
    .stSpinner > div { border-top-color: var(--accent) !important; }

    /* ========== キャプション ========== */
    .stCaption, [data-testid="stCaptionContainer"] {
        color: var(--text-muted) !important;
        font-size: 0.8rem !important;
    }

    /* ========== スコアシート テーブル ========== */
    .score-sheet {
        border-collapse: collapse;
        width: 100%;
        margin-bottom: 1.5rem;
        font-family: 'Noto Sans JP', sans-serif;
        color: var(--text-primary);
        background: var(--bg-card);
        border-radius: var(--radius);
        overflow: hidden;
        box-shadow: var(--shadow);
    }
    .score-sheet th, .score-sheet td {
        border: 1px solid var(--border);
        padding: 7px 6px;
        text-align: center;
        font-size: 13px;
        vertical-align: middle;
    }
    .score-sheet th {
        background: var(--bg-card2);
        color: var(--text-muted);
        font-weight: 600;
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .score-sheet .set-header {
        background: linear-gradient(90deg, rgba(240,192,64,0.15) 0%, transparent 100%);
        text-align: left;
        padding-left: 14px;
        font-weight: 700;
        font-size: 14px;
        color: var(--accent);
        border-bottom: 1px solid var(--border-accent);
    }
    .rank-num {
        font-weight: 700;
        font-size: 15px;
        margin-left: 5px;
        display: inline-block;
        width: 22px;
        text-align: center;
    }
    .cell-top {
        background: rgba(240,192,64,0.07) !important;
    }
    .rank-special {
        background: var(--accent);
        color: #0f1117;
        border-radius: 50%;
        width: 22px;
        height: 22px;
        line-height: 22px;
        font-size: 12px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
    }
    .score-sheet .summary-row td {
        background: rgba(240,192,64,0.08);
        font-weight: 700;
        border-top: 2px solid var(--border-accent);
        color: var(--accent);
    }

    /* ========== 統計テーブル ========== */
    .stats-table {
        border-collapse: collapse;
        width: 100%;
        margin-bottom: 1.2rem;
        font-family: 'Noto Sans JP', sans-serif;
        border-radius: var(--radius);
        overflow: hidden;
        box-shadow: var(--shadow);
    }
    .stats-table th {
        background: var(--bg-card2);
        color: var(--text-muted);
        padding: 10px;
        border: 1px solid var(--border);
        text-align: center;
        font-weight: 600;
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .stats-table td {
        background: var(--bg-card);
        color: var(--text-primary);
        padding: 14px;
        border: 1px solid var(--border);
        text-align: center;
        font-weight: 700;
        font-size: 17px;
    }
    .stats-sub {
        font-size: 11px;
        color: var(--text-muted);
        display: block;
        margin-top: 3px;
    }

    /* ========== 席入力カード ========== */
    .seat-label {
        display: inline-block;
        background: var(--accent);
        color: #0f1117;
        font-weight: 900;
        font-size: 0.78rem;
        letter-spacing: 0.08em;
        padding: 2px 10px;
        border-radius: 4px;
        margin-bottom: 0.6rem;
    }

    /* ========== 入力セクション区切り ========== */
    .section-divider {
        border: none;
        border-top: 1px dashed var(--border);
        margin: 0.8rem 0;
    }

    /* ========== ホームヘッダー ========== */
    .home-header {
        text-align: center;
        padding: 1.5rem 0 2rem;
        margin-bottom: 0.5rem;
    }
    .home-header .app-title {
        font-family: 'Zen Kaku Gothic New', sans-serif;
        font-size: 2.2rem;
        font-weight: 900;
        color: var(--accent);
        letter-spacing: 0.05em;
        line-height: 1.2;
    }
    .home-header .app-sub {
        color: var(--text-muted);
        font-size: 0.85rem;
        margin-top: 0.3rem;
        letter-spacing: 0.1em;
    }

    /* ========== バッジ ========== */
    .badge {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.04em;
    }
    .badge-a { background: var(--blue-soft); color: var(--blue); border: 1px solid var(--blue); }
    .badge-b { background: var(--accent2-soft); color: var(--accent2); border: 1px solid var(--accent2); }
    .badge-as { background: var(--green-soft); color: var(--green); border: 1px solid var(--green); }
    .badge-bs { background: var(--red-soft); color: var(--red); border: 1px solid var(--red); }

    /* ========== data_editor ========== */
    [data-testid="stDataEditor"] {
        border: 1px solid var(--border) !important;
        border-radius: var(--radius) !important;
    }

    /* ========== ナンバー入力 ========== */
    .stNumberInput button {
        background: var(--bg-card2) !important;
        border: 1px solid var(--border) !important;
        color: var(--text-primary) !important;
    }
    </style>
"""
st.markdown(hide_style, unsafe_allow_html=True)

# ==========================================
# 2. パスワード認証
# ==========================================

    

# ==========================================
# 3. データ管理関数 (変更なし)
# ==========================================
SHEET_SCORE = "score"
SHEET_MEMBER = "members"
SHEET_LOG = "logs"
SHEET_PROFIT = "daily_profits"

EXPECTED_COLS = [
    "GameNo", "TableNo", "SetNo", "日時", "備考",
    "Aさん", "Aタイプ", "A着順",
    "Bさん", "Bタイプ", "B着順",
    "Cさん", "Cタイプ", "C着順"
]

def get_conn():
    return st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=60)
def fetch_data_cached(_conn, sheet_name):
    return _conn.read(worksheet=sheet_name, ttl=0)

def fetch_data_fresh(conn, sheet_name):
    max_retries = 3
    for i in range(max_retries):
        try:
            return conn.read(worksheet=sheet_name, ttl=0)
        except Exception:
            if i < max_retries - 1:
                time.sleep(2)
                continue
            else:
                raise

def process_score_df(df):
    if df.empty:
        return pd.DataFrame(columns=EXPECTED_COLS)
    df.columns = df.columns.astype(str).str.strip()
    missing_cols = [c for c in EXPECTED_COLS if c not in df.columns]
    if missing_cols:
        return None
    numeric_cols = ["GameNo", "TableNo", "SetNo", "A着順", "B着順", "C着順"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
    df = df.fillna("")
    if "日時" in df.columns:
        df["日時Obj"] = pd.to_datetime(df["日時"], errors='coerce')
        df["日時Obj"] = df["日時Obj"].fillna(pd.Timestamp("1900-01-01"))
        df["論理日付"] = (df["日時Obj"] - timedelta(hours=9)).dt.date
        df = df.sort_values(["論理日付", "TableNo", "日時Obj"])
        if not df.empty:
            df["DailyNo"] = df.groupby(["論理日付", "TableNo"]).cumcount() + 1
        else:
            df["DailyNo"] = []
    else:
        df["DailyNo"] = []
    return df

def load_score_data():
    conn = get_conn()
    try:
        df = fetch_data_cached(conn, SHEET_SCORE)
        processed_df = process_score_df(df)
        if processed_df is None:
            fetch_data_cached.clear()
            df = fetch_data_cached(conn, SHEET_SCORE)
            processed_df = process_score_df(df)
        if processed_df is None:
            st.error("⚠️ データの読み込みエラー: スプレッドシートの列名が正しく認識できませんでした。")
            st.stop()
        return processed_df
    except Exception:
        return pd.DataFrame(columns=EXPECTED_COLS)

def load_score_data_fresh():
    conn = get_conn()
    try:
        df = fetch_data_fresh(conn, SHEET_SCORE)
    except Exception as e:
        st.error(f"データの読み込みに失敗しました: {e}")
        st.stop()
    processed_df = process_score_df(df)
    if processed_df is None:
        st.error("⚠️ 保存エラー: 最新のスプレッドシート形式が不正です。保存を中止しました。")
        st.stop()
    return processed_df

def save_score_data(df):
    conn = get_conn()
    missing_cols = [c for c in EXPECTED_COLS if c not in df.columns]
    if missing_cols:
        st.error("保存データに不備があります。処理を中止しました。")
        st.stop()
    df_to_save = df[EXPECTED_COLS]
    if "GameNo" in df_to_save.columns:
        df_to_save["GameNo"] = pd.to_numeric(df_to_save["GameNo"], errors='coerce').fillna(0)
        df_to_save = df_to_save.sort_values("GameNo")
    conn.update(worksheet=SHEET_SCORE, data=df_to_save)
    time.sleep(1)
    fetch_data_cached.clear()

def save_action_log(action, game_no, detail=""):
    conn = get_conn()
    try:
        df_log = fetch_data_fresh(conn, SHEET_LOG)
    except:
        df_log = pd.DataFrame(columns=["日時", "操作", "GameNo", "詳細"])
    jst_now = datetime.now(timezone(timedelta(hours=9), 'JST')).strftime("%Y-%m-%d %H:%M:%S")
    new_log = pd.DataFrame([{"日時": jst_now, "操作": action, "GameNo": game_no, "詳細": detail}])
    df_log = pd.concat([df_log, new_log], ignore_index=True)
    conn.update(worksheet=SHEET_LOG, data=df_log)
    fetch_data_cached.clear()

def load_log_data():
    conn = get_conn()
    try:
        df = fetch_data_cached(conn, SHEET_LOG)
    except:
        return pd.DataFrame()
    if df.empty: return pd.DataFrame(columns=["日時", "操作", "GameNo", "詳細"])
    if "日時" in df.columns:
        df = df.sort_values("日時", ascending=False)
    return df

def load_member_data():
    conn = get_conn()
    try:
        df = fetch_data_cached(conn, SHEET_MEMBER).fillna("")
        if "名前" not in df.columns: df["名前"] = []
        if "登録日" not in df.columns: df["登録日"] = []
        if "最大飜数" not in df.columns: df["最大飜数"] = 0
        if "役満回数" not in df.columns: df["役満回数"] = 0
        if "タイプ" not in df.columns: df["タイプ"] = "A客"
        if "最大飜数詳細" not in df.columns: df["最大飜数詳細"] = ""
        if "最大飜数記録日" not in df.columns: df["最大飜数記録日"] = ""
        df["最大飜数"] = pd.to_numeric(df["最大飜数"], errors='coerce').fillna(0).astype(int)
        df["役満回数"] = pd.to_numeric(df["役満回数"], errors='coerce').fillna(0).astype(int)
        return df
    except:
        return pd.DataFrame({"名前": [], "登録日": [], "最大飜数": [], "役満回数": [], "タイプ": [], "最大飜数詳細": [], "最大飜数記録日": []})

def save_member_data(df):
    conn = get_conn()
    conn.update(worksheet=SHEET_MEMBER, data=df)
    fetch_data_cached.clear()

def get_all_member_names():
    df_mem = load_member_data()
    all_members = df_mem["名前"].tolist() if not df_mem.empty else []
    df_score = load_score_data()
    if df_score.empty:
        return sorted(list(set(all_members)))
    last_played = {}
    for _, row in df_score.iterrows():
        dt = row["日時Obj"]
        for seat in ["A", "B", "C"]:
            name = row[f"{seat}さん"]
            if name:
                if name not in last_played or dt > last_played[name]:
                    last_played[name] = dt
    formatted_list = []
    for m in all_members:
        last_dt = last_played.get(m, pd.Timestamp("1900-01-01"))
        formatted_list.append({"name": m, "last_dt": last_dt})
    for m in last_played.keys():
        if m not in all_members:
            formatted_list.append({"name": m, "last_dt": last_played[m]})
    sorted_data = sorted(formatted_list, key=lambda x: x["last_dt"], reverse=True)
    return [x["name"] for x in sorted_data]

def load_profit_data():
    conn = get_conn()
    try:
        df = fetch_data_cached(conn, SHEET_PROFIT)
        if "Date" not in df.columns: df = pd.DataFrame(columns=["Date", "TimeSlot", "MixDiff", "RealProfit"])
    except:
        df = pd.DataFrame(columns=["Date", "TimeSlot", "MixDiff", "RealProfit"])
    return df

def save_profit_data(df):
    conn = get_conn()
    try:
        conn.update(worksheet=SHEET_PROFIT, data=df)
        time.sleep(1)
        fetch_data_cached.clear()
    except Exception as e:
        if "WorksheetNotFound" in str(e):
            st.error(f"エラー: '{SHEET_PROFIT}' シートが見つかりません。")
        else:
            st.error(f"保存エラー: {e}")
        st.stop()

# ==========================================
# 4. 集計 & レンダリング
# ==========================================

def calculate_set_summary(subset_df):
    target_types = ["A客", "B客", "AS", "BS"]
    type_stats = {t: 0 for t in target_types}
    FEE_MAP = {"A客": 3, "B客": 5, "AS": 1, "BS": 1}
    total_fee = 0
    for _, row in subset_df.iterrows():
        w_type = None
        try:
            r_a = int(float(row["A着順"]))
            r_b = int(float(row["B着順"]))
            r_c = int(float(row["C着順"]))
        except:
            r_a, r_b, r_c = 0, 0, 0
        if r_a == 1: w_type = row["Aタイプ"]
        elif r_b == 1: w_type = row["Bタイプ"]
        elif r_c == 1: w_type = row["Cタイプ"]
        if w_type in target_types:
            type_stats[w_type] += 1
            if w_type in FEE_MAP: total_fee += FEE_MAP[w_type]
        note = str(row["備考"])
        if note == "東１終了": total_fee -= 1
        elif note == "２人飛ばし": total_fee -= 2
        elif note == "５連勝〜": total_fee -= 5
    return total_fee, type_stats

def render_paper_sheet(df):
    if df.empty:
        st.info("データがありません")
        return

    groups = df.groupby(["TableNo", "SetNo"])
    sorted_keys = sorted(groups.groups.keys())

    for key in sorted_keys:
        table_no, set_no = key
        subset = groups.get_group(key).sort_values("DailyNo")
        if subset.empty: continue

        fee, stats = calculate_set_summary(subset)

        html = f'''
        <table class="score-sheet">
            <thead>
                <tr class="set-header">
                    <td colspan="6">📄 第 {int(set_no)} セット &nbsp;<span style="font-size:12px;color:#8890a8;font-weight:400;">卓 {int(table_no)}</span></td>
                </tr>
                <tr>
                    <th style="width:5%">No</th>
                    <th style="width:9%">時刻</th>
                    <th style="width:24%">A席</th>
                    <th style="width:24%">B席</th>
                    <th style="width:24%">C席</th>
                    <th style="width:14%">備考</th>
                </tr>
            </thead>
            <tbody>'''

        last_names = {"A": None, "B": None, "C": None}

        for _, row in subset.iterrows():
            ranks_html_list = []
            try:
                dt_obj = pd.to_datetime(row["日時"])
                time_str = dt_obj.strftime("%H:%M")
            except: time_str = ""

            for p_char in ["A", "B", "C"]:
                try:
                    r_float = float(row[f"{p_char}着順"])
                    rank_val = str(int(r_float))
                except: rank_val = "0"

                is_1st = (rank_val == "1")
                SPECIAL_NOTES = ["東１終了", "２人飛ばし", "５連勝〜"]
                is_special = (row["備考"] in SPECIAL_NOTES) and is_1st
                td_class = ' class="cell-top"' if is_1st else ""

                if is_special:
                    rank_span = f'<span class="rank-num"><span class="rank-special">❶</span></span>'
                else:
                    char_map = {"1": "①", "2": "②", "3": "③"}
                    d_char = char_map.get(rank_val, rank_val)
                    color = "#f0c040" if is_1st else ("#8890a8" if rank_val == "3" else "#e8e8f0")
                    rank_span = f'<span class="rank-num" style="color:{color};">{d_char}</span>'

                p_name = row[f"{p_char}さん"]
                p_type = row[f"{p_char}タイプ"]
                type_colors = {"A客": "#5b9cf6", "B客": "#e07b39", "AS": "#4caf87", "BS": "#e05c5c"}
                type_color = type_colors.get(p_type, "#8890a8")

                if p_name == last_names[p_char]:
                    display_text = ""
                else:
                    display_text = f"{p_name}<span style='font-size:10px;color:{type_color};margin-left:4px;background:rgba(0,0,0,0.2);padding:1px 5px;border-radius:3px;'>{p_type}</span>"
                    last_names[p_char] = p_name

                cell_content = f'<div style="display:flex;justify-content:space-between;align-items:center;padding:0 4px;"><span>{display_text}</span>{rank_span}</div>'
                ranks_html_list.append(f'<td{td_class}>{cell_content}</td>')

            note_txt = row["備考"] if row["備考"] else ""
            note_color = "#e05c5c" if note_txt else "transparent"
            html += f'<tr><td style="color:#8890a8;font-size:12px;">{row["DailyNo"]}</td><td style="color:#8890a8;font-size:12px;">{time_str}</td>{ranks_html_list[0]}{ranks_html_list[1]}{ranks_html_list[2]}<td style="color:{note_color};font-size:11px;font-weight:700;">{note_txt}</td></tr>'

        fee_color = "#4caf87" if fee >= 0 else "#e05c5c"
        html += f'''<tr class="summary-row">
            <td colspan="2" style="text-align:right;color:#8890a8;font-size:12px;">合計</td>
            <td>ゲーム代: <span style="font-size:18px;color:{fee_color};">{fee}</span> 枚</td>
            <td colspan="3" style="font-size:11px;text-align:left;color:#8890a8;">
                A客:{stats["A客"]} / B客:{stats["B客"]} / AS:{stats["AS"]} / BS:{stats["BS"]}
            </td>
        </tr></tbody></table>'''

        st.markdown(html, unsafe_allow_html=True)

# ==========================================
# 5. ユーティリティ
# ==========================================

def page_back_button(target="home", label="🏠 ホームに戻る"):
    """共通の戻るボタン"""
    st.markdown('<div class="back-btn">', unsafe_allow_html=True)
    if st.button(label, key=f"back_{target}_{id(label)}"):
        st.session_state["page"] = target
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

def update_type_by_name(key_name, key_type, type_map):
    name = st.session_state[key_name]
    if name in type_map:
        st.session_state[key_type] = type_map[name]

def player_input_row_dynamic(label, member_list, def_n, def_t, def_r, available_ranks, key_suffix="", type_map=None):
    TYPE_OPTS = ["A客", "B客", "AS", "BS"]
    seat_colors = {"A席": "#5b9cf6", "B席": "#e07b39", "C席": "#4caf87"}
    color = seat_colors.get(label, "#f0c040")

    st.markdown(f'<div class="seat-label" style="background:{color};">{label}</div>', unsafe_allow_html=True)

    def get_idx_in_list(lst, val): return lst.index(val) if val in lst else None
    def get_idx_in_opts(opts, val): return opts.index(val) if val in opts else 0

    c1, c2 = st.columns([1, 2])
    with c1:
        idx_val = get_idx_in_list(member_list, def_n) if def_n else None
        k_name = f"n_{label}{key_suffix}"
        k_type = f"t_{label}{key_suffix}"
        name = st.selectbox(
            "名前", member_list, index=idx_val, key=k_name,
            on_change=update_type_by_name if type_map else None,
            args=(k_name, k_type, type_map) if type_map else None
        )
    with c2:
        final_idx = 0
        if def_r in available_ranks:
            final_idx = available_ranks.index(def_r)
        rank = st.radio("着順", available_ranks, index=final_idx, horizontal=True, key=f"r_{label}{key_suffix}")

        if k_type not in st.session_state:
            st.session_state[k_type] = def_t if def_t in TYPE_OPTS else TYPE_OPTS[0]
        type_ = st.radio("タイプ", TYPE_OPTS, horizontal=True, key=k_type)

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    return name, type_, rank

# ==========================================
# 6. 各ページ
# ==========================================

# --- ホーム ---
def page_home():
    st.markdown("""
    <div class="home-header">
        <div class="app-title">🀄 ぱいん成績管理</div>
        <div class="app-sub">PINE SCORE MANAGER</div>
    </div>
    """, unsafe_allow_html=True)

    nav_items = [
        ("📝", "成績をつける", "input"),
        ("📊", "データを見る", "history"),
        ("🏆", "ランキング", "ranking"),
        ("👥", "メンバー管理", "members"),
        ("💰", "利益管理", "profit"),
        ("📜", "操作ログ", "logs"),
    ]

    cols = st.columns(2)
    for i, (icon, label, page) in enumerate(nav_items):
        with cols[i % 2]:
            if st.button(f"{icon}　{label}", key=f"home_{page}", use_container_width=True):
                st.session_state["page"] = page
                st.rerun()
            st.write("")

# --- 利益管理 ---
def page_profit():
    st.title("💰 利益管理")
    page_back_button()
    st.write("")

    JST = timezone(timedelta(hours=9), 'JST')
    current_dt = datetime.now(JST)
    default_date_obj = (current_dt - timedelta(hours=9)).date()

    input_date = st.date_input("対象日付 (朝9時切替)", value=default_date_obj)

    df_profit = load_profit_data()
    search_date_str = input_date.strftime("%Y-%m-%d")

    init_day_mix, init_day_real = 0, 0
    init_night_mix, init_night_real = 0, 0

    if not df_profit.empty:
        row_day = df_profit[(df_profit["Date"] == search_date_str) & (df_profit["TimeSlot"] == "Day")]
        if not row_day.empty:
            init_day_mix = int(row_day.iloc[0]["MixDiff"])
            init_day_real = int(row_day.iloc[0]["RealProfit"])
        row_night = df_profit[(df_profit["Date"] == search_date_str) & (df_profit["TimeSlot"] == "Night")]
        if not row_night.empty:
            init_night_mix = int(row_night.iloc[0]["MixDiff"])
            init_night_real = int(row_night.iloc[0]["RealProfit"])

    with st.form("daily_profit_form"):
        st.markdown(f"### 📅 {input_date} の利益データ")
        col_d, col_n = st.columns(2)
        with col_d:
            st.info("🌞 昼の部　9:00 - 21:00")
            d_mix = st.number_input("MIX差", value=init_day_mix, key="d_mix")
            d_real = st.number_input("実利益", value=init_day_real, key="d_real")
        with col_n:
            st.success("🌙 夜の部　21:00 - 33:00")
            n_mix = st.number_input("MIX差", value=init_night_mix, key="n_mix")
            n_real = st.number_input("実利益", value=init_night_real, key="n_real")

        st.divider()
        profit_pass = st.text_input("🔒 保存用パスワード", type="password")

        if st.form_submit_button("💾 保存する", type="primary", use_container_width=True):
            if profit_pass == "7777":
                df_new = df_profit[df_profit["Date"] != search_date_str].copy()
                new_rows = [
                    {"Date": search_date_str, "TimeSlot": "Day", "MixDiff": d_mix, "RealProfit": d_real},
                    {"Date": search_date_str, "TimeSlot": "Night", "MixDiff": n_mix, "RealProfit": n_real}
                ]
                df_new = pd.concat([df_new, pd.DataFrame(new_rows)], ignore_index=True)
                save_profit_data(df_new)
                st.success(f"✅ {input_date} のデータを保存しました！")
                time.sleep(1)
                st.rerun()
            else:
                st.error("パスワードが違います")

# --- メンバー管理 ---
def page_members():
    st.title("👥 メンバー管理")
    page_back_button()
    st.write("")

    df_mem = load_member_data()
    tab_list, tab_add = st.tabs(["📋 一覧・編集", "➕ 新規追加"])

    with tab_list:
        st.markdown("### メンバー情報の編集")
        st.caption("「タイプ」を設定すると、成績入力時に自動で反映されます。")

        if not df_mem.empty:
            edited_df = st.data_editor(
                df_mem[["名前", "タイプ", "最大飜数", "最大飜数詳細", "最大飜数記録日", "役満回数"]],
                column_config={
                    "タイプ": st.column_config.SelectboxColumn(
                        "タイプ", width="medium",
                        options=["A客", "B客", "AS", "BS"], required=True,
                    ),
                    "最大飜数詳細": st.column_config.TextColumn("最大飜数詳細", width="medium"),
                    "最大飜数記録日": st.column_config.TextColumn("最大飜数記録日", width="small"),
                },
                hide_index=True, use_container_width=True, num_rows="dynamic"
            )
            st.write("")
            if st.button("💾 変更を保存する", type="primary"):
                df_merged = pd.merge(edited_df, df_mem[["名前", "登録日"]], on="名前", how="left")
                df_merged["登録日"] = df_merged["登録日"].fillna(date.today())
                save_member_data(df_merged)
                st.success("✅ メンバー情報を更新しました！")
                time.sleep(1)
                st.rerun()
        else:
            st.info("メンバーがいません")

        st.divider()
        st.markdown("### メンバーリンク一覧")
        st.caption("名前をクリックすると詳細データへ移動します")

        if not df_mem.empty:
            guests = df_mem[df_mem["タイプ"].isin(["A客", "B客"])].reset_index(drop=True)
            staffs = df_mem[df_mem["タイプ"].isin(["AS", "BS"])].reset_index(drop=True)
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("#### 🧑‍🤝‍🧑 お客さん")
                for i, row in guests.iterrows():
                    badge = f'<span class="badge badge-{"b" if row["タイプ"]=="B客" else "a"}">{row["タイプ"]}</span>'
                    if st.button(f"👤 {row['名前']}", key=f"lnk_g_{i}"):
                        st.session_state["page"] = "history"
                        st.session_state["jump_to_player"] = row['名前']
                        st.rerun()
            with c2:
                st.markdown("#### 👔 スタッフ")
                for i, row in staffs.iterrows():
                    if st.button(f"👔 {row['名前']}", key=f"lnk_s_{i}"):
                        st.session_state["page"] = "history"
                        st.session_state["jump_to_player"] = row['名前']
                        st.rerun()

    with tab_add:
        st.markdown("### 新規メンバー追加")
        with st.form("add_member_form"):
            c1, c2 = st.columns(2)
            with c1:
                new_name = st.text_input("名前", placeholder="名前を入力")
            with c2:
                new_type = st.selectbox("タイプ", ["A客", "B客", "AS", "BS"])
            if st.form_submit_button("➕ 追加する", type="primary", use_container_width=True) and new_name:
                if new_name in df_mem["名前"].values:
                    st.error(f"「{new_name}」は既に登録されています")
                else:
                    new_row = {
                        "名前": new_name, "登録日": date.today(), "タイプ": new_type,
                        "最大飜数": 0, "最大飜数詳細": "", "最大飜数記録日": "", "役満回数": 0
                    }
                    df_mem = pd.concat([df_mem, pd.DataFrame([new_row])], ignore_index=True)
                    save_member_data(df_mem)
                    st.success(f"✅「{new_name}」を追加しました")
                    st.rerun()

# --- 編集専用画面 ---
def page_edit():
    st.title("🔧 データ修正・削除")

    edit_id = st.session_state.get("editing_game_id")
    if not edit_id:
        st.error("編集対象が選択されていません")
        page_back_button("input", "← 戻る")
        return

    df = load_score_data()
    target_row = df[df["GameNo"] == edit_id]

    if target_row.empty:
        st.error("データが見つかりません（削除された可能性があります）")
        page_back_button("input", "← 戻る")
        return

    row = target_row.iloc[0]
    df_mem = load_member_data()
    member_list = get_all_member_names()
    type_map = dict(zip(df_mem["名前"], df_mem["タイプ"]))

    st.info(f"編集中: No.{row['DailyNo']}  ／  卓: {row['TableNo']}  ／  セット: {row['SetNo']}")

    with st.form("edit_form"):
        p1_n, p1_t, p1_r = player_input_row_dynamic("A席", member_list, row["Aさん"], row["Aタイプ"], int(float(row["A着順"])), [1, 2, 3], "_edit", type_map)
        p2_n, p2_t, p2_r = player_input_row_dynamic("B席", member_list, row["Bさん"], row["Bタイプ"], int(float(row["B着順"])), [1, 2, 3], "_edit", type_map)
        p3_n, p3_t, p3_r = player_input_row_dynamic("C席", member_list, row["Cさん"], row["Cタイプ"], int(float(row["C着順"])), [1, 2, 3], "_edit", type_map)

        st.markdown("**備考**")
        NOTE_OPTS = ["なし", "東１終了", "２人飛ばし", "５連勝〜"]
        def idx(opts, val): return opts.index(val) if val in opts else 0
        cur_note = row["備考"] if row["備考"] else "なし"
        opts = NOTE_OPTS if cur_note in NOTE_OPTS else NOTE_OPTS + [cur_note]
        note = st.radio("内容", opts, index=idx(opts, cur_note), horizontal=True)

        st.divider()
        c_up, c_del, c_can = st.columns(3)
        with c_up:
            submit_update = st.form_submit_button("🔄 更新して保存", type="primary", use_container_width=True)
        with c_del:
            submit_delete = st.form_submit_button("🗑 削除する", use_container_width=True)
        with c_can:
            submit_cancel = st.form_submit_button("キャンセル", use_container_width=True)

        if submit_cancel:
            st.session_state["page"] = "input"
            st.session_state["editing_game_id"] = None
            st.rerun()

        if submit_update:
            fetch_data_cached.clear()
            df_latest = load_score_data_fresh()
            if edit_id not in df_latest["GameNo"].values:
                st.error("データが他で削除された可能性があります")
            else:
                if not p1_n or not p2_n or not p3_n:
                    st.error("名前を選択してください")
                elif sorted([p1_r, p2_r, p3_r]) != [1, 2, 3]:
                    st.error("着順が重複しています")
                else:
                    new_data = {
                        "GameNo": row["GameNo"], "TableNo": row["TableNo"], "SetNo": row["SetNo"],
                        "日時": row["日時"], "備考": ("" if note == "なし" else note),
                        "Aさん": p1_n, "Aタイプ": p1_t, "A着順": p1_r,
                        "Bさん": p2_n, "Bタイプ": p2_t, "B着順": p2_r,
                        "Cさん": p3_n, "Cタイプ": p3_t, "C着順": p3_r
                    }
                    changes = []
                    compare_keys = [
                        ("備考", "備考"), ("A名前", "Aさん"), ("A着順", "A着順"), ("Aタイプ", "Aタイプ"),
                        ("B名前", "Bさん"), ("B着順", "B着順"), ("Bタイプ", "Bタイプ"),
                        ("C名前", "Cさん"), ("C着順", "C着順"), ("Cタイプ", "Cタイプ"),
                    ]
                    for label, key in compare_keys:
                        old_val = row[key]
                        new_val = new_data[key]
                        if str(old_val) != str(new_val):
                            changes.append(f"{label}: {old_val}→{new_val}")
                    diff_text = ", ".join(changes) if changes else "変更なし"
                    idx_pos = df_latest[df_latest["GameNo"] == edit_id].index[0]
                    df_latest.loc[idx_pos, list(new_data.keys())] = list(new_data.values())
                    save_score_data(df_latest)
                    save_action_log("修正", row["DailyNo"], diff_text)
                    st.session_state["success_msg"] = "✅ 修正しました！"
                    st.session_state["page"] = "input"
                    st.session_state["editing_game_id"] = None
                    st.rerun()

        if submit_delete:
            fetch_data_cached.clear()
            df_latest = load_score_data_fresh()
            if edit_id in df_latest["GameNo"].values:
                df_latest = df_latest[df_latest["GameNo"] != edit_id]
                save_score_data(df_latest)
                del_info = f"{row['日時']} {row['TableNo']}卓 Set{row['SetNo']}"
                save_action_log("削除", row["DailyNo"], del_info)
                st.session_state["success_msg"] = "🗑 削除しました"
                st.session_state["page"] = "input"
                st.session_state["editing_game_id"] = None
                st.rerun()
            else:
                st.error("既に削除されています")

# --- 入力画面 ---
def page_input():
    st.title("📝 成績入力")

    if "success_msg" in st.session_state and st.session_state.get("success_msg"):
        st.success(st.session_state["success_msg"])
        components.html("""<script>try{var main=window.parent.document.querySelector('section.main');if(main){main.scrollTo(0,0);}window.parent.scrollTo(0,0);}catch(e){}</script>""", height=0)
        st.session_state["success_msg"] = None

    page_back_button()
    st.write("")

    df = load_score_data()
    df_mem = load_member_data()
    member_list = get_all_member_names()
    type_map = dict(zip(df_mem["名前"], df_mem["タイプ"]))

    JST = timezone(timedelta(hours=9), 'JST')

    # 上部コントロール
    c_top1, c_top2 = st.columns(2)
    with c_top1:
        current_table = st.selectbox("🀄 対局卓", [1, 2, 3], index=0)
    with c_top2:
        current_dt = datetime.now(JST)
        default_date_obj = (current_dt - timedelta(hours=9)).date()
        input_date = st.date_input("📅 日付 (朝9時切替)", value=default_date_obj)

    mask_all = df["論理日付"].apply(lambda x: x == input_date if pd.notnull(x) else False)
    df_all_today = df[mask_all]
    df_table_today = df_all_today[df_all_today["TableNo"] == current_table]

    # セット・No 計算
    if not df_table_today.empty and "SetNo" in df_table_today.columns:
        current_set_no = int(df_table_today["SetNo"].max())
    else:
        current_set_no = 1

    if not df_table_today.empty and "DailyNo" in df_table_today.columns:
        next_display_no = int(df_table_today["DailyNo"].max()) + 1
    else:
        next_display_no = 1

    if not df.empty and "GameNo" in df.columns:
        next_internal_game_no = df["GameNo"].max() + 1
    else:
        next_internal_game_no = 1

    # 前回データ引き継ぎ
    last_n1, last_t1 = None, "A客"
    last_n2, last_t2 = None, "B客"
    last_n3, last_t3 = None, "AS"
    if not df_table_today.empty:
        last_game = df_table_today.iloc[-1]
        last_n1, last_t1 = last_game["Aさん"], last_game["Aタイプ"]
        last_n2, last_t2 = last_game["Bさん"], last_game["Bタイプ"]
        last_n3, last_t3 = last_game["Cさん"], last_game["Cタイプ"]

    st.markdown(f"""
    <div style="background:var(--bg-card);border:1px solid var(--border-accent);border-radius:var(--radius);
                padding:0.7rem 1.2rem;margin-bottom:1rem;display:flex;align-items:center;gap:1rem;">
        <span style="color:var(--accent);font-weight:700;">🀄 {current_table}卓 — 第 {current_set_no} セット</span>
        <span style="color:var(--text-muted);font-size:0.85rem;">次の記録: No.{next_display_no}</span>
    </div>
    """, unsafe_allow_html=True)

    n1, t1, r1 = player_input_row_dynamic("A席", member_list, last_n1, last_t1, 1, [1, 2, 3], "_input", type_map)
    ranks_for_2 = [x for x in [1, 2, 3] if x != r1]
    def_r2 = 2 if 2 in ranks_for_2 else ranks_for_2[0]
    n2, t2, r2 = player_input_row_dynamic("B席", member_list, last_n2, last_t2, def_r2, ranks_for_2, "_input", type_map)
    ranks_for_3 = [x for x in ranks_for_2 if x != r2]
    def_r3 = 3 if 3 in ranks_for_3 else (ranks_for_3[0] if ranks_for_3 else 0)
    n3, t3, r3 = player_input_row_dynamic("C席", member_list, last_n3, last_t3, def_r3, ranks_for_3, "_input", type_map)

    st.markdown("**備考**")
    NOTE_OPTS = ["なし", "東１終了", "２人飛ばし", "５連勝〜"]
    note = st.radio("内容を選択", NOTE_OPTS, index=0, horizontal=True)

    start_new_set = st.checkbox(f"🆕 新しいセットへ ({current_table}卓 → 第{current_set_no+1}セット)")
    st.write("")

    if st.button("📝 記録する", type="primary", use_container_width=True):
        if not n1 or not n2 or not n3:
            st.error("⚠️ 名前が選択されていません！")
        else:
            with st.spinner("保存中..."):
                fetch_data_cached.clear()
                try:
                    df_latest = load_score_data_fresh()
                except:
                    st.error("データの読み込みに失敗しました。再試行してください。")
                    st.stop()

                if not df.empty and df_latest.empty:
                    st.error("🚨 最新データの取得に失敗しました。保存を中止しました。")
                    st.stop()

                if not df_latest.empty and "GameNo" in df_latest.columns:
                    next_internal_game_no = df_latest["GameNo"].max() + 1
                else:
                    next_internal_game_no = 1

                df_table_latest = df_latest[df_latest["TableNo"] == current_table]
                mask_latest = df_table_latest["論理日付"].apply(lambda x: x == input_date if pd.notnull(x) else False)
                df_today_latest = df_table_latest[mask_latest]

                if not df_today_latest.empty:
                    next_display_no = int(df_today_latest["DailyNo"].max()) + 1
                else:
                    next_display_no = 1

                now_jst = datetime.now(JST)
                save_date_obj = input_date
                if now_jst.hour < 9:
                    save_date_obj = input_date + timedelta(days=1)
                save_date_str = save_date_obj.strftime("%Y-%m-%d") + " " + now_jst.strftime("%H:%M")
                final_set_no = current_set_no + (1 if start_new_set else 0)

                new_row = {
                    "GameNo": next_internal_game_no, "TableNo": current_table, "SetNo": final_set_no,
                    "日時": save_date_str, "備考": ("" if note == "なし" else note),
                    "Aさん": n1, "Aタイプ": t1, "A着順": r1,
                    "Bさん": n2, "Bタイプ": t2, "B着順": r2,
                    "Cさん": n3, "Cタイプ": t3, "C着順": r3
                }

                df_final = pd.concat([df_latest, pd.DataFrame([new_row])], ignore_index=True)
                save_score_data(df_final)
                save_action_log("新規登録", next_internal_game_no, f"新規: {current_table}卓 No.{next_display_no}")

            time_str = now_jst.strftime("%H:%M")
            st.session_state["success_msg"] = f"✅ 記録しました！ ({time_str} / No.{next_display_no})"
            st.rerun()

    st.divider()

    if not df_all_today.empty:
        # 本日サマリー
        total_games_today = len(df_all_today)
        total_fee_today = 0
        type_counts = {"A客": 0, "B客": 0, "AS": 0, "BS": 0}
        total_back_a = 0
        total_back_b = 0
        FEE_MAP = {"A客": 3, "B客": 5, "AS": 1, "BS": 1}

        for _, row in df_all_today.iterrows():
            try:
                r_a = int(float(row["A着順"]))
                r_b = int(float(row["B着順"]))
                r_c = int(float(row["C着順"]))
            except:
                r_a, r_b, r_c = 0, 0, 0

            winner_type = None
            if r_a == 1: winner_type = row["Aタイプ"]
            elif r_b == 1: winner_type = row["Bタイプ"]
            elif r_c == 1: winner_type = row["Cタイプ"]

            if winner_type in type_counts:
                type_counts[winner_type] += 1
                total_fee_today += FEE_MAP[winner_type]

            note_val = str(row["備考"])
            discount = 0
            if note_val == "東１終了": discount = 1
            elif note_val == "２人飛ばし": discount = 2
            elif note_val == "５連勝〜": discount = 5
            total_fee_today -= discount
            if discount > 0 and winner_type:
                if winner_type == "A客": total_back_a += discount
                elif winner_type == "B客": total_back_b += discount

        st.markdown("### 📋 本日の集計 (全卓)")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("ゲーム代", f"{total_fee_today} 枚")
        col2.metric("総回数", f"{total_games_today} 回")
        col3.metric("A客バック", f"{total_back_a} 枚")
        col4.metric("B客バック", f"{total_back_b} 枚")

        st.caption(f"内訳: A客 {type_counts['A客']} / B客 {type_counts['B客']} / AS {type_counts['AS']} / BS {type_counts['BS']}")

        st.write("")
        render_paper_sheet(df_all_today)
        st.write("")

        st.caption("👇 修正したい行をクリックすると編集画面へ移動します")
        df_display = df_all_today.sort_values(["TableNo", "DailyNo"])[["TableNo", "DailyNo", "SetNo", "日時", "Aさん", "Bさん", "Cさん"]].copy()

        def safe_strftime(x):
            try: return pd.to_datetime(x).strftime('%H:%M')
            except: return ""
        df_display["日時"] = df_display["日時"].apply(safe_strftime)

        event = st.dataframe(
            df_display, use_container_width=True, hide_index=True,
            on_select="rerun", selection_mode="single-row"
        )

        if len(event.selection.rows) > 0:
            selected_idx = event.selection.rows[0]
            target_daily_no = df_display.iloc[selected_idx]["DailyNo"]
            target_table_no = df_display.iloc[selected_idx]["TableNo"]
            target_rows = df_all_today[(df_all_today["DailyNo"] == target_daily_no) & (df_all_today["TableNo"] == target_table_no)]
            if not target_rows.empty:
                st.session_state["editing_game_id"] = target_rows.iloc[0]["GameNo"]
                st.session_state["page"] = "edit"
                st.rerun()
    else:
        st.info("今日のデータはまだありません")

# --- 履歴画面 ---
def page_history():
    st.title("📊 過去データ参照")
    page_back_button()
    st.write("")

    df = load_score_data()
    if df.empty:
        st.info("データがありません")
        return

    if "hist_sel_date" not in st.session_state:
        st.session_state.hist_sel_date = "(指定なし)"
    if "hist_sel_time" not in st.session_state:
        st.session_state.hist_sel_time = "全日"
    if "hist_sel_player" not in st.session_state:
        st.session_state.hist_sel_player = "(指定なし)"

    if "jump_to_player" in st.session_state:
        st.session_state.hist_sel_player = st.session_state["jump_to_player"]
        st.session_state.hist_sel_date = "(指定なし)"
        st.session_state.hist_sel_time = "全日"
        del st.session_state["jump_to_player"]

    # --- 期間別統計 ---
    st.markdown("### 📈 期間別統計")

    if "論理日付" in df.columns:
        min_date = df["論理日付"].min()
        max_date = df["論理日付"].max()
    else:
        min_date = max_date = date.today()

    c1, c2 = st.columns([2, 1])
    with c1:
        stats_range = st.date_input("集計期間", value=(min_date, max_date))
    with c2:
        stats_time_range = st.selectbox("時間帯", ["全日", "9:00-21:00", "21:00-33:00(翌9:00)"], key="stats_time")

    df_target = df.copy()
    if isinstance(stats_range, tuple) and len(stats_range) == 2:
        start, end = stats_range
        df_target = df_target[(df_target["論理日付"] >= start) & (df_target["論理日付"] <= end)]
    elif isinstance(stats_range, tuple) and len(stats_range) == 1:
        start = end = stats_range[0]
        df_target = df_target[df_target["論理日付"] == start]
    else:
        start, end = min_date, max_date

    if stats_time_range == "9:00-21:00":
        df_target = df_target[df_target["日時Obj"].dt.hour.between(9, 20)]
    elif stats_time_range == "21:00-33:00(翌9:00)":
        df_target = df_target[~df_target["日時Obj"].dt.hour.between(9, 20)]

    if df_target.empty:
        st.warning("指定期間のデータはありません")
    else:
        total_games = len(df_target)
        unique_days = df_target["論理日付"].nunique()
        avg_games_day = total_games / unique_days if unique_days > 0 else 0

        total_back_a = 0
        total_back_b = 0
        pattern_counts = {"A3人": 0, "A2人B1人": 0, "A1人B2人": 0, "B3人": 0}
        pattern_wins_a = {"A3人": 0, "A2人B1人": 0, "A1人B2人": 0, "B3人": 0}
        seat_counts = {s: {"1": 0, "2": 0, "3": 0, "sum": 0, "count": 0} for s in ["A", "B", "C"]}
        type_data = []

        for _, row in df_target.iterrows():
            note = str(row["備考"])
            discount = 0
            if note == "東１終了": discount = 1
            elif note == "２人飛ばし": discount = 2
            elif note == "５連勝〜": discount = 5

            winner_is_a = False
            winner_type = None
            try:
                r_a = int(float(row["A着順"]))
                r_b = int(float(row["B着順"]))
                r_c = int(float(row["C着順"]))
                if r_a == 1: winner_type = row["Aタイプ"]
                elif r_b == 1: winner_type = row["Bタイプ"]
                elif r_c == 1: winner_type = row["Cタイプ"]
                if winner_type in ["A客", "AS"]: winner_is_a = True
            except: pass

            if discount > 0 and winner_type:
                if winner_type == "A客": total_back_a += discount
                elif winner_type == "B客": total_back_b += discount

            p_types = [row["Aタイプ"], row["Bタイプ"], row["Cタイプ"]]
            a_side = sum(1 for t in p_types if t in ["A客", "AS"])
            key = None
            if a_side == 3: key = "A3人"
            elif a_side == 2: key = "A2人B1人"
            elif a_side == 1: key = "A1人B2人"
            elif a_side == 0: key = "B3人"
            if key:
                pattern_counts[key] += 1
                if winner_is_a: pattern_wins_a[key] += 1

            for seat in ["A", "B", "C"]:
                t = row[f"{seat}タイプ"]
                r_str = row[f"{seat}着順"]
                try:
                    r = int(float(r_str))
                    if r in [1, 2, 3]:
                        type_data.append({"Type": t, "Rank": r})
                        seat_counts[seat][str(r)] += 1
                        seat_counts[seat]["sum"] += r
                        seat_counts[seat]["count"] += 1
                except: pass

        avg_back_a = total_back_a / unique_days if unique_days > 0 else 0
        avg_back_b = total_back_b / unique_days if unique_days > 0 else 0

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("総ゲーム数", f"{total_games} 回")
        c2.metric("平均/日", f"{avg_games_day:.1f} 回")
        c3.metric("A客バック累計", f"{total_back_a} 枚", f"平均 {avg_back_a:.1f}/日")
        c4.metric("B客バック累計", f"{total_back_b} 枚", f"平均 {avg_back_b:.1f}/日")

        df_profit = load_profit_data()
        if not df_profit.empty:
            df_profit["MixDiff"] = pd.to_numeric(df_profit["MixDiff"], errors='coerce').fillna(0)
            df_profit["RealProfit"] = pd.to_numeric(df_profit["RealProfit"], errors='coerce').fillna(0)
            df_profit["DateObj"] = pd.to_datetime(df_profit["Date"]).dt.date
            df_p_target = df_profit.copy()
            if isinstance(stats_range, tuple) and len(stats_range) == 2:
                df_p_target = df_p_target[(df_p_target["DateObj"] >= start) & (df_p_target["DateObj"] <= end)]
            if stats_time_range == "9:00-21:00":
                df_p_target = df_p_target[df_p_target["TimeSlot"] == "Day"]
            elif stats_time_range == "21:00-33:00(翌9:00)":
                df_p_target = df_p_target[df_p_target["TimeSlot"] == "Night"]
            sum_mix = int(df_p_target["MixDiff"].sum())
            sum_real = int(df_p_target["RealProfit"].sum())
            st.markdown("##### 💰 利益集計")
            cp1, cp2 = st.columns(2)
            cp1.metric("MIX差 合計", f"{sum_mix:,}")
            cp2.metric("実利益 合計", f"{sum_real:,}")

        st.caption(f"卓組構成の割合 ({start} 〜 {end})")
        df_pattern = pd.DataFrame({"構成": list(pattern_counts.keys()), "回数": list(pattern_counts.values())})
        total_p = df_pattern["回数"].sum()
        df_pattern["割合"] = (df_pattern["回数"] / total_p * 100).map('{:.1f}%'.format) if total_p > 0 else "0.0%"
        win_rates = []
        for k in df_pattern["構成"]:
            cnt = pattern_counts[k]
            wins_a = pattern_wins_a[k]
            if k in ["A2人B1人", "A1人B2人"] and cnt > 0:
                win_rates.append(f"A: {wins_a/cnt*100:.0f}% / B: {(cnt-wins_a)/cnt*100:.0f}%")
            else:
                win_rates.append("-")
        df_pattern["勝率"] = win_rates
        st.dataframe(df_pattern, hide_index=True, use_container_width=True)

        if type_data:
            st.markdown("##### 📊 タイプ別成績")
            df_type_raw = pd.DataFrame(type_data)
            stats_by_type = df_type_raw.groupby("Type")["Rank"].agg(
                games="count", avg="mean",
                r1=lambda x: (x==1).sum(), r2=lambda x: (x==2).sum(), r3=lambda x: (x==3).sum()
            ).reset_index()
            stats_by_type["avg"] = stats_by_type["avg"].map('{:.2f}'.format)
            stats_by_type["1着"] = stats_by_type.apply(lambda x: f"{x['r1']} ({x['r1']/x['games']*100:.1f}%)", axis=1)
            stats_by_type["2着"] = stats_by_type.apply(lambda x: f"{x['r2']} ({x['r2']/x['games']*100:.1f}%)", axis=1)
            stats_by_type["3着"] = stats_by_type.apply(lambda x: f"{x['r3']} ({x['r3']/x['games']*100:.1f}%)", axis=1)
            type_order = {"A客": 0, "B客": 1, "AS": 2, "BS": 3}
            stats_by_type["order"] = stats_by_type["Type"].map(lambda x: type_order.get(x, 99))
            stats_by_type = stats_by_type.sort_values("order").drop("order", axis=1)
            st.dataframe(
                stats_by_type.rename(columns={"Type": "タイプ", "games": "打数", "avg": "平均着順"})[["タイプ", "打数", "平均着順", "1着", "2着", "3着"]],
                hide_index=True, use_container_width=True
            )

        seat_rows = []
        for s in ["A", "B", "C"]:
            d = seat_counts[s]
            c = d["count"]
            if c > 0:
                avg = d["sum"] / c
                seat_rows.append({
                    "席": f"{s}席", "打数": c, "平均着順": f"{avg:.2f}",
                    "1着": f"{d['1']} ({d['1']/c*100:.1f}%)",
                    "2着": f"{d['2']} ({d['2']/c*100:.1f}%)",
                    "3着": f"{d['3']} ({d['3']/c*100:.1f}%)"
                })
        if seat_rows:
            st.markdown("##### 🪑 席別成績")
            st.dataframe(pd.DataFrame(seat_rows), hide_index=True, use_container_width=True)

    st.divider()

    # --- 詳細検索 ---
    if "論理日付" in df.columns:
        valid_dates = [d for d in df["論理日付"].unique() if pd.notnull(d) and d != pd.Timestamp("1900-01-01").date()]
        unique_dates = sorted(valid_dates, reverse=True)
    else:
        unique_dates = []

    all_players = get_all_member_names()
    date_options = ["(指定なし)"] + list(unique_dates)
    time_options = ["全日", "9:00-21:00", "21:00-33:00(翌9:00)"]
    player_options = ["(指定なし)"] + list(all_players)

    def get_idx(lst, val): return lst.index(val) if val in lst else 0

    st.markdown("### 🔍 詳細検索")
    with st.form("history_search_form"):
        c1, c2, c3 = st.columns(3)
        with c1:
            sel_date = st.selectbox("📅 日付", date_options, index=get_idx(date_options, st.session_state.hist_sel_date))
        with c2:
            sel_time = st.selectbox("⏰ 時間帯", time_options, index=get_idx(time_options, st.session_state.hist_sel_time))
        with c3:
            sel_player = st.selectbox("👤 プレイヤー", player_options, index=get_idx(player_options, st.session_state.hist_sel_player))
        submitted = st.form_submit_button("🔍 絞り込み", type="primary", use_container_width=True)

    st.divider()

    if submitted:
        st.session_state.hist_sel_date = sel_date
        st.session_state.hist_sel_time = sel_time
        st.session_state.hist_sel_player = sel_player
        st.rerun()

    active_date = st.session_state.hist_sel_date
    active_time = st.session_state.hist_sel_time
    active_player = st.session_state.hist_sel_player

    if active_date == "(指定なし)" and active_player == "(指定なし)":
        st.info("☝️ 条件を選択して「絞り込み」を押してください")
        return

    df_filtered = df.copy()
    if active_date != "(指定なし)":
        df_filtered = df_filtered[df_filtered["論理日付"] == active_date]
    if active_player != "(指定なし)":
        df_filtered = df_filtered[
            (df_filtered["Aさん"] == active_player) |
            (df_filtered["Bさん"] == active_player) |
            (df_filtered["Cさん"] == active_player)
        ]
    if active_time == "9:00-21:00":
        df_filtered = df_filtered[df_filtered["日時Obj"].dt.hour.between(9, 20)]
    elif active_time == "21:00-33:00(翌9:00)":
        df_filtered = df_filtered[~df_filtered["日時Obj"].dt.hour.between(9, 20)]

    if df_filtered.empty:
        st.warning("条件に一致するデータが見つかりませんでした")
        return

    # 検索結果サマリー
    st.markdown("### 📅 選択期間の集計")
    total_games_day = len(df_filtered)
    day_back_a = 0
    day_back_b = 0
    pattern_counts = {"A3人": 0, "A2人B1人": 0, "A1人B2人": 0, "B3人": 0}
    pattern_wins_a = {"A3人": 0, "A2人B1人": 0, "A1人B2人": 0, "B3人": 0}

    for _, row in df_filtered.iterrows():
        note = str(row["備考"])
        discount = 0
        if note == "東１終了": discount = 1
        elif note == "２人飛ばし": discount = 2
        elif note == "５連勝〜": discount = 5
        winner_is_a = False
        winner_type = None
        try:
            r_a = int(float(row["A着順"]))
            r_b = int(float(row["B着順"]))
            r_c = int(float(row["C着順"]))
            if r_a == 1: winner_type = row["Aタイプ"]
            elif r_b == 1: winner_type = row["Bタイプ"]
            elif r_c == 1: winner_type = row["Cタイプ"]
            if winner_type in ["A客", "AS"]: winner_is_a = True
        except: pass
        if discount > 0 and winner_type:
            if winner_type == "A客": day_back_a += discount
            elif winner_type == "B客": day_back_b += discount
        p_types = [row["Aタイプ"], row["Bタイプ"], row["Cタイプ"]]
        a_side = sum(1 for t in p_types if t in ["A客", "AS"])
        key = None
        if a_side == 3: key = "A3人"
        elif a_side == 2: key = "A2人B1人"
        elif a_side == 1: key = "A1人B2人"
        elif a_side == 0: key = "B3人"
        if key:
            pattern_counts[key] += 1
            if winner_is_a: pattern_wins_a[key] += 1

    c_s1, c_s2, c_s3 = st.columns(3)
    c_s1.metric("ゲーム回数", f"{total_games_day} 回")
    c_s2.metric("A客バック", f"{day_back_a} 枚")
    c_s3.metric("B客バック", f"{day_back_b} 枚")

    df_pattern = pd.DataFrame({"構成": list(pattern_counts.keys()), "回数": list(pattern_counts.values())})
    total = df_pattern["回数"].sum()
    df_pattern["割合"] = (df_pattern["回数"] / total * 100).map('{:.1f}%'.format) if total > 0 else "0.0%"
    win_rates = []
    for k in df_pattern["構成"]:
        cnt = pattern_counts[k]
        wins_a = pattern_wins_a[k]
        if k in ["A2人B1人", "A1人B2人"] and cnt > 0:
            win_rates.append(f"A: {wins_a/cnt*100:.0f}% / B: {(cnt-wins_a)/cnt*100:.0f}%")
        else:
            win_rates.append("-")
    df_pattern["勝率"] = win_rates
    st.caption("卓組構成")
    st.dataframe(df_pattern, hide_index=True, use_container_width=True)
    st.divider()

    if active_player != "(指定なし)":
        st.markdown(f"#### 👤 {active_player} さんの成績")
        ranks = []
        played_dates = set()
        compatibility = {}
        player_seat_ranks = {"A": [], "B": [], "C": []}

        for _, row in df_filtered.iterrows():
            my_rank = None
            my_seat = None
            for s in ["A", "B", "C"]:
                if row[f"{s}さん"] == active_player:
                    try:
                        my_rank = int(float(row[f"{s}着順"]))
                        my_seat = s
                    except: pass
                    break
            if my_rank:
                ranks.append(my_rank)
                played_dates.add(row["論理日付"])
                if my_seat in player_seat_ranks:
                    player_seat_ranks[my_seat].append(my_rank)
                for s in ["A", "B", "C"]:
                    if s == my_seat: continue
                    opp_name = row[f"{s}さん"]
                    if not opp_name: continue
                    try:
                        opp_rank = int(float(row[f"{s}着順"]))
                    except: opp_rank = 0
                    if opp_rank == 0: continue
                    if opp_name not in compatibility:
                        compatibility[opp_name] = {"count": 0, "score": 0}
                    compatibility[opp_name]["count"] += 1
                    compatibility[opp_name]["score"] += opp_rank - my_rank

        if ranks:
            games = len(ranks)
            avg = sum(ranks) / games
            c1_cnt = ranks.count(1)
            c2_cnt = ranks.count(2)
            c3_cnt = ranks.count(3)

            stats_html = f"""
            <table class="stats-table">
                <thead><tr>
                    <th>総回数</th><th>平均着順</th>
                    <th>1着</th><th>2着</th><th>3着</th>
                </tr></thead>
                <tbody><tr>
                    <td>{games} 回</td>
                    <td style="color:var(--accent)">{avg:.2f}</td>
                    <td>{c1_cnt}<span class="stats-sub">{c1_cnt/games*100:.1f}%</span></td>
                    <td>{c2_cnt}<span class="stats-sub">{c2_cnt/games*100:.1f}%</span></td>
                    <td>{c3_cnt}<span class="stats-sub">{c3_cnt/games*100:.1f}%</span></td>
                </tr></tbody>
            </table>
            """
            st.markdown(stats_html, unsafe_allow_html=True)

            p_seat_rows = []
            for s in ["A", "B", "C"]:
                rs = player_seat_ranks[s]
                c = len(rs)
                if c > 0:
                    p_seat_rows.append({
                        "席": f"{s}席", "打数": c, "平均着順": f"{sum(rs)/c:.2f}",
                        "1着": f"{rs.count(1)} ({rs.count(1)/c*100:.1f}%)",
                        "2着": f"{rs.count(2)} ({rs.count(2)/c*100:.1f}%)",
                        "3着": f"{rs.count(3)} ({rs.count(3)/c*100:.1f}%)"
                    })
            if p_seat_rows:
                st.markdown("##### 🪑 席別成績")
                st.dataframe(pd.DataFrame(p_seat_rows), hide_index=True, use_container_width=True)

            st.divider()
            c_graph, c_dates = st.columns([2, 1])
            with c_graph:
                st.markdown("##### 📈 直近10戦の着順推移")
                recent_ranks = ranks[-10:]
                df_trend = pd.DataFrame({"戦数": range(1, len(recent_ranks) + 1), "着順": recent_ranks})
                line_chart = alt.Chart(df_trend).mark_line(
                    point=alt.OverlayMarkDef(color="#f0c040", size=80),
                    color="#f0c040", strokeWidth=2
                ).encode(
                    x=alt.X("戦数", axis=alt.Axis(tickMinStep=1), title="直近ゲーム"),
                    y=alt.Y("着順", scale=alt.Scale(domain=[3.3, 0.7]), title="着順"),
                    tooltip=["戦数", "着順"]
                ).properties(height=260).configure_view(
                    strokeWidth=0, fill="#1a1d2e"
                ).configure_axis(
                    gridColor="#2a2d3e", labelColor="#8890a8", titleColor="#8890a8"
                )
                st.altair_chart(line_chart, use_container_width=True)
            with c_dates:
                st.markdown("##### 📅 稼働日")
                date_list = sorted(list(played_dates), reverse=True)
                st.dataframe(pd.DataFrame(date_list, columns=["日付"]), hide_index=True, use_container_width=True)

        if compatibility:
            st.divider()
            st.markdown("##### 🤝 対戦相手データ (TOP5)")
            comp_data = [{"名前": n, "同卓回数": d["count"], "相性スコア": d["score"]} for n, d in compatibility.items()]
            df_comp = pd.DataFrame(comp_data)
            c_freq, c_good, c_bad = st.columns(3)
            with c_freq:
                st.markdown("**👬 同卓回数**")
                st.dataframe(df_comp.sort_values("同卓回数", ascending=False).head(5).reset_index(drop=True)[["名前", "同卓回数"]], hide_index=True, use_container_width=True)
            with c_good:
                st.markdown("**💖 カモ**")
                st.dataframe(df_comp.sort_values("相性スコア", ascending=False).head(5).reset_index(drop=True)[["名前", "相性スコア"]], hide_index=True, use_container_width=True)
            with c_bad:
                st.markdown("**💀 天敵**")
                st.dataframe(df_comp.sort_values("相性スコア", ascending=True).head(5).reset_index(drop=True)[["名前", "相性スコア"]], hide_index=True, use_container_width=True)

        st.divider()
        st.markdown("#### 🀄 個人記録の更新")
        df_mem = load_member_data()
        current_max = 0
        current_yaku = 0
        current_detail = ""
        current_date_str = ""
        target_idx = df_mem.index[df_mem["名前"] == active_player].tolist()

        if target_idx:
            idx = target_idx[0]
            current_max = int(df_mem.at[idx, "最大飜数"])
            current_yaku = int(df_mem.at[idx, "役満回数"])
            current_detail = df_mem.at[idx, "最大飜数詳細"] if "最大飜数詳細" in df_mem.columns else ""
            current_date_str = df_mem.at[idx, "最大飜数記録日"] if "最大飜数記録日" in df_mem.columns else ""

        with st.form("update_personal_stats"):
            c_in1, c_in2 = st.columns(2)
            with c_in1:
                new_max = st.number_input("最大飜数", min_value=0, value=current_max)
                new_detail = st.text_input("最大飜数詳細 (役名など)", value=current_detail)
                new_date_val = st.text_input("記録日 (例: 2026/02/20)", value=current_date_str)
            with c_in2:
                new_yaku = st.number_input("役満回数", min_value=0, value=current_yaku)
            if st.form_submit_button("💾 更新する", type="primary"):
                if target_idx:
                    df_mem.at[idx, "最大飜数"] = new_max
                    df_mem.at[idx, "役満回数"] = new_yaku
                    if "最大飜数詳細" not in df_mem.columns: df_mem["最大飜数詳細"] = ""
                    if "最大飜数記録日" not in df_mem.columns: df_mem["最大飜数記録日"] = ""
                    df_mem.at[idx, "最大飜数詳細"] = new_detail
                    df_mem.at[idx, "最大飜数記録日"] = new_date_val
                    save_member_data(df_mem)
                    st.success(f"✅ {active_player}さんの記録を更新しました！")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("メンバー登録されていません。「メンバー管理」から登録してください。")
    else:
        st.markdown("#### 📝 集計表")
        render_paper_sheet(df_filtered)

# --- ランキング画面 ---
def page_ranking():
    st.title("🏆 ランキング")
    page_back_button()
    st.write("")

    df = load_score_data()
    if df.empty:
        st.info("データがありません")
        return

    valid_dates = pd.to_datetime(df["論理日付"]).dropna()
    if not valid_dates.empty:
        min_date = valid_dates.min().date()
        max_date = valid_dates.max().date()
    else:
        min_date = max_date = date.today()

    c1, c2 = st.columns([2, 1])
    with c1:
        date_range = st.date_input("📅 集計期間", value=(min_date, max_date), min_value=min_date, max_value=max_date)
    with c2:
        min_games = st.number_input("規定打数", min_value=1, value=5, help="これ未満は非表示")

    if len(date_range) == 2:
        start_d, end_d = date_range
        mask = (df["論理日付"] >= start_d) & (df["論理日付"] <= end_d)
        df_filtered = df[mask]
    else:
        df_filtered = df

    if df_filtered.empty:
        st.warning("指定された期間のデータはありません")
        return

    records = []
    for _, row in df_filtered.iterrows():
        for seat in ["A", "B", "C"]:
            name = row[f"{seat}さん"]
            rank = row[f"{seat}着順"]
            if name:
                try: r = int(float(rank))
                except: r = 0
                if r > 0:
                    records.append({"name": name, "rank": r, "date": row["論理日付"]})

    if not records:
        st.warning("集計できるデータがありません")
        return

    df_raw = pd.DataFrame(records)
    stats = df_raw.groupby("name").agg(
        games=("rank", "count"),
        avg_rank=("rank", "mean"),
        first_count=("rank", lambda x: (x==1).sum()),
        third_count=("rank", lambda x: (x==3).sum()),
        days=("date", "nunique")
    ).reset_index()
    stats["games_per_day"] = stats["games"] / stats["days"]
    stats["top_rate"] = (stats["first_count"] / stats["games"]) * 100
    stats["last_avoid_rate"] = ((stats["games"] - stats["third_count"]) / stats["games"]) * 100
    stats["type"] = stats["name"].apply(lambda x: "staff" if str(x).lower().endswith("s") else "guest")
    stats["name"] = stats["name"].astype(str).str.replace(r'[（\(].*?[）\)]', '', regex=True)

    stats_guest = stats[(stats["type"] == "guest") & (stats["games"] >= min_games)]
    stats_staff = stats[(stats["type"] == "staff") & (stats["games"] >= min_games)]

    if stats_guest.empty and stats_staff.empty:
        st.warning(f"打数 {min_games} 回以上のプレイヤーがいません。")
        return

    def show_ranking_split(df_g, df_s, sort_col, asc=False, format_func=None, val_col=None):
        c1, c2 = st.columns(2)
        for col_obj, df_r, title, icon in [(c1, df_g, "お客さん", "🧑‍🤝‍🧑"), (c2, df_s, "スタッフ", "👔")]:
            with col_obj:
                st.markdown(f"#### {icon} {title} Top10")
                if not df_r.empty:
                    res = df_r.sort_values(sort_col, ascending=asc).reset_index(drop=True).head(10)
                    res["順位"] = res.index + 1
                    if format_func and val_col and val_col != "games":
                        res[val_col] = res[val_col].map(format_func)
                    cols = ["順位", "name"]
                    if val_col == "games":
                        cols.extend(["games", "games_per_day"])
                        res["games_per_day"] = res["games_per_day"].map('{:.1f}'.format)
                        rmap = {"name": "名前", "games": "打数", "games_per_day": "平均/日"}
                    else:
                        cols.extend([val_col, "games"])
                        rmap = {"name": "名前", "games": "打数",
                                "avg_rank": "平均着順", "top_rate": "トップ率", "last_avoid_rate": "ラス回避率"}
                    st.dataframe(res[cols].rename(columns=rmap), hide_index=True, use_container_width=True)
                else:
                    st.info("データなし")

    t1, t2, t3, t4, t5, t6 = st.tabs(["📊 打数", "🥇 平均着順", "👑 トップ率", "🛡 ラス回避率", "💥 最大飜数", "🀅 役満回数"])

    with t1: show_ranking_split(stats_guest, stats_staff, "games", False, None, "games")
    with t2: show_ranking_split(stats_guest, stats_staff, "avg_rank", True, '{:.2f}'.format, "avg_rank")
    with t3: show_ranking_split(stats_guest, stats_staff, "top_rate", False, '{:.1f}%'.format, "top_rate")
    with t4: show_ranking_split(stats_guest, stats_staff, "last_avoid_rate", False, '{:.1f}%'.format, "last_avoid_rate")

    df_mem = load_member_data()
    df_mem["type"] = df_mem["名前"].apply(lambda x: "staff" if str(x).lower().endswith("s") else "guest")
    df_mem["名前"] = df_mem["名前"].astype(str).str.replace(r'[（\(].*?[）\)]', '', regex=True)
    mem_g = df_mem[df_mem["type"] == "guest"]
    mem_s = df_mem[df_mem["type"] == "staff"]

    def show_mem_ranking(df_g, df_s, col):
        c1, c2 = st.columns(2)
        for col_obj, df_r, title, icon in [(c1, df_g, "お客さん", "🧑‍🤝‍🧑"), (c2, df_s, "スタッフ", "👔")]:
            with col_obj:
                st.markdown(f"#### {icon} {title} Top10")
                if not df_r.empty:
                    res = df_r.sort_values(col, ascending=False).reset_index(drop=True).head(10)
                    res = res[res[col] > 0]
                    if not res.empty:
                        res["順位"] = res.index + 1
                        cols = ["順位", "名前", col]
                        if col == "最大飜数":
                            for extra in ["最大飜数詳細", "最大飜数記録日"]:
                                if extra in res.columns: cols.append(extra)
                        st.dataframe(res[cols], hide_index=True, use_container_width=True)
                    else: st.info("データなし")
                else: st.info("データなし")

    with t5: show_mem_ranking(mem_g, mem_s, "最大飜数")
    with t6: show_mem_ranking(mem_g, mem_s, "役満回数")

# --- ログ画面 ---
def page_logs():
    st.title("📜 操作ログ")
    page_back_button()
    st.write("")

    df_logs = load_log_data()
    if not df_logs.empty and "操作" in df_logs.columns:
        df_logs = df_logs[df_logs["操作"].isin(["修正", "削除"])]
    if not df_logs.empty and "GameNo" in df_logs.columns:
        df_logs = df_logs.rename(columns={"GameNo": "DailyNo"})

    if df_logs.empty:
        st.info("修正・削除の履歴はありません")
    else:
        st.dataframe(df_logs, use_container_width=True, hide_index=True)

# ==========================================
# 7. メインルーティング
# ==========================================
if "page" not in st.session_state:
    st.session_state["page"] = "home"

page = st.session_state["page"]
if page == "home":       page_home()
elif page == "members":  page_members()
elif page == "input":    page_input()
elif page == "history":  page_history()
elif page == "edit":     page_edit()
elif page == "ranking":  page_ranking()
elif page == "profit":   page_profit()
elif page == "logs":     page_logs()
else:                    page_home()
