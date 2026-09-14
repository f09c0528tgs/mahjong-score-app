import streamlit as st
import pandas as pd
import altair as alt
import streamlit.components.v1 as components
import time
from datetime import datetime, date, timedelta, timezone
from streamlit_gsheets import GSheetsConnection

# ==========================================
# 1. ページ設定 & デザイン
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
        --accent-bright: #ffd560;
        --accent2:       #e07b39;
        --accent-soft:   rgba(240,192,64,0.12);
        --accent2-soft:  rgba(224,123,57,0.12);
        --green:         #4caf87;
        --green-soft:    rgba(76,175,135,0.12);
        --red:           #e05c5c;
        --red-soft:      rgba(224,92,92,0.12);
        --blue:          #5b9cf6;
        --blue-soft:     rgba(91,156,246,0.12);
        --purple:        #b372e0;
        --purple-soft:   rgba(179,114,224,0.12);
        --text-primary:  #e8e8f0;
        --text-muted:    #8890a8;
        --text-dim:      #5a6175;
        --border:        rgba(255,255,255,0.07);
        --border-strong: rgba(255,255,255,0.14);
        --border-accent: rgba(240,192,64,0.3);
        --shadow:        0 4px 24px rgba(0,0,0,0.4);
        --shadow-lg:     0 8px 32px rgba(0,0,0,0.5);
        --radius:        12px;
        --radius-sm:     8px;
        --radius-lg:     16px;
    }

    /* ========== 全体背景 ========== */
    .stApp {
        background-color: var(--bg-base);
        font-family: 'Noto Sans JP', sans-serif;
        color: var(--text-primary);
    }
    .main .block-container {
        padding: 1rem 1.5rem 5rem;
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
        font-size: 1.7rem !important;
        font-weight: 900 !important;
        letter-spacing: 0.02em;
        margin-bottom: 0.8rem !important;
        margin-top: 0.3rem !important;
    }
    h2 { font-size: 1.25rem !important; font-weight: 700 !important; }
    h3 { font-size: 1.05rem !important; font-weight: 700 !important; }

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
        background: linear-gradient(135deg, var(--accent) 0%, var(--accent-bright) 100%) !important;
        color: #0f1117 !important;
        border-color: var(--accent) !important;
        font-weight: 800 !important;
        box-shadow: 0 2px 12px rgba(240,192,64,0.3) !important;
    }
    .stButton > button[kind="primary"]:hover {
        box-shadow: 0 4px 20px rgba(240,192,64,0.5) !important;
        transform: translateY(-1px) !important;
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
    /* 外側のウィジェットラベル (例: 「着順」「タイプ」等のフィールド名) - 直接子のみ指定 */
    .stSelectbox > label,
    .stTextInput > label,
    .stNumberInput > label,
    .stDateInput > label,
    .stTextArea > label,
    .stRadio > label,
    .stCheckbox > label,
    [data-testid="stWidgetLabel"] {
        color: var(--text-muted) !important;
        font-size: 0.8rem !important;
        font-weight: 500 !important;
        letter-spacing: 0.04em !important;
        text-transform: uppercase !important;
    }

    /* ========== ラジオボタン ========== */
    .stRadio > div {
        gap: 0.4rem !important;
        flex-wrap: wrap !important;
    }
    /* 各オプションのスタイル (data-baseweb属性で直接ターゲットして確実に適用) */
    label[data-baseweb="radio"] {
        background: var(--bg-card2) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius-sm) !important;
        padding: 0.45rem 0.9rem !important;
        color: var(--text-primary) !important;
        font-size: 0.92rem !important;
        font-weight: 500 !important;
        text-transform: none !important;
        letter-spacing: 0 !important;
        cursor: pointer !important;
        transition: all 0.15s ease !important;
        min-height: 40px !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        gap: 0.3rem !important;
    }
    /* 内部のテキスト要素 (div/p/span) にも色を強制継承させる */
    label[data-baseweb="radio"],
    label[data-baseweb="radio"] *,
    label[data-baseweb="radio"] div,
    label[data-baseweb="radio"] p,
    label[data-baseweb="radio"] span {
        color: var(--text-primary) !important;
        opacity: 1 !important;
    }
    /* マークダウンコンテナの背景もクリア */
    label[data-baseweb="radio"] [data-testid="stMarkdownContainer"],
    label[data-baseweb="radio"] [data-testid="stMarkdownContainer"] * {
        background: transparent !important;
        color: var(--text-primary) !important;
    }
    label[data-baseweb="radio"]:hover {
        border-color: var(--accent) !important;
        background: var(--bg-card) !important;
    }
    /* チェック済みオプション */
    label[data-baseweb="radio"]:has(input:checked) {
        background: var(--accent-soft) !important;
        border-color: var(--accent) !important;
        font-weight: 800 !important;
        box-shadow: 0 0 0 2px rgba(240,192,64,0.2) !important;
    }
    label[data-baseweb="radio"]:has(input:checked),
    label[data-baseweb="radio"]:has(input:checked) *,
    label[data-baseweb="radio"]:has(input:checked) div,
    label[data-baseweb="radio"]:has(input:checked) p,
    label[data-baseweb="radio"]:has(input:checked) span {
        color: var(--accent-bright) !important;
    }
    /* ネイティブのラジオUI(丸印)のみを非表示にし、テキスト部分は残す */
    [data-baseweb="radio"] input { display: none !important; }
    [data-baseweb="radio"] > div:first-child { display: none !important; }

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
        overflow-x: auto !important;
        flex-wrap: nowrap !important;
    }
    .stTabs [data-baseweb="tab-list"]::-webkit-scrollbar { height: 4px; }
    .stTabs [data-baseweb="tab-list"]::-webkit-scrollbar-thumb {
        background: var(--border-strong);
        border-radius: 2px;
    }

    /* ========== 非選択タブ: 明るいカード背景 ========== */
    .stTabs [data-baseweb="tab"],
    .stTabs [role="tab"],
    .stTabs button[role="tab"] {
        background: #2f3550 !important;
        border-radius: var(--radius-sm) !important;
        font-family: 'Noto Sans JP', sans-serif !important;
        font-size: 0.9rem !important;
        font-weight: 700 !important;
        padding: 0.55rem 1.1rem !important;
        border: 1.5px solid rgba(255,255,255,0.25) !important;
        transition: all 0.15s ease !important;
        white-space: nowrap !important;
        flex-shrink: 0 !important;
        min-height: 42px !important;
    }

    /* 【最強セレクタ】タブ内部のあらゆる要素に白色を強制 */
    .stTabs [data-baseweb="tab"] *,
    .stTabs [role="tab"] *,
    .stTabs button[role="tab"] *,
    .stTabs [data-baseweb="tab"] p,
    .stTabs [data-baseweb="tab"] div,
    .stTabs [data-baseweb="tab"] span,
    .stTabs [data-baseweb="tab"] label,
    .stTabs [role="tab"] p,
    .stTabs [role="tab"] div,
    .stTabs [role="tab"] span,
    .stTabs [role="tab"] label,
    .stTabs [data-baseweb="tab"] [data-testid="stMarkdownContainer"],
    .stTabs [data-baseweb="tab"] [data-testid="stMarkdownContainer"] *,
    .stTabs [role="tab"] [data-testid="stMarkdownContainer"],
    .stTabs [role="tab"] [data-testid="stMarkdownContainer"] * {
        color: #ffffff !important;
        opacity: 1 !important;
        font-weight: 700 !important;
    }

    /* タブ本体そのものの文字色も指定 (直接テキストが入っているケース) */
    .stTabs [data-baseweb="tab"],
    .stTabs [role="tab"] {
        color: #ffffff !important;
    }

    /* ========== ホバー時 ========== */
    .stTabs [data-baseweb="tab"]:hover,
    .stTabs [role="tab"]:hover {
        background: rgba(240,192,64,0.2) !important;
        border-color: var(--accent) !important;
    }
    .stTabs [data-baseweb="tab"]:hover *,
    .stTabs [role="tab"]:hover * {
        color: var(--accent-bright) !important;
    }

    /* ========== 選択中のタブ: 金背景+黒文字で最大強調 ========== */
    .stTabs [data-baseweb="tab"][aria-selected="true"],
    .stTabs [role="tab"][aria-selected="true"] {
        background: var(--accent) !important;
        border-color: var(--accent) !important;
        font-weight: 900 !important;
        box-shadow: 0 3px 12px rgba(240,192,64,0.5) !important;
        color: #0f1117 !important;
    }
    .stTabs [data-baseweb="tab"][aria-selected="true"] *,
    .stTabs [role="tab"][aria-selected="true"] *,
    .stTabs [data-baseweb="tab"][aria-selected="true"] p,
    .stTabs [data-baseweb="tab"][aria-selected="true"] div,
    .stTabs [data-baseweb="tab"][aria-selected="true"] span,
    .stTabs [role="tab"][aria-selected="true"] p,
    .stTabs [role="tab"][aria-selected="true"] div,
    .stTabs [role="tab"][aria-selected="true"] span {
        color: #0f1117 !important;
        font-weight: 900 !important;
    }

    /* ========== タブパネル ========== */
    .stTabs [data-baseweb="tab-panel"] {
        background: var(--bg-card) !important;
        border: 1px solid var(--border) !important;
        border-top: none !important;
        border-radius: 0 0 var(--radius) var(--radius) !important;
        padding: 1.2rem !important;
    }

    /* 標準のハイライト下線は非表示 */
    .stTabs [data-baseweb="tab-highlight"],
    .stTabs [data-baseweb="tab-border"] {
        display: none !important;
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
        font-size: 0.75rem !important;
        font-weight: 600 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05em !important;
    }
    [data-testid="stMetricValue"] {
        color: var(--accent) !important;
        font-size: 1.5rem !important;
        font-weight: 900 !important;
        font-family: 'Zen Kaku Gothic New', sans-serif !important;
    }
    [data-testid="stMetricDelta"] { font-size: 0.78rem !important; }

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
        padding: 0.8rem 1rem !important;
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
    .cell-top { background: rgba(240,192,64,0.07) !important; }
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

    /* ========== 改善: トップナビバー ========== */
    .top-nav-bar {
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: var(--radius);
        padding: 0.4rem;
        margin-bottom: 1.2rem;
        display: flex;
        gap: 0.3rem;
        overflow-x: auto;
        -webkit-overflow-scrolling: touch;
        box-shadow: var(--shadow);
    }
    .top-nav-bar::-webkit-scrollbar { display: none; }

    /* ========== 改善: クイック統計バー ========== */
    .quick-stat-bar {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
        gap: 10px;
        margin-bottom: 1.2rem;
    }
    .quick-stat-item {
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: var(--radius);
        padding: 12px 16px;
        text-align: center;
        position: relative;
        overflow: hidden;
    }
    .quick-stat-item::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 3px;
        background: var(--accent);
    }
    .quick-stat-item.green::before { background: var(--green); }
    .quick-stat-item.red::before { background: var(--red); }
    .quick-stat-item.blue::before { background: var(--blue); }
    .quick-stat-item .qs-label {
        font-size: 10px;
        color: var(--text-muted);
        text-transform: uppercase;
        letter-spacing: 0.06em;
        margin-bottom: 4px;
        font-weight: 600;
    }
    .quick-stat-item .qs-value {
        font-size: 1.4rem;
        font-weight: 900;
        color: var(--accent);
        font-family: 'Zen Kaku Gothic New', sans-serif;
        line-height: 1.1;
    }
    .quick-stat-item.green .qs-value { color: var(--green); }
    .quick-stat-item.red .qs-value { color: var(--red); }
    .quick-stat-item.blue .qs-value { color: var(--blue); }

    /* ========== 新ホームヘッダー (ヒーロー) ========== */
    .hero-header {
        position: relative;
        overflow: hidden;
        border-radius: var(--radius-lg);
        padding: 1.6rem 1.5rem 1.4rem;
        margin-bottom: 1rem;
        background: linear-gradient(135deg,
            rgba(240,192,64,0.12) 0%,
            rgba(91,156,246,0.10) 50%,
            rgba(160,108,213,0.10) 100%);
        border: 1px solid rgba(240,192,64,0.25);
        box-shadow: 0 10px 40px rgba(0,0,0,0.3), inset 0 1px 0 rgba(255,255,255,0.05);
    }
    .hero-bg-decoration {
        position: absolute;
        inset: 0;
        pointer-events: none;
        overflow: hidden;
    }
    .hero-orb {
        position: absolute;
        border-radius: 50%;
        filter: blur(40px);
        opacity: 0.35;
    }
    .hero-orb-1 {
        width: 200px;
        height: 200px;
        background: radial-gradient(circle, var(--accent) 0%, transparent 70%);
        top: -80px;
        right: -60px;
        animation: heroFloat 8s ease-in-out infinite;
    }
    .hero-orb-2 {
        width: 180px;
        height: 180px;
        background: radial-gradient(circle, var(--accent2) 0%, transparent 70%);
        bottom: -60px;
        left: -40px;
        animation: heroFloat 10s ease-in-out infinite reverse;
    }
    @keyframes heroFloat {
        0%, 100% { transform: translate(0, 0) scale(1); }
        50% { transform: translate(20px, -15px) scale(1.05); }
    }
    .hero-content {
        position: relative;
        text-align: center;
    }
    .hero-badge {
        display: inline-block;
        padding: 0.3rem 0.9rem;
        background: rgba(240,192,64,0.15);
        border: 1px solid rgba(240,192,64,0.35);
        border-radius: 999px;
        font-size: 0.7rem;
        font-weight: 800;
        letter-spacing: 0.18em;
        color: var(--accent);
        margin-bottom: 0.6rem;
    }
    .hero-title {
        font-family: 'Zen Kaku Gothic New', sans-serif;
        font-size: 2.4rem;
        font-weight: 900;
        background: linear-gradient(135deg, var(--accent) 0%, #ffd97a 50%, var(--accent2) 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        letter-spacing: 0.06em;
        line-height: 1.15;
        margin-bottom: 0;
        text-shadow: 0 2px 20px rgba(240,192,64,0.3);
    }

    /* ========== メニューボタン (カラー別グラデーション) ========== */
    .menu-btn-wrap {
        margin-bottom: 0.7rem;
    }
    /* 全メニューボタンの基本スタイル */
    .menu-btn-wrap .stButton > button {
        position: relative !important;
        min-height: 62px !important;
        padding: 1rem 1.2rem 1rem 1.5rem !important;
        background: linear-gradient(135deg, rgba(35,39,57,0.95) 0%, rgba(47,53,80,0.85) 100%) !important;
        border: 1px solid rgba(255,255,255,0.08) !important;
        border-radius: 14px !important;
        color: var(--text-primary) !important;
        font-family: 'Zen Kaku Gothic New', sans-serif !important;
        font-weight: 700 !important;
        text-align: left !important;
        display: flex !important;
        align-items: center !important;
        line-height: 1.3 !important;
        overflow: hidden !important;
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.2), inset 0 1px 0 rgba(255,255,255,0.04) !important;
    }
    /* 左サイドの色付きアクセントバー */
    .menu-btn-wrap .stButton > button::before {
        content: '';
        position: absolute;
        left: 0;
        top: 0;
        bottom: 0;
        width: 5px;
        border-radius: 14px 0 0 14px;
        transition: width 0.25s;
    }
    /* 右上のグロー効果 */
    .menu-btn-wrap .stButton > button::after {
        content: '';
        position: absolute;
        top: -30px;
        right: -30px;
        width: 90px;
        height: 90px;
        border-radius: 50%;
        opacity: 0.15;
        filter: blur(20px);
        transition: opacity 0.25s;
    }
    .menu-btn-wrap .stButton > button:hover {
        transform: translateY(-3px) !important;
        border-color: rgba(255,255,255,0.15) !important;
        box-shadow: 0 10px 30px rgba(0,0,0,0.4),
                    inset 0 1px 0 rgba(255,255,255,0.08) !important;
    }
    .menu-btn-wrap .stButton > button:hover::before {
        width: 7px;
    }
    .menu-btn-wrap .stButton > button:hover::after {
        opacity: 0.3;
    }
    /* ボタン内テキスト (Streamlitがpタグでラップする) */
    .menu-btn-wrap .stButton > button p {
        margin: 0 !important;
        color: var(--text-primary) !important;
        font-size: 1.0rem !important;
        font-weight: 800 !important;
        letter-spacing: 0.02em !important;
    }

    /* === カラーバリエーション === */
    /* 青系: 個人成績 */
    .menu-color-blue .stButton > button::before {
        background: linear-gradient(180deg, #6ca9ff 0%, #4183db 100%);
    }
    .menu-color-blue .stButton > button::after {
        background: radial-gradient(circle, #5b9cf6 0%, transparent 70%);
    }
    .menu-color-blue .stButton > button:hover {
        border-color: rgba(91,156,246,0.4) !important;
        box-shadow: 0 10px 30px rgba(91,156,246,0.25),
                    inset 0 1px 0 rgba(255,255,255,0.08) !important;
    }

    /* 緑系: データ参照 */
    .menu-color-green .stButton > button::before {
        background: linear-gradient(180deg, #5fc99b 0%, #38956d 100%);
    }
    .menu-color-green .stButton > button::after {
        background: radial-gradient(circle, #4caf87 0%, transparent 70%);
    }
    .menu-color-green .stButton > button:hover {
        border-color: rgba(76,175,135,0.4) !important;
        box-shadow: 0 10px 30px rgba(76,175,135,0.25),
                    inset 0 1px 0 rgba(255,255,255,0.08) !important;
    }

    /* 金系: ランキング */
    .menu-color-gold .stButton > button::before {
        background: linear-gradient(180deg, #ffd57a 0%, #e0a828 100%);
    }
    .menu-color-gold .stButton > button::after {
        background: radial-gradient(circle, #f0c040 0%, transparent 70%);
    }
    .menu-color-gold .stButton > button:hover {
        border-color: rgba(240,192,64,0.5) !important;
        box-shadow: 0 10px 30px rgba(240,192,64,0.3),
                    inset 0 1px 0 rgba(255,255,255,0.08) !important;
    }

    /* 橙系: 月間成績 */
    .menu-color-orange .stButton > button::before {
        background: linear-gradient(180deg, #ff9b5e 0%, #c96422 100%);
    }
    .menu-color-orange .stButton > button::after {
        background: radial-gradient(circle, #e07b39 0%, transparent 70%);
    }
    .menu-color-orange .stButton > button:hover {
        border-color: rgba(224,123,57,0.4) !important;
        box-shadow: 0 10px 30px rgba(224,123,57,0.25),
                    inset 0 1px 0 rgba(255,255,255,0.08) !important;
    }

    /* 紫系: 2人対戦 */
    .menu-color-purple .stButton > button::before {
        background: linear-gradient(180deg, #bd8af0 0%, #8a4fc4 100%);
    }
    .menu-color-purple .stButton > button::after {
        background: radial-gradient(circle, #a06cd5 0%, transparent 70%);
    }
    .menu-color-purple .stButton > button:hover {
        border-color: rgba(160,108,213,0.4) !important;
        box-shadow: 0 10px 30px rgba(160,108,213,0.25),
                    inset 0 1px 0 rgba(255,255,255,0.08) !important;
    }

    /* ピンク系: 3人対戦 */
    .menu-color-pink .stButton > button::before {
        background: linear-gradient(180deg, #f078a5 0%, #c04477 100%);
    }
    .menu-color-pink .stButton > button::after {
        background: radial-gradient(circle, #d95a8c 0%, transparent 70%);
    }
    .menu-color-pink .stButton > button:hover {
        border-color: rgba(217,90,140,0.4) !important;
        box-shadow: 0 10px 30px rgba(217,90,140,0.25),
                    inset 0 1px 0 rgba(255,255,255,0.08) !important;
    }

    /* ========== ランキングPT 情報パネル ========== */
    .rankpt-info-panel {
        background: linear-gradient(135deg, rgba(35,39,57,0.9) 0%, rgba(47,53,80,0.7) 100%);
        border: 1px solid rgba(240,192,64,0.2);
        border-radius: 14px;
        padding: 1rem 1.2rem;
        margin-bottom: 0.8rem;
    }
    .rankpt-section-title {
        font-size: 0.78rem;
        font-weight: 800;
        color: var(--accent);
        letter-spacing: 0.05em;
        margin-bottom: 0.55rem;
    }
    .rankpt-items {
        display: flex;
        flex-wrap: wrap;
        gap: 0.4rem;
    }
    .rankpt-item {
        display: inline-flex;
        align-items: center;
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 8px;
        padding: 0.32rem 0.6rem;
        font-size: 0.76rem;
        font-weight: 600;
        color: var(--text-primary);
        white-space: nowrap;
    }
    .rankpt-divider {
        height: 1px;
        background: linear-gradient(90deg,
            transparent 0%,
            rgba(240,192,64,0.25) 50%,
            transparent 100%);
        margin: 0.9rem 0;
    }
    .rankpt-pts {
        display: flex;
        flex-wrap: wrap;
        gap: 0.4rem;
    }
    .rankpt-pt {
        display: inline-flex;
        align-items: center;
        gap: 0.3rem;
        background: rgba(0,0,0,0.25);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 999px;
        padding: 0.3rem 0.7rem;
        font-size: 0.75rem;
        color: var(--text-muted);
        white-space: nowrap;
    }
    .rankpt-pt strong {
        color: var(--text-primary);
        font-weight: 900;
        font-family: 'Zen Kaku Gothic New', sans-serif;
    }
    .rankpt-pt.pt-gold {
        border-color: rgba(240,192,64,0.4);
        background: rgba(240,192,64,0.08);
    }
    .rankpt-pt.pt-gold strong { color: var(--accent); }
    .rankpt-pt.pt-silver {
        border-color: rgba(200,205,220,0.3);
        background: rgba(200,205,220,0.06);
    }
    .rankpt-pt.pt-silver strong { color: #c8cddc; }
    .rankpt-pt.pt-bronze {
        border-color: rgba(224,123,57,0.3);
        background: rgba(224,123,57,0.06);
    }
    .rankpt-pt.pt-bronze strong { color: #e07b39; }

    /* ========== ランキングPT 内訳 (expander内) ========== */
    .rankpt-breakdown {
        display: flex;
        flex-direction: column;
        gap: 0.35rem;
        padding: 0.2rem 0;
    }
    .rankpt-bd-row {
        display: flex;
        align-items: center;
        gap: 0.6rem;
        padding: 0.5rem 0.75rem;
        border-radius: 10px;
        border: 1px solid rgba(255,255,255,0.06);
        background: rgba(255,255,255,0.02);
        position: relative;
        overflow: hidden;
        transition: transform 0.15s;
    }
    .rankpt-bd-row::before {
        content: '';
        position: absolute;
        left: 0; top: 0; bottom: 0;
        width: 3px;
    }
    /* ランクバッジ (順位) */
    .rankpt-bd-rankbadge {
        font-size: 0.8rem;
        font-weight: 800;
        white-space: nowrap;
        min-width: 52px;
        text-align: center;
        padding: 0.15rem 0.3rem;
        border-radius: 6px;
    }
    .rankpt-bd-item {
        flex: 1;
        font-size: 0.85rem;
        font-weight: 700;
        color: var(--text-primary);
        min-width: 0;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    /* スコア値 (平均着順など) */
    .rankpt-bd-score {
        font-size: 0.8rem;
        font-weight: 700;
        font-family: 'Zen Kaku Gothic New', sans-serif;
        color: var(--text-muted);
        white-space: nowrap;
        min-width: 48px;
        text-align: right;
        letter-spacing: 0.01em;
    }
    /* 獲得pt */
    .rankpt-bd-pt {
        font-size: 0.92rem;
        font-weight: 900;
        font-family: 'Zen Kaku Gothic New', sans-serif;
        white-space: nowrap;
        min-width: 42px;
        text-align: right;
    }
    /* === Tier別カラー === */
    .rankpt-bd-row.tier-gold {
        background: linear-gradient(90deg, rgba(240,192,64,0.14) 0%, rgba(240,192,64,0.03) 100%);
        border-color: rgba(240,192,64,0.3);
    }
    .rankpt-bd-row.tier-gold::before { background: var(--accent); }
    .rankpt-bd-row.tier-gold .rankpt-bd-rankbadge {
        color: #1a1d2e; background: var(--accent);
    }
    .rankpt-bd-row.tier-gold .rankpt-bd-pt { color: var(--accent); }

    .rankpt-bd-row.tier-silver {
        background: linear-gradient(90deg, rgba(200,205,220,0.1) 0%, rgba(200,205,220,0.02) 100%);
        border-color: rgba(200,205,220,0.22);
    }
    .rankpt-bd-row.tier-silver::before { background: #c8cddc; }
    .rankpt-bd-row.tier-silver .rankpt-bd-rankbadge {
        color: #1a1d2e; background: #c8cddc;
    }
    .rankpt-bd-row.tier-silver .rankpt-bd-pt { color: #c8cddc; }

    .rankpt-bd-row.tier-bronze {
        background: linear-gradient(90deg, rgba(224,123,57,0.12) 0%, rgba(224,123,57,0.02) 100%);
        border-color: rgba(224,123,57,0.25);
    }
    .rankpt-bd-row.tier-bronze::before { background: #e07b39; }
    .rankpt-bd-row.tier-bronze .rankpt-bd-rankbadge {
        color: #fff; background: #e07b39;
    }
    .rankpt-bd-row.tier-bronze .rankpt-bd-pt { color: #e07b39; }

    .rankpt-bd-row.tier-plain::before { background: rgba(255,255,255,0.15); }
    .rankpt-bd-row.tier-plain .rankpt-bd-rankbadge {
        color: var(--text-muted); background: rgba(255,255,255,0.06);
    }
    .rankpt-bd-row.tier-plain .rankpt-bd-pt { color: var(--text-muted); }

    /* 合計行 */
    .rankpt-bd-total {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-top: 0.5rem;
        padding: 0.6rem 0.85rem;
        background: linear-gradient(135deg, rgba(240,192,64,0.14) 0%, rgba(240,192,64,0.05) 100%);
        border: 1px solid rgba(240,192,64,0.3);
        border-radius: 10px;
    }
    .rankpt-bd-total-label {
        font-size: 0.8rem;
        color: var(--text-muted);
        font-weight: 700;
    }
    .rankpt-bd-total-pt {
        font-size: 1.4rem;
        font-weight: 900;
        color: var(--accent);
        font-family: 'Zen Kaku Gothic New', sans-serif;
        line-height: 1;
    }
    .rankpt-bd-total-unit {
        font-size: 0.8rem;
        margin-left: 0.15rem;
        color: var(--accent);
        opacity: 0.7;
    }

    /* ========== expander (ランキングPT用) の装飾 ========== */
    /* Streamlit の expander ヘッダーをカッコよく */
    div[data-testid="stExpander"] {
        border: none !important;
        margin-bottom: 0.5rem !important;
    }
    div[data-testid="stExpander"] details {
        background: linear-gradient(135deg, rgba(35,39,57,0.95) 0%, rgba(47,53,80,0.8) 100%) !important;
        border: 1px solid rgba(255,255,255,0.09) !important;
        border-radius: 12px !important;
        overflow: hidden !important;
        transition: all 0.2s !important;
    }
    div[data-testid="stExpander"] details:hover {
        border-color: rgba(240,192,64,0.35) !important;
        box-shadow: 0 4px 16px rgba(0,0,0,0.3) !important;
    }
    div[data-testid="stExpander"] details[open] {
        border-color: rgba(240,192,64,0.3) !important;
        box-shadow: 0 6px 24px rgba(0,0,0,0.35) !important;
    }
    div[data-testid="stExpander"] summary {
        padding: 0.75rem 1rem !important;
        font-family: 'Zen Kaku Gothic New', sans-serif !important;
        font-weight: 800 !important;
        font-size: 1.0rem !important;
        color: var(--text-primary) !important;
        transition: background 0.2s !important;
    }
    div[data-testid="stExpander"] summary:hover {
        background: rgba(240,192,64,0.06) !important;
        color: var(--accent) !important;
    }
    div[data-testid="stExpander"] details[open] summary {
        border-bottom: 1px solid rgba(255,255,255,0.08) !important;
        background: rgba(240,192,64,0.04) !important;
    }

    /* ========== ホームフッター ========== */
    .home-footer {
        margin-top: 2rem;
        padding: 1.2rem 0 0.5rem;
        text-align: center;
    }
    .home-footer-line {
        height: 1px;
        background: linear-gradient(90deg,
            transparent 0%,
            rgba(240,192,64,0.3) 50%,
            transparent 100%);
        margin-bottom: 0.8rem;
    }
    .home-footer-text {
        font-size: 0.7rem;
        color: rgba(255,255,255,0.25);
        letter-spacing: 0.18em;
        font-weight: 600;
    }

    /* ========== 席カード (入力画面) ========== */
    .seat-card {
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: var(--radius);
        padding: 0.9rem 1.1rem;
        margin-bottom: 0.7rem;
        position: relative;
        overflow: hidden;
    }
    .seat-card.seat-a { border-left: 4px solid var(--blue); }
    .seat-card.seat-b { border-left: 4px solid var(--accent2); }
    .seat-card.seat-c { border-left: 4px solid var(--green); }

    .seat-header-row {
        display: flex;
        align-items: center;
        gap: 0.7rem;
        margin-bottom: 0.6rem;
    }
    .seat-badge {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 36px;
        height: 36px;
        background: var(--accent);
        color: #0f1117;
        font-weight: 900;
        font-size: 1.1rem;
        border-radius: 50%;
        box-shadow: 0 2px 6px rgba(0,0,0,0.3);
        flex-shrink: 0;
    }
    .seat-badge.a { background: var(--blue); color: white; }
    .seat-badge.b { background: var(--accent2); color: white; }
    .seat-badge.c { background: var(--green); color: white; }
    .seat-card-label {
        font-size: 0.85rem;
        color: var(--text-muted);
        font-weight: 600;
        letter-spacing: 0.05em;
    }

    /* ========== 改善: 入力ステータスバー ========== */
    .input-status-bar {
        background: linear-gradient(135deg, var(--bg-card) 0%, rgba(240,192,64,0.05) 100%);
        border: 1px solid var(--border-accent);
        border-radius: var(--radius);
        padding: 0.85rem 1.2rem;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 1rem;
        flex-wrap: wrap;
    }
    .input-status-bar .isb-main {
        color: var(--accent);
        font-weight: 800;
        font-size: 1rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    .input-status-bar .isb-sub {
        color: var(--text-muted);
        font-size: 0.82rem;
        margin-left: auto;
    }

    /* ========== 改善: 保存成功通知 (トースト風) ========== */
    .toast-success {
        background: linear-gradient(135deg, var(--green-soft) 0%, rgba(76,175,135,0.18) 100%);
        border: 1px solid var(--green);
        border-radius: var(--radius);
        padding: 1rem 1.3rem;
        margin-bottom: 1rem;
        color: var(--green);
        font-weight: 700;
        font-size: 0.95rem;
        display: flex;
        align-items: center;
        gap: 0.7rem;
        box-shadow: 0 4px 16px rgba(76,175,135,0.2);
        animation: slideDown 0.3s ease-out;
    }
    @keyframes slideDown {
        from { opacity: 0; transform: translateY(-12px); }
        to   { opacity: 1; transform: translateY(0); }
    }
    .toast-success .toast-icon {
        font-size: 1.3rem;
    }

    /* ========== 改善: 入力プレビュー ========== */
    .preview-card {
        background: linear-gradient(135deg, var(--bg-card) 0%, var(--bg-card2) 100%);
        border: 1px dashed var(--border-accent);
        border-radius: var(--radius);
        padding: 1rem 1.2rem;
        margin: 0.8rem 0;
    }
    .preview-card .preview-title {
        font-size: 0.75rem;
        color: var(--accent);
        font-weight: 700;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        margin-bottom: 0.6rem;
    }
    .preview-row {
        display: flex;
        align-items: center;
        gap: 0.8rem;
        padding: 0.4rem 0;
        border-bottom: 1px dashed var(--border);
    }
    .preview-row:last-child { border-bottom: none; }
    .preview-rank {
        width: 32px;
        height: 32px;
        border-radius: 50%;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-weight: 900;
        font-size: 1.1rem;
        flex-shrink: 0;
    }
    .preview-rank.r1 { background: linear-gradient(135deg, #ffd700 0%, #f0c040 100%); color: #0f1117; }
    .preview-rank.r2 { background: linear-gradient(135deg, #c0c0c0 0%, #a0a0a0 100%); color: #0f1117; }
    .preview-rank.r3 { background: linear-gradient(135deg, #cd7f32 0%, #a06228 100%); color: #fff; }
    .preview-name { font-weight: 700; color: var(--text-primary); }
    .preview-seat {
        font-size: 0.7rem;
        color: var(--text-muted);
        font-weight: 600;
        letter-spacing: 0.05em;
        background: rgba(255,255,255,0.04);
        padding: 1px 6px;
        border-radius: 3px;
    }

    /* ========== 改善: ホームメニューカード ========== */
    .menu-grid-card {
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: var(--radius);
        padding: 1rem 1.2rem;
        transition: all 0.18s ease;
        cursor: pointer;
        display: flex;
        align-items: center;
        gap: 0.8rem;
    }
    .menu-grid-card:hover {
        border-color: var(--accent);
        background: var(--accent-soft);
        transform: translateY(-2px);
    }

    /* ========== セクションタイトル ========== */
    .section-title {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        font-size: 1.05rem;
        font-weight: 700;
        color: var(--text-primary);
        margin-bottom: 0.8rem;
        margin-top: 0.5rem;
        font-family: 'Zen Kaku Gothic New', sans-serif;
    }
    .section-title .section-icon {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 28px;
        height: 28px;
        background: var(--accent-soft);
        border-radius: 8px;
        color: var(--accent);
        font-size: 1rem;
    }

    /* ========== モバイル対応 ========== */
    @media (max-width: 640px) {
        .main .block-container { padding: 0.8rem 1rem 5rem; }
        .hero-header { padding: 1.6rem 1rem 1.4rem; }
        .hero-title { font-size: 1.8rem; }
        .menu-btn-wrap .stButton > button {
            min-height: 54px !important;
            padding: 0.8rem 0.8rem 0.8rem 1.2rem !important;
        }
        .menu-btn-wrap .stButton > button p {
            font-size: 0.88rem !important;
        }
        h1 { font-size: 1.4rem !important; }
        [data-testid="stMetricValue"] { font-size: 1.2rem !important; }
        .stats-table td { font-size: 14px; padding: 8px; }
        .stats-table th { font-size: 10px; padding: 6px; }
        .seat-badge { width: 32px; height: 32px; font-size: 1rem; }
        .quick-stat-item .qs-value { font-size: 1.2rem; }
    }

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

    /* ========== セクション区切り ========== */
    .section-divider {
        border: none;
        border-top: 1px dashed var(--border);
        margin: 0.8rem 0;
    }
    </style>
"""
st.markdown(hide_style, unsafe_allow_html=True)

# ==========================================
# 2. データ管理関数 (元のまま)
# ==========================================
SHEET_SCORE = "score"
SHEET_MEMBER = "members"
SHEET_LOG = "logs"
SHEET_PROFIT = "daily_profits"
SHEET_PENDING = "pending_buffer"  # 仮保存データ用の専用シート
SHEET_RATING = "ratings"  # レーティング/段位データ

# pending_buffer シートに必要な列
PENDING_COLS = [
    "EntryId",         # 一意ID (ISO日時+ランダム)
    "Type",            # add / update / delete
    "TargetGameNo",    # update/delete時の対象GameNo (addは仮の負の数)
    "Timestamp",       # 追加日時
    "Detail",          # 編集/削除の差分テキスト
    "Info",            # 削除時の情報
    # 以下、addとupdateで使うペイロード列 (EXPECTED_COLSと同じ)
    "GameNo", "TableNo", "SetNo", "日時", "備考",
    "Aさん", "Aタイプ", "A着順",
    "Bさん", "Bタイプ", "B着順",
    "Cさん", "Cタイプ", "C着順",
    "LogDetail",       # add時のログ用詳細
]

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
# 2.5 永続バッファ機構 (一括保存)
# ==========================================
# 仮保存データを専用シート `pending_buffer` に書き込み、ページ遷移・ブラウザ閉じても消えないようにする。
# session_state はキャッシュとして使い、シートとの同期はライフサイクル要所で行う。
#
# 各エントリ (PENDING_COLS) は以下:
#   EntryId, Type (add/update/delete), TargetGameNo, Timestamp, Detail, Info,
#   GameNo, TableNo, SetNo, 日時, 備考, Aさん,Aタイプ,A着順, Bさん,Bタイプ,B着順, Cさん,Cタイプ,C着順,
#   LogDetail

import uuid as _uuid

@st.cache_data(ttl=60, show_spinner=False)
def _fetch_pending_cached(_conn):
    """
    pending_buffer シートを長めのキャッシュで読む (60秒)。
    書き込み時に明示的にキャッシュクリアされる。
    タイムアウト時は空DataFrameを返してアプリを止めない。
    """
    try:
        result = _conn.read(worksheet=SHEET_PENDING, ttl=0)
        return result
    except Exception as e:
        # シートが無い / タイムアウト / API制限 → 空DataFrame
        return pd.DataFrame(columns=PENDING_COLS)

def _save_pending_df(df):
    """pending_buffer シートを上書き保存 (シートが無ければ自動作成)"""
    conn = get_conn()
    # 列を統一
    for c in PENDING_COLS:
        if c not in df.columns:
            df[c] = ""
    df = df[PENDING_COLS]
    try:
        conn.update(worksheet=SHEET_PENDING, data=df)
        _fetch_pending_cached.clear()
    except Exception as e:
        err_msg = str(e)
        # シートが存在しない場合は自動作成を試みる
        if "WorksheetNotFound" in err_msg or "worksheet" in err_msg.lower() or "not found" in err_msg.lower():
            try:
                # ヘッダ行だけ含む空のDataFrameでシートを作成
                empty_df = pd.DataFrame(columns=PENDING_COLS)
                # create メソッドでシートを新規作成
                try:
                    conn.create(worksheet=SHEET_PENDING, data=empty_df)
                except Exception:
                    # create が使えない場合は update が新規シートを作るかもしれない (gsheets版による)
                    pass
                # 作成後、再度書き込み
                time.sleep(1)
                conn.update(worksheet=SHEET_PENDING, data=df)
                _fetch_pending_cached.clear()
                st.success(f"✅ 仮保存用シート `{SHEET_PENDING}` を自動作成しました")
                return
            except Exception as e2:
                st.error(f"仮保存シートの自動作成に失敗しました: {e2}")
                st.info(
                    f"💡 手動でスプレッドシートに `{SHEET_PENDING}` という名前のシートを追加してください。\n"
                    f"1行目(A1セル)に次のヘッダーをタブ区切りで貼り付けてください:\n\n"
                    f"`{chr(9).join(PENDING_COLS)}`"
                )
                st.stop()
        else:
            st.error(f"仮保存シートの更新に失敗しました: {e}")
            st.stop()

def _load_pending_df():
    """pending_buffer シートから読み込み、DataFrameを返す。失敗時は空DataFrame"""
    conn = get_conn()
    df = _fetch_pending_cached(conn)
    if df is None:
        # シートが無い場合は空DataFrameを返す (作成は保存時に試行)
        return pd.DataFrame(columns=PENDING_COLS)
    if df.empty:
        return pd.DataFrame(columns=PENDING_COLS)
    # 必要な列を補完
    for c in PENDING_COLS:
        if c not in df.columns:
            df[c] = ""
    df = df.fillna("")
    # 型変換
    for nc in ["TargetGameNo", "GameNo", "TableNo", "SetNo", "A着順", "B着順", "C着順"]:
        df[nc] = pd.to_numeric(df[nc], errors='coerce').fillna(0).astype(int)
    return df

def _df_row_to_entry(row):
    """pending_buffer の1行を内部entry辞書に変換"""
    return {
        "EntryId": str(row["EntryId"]),
        "type": str(row["Type"]),
        "target_game_no": int(row["TargetGameNo"]) if str(row["TargetGameNo"]).strip() else 0,
        "timestamp": str(row["Timestamp"]),
        "detail": str(row["Detail"]),
        "info": str(row["Info"]),
        "data": {
            "GameNo": int(row["GameNo"]),
            "TableNo": int(row["TableNo"]),
            "SetNo": int(row["SetNo"]),
            "日時": str(row["日時"]),
            "備考": str(row["備考"]),
            "Aさん": str(row["Aさん"]), "Aタイプ": str(row["Aタイプ"]), "A着順": int(row["A着順"]),
            "Bさん": str(row["Bさん"]), "Bタイプ": str(row["Bタイプ"]), "B着順": int(row["B着順"]),
            "Cさん": str(row["Cさん"]), "Cタイプ": str(row["Cタイプ"]), "C着順": int(row["C着順"]),
            "_log_detail": str(row["LogDetail"]),
        },
    }

def _entry_to_df_row(entry):
    """内部entry辞書を pending_buffer の1行に変換"""
    data = entry.get("data", {})
    return {
        "EntryId": entry.get("EntryId", str(_uuid.uuid4())),
        "Type": entry["type"],
        "TargetGameNo": entry.get("target_game_no", 0),
        "Timestamp": entry.get("timestamp", datetime.now().isoformat()),
        "Detail": entry.get("detail", ""),
        "Info": entry.get("info", ""),
        "GameNo": data.get("GameNo", 0),
        "TableNo": data.get("TableNo", 0),
        "SetNo": data.get("SetNo", 0),
        "日時": data.get("日時", ""),
        "備考": data.get("備考", ""),
        "Aさん": data.get("Aさん", ""), "Aタイプ": data.get("Aタイプ", ""), "A着順": data.get("A着順", 0),
        "Bさん": data.get("Bさん", ""), "Bタイプ": data.get("Bタイプ", ""), "B着順": data.get("B着順", 0),
        "Cさん": data.get("Cさん", ""), "Cタイプ": data.get("Cタイプ", ""), "C着順": data.get("C着順", 0),
        "LogDetail": data.get("_log_detail", ""),
    }

def load_pending_changes(force_refresh=False):
    """
    pending_buffer から全エントリを読み込みリストで返す。
    session_state にキャッシュを持ち、同一リクエスト内で複数回呼ばれても1度しか読まない。

    Args:
        force_refresh: Trueにすると強制的に再読込
    """
    # セッション内キャッシュを使用
    cache_key = "_pending_changes_cache"
    if not force_refresh and cache_key in st.session_state:
        return st.session_state[cache_key]

    df = _load_pending_df()
    if df.empty:
        entries = []
    else:
        entries = [_df_row_to_entry(row) for _, row in df.iterrows()]
        entries.sort(key=lambda e: e.get("timestamp", ""))

    st.session_state[cache_key] = entries
    return entries

def _invalidate_pending_cache():
    """pending_changes キャッシュを無効化 (書き込み後に呼ぶ)"""
    if "_pending_changes_cache" in st.session_state:
        del st.session_state["_pending_changes_cache"]

def save_pending_changes(entries):
    """エントリのリストを pending_buffer シートに保存"""
    if not entries:
        # 空の場合はヘッダだけのDataFrameを書く
        df = pd.DataFrame(columns=PENDING_COLS)
    else:
        rows = [_entry_to_df_row(e) for e in entries]
        df = pd.DataFrame(rows)
    _save_pending_df(df)
    # 書いた直後は session_state のキャッシュも更新
    st.session_state["_pending_changes_cache"] = list(entries)

def has_pending_changes():
    return pending_count() > 0

def pending_count():
    return len(load_pending_changes())

def _next_temp_game_no(entries):
    """既存entriesの中で最小の(最も負の)target_game_noの次を発番"""
    existing = [e.get("target_game_no", 0) for e in entries if e.get("target_game_no", 0) < 0]
    if not existing:
        return -1
    return min(existing) - 1

def buffer_add(new_row):
    """新規行をバッファに追加 (シートに書き込み)"""
    entries = load_pending_changes()
    temp_no = _next_temp_game_no(entries)
    new_row = dict(new_row)
    new_row["GameNo"] = temp_no
    entry = {
        "EntryId": str(_uuid.uuid4()),
        "type": "add",
        "target_game_no": temp_no,
        "data": new_row,
        "timestamp": datetime.now().isoformat(),
        "detail": "",
        "info": "",
    }
    entries.append(entry)
    save_pending_changes(entries)

def buffer_update(target_game_no, new_data, detail=""):
    """既存または未保存行の更新をバッファに記録"""
    entries = load_pending_changes()
    # 同じ target_game_no に対する既存のadd/update/deleteを統合
    for i, e in enumerate(entries):
        if e.get("target_game_no") == target_game_no:
            if e["type"] == "add":
                # 未保存add: dataを書き換えて add のまま残す
                merged = dict(e["data"])
                merged.update(new_data)
                merged["GameNo"] = target_game_no
                entries[i]["data"] = merged
                entries[i]["timestamp"] = datetime.now().isoformat()
                save_pending_changes(entries)
                return
            elif e["type"] == "update":
                entries[i]["data"] = new_data
                entries[i]["detail"] = detail
                entries[i]["timestamp"] = datetime.now().isoformat()
                save_pending_changes(entries)
                return
            elif e["type"] == "delete":
                # 削除予定→更新に切替
                entries[i] = {
                    "EntryId": str(_uuid.uuid4()),
                    "type": "update",
                    "target_game_no": target_game_no,
                    "data": new_data,
                    "detail": detail,
                    "info": "",
                    "timestamp": datetime.now().isoformat(),
                }
                save_pending_changes(entries)
                return
    # 新規update
    entries.append({
        "EntryId": str(_uuid.uuid4()),
        "type": "update",
        "target_game_no": target_game_no,
        "data": new_data,
        "detail": detail,
        "info": "",
        "timestamp": datetime.now().isoformat(),
    })
    save_pending_changes(entries)

def buffer_delete(target_game_no, info=""):
    """既存または未保存行の削除をバッファに記録"""
    entries = load_pending_changes()
    for i, e in enumerate(entries):
        if e.get("target_game_no") == target_game_no:
            if e["type"] == "add":
                # 未保存add → エントリ消去
                entries.pop(i)
                save_pending_changes(entries)
                return
            elif e["type"] == "update":
                # update予定→deleteに切替
                entries[i] = {
                    "EntryId": str(_uuid.uuid4()),
                    "type": "delete",
                    "target_game_no": target_game_no,
                    "data": {},
                    "detail": "",
                    "info": info,
                    "timestamp": datetime.now().isoformat(),
                }
                save_pending_changes(entries)
                return
            elif e["type"] == "delete":
                return
    entries.append({
        "EntryId": str(_uuid.uuid4()),
        "type": "delete",
        "target_game_no": target_game_no,
        "data": {},
        "detail": "",
        "info": info,
        "timestamp": datetime.now().isoformat(),
    })
    save_pending_changes(entries)

def buffer_clear():
    """全バッファをクリア (シートも空に)"""
    save_pending_changes([])

def apply_buffer_to_df(df):
    """
    DataFrameにバッファの変更を適用し、表示用の実効DataFrameを返す。
    df: load_score_data() の結果 (派生カラム含む)
    """
    changes = load_pending_changes()
    if not changes:
        return df

    df = df.copy() if not df.empty else pd.DataFrame(columns=EXPECTED_COLS)

    # 削除を先に適用
    delete_ids = [e["target_game_no"] for e in changes if e["type"] == "delete"]
    if delete_ids and not df.empty:
        df = df[~df["GameNo"].isin(delete_ids)]

    # 更新を適用
    for e in changes:
        if e["type"] == "update":
            target = e["target_game_no"]
            if not df.empty and target in df["GameNo"].values:
                idx_pos = df[df["GameNo"] == target].index
                for col, val in e["data"].items():
                    if col in df.columns:
                        df.loc[idx_pos, col] = val

    # 新規追加を適用 (EXPECTED_COLSのみ取り出して追加)
    add_rows = []
    for e in changes:
        if e["type"] == "add":
            row = {c: e["data"].get(c, "") for c in EXPECTED_COLS}
            add_rows.append(row)
    if add_rows:
        df_add = pd.DataFrame(add_rows)
        if df.empty:
            df = df_add
        else:
            df = pd.concat([df, df_add], ignore_index=True)

    # 派生カラムを再計算
    df = process_score_df(df[EXPECTED_COLS]) if not df.empty else df
    if df is None:
        return pd.DataFrame(columns=EXPECTED_COLS)
    return df

def load_score_data_effective():
    """実効スコアデータ (スプレッドシート + バッファ) を返す"""
    base_df = load_score_data()
    return apply_buffer_to_df(base_df)

# ==========================================
# 2.6 レーティング & 段位システム
# ==========================================
# 天鳳ライクの計算式を3人麻雀向けに調整。
# 着順ポイントは 1着:+15 / 2着:-4.5 / 3着:-9.5 (合計+1.0)
# 補正: 卓平均レートとの差を40で割ったものを加算 → 強い人に勝つと大幅アップ
# 対局数に応じた調整係数で徐々に安定させる
#
# 段位は独立のポイント制。段位ptは着順ごとに増減し、閾値で昇段/降段。
# 段位が高いほど1着で得られるptが少なく、3着で失うptが多くなる (難易度上昇)

# --- 定数 ---
RATING_INIT = 1500          # 初期レート
RANK_POINTS_1 = 15.0        # 1着の基本ポイント
RANK_POINTS_2 = -4.0        # 2着 (合計+2で少しインフレ気味の設計)
RANK_POINTS_3 = -9.0        # 3着

# 段位定義 (累積ptベース方式):
#  (段位名, 段位到達に必要な累積pt閾値, 表示色)
#
# 【仕様】
#  - 段位ptは常に累積される (リセットなし)
#  - 累積ptが段位閾値を超えたらその段位、下回れば下段へ
#  - 着順ptは全段位共通: 1着 +30 / 2着 -3 / 3着 -15
#  - 平均獲得pt/戦 = 0.36*30 - 0.34*3 - 0.30*15 = +5.28 (平均着順1.95のプレイヤー)
#  - 2000戦で +10560pt → 八段 (要件達成)
#
# 【平均着順と段位の相関】
#  平均1.94 (トップ率36%) → 2000戦で八段
#  平均2.00 (完全平均)   → 2000戦で六段
#  平均2.10             → 2000戦で二段
#  平均2.15             → 2000戦で4級
#  平均2.25             → 2000戦で新人
#
# 【降段】累積ptが下がれば自然に降段。閾値による段位判定なので、
#         一時的にptが下がっても、戻れば同じ段位に戻る (安定した昇降段)

# 段位判定用の閾値: (段位Index, 段位名, 累積pt閾値, 表示色)
# 「その閾値以上の累積ptがあればその段位」
DAN_TABLE = [
    # (段位名,   累積pt閾値, 表示色)
    ("新人",     -99999,  "#8890a8"),  # 最下位 (負の累積ptでも新人)
    ("9級",       -100,  "#8890a8"),
    ("8級",          0,  "#8890a8"),  # 累積0pt以上で8級
    ("7級",        100,  "#a8a8b8"),
    ("6級",        250,  "#a8a8b8"),
    ("5級",        450,  "#c0c0c8"),
    ("4級",        700,  "#c0c0c8"),
    ("3級",       1000,  "#d0d0d8"),
    ("2級",       1400,  "#d0d0d8"),
    ("1級",       1800,  "#e8e8f0"),
    ("初段",      2300,  "#5b9cf6"),   # 有段者
    ("二段",      3000,  "#5b9cf6"),
    ("三段",      3800,  "#4caf87"),
    ("四段",      4700,  "#4caf87"),
    ("五段",      5700,  "#f0c040"),
    ("六段",      6800,  "#f0c040"),
    ("七段",      8100,  "#e07b39"),
    ("八段",      9500,  "#e07b39"),   # 平均1.95のプレイヤー2000戦で10560pt → 八段
    ("九段",     11500,  "#e05c5c"),
    ("十段",     14000,  "#b372e0"),   # 最上位
]

# 着順ptは全段位共通 (段位別ではなくシンプルに)
DAN_POINTS_1 = 30    # 1着ポイント
DAN_POINTS_2 = -3    # 2着ポイント
DAN_POINTS_3 = -15   # 3着ポイント

# レーティング/段位を保存するシートの列
RATING_COLS = ["名前", "レート", "対局数", "段位Index", "段位pt"]

def _get_rank_points(rank):
    """着順から基本ポイントを返す"""
    if rank == 1: return RANK_POINTS_1
    if rank == 2: return RANK_POINTS_2
    if rank == 3: return RANK_POINTS_3
    return 0.0

def _get_dan_rank_points(rank):
    """着順から段位ポイントを返す (全段位共通)"""
    if rank == 1: return DAN_POINTS_1
    if rank == 2: return DAN_POINTS_2
    if rank == 3: return DAN_POINTS_3
    return 0

def _get_dan_index_from_pts(cumulative_pts):
    """累積ptから段位Indexを判定"""
    dan_idx = 0
    for i, dan in enumerate(DAN_TABLE):
        if cumulative_pts >= dan[1]:
            dan_idx = i
    return dan_idx

def _rating_adjust_factor(games):
    """
    対局数に応じた調整係数。
    序盤は変動大きめ、300戦で完全安定期(0.4固定)。
    """
    if games >= 300:
        return 0.4
    return max(0.4, 1.0 - games * 0.002)

def compute_ratings_from_scratch(df_score, until_dt=None, from_dt=None):
    """
    scoreデータから全プレイヤーのレーティング/段位を1試合ずつ順に計算して返す。
    Returns: dict {name: {"レート": float, "対局数": int, "段位Index": int, "段位pt": float}}

    プレイヤーが登録メンバーでなくても集計対象になる。

    Args:
        df_score: 対局データDataFrame
        until_dt: 指定した場合、この日時 (pd.Timestamp) 以前の対局のみを集計対象とする
        from_dt: 指定した場合、この日時以降の対局のみを集計対象とする
    """
    ratings = {}  # name -> dict

    def ensure_player(name):
        if name and name not in ratings:
            ratings[name] = {
                "レート": float(RATING_INIT),
                "対局数": 0,
                "段位Index": 0,
                "段位pt": 0.0,
            }

    if df_score is None or df_score.empty:
        return ratings

    # 時系列で並べる (GameNoを最終キーにして順序を確定)
    df = df_score.copy()
    if "日時Obj" in df.columns:
        # NaTを含む行を除外 (比較でエラーになるため)
        df = df[df["日時Obj"].notna()]
        # 期間指定 (from/until)
        if from_dt is not None:
            df = df[df["日時Obj"] >= from_dt]
        if until_dt is not None:
            df = df[df["日時Obj"] <= until_dt]
        # GameNoを最終ソートキーにして順序を確定 (同時刻の対局でも一貫した順序)
        sort_keys = ["日時Obj", "TableNo", "SetNo"]
        if "GameNo" in df.columns:
            sort_keys.append("GameNo")
        df = df.sort_values(sort_keys)
    elif "GameNo" in df.columns:
        df = df.sort_values(["GameNo"])

    if df.empty:
        return ratings

    for _, row in df.iterrows():
        # 3人の名前と着順を取り出す
        players = []
        valid = True
        for seat in ["A", "B", "C"]:
            n = row.get(f"{seat}さん", "")
            n = str(n).strip() if n else ""
            try:
                r = int(float(row.get(f"{seat}着順", 0)))
            except:
                r = 0
            if not n or r not in [1, 2, 3]:
                valid = False
                break
            players.append((n, r))

        if not valid:
            continue

        # 3人の着順が [1,2,3] を成すか
        if sorted([p[1] for p in players]) != [1, 2, 3]:
            continue

        # 同一プレイヤーが同じ卓に複数人いる異常データはスキップ
        if len({p[0] for p in players}) != 3:
            continue

        for name, _ in players:
            ensure_player(name)

        # 【重要】試合開始時点のレートをスナップショット。全員のレートをこの時点で確定し、
        # 一斉に更新する (順序依存を排除)。
        snapshot = {name: ratings[name]["レート"] for name, _ in players}
        snapshot_games = {name: ratings[name]["対局数"] for name, _ in players}

        # 【重要】各プレイヤーの卓平均補正は「自分以外の平均レート」を使う
        # これによりゼロサム性が保たれ、卓平均補正が意味を持つ
        # (自レートを含めると、自分-自分の項が入って補正効果が減衰する)
        for name, rank in players:
            others = [snapshot[n] for n, _ in players if n != name]
            opp_avg = sum(others) / len(others)  # 自分以外の平均

            cur = snapshot[name]
            games = snapshot_games[name]
            base = _get_rank_points(rank)
            correction = (opp_avg - cur) / 40.0
            delta = (base + correction) * _rating_adjust_factor(games)
            ratings[name]["レート"] = cur + delta
            ratings[name]["対局数"] = games + 1

            # ---- 段位ポイント計算 (累積pt方式) ----
            # 【仕様】
            #  - 段位ptは常に累積 (リセットなし)
            #  - 累積ptが段位閾値を超えたらその段位に自動判定
            #  - 平均着順との相関が強く出る設計
            dan_pts = _get_dan_rank_points(rank)
            new_cum_pts = ratings[name]["段位pt"] + dan_pts
            new_dan_idx = _get_dan_index_from_pts(new_cum_pts)

            ratings[name]["段位Index"] = new_dan_idx
            ratings[name]["段位pt"] = new_cum_pts

    return ratings

def ratings_dict_to_df(ratings):
    """辞書形式のレーティングデータをDataFrameに変換"""
    if not ratings:
        return pd.DataFrame(columns=RATING_COLS + ["段位名"])
    rows = []
    for name, d in ratings.items():
        dan_idx = d["段位Index"]
        # 次の段位の閾値 (最上位なら-)
        next_threshold = DAN_TABLE[dan_idx + 1][1] if dan_idx + 1 < len(DAN_TABLE) else None
        rows.append({
            "名前": name,
            "レート": round(d["レート"], 2),
            "対局数": d["対局数"],
            "段位Index": dan_idx,
            "段位pt": round(d["段位pt"], 2),
            "段位名": DAN_TABLE[dan_idx][0],
            "段位色": DAN_TABLE[dan_idx][2],  # 新構造: [0]名前, [1]閾値, [2]色
            "昇段まで": next_threshold if next_threshold is not None else 0,  # 次段位の閾値
        })
    df = pd.DataFrame(rows)
    df = df.sort_values("レート", ascending=False).reset_index(drop=True)
    return df

def _load_rating_df():
    """ratings シートから読み込み"""
    conn = get_conn()
    try:
        df = fetch_data_cached(conn, SHEET_RATING)
        if df is None or df.empty:
            return pd.DataFrame(columns=RATING_COLS)
        for c in RATING_COLS:
            if c not in df.columns:
                df[c] = "" if c == "名前" else 0
        df["レート"] = pd.to_numeric(df["レート"], errors='coerce').fillna(RATING_INIT).astype(float)
        df["対局数"] = pd.to_numeric(df["対局数"], errors='coerce').fillna(0).astype(int)
        df["段位Index"] = pd.to_numeric(df["段位Index"], errors='coerce').fillna(0).astype(int)
        df["段位pt"] = pd.to_numeric(df["段位pt"], errors='coerce').fillna(0).astype(float)
        return df[RATING_COLS]
    except Exception:
        return pd.DataFrame(columns=RATING_COLS)

def _save_rating_df(df):
    """ratings シートを上書き保存 (シートが無ければ自動作成)"""
    conn = get_conn()
    df = df[RATING_COLS].copy()
    try:
        conn.update(worksheet=SHEET_RATING, data=df)
        fetch_data_cached.clear()
    except Exception as e:
        err_msg = str(e)
        if "WorksheetNotFound" in err_msg or "not found" in err_msg.lower():
            try:
                empty_df = pd.DataFrame(columns=RATING_COLS)
                try:
                    conn.create(worksheet=SHEET_RATING, data=empty_df)
                except Exception:
                    pass
                time.sleep(1)
                conn.update(worksheet=SHEET_RATING, data=df)
                fetch_data_cached.clear()
                st.success(f"✅ レーティング用シート `{SHEET_RATING}` を自動作成しました")
                return
            except Exception as e2:
                st.warning(f"レーティングシート自動作成失敗: {e2}")
                return
        else:
            st.warning(f"レーティング保存エラー: {e}")

def recompute_and_save_ratings():
    """スプレッドシート上の全対局データからレーティングを再計算して保存"""
    df_score = load_score_data()  # バッファ含めない (確定データのみ)
    ratings = compute_ratings_from_scratch(df_score)
    if not ratings:
        return
    rows = []
    for name, d in ratings.items():
        rows.append({
            "名前": name,
            "レート": round(d["レート"], 2),
            "対局数": d["対局数"],
            "段位Index": d["段位Index"],
            "段位pt": round(d["段位pt"], 2),
        })
    df = pd.DataFrame(rows)
    _save_rating_df(df)

@st.cache_data(ttl=120, show_spinner=False)
def load_ratings_effective(until_dt_iso=None, from_dt_iso=None):
    """
    レーティングデータをDataFrameで取得。実効スコア(バッファ含む)を用いた計算を返す。
    重い処理なので長めにキャッシュ (120秒)。

    Args:
        until_dt_iso: ISO形式の日時文字列。この時点までのレートを再現。
        from_dt_iso: ISO形式の日時文字列。この時点以降のデータのみで計算。
                     両方指定すれば区間指定になる。
    """
    df_score = load_score_data_effective()
    until_dt = None
    from_dt = None
    if until_dt_iso:
        try:
            until_dt = pd.Timestamp(until_dt_iso)
        except:
            until_dt = None
    if from_dt_iso:
        try:
            from_dt = pd.Timestamp(from_dt_iso)
        except:
            from_dt = None
    ratings = compute_ratings_from_scratch(df_score, until_dt=until_dt, from_dt=from_dt)
    return ratings_dict_to_df(ratings)

def get_player_rating(name):
    """指定プレイヤーの現在レートと段位情報を返す"""
    df = load_ratings_effective()
    if df.empty:
        return None
    row = df[df["名前"] == name]
    if row.empty:
        return None
    r = row.iloc[0]
    return {
        "レート": float(r["レート"]),
        "対局数": int(r["対局数"]),
        "段位Index": int(r["段位Index"]),
        "段位pt": float(r["段位pt"]),
        "段位名": r["段位名"],
        "段位色": r["段位色"],
        "昇段まで": int(r["昇段まで"]),
    }

def get_player_rating_history(target_name, last_n=10):
    """
    指定プレイヤーの直近N戦のレーティング変動履歴を返す。
    Returns: list of dict {
        "GameNo", "日時", "TableNo", "SetNo",
        "自着順", "対戦相手": [{"名前", "着順", "レート"}, ...],
        "開始レート", "終了レート", "変動pt",
        "段位名(開始)", "段位名(終了)", "段位色(終了)",
    }
    または None (該当データなし)
    """
    df_score = load_score_data_effective()
    if df_score is None or df_score.empty:
        return None

    # 時系列で並べる
    df = df_score.copy()
    if "日時Obj" in df.columns:
        df = df[df["日時Obj"].notna()]
        sort_keys = ["日時Obj", "TableNo", "SetNo"]
        if "GameNo" in df.columns:
            sort_keys.append("GameNo")
        df = df.sort_values(sort_keys).reset_index(drop=True)
    elif "GameNo" in df.columns:
        df = df.sort_values(["GameNo"]).reset_index(drop=True)

    if df.empty:
        return None

    # 全対局を1試合ずつ処理し、レーティングを再計算しつつ
    # 対象プレイヤーが参加した対局だけを履歴として記録
    ratings = {}  # name -> {"レート", "対局数", "段位Index", "段位pt"}

    def ensure_player(nm):
        if nm and nm not in ratings:
            ratings[nm] = {
                "レート": float(RATING_INIT),
                "対局数": 0,
                "段位Index": 0,
                "段位pt": 0.0,
            }

    target_history = []  # 対象プレイヤーの参加履歴 (時系列全部)

    for _, row in df.iterrows():
        # 3人の名前と着順を取り出す
        players = []
        valid = True
        for seat in ["A", "B", "C"]:
            n = row.get(f"{seat}さん", "")
            n = str(n).strip() if n else ""
            try:
                r = int(float(row.get(f"{seat}着順", 0)))
            except:
                r = 0
            if not n or r not in [1, 2, 3]:
                valid = False
                break
            players.append((n, r, seat))

        if not valid:
            continue
        if sorted([p[1] for p in players]) != [1, 2, 3]:
            continue
        if len({p[0] for p in players}) != 3:
            continue

        for name, _, _ in players:
            ensure_player(name)

        # 試合開始時のスナップショット
        snapshot = {name: ratings[name]["レート"] for name, _, _ in players}
        snapshot_games = {name: ratings[name]["対局数"] for name, _, _ in players}
        snapshot_dan = {name: (ratings[name]["段位Index"], ratings[name]["段位pt"]) for name, _, _ in players}

        # 対象プレイヤーがこの試合に参加しているか
        target_in_game = any(p[0] == target_name for p in players)

        # レーティング更新
        for name, rank, seat in players:
            others = [snapshot[n] for n, _, _ in players if n != name]
            opp_avg = sum(others) / len(others)

            cur = snapshot[name]
            games = snapshot_games[name]
            base = _get_rank_points(rank)
            correction = (opp_avg - cur) / 40.0
            delta = (base + correction) * _rating_adjust_factor(games)
            ratings[name]["レート"] = cur + delta
            ratings[name]["対局数"] = games + 1

            # 段位更新
            dan_pts = _get_dan_rank_points(rank)
            new_cum_pts = ratings[name]["段位pt"] + dan_pts
            new_dan_idx = _get_dan_index_from_pts(new_cum_pts)
            ratings[name]["段位Index"] = new_dan_idx
            ratings[name]["段位pt"] = new_cum_pts

        # 対象プレイヤーが参加した試合は履歴に追加
        if target_in_game:
            # 対象プレイヤーの情報
            target_info = next(p for p in players if p[0] == target_name)
            target_rank = target_info[1]
            target_seat = target_info[2]
            start_rate = snapshot[target_name]
            end_rate = ratings[target_name]["レート"]
            start_dan_idx, start_dan_pts = snapshot_dan[target_name]
            end_dan_idx = ratings[target_name]["段位Index"]

            # 対戦相手の情報 (2人)
            opponents = []
            for n, rk, _ in players:
                if n != target_name:
                    opponents.append({
                        "名前": n,
                        "着順": rk,
                        "レート": snapshot[n],  # 試合開始時のレート
                    })
            opponents.sort(key=lambda x: x["着順"])  # 着順順

            target_history.append({
                "GameNo": row.get("GameNo", 0),
                "日時": row.get("日時", ""),
                "日時Obj": row.get("日時Obj", None),
                "TableNo": row.get("TableNo", 0),
                "SetNo": row.get("SetNo", 0),
                "自席": target_seat,
                "自着順": target_rank,
                "対戦相手": opponents,
                "開始レート": start_rate,
                "終了レート": end_rate,
                "変動pt": end_rate - start_rate,
                "開始段位Index": start_dan_idx,
                "開始段位名": DAN_TABLE[start_dan_idx][0],
                "終了段位Index": end_dan_idx,
                "終了段位名": DAN_TABLE[end_dan_idx][0],
                "終了段位色": DAN_TABLE[end_dan_idx][2],
                "段位変化": end_dan_idx - start_dan_idx,  # 正なら昇段、負なら降段
            })

    if not target_history:
        return None

    # 直近N戦を返す (最新順)
    return target_history[-last_n:][::-1]


def get_player_top5_rankings(target_name, top_n=5, min_games=30):
    """
    指定プレイヤーがTOP N (デフォルト5位以内) にランクインしている全ランキング項目を返す。
    Returns: list of dict {
        "ランキング項目名",
        "順位",
        "値" (整形済み文字列),
        "総エントリ数",
        "カテゴリ": "guest" or "staff",
    }
    """
    df = load_score_data_effective()
    if df is None or df.empty:
        return None

    # 全プレイヤーの records を作成 (page_ranking と同じロジック)
    records = []
    for _, row in df.iterrows():
        for seat in ["A", "B", "C"]:
            name = row.get(f"{seat}さん", "")
            rank = row.get(f"{seat}着順", 0)
            player_type = row.get(f"{seat}タイプ", "")
            if name:
                try:
                    r = int(float(rank))
                except:
                    r = 0
                if r > 0:
                    records.append({
                        "name": name, "rank": r,
                        "date": row.get("論理日付", pd.Timestamp("1900-01-01")),
                        "dt": row.get("日時Obj", pd.Timestamp("1900-01-01")),
                        "game_no": row.get("GameNo", 0),
                        "player_type": str(player_type) if player_type else "",
                        "seat": seat,
                    })
    if not records:
        return None
    df_raw = pd.DataFrame(records)

    # --- 全プレイヤーのストリーク統計を計算 ---
    def _compute_streaks(group):
        g = group.sort_values(["dt", "game_no"])
        ranks = g["rank"].tolist()
        max_win = max_last = max_second = 0
        max_last_avoid = max_no_top = 0
        four_win = five_win = 0
        second_total = ranks.count(2)
        top_after_top_d = top_after_top_n = 0
        sec_after_sec_d = sec_after_sec_n = 0
        last_after_last_d = last_after_last_n = 0
        for i in range(len(ranks) - 1):
            cur_r = ranks[i]
            next_r = ranks[i + 1]
            if cur_r == 1:
                top_after_top_d += 1
                if next_r == 1: top_after_top_n += 1
            elif cur_r == 2:
                sec_after_sec_d += 1
                if next_r == 2: sec_after_sec_n += 1
            elif cur_r == 3:
                last_after_last_d += 1
                if next_r == 3: last_after_last_n += 1

        cur_win = cur_last = cur_second = 0
        cur_last_avoid = cur_no_top = 0
        for r in ranks:
            if r == 1:
                cur_win += 1
                cur_last = cur_second = 0
                if cur_win == 4: four_win += 1
                if cur_win == 5: five_win += 1
            elif r == 2:
                cur_second += 1
                cur_win = cur_last = 0
            elif r == 3:
                cur_last += 1
                cur_win = cur_second = 0
            else:
                cur_win = cur_last = cur_second = 0
            max_win = max(max_win, cur_win)
            max_last = max(max_last, cur_last)
            max_second = max(max_second, cur_second)
            if r in (1, 2):
                cur_last_avoid += 1
                max_last_avoid = max(max_last_avoid, cur_last_avoid)
            else:
                cur_last_avoid = 0
            if r in (2, 3):
                cur_no_top += 1
                max_no_top = max(max_no_top, cur_no_top)
            else:
                cur_no_top = 0
        return pd.Series({
            "max_win_streak": max_win, "max_last_streak": max_last,
            "max_second_streak": max_second, "max_last_avoid_streak": max_last_avoid,
            "max_no_top_streak": max_no_top,
            "four_win_count": four_win, "five_win_count": five_win,
            "second_count": second_total,
            "top_after_top_rate": (top_after_top_n / top_after_top_d * 100) if top_after_top_d > 0 else None,
            "top_after_top_samples": top_after_top_d,
            "second_after_second_rate": (sec_after_sec_n / sec_after_sec_d * 100) if sec_after_sec_d > 0 else None,
            "second_after_second_samples": sec_after_sec_d,
            "last_after_last_rate": (last_after_last_n / last_after_last_d * 100) if last_after_last_d > 0 else None,
            "last_after_last_samples": last_after_last_d,
        })

    streaks = df_raw.groupby("name", group_keys=False).apply(_compute_streaks).reset_index()

    # --- ベスト100半荘計算 ---
    WINDOW_SIZE_ = 100
    def _compute_best_window(group):
        g = group.sort_values(["dt", "game_no"]).reset_index(drop=True)
        n = len(g)
        if n < WINDOW_SIZE_:
            return pd.Series({"best100_avg": None, "best100_first": 0, "best100_top_rate": None})
        ranks = g["rank"].tolist()
        window_sum = sum(ranks[:WINDOW_SIZE_])
        best_avg = window_sum / WINDOW_SIZE_
        best_start = 0
        for i in range(1, n - WINDOW_SIZE_ + 1):
            window_sum += ranks[i + WINDOW_SIZE_ - 1] - ranks[i - 1]
            avg = window_sum / WINDOW_SIZE_
            if avg < best_avg:
                best_avg = avg
                best_start = i
        best_end = best_start + WINDOW_SIZE_ - 1
        window_ranks = ranks[best_start:best_end + 1]
        return pd.Series({
            "best100_avg": best_avg,
            "best100_first": window_ranks.count(1),
            "best100_top_rate": window_ranks.count(1) / WINDOW_SIZE_ * 100,
        })

    best_windows = df_raw.groupby("name", group_keys=False).apply(_compute_best_window).reset_index()

    # --- 基本stats ---
    stats = df_raw.groupby("name").agg(
        games=("rank", "count"),
        avg_rank=("rank", "mean"),
        first_count=("rank", lambda x: (x == 1).sum()),
        third_count=("rank", lambda x: (x == 3).sum()),
    ).reset_index()
    stats = stats.merge(streaks, on="name", how="left")
    stats = stats.merge(best_windows, on="name", how="left")
    stats["top_rate"] = (stats["first_count"] / stats["games"]) * 100
    stats["second_rate"] = (stats["second_count"] / stats["games"]) * 100
    stats["last_avoid_rate"] = ((stats["games"] - stats["third_count"]) / stats["games"]) * 100

    # タイプ別・席別集計
    for tt in ["A客", "AS", "B客", "BS"]:
        df_type = df_raw[df_raw["player_type"] == tt]
        if not df_type.empty:
            ts = df_type.groupby("name").agg(
                **{f"avg_rank_{tt}": ("rank", "mean"), f"games_{tt}": ("rank", "count")}
            ).reset_index()
            stats = stats.merge(ts, on="name", how="left")
    for sk in ["A", "B", "C"]:
        df_seat = df_raw[df_raw["seat"] == sk]
        if not df_seat.empty:
            ss = df_seat.groupby("name").agg(
                **{f"avg_rank_seat_{sk}": ("rank", "mean"), f"games_seat_{sk}": ("rank", "count")}
            ).reset_index()
            stats = stats.merge(ss, on="name", how="left")

    # プレイヤータイプ判定 (末尾s → staff)
    stats["cat"] = stats["name"].apply(lambda x: "staff" if str(x).lower().endswith("s") else "guest")

    # --- レーティング取得 ---
    df_rating = load_ratings_effective()
    if df_rating is not None and not df_rating.empty:
        df_r_slim = df_rating[["名前", "レート", "対局数", "段位Index", "段位pt"]].rename(columns={"名前": "name"})
        stats = stats.merge(df_r_slim, on="name", how="left")

    # --- 対象プレイヤーがどのランキングに入っているかを判定 ---
    # 対象プレイヤーの正規化名 (末尾のsを保持したまま)
    target_row = stats[stats["name"] == target_name]
    if target_row.empty:
        return None
    target_cat = target_row.iloc[0]["cat"]

    # このカテゴリのみでランキング判定
    stats_cat = stats[stats["cat"] == target_cat].copy()

    # ランキング項目定義: (列名, 表示名, ascending, フォーマット関数, 追加フィルタ関数)
    ranking_defs = [
        ("games", "📊 打数", False, lambda v: f"{int(v)} 戦", lambda df: df[df["games"].fillna(0) >= 1]),
        ("avg_rank", "🥇 平均着順", True, lambda v: f"{v:.3f}", lambda df: df[df["games"].fillna(0) >= min_games]),
        ("top_rate", "👑 トップ率", False, lambda v: f"{v:.2f}%", lambda df: df[df["games"].fillna(0) >= min_games]),
        ("second_rate", "🥈 2着率", False, lambda v: f"{v:.2f}%", lambda df: df[df["games"].fillna(0) >= min_games]),
        ("last_avoid_rate", "🛡 ラス回避率", False, lambda v: f"{v:.2f}%", lambda df: df[df["games"].fillna(0) >= min_games]),
        ("max_win_streak", "🔥 最長連勝", False, lambda v: f"{int(v)} 連勝", None),
        ("max_last_streak", "💀 最長連続ラス", False, lambda v: f"{int(v)} 連続", None),
        ("max_second_streak", "😐 最長連続2着", False, lambda v: f"{int(v)} 連続", None),
        ("max_last_avoid_streak", "🛡️ 最長連続ラス回避", False, lambda v: f"{int(v)} 連続", None),
        ("max_no_top_streak", "😑 最長連続トップ無し", False, lambda v: f"{int(v)} 連続", None),
        ("four_win_count", "✨ 4連勝以上回数", False, lambda v: f"{int(v)} 回", None),
        ("five_win_count", "⭐ 5連勝以上回数", False, lambda v: f"{int(v)} 回", None),
        ("best100_avg", "🌟 ベスト100半荘 平均着順", True, lambda v: f"{v:.3f}",
         lambda df: df[df["best100_avg"].notna()]),
        ("top_after_top_rate", "🔁 連勝確率", False, lambda v: f"{v:.2f}%",
         lambda df: df[(df["top_after_top_rate"].notna()) & (df["top_after_top_samples"].fillna(0) >= 10)]),
        ("second_after_second_rate", "🔄 連続2着率", False, lambda v: f"{v:.2f}%",
         lambda df: df[(df["second_after_second_rate"].notna()) & (df["second_after_second_samples"].fillna(0) >= 10)]),
        ("last_after_last_rate", "☠️ 連続ラス率", False, lambda v: f"{v:.2f}%",
         lambda df: df[(df["last_after_last_rate"].notna()) & (df["last_after_last_samples"].fillna(0) >= 10)]),
        # タイプ別平均着順
        ("avg_rank_A客", "🎯 平均着順 (A客)", True, lambda v: f"{v:.3f}",
         lambda df: df[df.get("games_A客", pd.Series([0]*len(df))).fillna(0) >= 10]) if "avg_rank_A客" in stats_cat.columns else None,
        ("avg_rank_AS", "🎯 平均着順 (AS)", True, lambda v: f"{v:.3f}",
         lambda df: df[df.get("games_AS", pd.Series([0]*len(df))).fillna(0) >= 10]) if "avg_rank_AS" in stats_cat.columns else None,
        ("avg_rank_B客", "🎯 平均着順 (B客)", True, lambda v: f"{v:.3f}",
         lambda df: df[df.get("games_B客", pd.Series([0]*len(df))).fillna(0) >= 10]) if "avg_rank_B客" in stats_cat.columns else None,
        ("avg_rank_BS", "🎯 平均着順 (BS)", True, lambda v: f"{v:.3f}",
         lambda df: df[df.get("games_BS", pd.Series([0]*len(df))).fillna(0) >= 10]) if "avg_rank_BS" in stats_cat.columns else None,
        # 席別平均着順
        ("avg_rank_seat_A", "💺 平均着順 (A席)", True, lambda v: f"{v:.3f}",
         lambda df: df[df.get("games_seat_A", pd.Series([0]*len(df))).fillna(0) >= 10]) if "avg_rank_seat_A" in stats_cat.columns else None,
        ("avg_rank_seat_B", "💺 平均着順 (B席)", True, lambda v: f"{v:.3f}",
         lambda df: df[df.get("games_seat_B", pd.Series([0]*len(df))).fillna(0) >= 10]) if "avg_rank_seat_B" in stats_cat.columns else None,
        ("avg_rank_seat_C", "💺 平均着順 (C席)", True, lambda v: f"{v:.3f}",
         lambda df: df[df.get("games_seat_C", pd.Series([0]*len(df))).fillna(0) >= 10]) if "avg_rank_seat_C" in stats_cat.columns else None,
        # レーティング・段位
        ("レート", "🏅 レーティング", False, lambda v: f"R{v:.1f}",
         lambda df: df[df.get("レート", pd.Series([None]*len(df))).notna()]) if "レート" in stats_cat.columns else None,
        ("段位pt", "🎖️ 段位(累積pt)", False, lambda v: f"{v:.0f} pt",
         lambda df: df[df.get("段位pt", pd.Series([None]*len(df))).notna()]) if "段位pt" in stats_cat.columns else None,
    ]

    results = []
    for defn in ranking_defs:
        if defn is None:
            continue
        col, label, ascending, formatter, filter_fn = defn
        if col not in stats_cat.columns:
            continue
        df_r = stats_cat.copy()
        if filter_fn is not None:
            try:
                df_r = filter_fn(df_r)
            except Exception:
                continue
        df_r = df_r[df_r[col].notna()]
        if df_r.empty:
            continue
        # ランキング作成
        df_r = df_r.sort_values(col, ascending=ascending).reset_index(drop=True)
        target_idx = df_r[df_r["name"] == target_name].index
        if len(target_idx) == 0:
            continue
        rank_pos = int(target_idx[0]) + 1  # 1-indexed
        if rank_pos <= top_n:
            val = df_r.iloc[target_idx[0]][col]
            results.append({
                "項目": label,
                "順位": rank_pos,
                "値": formatter(val),
                "総エントリ数": len(df_r),
                "カテゴリ": target_cat,
            })

    return results


# ランキングPT配分 (順位 → pt)
RANKING_PT_TABLE = {
    1: 10, 2: 7, 3: 5, 4: 3, 5: 2,
    6: 1, 7: 1, 8: 1, 9: 1, 10: 1,
}


def _rank_to_pt(rank_pos):
    """順位からランキングPTを算出"""
    return RANKING_PT_TABLE.get(rank_pos, 0)


def assign_competition_rank(df, sort_col, ascending=False):
    """
    標準競争順位方式 (1224方式) で順位を付ける。
    同率スコアは同順位、次は人数分飛ばす。
    例: スコア [100, 90, 90, 80] → 順位 [1, 2, 2, 4]

    Args:
        df: 対象のDataFrame
        sort_col: ソート/順位判定に使う列
        ascending: True=小さいほど良い(平均着順など), False=大きいほど良い

    Returns:
        ソート済み + "順位" 列を追加した DataFrame (コピー)
    """
    if df.empty:
        result = df.copy()
        result["順位"] = []
        return result
    result = df.sort_values(sort_col, ascending=ascending).reset_index(drop=True)
    # 同率順位を計算 (min method = 標準競争順位)
    # rank() は昇順基準なので、ascendingに合わせて方向を指定
    result["順位"] = result[sort_col].rank(
        method="min",
        ascending=ascending
    ).astype(int)
    return result


def render_rankpt_breakdown(breakdown):
    """
    ランキングPTの内訳 (各項目で何位・スコア・pt) をHTMLで描画する。
    breakdown: [{"項目", "順位", "pt", "値"}, ...]
    """
    if not breakdown:
        st.markdown('<div style="color:var(--text-muted);font-size:0.85rem;padding:0.5rem;">ランクイン項目なし</div>',
                    unsafe_allow_html=True)
        return

    # 順位が良い順にソート済 (compute側で対応済みだが念のため)
    items = sorted(breakdown, key=lambda x: (x["順位"], x["項目"]))

    rank_medals = {1: "🥇", 2: "🥈", 3: "🥉"}
    total_pt = sum(b["pt"] for b in items)

    html = '<div class="rankpt-breakdown">'
    for b in items:
        pos = b["順位"]
        medal = rank_medals.get(pos, "")
        val_str = b.get("値", "")
        # 順位に応じた色クラス
        if pos == 1:
            tier = "tier-gold"
        elif pos == 2:
            tier = "tier-silver"
        elif pos == 3:
            tier = "tier-bronze"
        else:
            tier = "tier-plain"

        pos_disp = f"{medal} {pos}位" if medal else f"{pos}位"
        html += f'''<div class="rankpt-bd-row {tier}">
            <span class="rankpt-bd-rankbadge">{pos_disp}</span>
            <span class="rankpt-bd-item">{b["項目"]}</span>
            <span class="rankpt-bd-score">{val_str}</span>
            <span class="rankpt-bd-pt">+{b["pt"]}</span>
        </div>'''
    html += f'''<div class="rankpt-bd-total">
        <span class="rankpt-bd-total-label">{len(items)} 項目でランクイン</span>
        <span class="rankpt-bd-total-pt">{total_pt}<span class="rankpt-bd-total-unit">pt</span></span>
    </div>'''
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)


def compute_ranking_points_all(min_games=30, from_dt=None, until_dt=None):
    """
    全プレイヤーの「ランキングPT総合」を計算する。
    各ランキング項目について順位を判定し、1位10pt / 2位7pt / 3位5pt /
    4位3pt / 5位2pt / 6〜10位1pt を付与して合計。

    Args:
        min_games: 平均着順系ランキングの規定打数 (デフォルト30戦)
        from_dt: 期間開始日時 (Timestamp) or None
        until_dt: 期間終了日時 (Timestamp) or None
        両方指定すれば区間フィルタになる

    Returns: dict {
        "guest": [{"name", "total_pt", "breakdown": [{"項目", "順位", "pt"}, ...]}, ...],
        "staff": [同上]
    }
    """
    df = load_score_data_effective()
    if df is None or df.empty:
        return {"guest": [], "staff": []}

    # 期間フィルタ
    if from_dt is not None or until_dt is not None:
        df = df.copy()
        if "日時Obj" in df.columns:
            if from_dt is not None:
                df = df[df["日時Obj"] >= pd.Timestamp(from_dt)]
            if until_dt is not None:
                df = df[df["日時Obj"] <= pd.Timestamp(until_dt)]
        if df.empty:
            return {"guest": [], "staff": []}

    # records生成 (get_player_top5_rankings と同じロジック)
    records = []
    for _, row in df.iterrows():
        for seat in ["A", "B", "C"]:
            name = row.get(f"{seat}さん", "")
            rank = row.get(f"{seat}着順", 0)
            player_type = row.get(f"{seat}タイプ", "")
            if name:
                try:
                    r = int(float(rank))
                except:
                    r = 0
                if r > 0:
                    records.append({
                        "name": name, "rank": r,
                        "date": row.get("論理日付", pd.Timestamp("1900-01-01")),
                        "dt": row.get("日時Obj", pd.Timestamp("1900-01-01")),
                        "game_no": row.get("GameNo", 0),
                        "player_type": str(player_type) if player_type else "",
                        "seat": seat,
                    })
    if not records:
        return {"guest": [], "staff": []}
    df_raw = pd.DataFrame(records)

    # --- ストリーク統計 ---
    def _compute_streaks(group):
        g = group.sort_values(["dt", "game_no"])
        ranks = g["rank"].tolist()
        max_win = max_last = max_second = 0
        max_last_avoid = max_no_top = 0
        four_win = five_win = 0
        second_total = ranks.count(2)
        top_after_top_d = top_after_top_n = 0
        sec_after_sec_d = sec_after_sec_n = 0
        last_after_last_d = last_after_last_n = 0
        for i in range(len(ranks) - 1):
            cur_r = ranks[i]
            next_r = ranks[i + 1]
            if cur_r == 1:
                top_after_top_d += 1
                if next_r == 1: top_after_top_n += 1
            elif cur_r == 2:
                sec_after_sec_d += 1
                if next_r == 2: sec_after_sec_n += 1
            elif cur_r == 3:
                last_after_last_d += 1
                if next_r == 3: last_after_last_n += 1
        cur_win = cur_last = cur_second = 0
        cur_last_avoid = cur_no_top = 0
        for r in ranks:
            if r == 1:
                cur_win += 1
                cur_last = cur_second = 0
                if cur_win == 4: four_win += 1
                if cur_win == 5: five_win += 1
            elif r == 2:
                cur_second += 1
                cur_win = cur_last = 0
            elif r == 3:
                cur_last += 1
                cur_win = cur_second = 0
            else:
                cur_win = cur_last = cur_second = 0
            max_win = max(max_win, cur_win)
            max_last = max(max_last, cur_last)
            max_second = max(max_second, cur_second)
            if r in (1, 2):
                cur_last_avoid += 1
                max_last_avoid = max(max_last_avoid, cur_last_avoid)
            else:
                cur_last_avoid = 0
            if r in (2, 3):
                cur_no_top += 1
                max_no_top = max(max_no_top, cur_no_top)
            else:
                cur_no_top = 0
        return pd.Series({
            "max_win_streak": max_win, "max_last_streak": max_last,
            "max_second_streak": max_second, "max_last_avoid_streak": max_last_avoid,
            "max_no_top_streak": max_no_top,
            "four_win_count": four_win, "five_win_count": five_win,
            "second_count": second_total,
            "top_after_top_rate": (top_after_top_n / top_after_top_d * 100) if top_after_top_d > 0 else None,
            "top_after_top_samples": top_after_top_d,
            "second_after_second_rate": (sec_after_sec_n / sec_after_sec_d * 100) if sec_after_sec_d > 0 else None,
            "second_after_second_samples": sec_after_sec_d,
            "last_after_last_rate": (last_after_last_n / last_after_last_d * 100) if last_after_last_d > 0 else None,
            "last_after_last_samples": last_after_last_d,
        })
    streaks = df_raw.groupby("name", group_keys=False).apply(_compute_streaks).reset_index()

    # --- ベスト100半荘 ---
    W_ = 100
    def _compute_best_window(group):
        g = group.sort_values(["dt", "game_no"]).reset_index(drop=True)
        n = len(g)
        if n < W_:
            return pd.Series({"best100_avg": None})
        ranks = g["rank"].tolist()
        window_sum = sum(ranks[:W_])
        best_avg = window_sum / W_
        for i in range(1, n - W_ + 1):
            window_sum += ranks[i + W_ - 1] - ranks[i - 1]
            avg = window_sum / W_
            if avg < best_avg:
                best_avg = avg
        return pd.Series({"best100_avg": best_avg})
    best_windows = df_raw.groupby("name", group_keys=False).apply(_compute_best_window).reset_index()

    # --- 基本 stats ---
    stats = df_raw.groupby("name").agg(
        games=("rank", "count"),
        avg_rank=("rank", "mean"),
        first_count=("rank", lambda x: (x == 1).sum()),
        third_count=("rank", lambda x: (x == 3).sum()),
    ).reset_index()
    stats = stats.merge(streaks, on="name", how="left")
    stats = stats.merge(best_windows, on="name", how="left")
    stats["top_rate"] = (stats["first_count"] / stats["games"]) * 100
    stats["second_rate"] = (stats["second_count"] / stats["games"]) * 100
    stats["last_avoid_rate"] = ((stats["games"] - stats["third_count"]) / stats["games"]) * 100

    for tt in ["A客", "AS", "B客", "BS"]:
        df_type = df_raw[df_raw["player_type"] == tt]
        if not df_type.empty:
            ts = df_type.groupby("name").agg(
                **{f"avg_rank_{tt}": ("rank", "mean"), f"games_{tt}": ("rank", "count")}
            ).reset_index()
            stats = stats.merge(ts, on="name", how="left")
    for sk in ["A", "B", "C"]:
        df_seat = df_raw[df_raw["seat"] == sk]
        if not df_seat.empty:
            ss = df_seat.groupby("name").agg(
                **{f"avg_rank_seat_{sk}": ("rank", "mean"), f"games_seat_{sk}": ("rank", "count")}
            ).reset_index()
            stats = stats.merge(ss, on="name", how="left")

    stats["cat"] = stats["name"].apply(lambda x: "staff" if str(x).lower().endswith("s") else "guest")

    # レーティング
    df_rating = load_ratings_effective()
    if df_rating is not None and not df_rating.empty:
        df_r_slim = df_rating[["名前", "レート", "対局数", "段位Index", "段位pt"]].rename(columns={"名前": "name"})
        stats = stats.merge(df_r_slim, on="name", how="left")

    # ランキング項目定義 (8項目)
    # 【対象】※レーティング・段位は除外(それぞれ専用タブがあるため)
    #  1. 📊 打数
    #  2. 🥇 平均着順 (総合)
    #  3. 👑 トップ率
    #  4. 🛡 ラス回避率
    #  5. 🔥 最長連勝
    #  6. 🛡️ 最長連続ラス回避
    #  7. ⭐ 5連勝以上回数
    #  8. 🌟 ベスト100半荘
    def build_ranking_defs(stats_cat):
        # (col, label, ascending, filter_fn, value_formatter)
        return [d for d in [
            # 基本統計
            ("games", "📊 打数", False,
             lambda df: df[df["games"].fillna(0) >= 1],
             lambda v: f"{int(v)}戦"),
            ("avg_rank", "🥇 平均着順", True,
             lambda df: df[df["games"].fillna(0) >= min_games],
             lambda v: f"{v:.3f}"),
            ("top_rate", "👑 トップ率", False,
             lambda df: df[df["games"].fillna(0) >= min_games],
             lambda v: f"{v:.1f}%"),
            ("last_avoid_rate", "🛡 ラス回避率", False,
             lambda df: df[df["games"].fillna(0) >= min_games],
             lambda v: f"{v:.1f}%"),
            # 連続系
            ("max_win_streak", "🔥 最長連勝", False, None,
             lambda v: f"{int(v)}連勝"),
            ("max_last_avoid_streak", "🛡️ 最長連続ラス回避", False, None,
             lambda v: f"{int(v)}連続"),
            ("five_win_count", "⭐ 5連勝以上回数", False, None,
             lambda v: f"{int(v)}回"),
            # ベスト100半荘
            ("best100_avg", "🌟 ベスト100半荘", True,
             lambda df: df[df["best100_avg"].notna()],
             lambda v: f"{v:.3f}"),
        ] if d is not None]

    result = {"guest": [], "staff": []}
    for cat_key in ["guest", "staff"]:
        stats_cat = stats[stats["cat"] == cat_key].copy()
        if stats_cat.empty:
            continue

        # 各プレイヤーの合計ptとbreakdown
        pt_totals = {}  # name -> total pt
        breakdowns = {}  # name -> [{"項目", "順位", "pt", "値"}, ...]

        ranking_defs = build_ranking_defs(stats_cat)
        for col, label, ascending, filter_fn, value_formatter in ranking_defs:
            if col not in stats_cat.columns:
                continue
            df_r = stats_cat.copy()
            if filter_fn is not None:
                try:
                    df_r = filter_fn(df_r)
                except Exception:
                    continue
            df_r = df_r[df_r[col].notna()]
            if df_r.empty:
                continue
            # 同率順位で順位付け (標準競争順位: 1,2,2,4方式)
            df_r = df_r.sort_values(col, ascending=ascending).reset_index(drop=True)
            df_r["_順位"] = df_r[col].rank(method="min", ascending=ascending).astype(int)
            # 順位が10以下のプレイヤーにpt付与 (同率は同じ順位・同じpt)
            for _, row_r in df_r.iterrows():
                rank_pos = int(row_r["_順位"])
                if rank_pos > 10:
                    continue
                pt = _rank_to_pt(rank_pos)
                if pt <= 0:
                    continue
                name = row_r["name"]
                # 実際のスコア値をフォーマット
                raw_val = row_r[col]
                try:
                    val_str = value_formatter(raw_val)
                except Exception:
                    val_str = str(raw_val)
                pt_totals[name] = pt_totals.get(name, 0) + pt
                if name not in breakdowns:
                    breakdowns[name] = []
                breakdowns[name].append({
                    "項目": label, "順位": rank_pos, "pt": pt, "値": val_str,
                })

        # 合計ptでソート
        cat_result = []
        for name, total_pt in pt_totals.items():
            cat_result.append({
                "name": name,
                "total_pt": total_pt,
                "breakdown": sorted(breakdowns.get(name, []),
                                    key=lambda x: (x["順位"], x["項目"])),
            })
        cat_result.sort(key=lambda x: -x["total_pt"])
        result[cat_key] = cat_result

    return result


def compute_monthly_ranking_points(min_games=10, top_n=3):
    """
    全月について、その月のランキングPT総合を計算し、各月のTOP N を返す。

    Args:
        min_games: 各月内での規定打数 (デフォルト10戦)
        top_n: 各月のTOP何位まで返すか (デフォルト3)

    Returns: dict {
        "months": ["2026-01", "2026-02", ...],  # 新しい順
        "data": {
            "2026-01": {
                "guest": [{"name", "total_pt", "breakdown": [...]}, ...],
                "staff": [同上],
            },
            ...
        }
    }
    """
    df = load_score_data_effective()
    if df is None or df.empty or "日時Obj" not in df.columns:
        return {"months": [], "data": {}}

    # 対局が存在する月を全て抽出
    df_valid = df[df["日時Obj"].notna()].copy()
    if df_valid.empty:
        return {"months": [], "data": {}}
    df_valid["年月"] = df_valid["日時Obj"].dt.to_period("M")
    all_months = sorted(df_valid["年月"].unique(), reverse=True)  # 新しい順

    result = {"months": [], "data": {}}
    for ym in all_months:
        # その月の開始・終了日時
        from_dt = pd.Timestamp(ym.start_time)
        until_dt = pd.Timestamp(ym.end_time)
        ym_str = str(ym)  # "2026-01" 形式

        # その月のランキングPT総合を計算
        month_result = compute_ranking_points_all(
            min_games=min_games,
            from_dt=from_dt,
            until_dt=until_dt,
        )

        # TOP Nだけ抽出
        top_data = {
            "guest": month_result["guest"][:top_n],
            "staff": month_result["staff"][:top_n],
        }
        # 空の月はスキップ (両カテゴリともエントリなし)
        if not top_data["guest"] and not top_data["staff"]:
            continue

        result["months"].append(ym_str)
        result["data"][ym_str] = top_data

    return result

def commit_buffer_to_sheet():
    """
    バッファに溜まった全変更をスプレッドシートに一括反映する。
    成功時: バッファクリアして True
    失敗時: バッファ保持して False
    """
    changes = load_pending_changes()
    if not changes:
        return True

    # 最新データを取得
    try:
        df_latest = load_score_data_fresh()
    except Exception as e:
        st.error(f"最新データの取得に失敗しました: {e}")
        return False

    # 削除適用
    delete_ids = [e["target_game_no"] for e in changes if e["type"] == "delete"]
    if delete_ids and not df_latest.empty:
        df_latest = df_latest[~df_latest["GameNo"].isin(delete_ids)]

    # 更新適用
    for e in changes:
        if e["type"] == "update":
            target = e["target_game_no"]
            if not df_latest.empty and target in df_latest["GameNo"].values:
                idx_pos = df_latest[df_latest["GameNo"] == target].index[0]
                for col, val in e["data"].items():
                    if col in df_latest.columns:
                        df_latest.loc[idx_pos, col] = val

    # 新規追加適用 (GameNoを正の値で発番し直す)
    if not df_latest.empty and "GameNo" in df_latest.columns:
        max_no_series = pd.to_numeric(df_latest["GameNo"], errors='coerce').fillna(0)
        max_no = int(max_no_series[max_no_series > 0].max()) if (max_no_series > 0).any() else 0
    else:
        max_no = 0

    add_rows = []
    add_log_entries = []
    for e in changes:
        if e["type"] == "add":
            max_no += 1
            row = {c: e["data"].get(c, "") for c in EXPECTED_COLS}
            row["GameNo"] = max_no
            add_rows.append(row)
            add_log_entries.append({
                "real_game_no": max_no,
                "detail": e["data"].get("_log_detail", f"新規: {row.get('TableNo','?')}卓"),
            })
    if add_rows:
        df_add = pd.DataFrame(add_rows)
        if df_latest.empty:
            df_latest = df_add
        else:
            df_latest = pd.concat([df_latest[EXPECTED_COLS], df_add], ignore_index=True)

    # 保存
    try:
        save_score_data(df_latest)
    except Exception as e:
        st.error(f"保存に失敗しました: {e}")
        return False

    # ログを一括書き込み
    try:
        conn = get_conn()
        try:
            df_log = fetch_data_fresh(conn, SHEET_LOG)
        except:
            df_log = pd.DataFrame(columns=["日時", "操作", "GameNo", "詳細"])
        jst_now = datetime.now(timezone(timedelta(hours=9), 'JST')).strftime("%Y-%m-%d %H:%M:%S")
        new_log_rows = []
        for e in changes:
            if e["type"] == "update":
                new_log_rows.append({
                    "日時": jst_now,
                    "操作": "修正",
                    "GameNo": e["target_game_no"],
                    "詳細": e.get("detail", ""),
                })
            elif e["type"] == "delete":
                new_log_rows.append({
                    "日時": jst_now,
                    "操作": "削除",
                    "GameNo": e["target_game_no"],
                    "詳細": e.get("info", ""),
                })
        for entry in add_log_entries:
            new_log_rows.append({
                "日時": jst_now,
                "操作": "新規登録",
                "GameNo": entry["real_game_no"],
                "詳細": entry["detail"],
            })
        if new_log_rows:
            df_log = pd.concat([df_log, pd.DataFrame(new_log_rows)], ignore_index=True)
            conn.update(worksheet=SHEET_LOG, data=df_log)
            fetch_data_cached.clear()
    except Exception as e:
        st.warning(f"ログの保存に一部失敗しました: {e}")

    # バッファクリア
    buffer_clear()

    # レーティングを再計算して保存 (時間がかかる可能性あり)
    try:
        recompute_and_save_ratings()
        # レーティングキャッシュもクリア
        load_ratings_effective.clear()
    except Exception as e:
        st.warning(f"レーティング再計算に失敗しました: {e}")

    return True

# ==========================================
# 3. 集計関数 (元のまま)
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
# 4. UI ユーティリティ (改善版)
# ==========================================

# 改善: 永続的なトップナビゲーション
NAV_ITEMS = [
    ("🏠", "ホーム", "home"),
    ("👤", "個人", "personal"),
    ("📊", "データ", "history"),
    ("🏆", "順位", "ranking"),
    ("📅", "月間PT", "monthly"),
]

def render_top_nav(current_page):
    """全ページ共通の上部ナビゲーション (ホーム以外で表示)"""
    # versus2/versus3 はデータ系ページなので、トップナビ上では「データ」をアクティブ表示にする
    display_active = current_page
    if current_page in ("versus2", "versus3"):
        display_active = "history"

    cols = st.columns(len(NAV_ITEMS))
    for i, (icon, label, page) in enumerate(NAV_ITEMS):
        with cols[i]:
            is_current = (page == display_active)
            btn_label = f"{icon}\n{label}"
            if is_current:
                # 現在のページは押せないようにdisabled風にするか、強調
                st.markdown(
                    f"""<div style='background:var(--accent-soft);border:1px solid var(--accent);
                    border-radius:8px;padding:8px 4px;text-align:center;color:var(--accent);
                    font-weight:700;font-size:0.78rem;line-height:1.3;'>
                    <div style='font-size:1.15rem;'>{icon}</div>{label}</div>""",
                    unsafe_allow_html=True
                )
            else:
                if st.button(btn_label, key=f"nav_{page}", use_container_width=True):
                    st.session_state["page"] = page
                    st.rerun()

def section_title(icon, text):
    """セクションタイトル"""
    st.markdown(
        f'<div class="section-title"><span class="section-icon">{icon}</span>{text}</div>',
        unsafe_allow_html=True
    )

def render_dan_badge(dan_name, dan_color, size="normal"):
    """段位バッジHTML"""
    if size == "large":
        fs = "1.15rem"; padding = "5px 14px"; radius = "8px"
    elif size == "small":
        fs = "0.75rem"; padding = "2px 8px"; radius = "4px"
    else:
        fs = "0.9rem"; padding = "3px 10px"; radius = "6px"
    return f'''<span style="background:{dan_color}22;color:{dan_color};
              border:1px solid {dan_color};padding:{padding};border-radius:{radius};
              font-weight:800;font-size:{fs};letter-spacing:0.03em;
              display:inline-block;">{dan_name}</span>'''

def render_rating_card(name, rating_info):
    """レーティング情報カード (累積pt方式対応)"""
    if rating_info is None:
        return
    dan_name = rating_info["段位名"]
    dan_color = rating_info["段位色"]
    rate = rating_info["レート"]
    games = rating_info["対局数"]
    cumulative_pts = rating_info["段位pt"]  # 累積pt
    next_threshold = rating_info["昇段まで"]  # 次段位の閾値 (累積pt基準)
    dan_idx = rating_info.get("段位Index", 0)

    # 現段位の閾値
    current_threshold = DAN_TABLE[dan_idx][1] if dan_idx < len(DAN_TABLE) else -99999

    # 進捗計算: (累積pt - 現段位閾値) / (次段位閾値 - 現段位閾値) * 100
    if next_threshold > 0 and next_threshold > current_threshold:
        span = next_threshold - current_threshold
        progress_pts = cumulative_pts - current_threshold
        progress = max(0, min(100, progress_pts / span * 100))
        remaining = max(0, next_threshold - cumulative_pts)
        show_progress = True
    else:
        progress = 100
        remaining = 0
        show_progress = False

    st.markdown(f"""
    <div style="background:linear-gradient(135deg, var(--bg-card) 0%, {dan_color}15 100%);
                border:1px solid {dan_color};border-radius:var(--radius);
                padding:1rem 1.3rem;margin-bottom:1rem;">
        <div style="display:flex;align-items:center;gap:1rem;flex-wrap:wrap;margin-bottom:0.7rem;">
            <div>{render_dan_badge(dan_name, dan_color, size="large")}</div>
            <div style="flex:1;">
                <div style="font-size:0.7rem;color:var(--text-muted);letter-spacing:0.08em;
                            text-transform:uppercase;font-weight:600;">RATING</div>
                <div style="font-family:'Zen Kaku Gothic New';font-size:1.8rem;font-weight:900;
                            color:{dan_color};line-height:1;">R{rate:.1f}</div>
            </div>
            <div style="text-align:right;color:var(--text-muted);font-size:0.85rem;">
                対局数<br>
                <span style="font-size:1.1rem;color:var(--text-primary);font-weight:700;">{games}</span> 戦
            </div>
        </div>
        <div style="background:rgba(255,255,255,0.04);border-radius:6px;height:8px;overflow:hidden;">
            <div style="width:{progress}%;height:100%;background:linear-gradient(90deg, {dan_color} 0%, {dan_color}aa 100%);"></div>
        </div>
        <div style="display:flex;justify-content:space-between;margin-top:5px;font-size:0.75rem;color:var(--text-muted);">
            <span>累積pt: {cumulative_pts:.0f}{f' / {next_threshold}' if show_progress else ''}</span>
            <span>{'昇段まで ' + str(int(remaining)) + ' pt' if show_progress else '最上位段位'}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_recent_rating_history(player_name, last_n=10):
    """指定プレイヤーの直近N戦のレーティング変動履歴を表示"""
    history = get_player_rating_history(player_name, last_n=last_n)
    if not history:
        st.info(f"「{player_name}」の対局履歴がありません")
        return

    n = len(history)

    # --- サマリ ---
    total_delta = sum(h["変動pt"] for h in history)
    avg_delta = total_delta / n
    plus_count = sum(1 for h in history if h["変動pt"] > 0)
    minus_count = sum(1 for h in history if h["変動pt"] < 0)
    avg_rank = sum(h["自着順"] for h in history) / n
    top_count = sum(1 for h in history if h["自着順"] == 1)

    # 合計変動の色
    total_color = "var(--green)" if total_delta > 0 else "var(--red)" if total_delta < 0 else "var(--text-primary)"
    total_sign = "+" if total_delta > 0 else ""

    st.markdown(f"""
    <div style="background:var(--bg-card);border:1px solid var(--border);border-radius:var(--radius);
                padding:0.9rem 1.2rem;margin-bottom:0.8rem;
                display:flex;gap:1.5rem;flex-wrap:wrap;align-items:center;">
        <div>
            <div style="font-size:0.7rem;color:var(--text-muted);letter-spacing:0.05em;">直近{n}戦の変動</div>
            <div style="font-size:1.6rem;font-weight:900;font-family:'Zen Kaku Gothic New';
                        color:{total_color};line-height:1.1;">{total_sign}{total_delta:.1f}</div>
        </div>
        <div style="border-left:1px solid var(--border);padding-left:1.2rem;">
            <div style="font-size:0.7rem;color:var(--text-muted);">平均変動</div>
            <div style="font-size:1.1rem;font-weight:700;color:var(--text-primary);">
                {'+' if avg_delta > 0 else ''}{avg_delta:.2f}pt/戦
            </div>
        </div>
        <div style="border-left:1px solid var(--border);padding-left:1.2rem;">
            <div style="font-size:0.7rem;color:var(--text-muted);">平均着順</div>
            <div style="font-size:1.1rem;font-weight:700;color:var(--text-primary);">{avg_rank:.2f}</div>
        </div>
        <div style="border-left:1px solid var(--border);padding-left:1.2rem;">
            <div style="font-size:0.7rem;color:var(--text-muted);">プラス / マイナス</div>
            <div style="font-size:1.0rem;font-weight:700;">
                <span style="color:var(--green);">{plus_count}戦</span>
                <span style="color:var(--text-muted);"> / </span>
                <span style="color:var(--red);">{minus_count}戦</span>
            </div>
        </div>
        <div style="border-left:1px solid var(--border);padding-left:1.2rem;">
            <div style="font-size:0.7rem;color:var(--text-muted);">トップ数</div>
            <div style="font-size:1.1rem;font-weight:700;color:var(--accent);">🥇 {top_count}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # --- 詳細テーブル ---
    rank_emoji = {1: "🥇", 2: "🥈", 3: "🥉"}
    html = '<table class="stats-table" style="width:100%;font-size:0.85rem;">'
    html += """<thead><tr>
        <th style="width:40px;">#</th>
        <th style="width:110px;">日時</th>
        <th style="width:55px;text-align:center;">着順</th>
        <th style="text-align:left;">対戦相手 (レート / 着順)</th>
        <th style="width:75px;text-align:center;">開始R</th>
        <th style="width:75px;text-align:center;">終了R</th>
        <th style="width:80px;text-align:center;">変動</th>
        <th style="width:65px;text-align:center;">段位</th>
    </tr></thead><tbody>"""

    for i, h in enumerate(history):
        # 日時表示
        try:
            dt_str = pd.to_datetime(h["日時"]).strftime("%m/%d %H:%M")
        except:
            dt_str = str(h["日時"])[:16]

        # 変動色
        delta = h["変動pt"]
        if delta > 0:
            delta_color = "var(--green)"
            delta_sign = "+"
        elif delta < 0:
            delta_color = "var(--red)"
            delta_sign = ""
        else:
            delta_color = "var(--text-primary)"
            delta_sign = ""

        # 着順表示
        my_rank_emoji = rank_emoji.get(h["自着順"], "")
        my_rank_color = ("var(--accent)" if h["自着順"] == 1
                        else "var(--text-primary)" if h["自着順"] == 2
                        else "var(--red)")

        # 対戦相手表示 (レート順ソート済)
        opp_parts = []
        for opp in h["対戦相手"]:
            opp_rank_emoji = rank_emoji.get(opp["着順"], "")
            opp_rank_color = ("var(--accent)" if opp["着順"] == 1
                             else "var(--text-primary)" if opp["着順"] == 2
                             else "var(--red)")
            opp_parts.append(
                f'<span style="display:inline-block;margin-right:0.6rem;">'
                f'<span style="color:{opp_rank_color};">{opp_rank_emoji}</span> '
                f'<span style="font-weight:600;">{opp["名前"]}</span> '
                f'<span style="color:var(--text-muted);font-size:0.8rem;">(R{opp["レート"]:.0f})</span>'
                f'</span>'
            )
        opp_html = "".join(opp_parts)

        # 段位変化表示
        dan_html = f'<span style="color:{h["終了段位色"]};font-weight:700;font-size:0.85rem;">{h["終了段位名"]}</span>'
        if h["段位変化"] > 0:
            dan_html = f'⬆{dan_html}'
        elif h["段位変化"] < 0:
            dan_html = f'⬇{dan_html}'

        row_bg = "rgba(76,175,135,0.05)" if delta > 0 else "rgba(224,92,92,0.05)" if delta < 0 else "transparent"

        html += f'''<tr style="background:{row_bg};">
            <td style="text-align:center;color:var(--text-muted);font-size:0.8rem;">{i+1}</td>
            <td style="color:var(--text-muted);font-size:0.8rem;">{dt_str}</td>
            <td style="text-align:center;">
                <span style="color:{my_rank_color};font-size:1.1rem;">{my_rank_emoji}</span>
            </td>
            <td style="text-align:left;">{opp_html}</td>
            <td style="text-align:center;color:var(--text-muted);font-family:'Zen Kaku Gothic New';">R{h["開始レート"]:.0f}</td>
            <td style="text-align:center;font-family:'Zen Kaku Gothic New';font-weight:700;">R{h["終了レート"]:.0f}</td>
            <td style="text-align:center;font-weight:900;color:{delta_color};
                       font-family:'Zen Kaku Gothic New';font-size:1.0rem;">
                {delta_sign}{delta:.1f}
            </td>
            <td style="text-align:center;">{dan_html}</td>
        </tr>'''
    html += '</tbody></table>'
    st.markdown(html, unsafe_allow_html=True)


def render_pending_bar(location_key=""):
    """
    未保存変更がある場合に表示する共通ステータスバー。
    全ページの上部 (top_navの直後) に配置する。
    """
    cnt = pending_count()
    if cnt == 0:
        return

    # 件数に応じて警告レベルを変える
    if cnt >= 20:
        bg_grad = "linear-gradient(135deg, rgba(224,92,92,0.18) 0%, rgba(224,123,57,0.15) 100%)"
        border_col = "var(--red)"
        text_col = "var(--red)"
        icon = "⚠️"
    elif cnt >= 10:
        bg_grad = "linear-gradient(135deg, rgba(224,123,57,0.18) 0%, rgba(240,192,64,0.12) 100%)"
        border_col = "var(--accent2)"
        text_col = "var(--accent2)"
        icon = "📌"
    else:
        bg_grad = "linear-gradient(135deg, rgba(91,156,246,0.15) 0%, rgba(240,192,64,0.1) 100%)"
        border_col = "var(--blue)"
        text_col = "var(--blue)"
        icon = "💾"

    st.markdown(f"""
    <div style="background:{bg_grad};border:1px solid {border_col};
                border-radius:var(--radius);padding:0.7rem 1.1rem;margin-bottom:1rem;
                display:flex;align-items:center;gap:0.7rem;">
        <span style="font-size:1.2rem;">{icon}</span>
        <span style="color:{text_col};font-weight:700;font-size:0.95rem;">
            未保存の変更: <span style="font-size:1.3rem;font-family:'Zen Kaku Gothic New';">{cnt}</span> 件
        </span>
    </div>
    """, unsafe_allow_html=True)

    c1, c2 = st.columns([2, 1])
    with c1:
        if st.button(f"💾 まとめて保存する ({cnt} 件)", key=f"commit_btn_{location_key}",
                     type="primary", use_container_width=True):
            with st.spinner(f"{cnt} 件の変更を保存中..."):
                ok = commit_buffer_to_sheet()
            if ok:
                st.session_state["success_msg"] = f"✨ {cnt} 件の変更を保存しました!"
                st.rerun()
    with c2:
        if st.button("🗑 破棄", key=f"discard_btn_{location_key}", use_container_width=True):
            st.session_state[f"_confirm_discard_{location_key}"] = True
            st.rerun()

    # 破棄確認
    if st.session_state.get(f"_confirm_discard_{location_key}", False):
        st.warning(f"⚠️ {cnt} 件の未保存データをすべて破棄しますか?この操作は取り消せません。")
        cc1, cc2 = st.columns(2)
        with cc1:
            if st.button("✅ はい、破棄する", key=f"discard_yes_{location_key}", use_container_width=True):
                buffer_clear()
                st.session_state[f"_confirm_discard_{location_key}"] = False
                st.rerun()
        with cc2:
            if st.button("キャンセル", key=f"discard_no_{location_key}", use_container_width=True):
                st.session_state[f"_confirm_discard_{location_key}"] = False
                st.rerun()

    st.write("")

def update_type_by_name(key_name, key_type, type_map):
    name = st.session_state[key_name]
    if name in type_map:
        st.session_state[key_type] = type_map[name]

def player_input_row_dynamic(label, member_list, def_n, def_t, def_r, available_ranks, key_suffix="", type_map=None):
    """席入力行 (見た目改善版)"""
    TYPE_OPTS = ["A客", "B客", "AS", "BS"]
    seat_class_map = {"A席": "a", "B席": "b", "C席": "c"}
    seat_class = seat_class_map.get(label, "a")

    # 着順を絵文字に変換
    rank_emoji = {1: "🥇 1着", 2: "🥈 2着", 3: "🥉 3着"}
    rank_labels = [rank_emoji.get(r, f"{r}着") for r in available_ranks]

    st.markdown(f'<div class="seat-card seat-{seat_class}">', unsafe_allow_html=True)
    st.markdown(
        f'''<div class="seat-header-row">
            <span class="seat-badge {seat_class}">{label[0]}</span>
            <span class="seat-card-label">{label}</span>
        </div>''',
        unsafe_allow_html=True
    )

    def get_idx_in_list(lst, val): return lst.index(val) if val in lst else None
    def get_idx_in_opts(opts, val): return opts.index(val) if val in opts else 0

    c1, c2 = st.columns([1, 1.4])
    with c1:
        idx_val = get_idx_in_list(member_list, def_n) if def_n else None
        k_name = f"n_{label}{key_suffix}"
        k_type = f"t_{label}{key_suffix}"
        name = st.selectbox(
            "プレイヤー", member_list, index=idx_val, key=k_name,
            on_change=update_type_by_name if type_map else None,
            args=(k_name, k_type, type_map) if type_map else None,
            placeholder="名前を選択"
        )
        if k_type not in st.session_state:
            st.session_state[k_type] = def_t if def_t in TYPE_OPTS else TYPE_OPTS[0]
        type_ = st.radio("タイプ", TYPE_OPTS, horizontal=True, key=k_type)
    with c2:
        final_idx = 0
        if def_r in available_ranks:
            final_idx = available_ranks.index(def_r)
        rank_label_to_val = {rank_emoji.get(r, f"{r}着"): r for r in available_ranks}
        chosen_label = st.radio("着順", rank_labels, index=final_idx, horizontal=True, key=f"r_{label}{key_suffix}")
        rank = rank_label_to_val.get(chosen_label, available_ranks[0])

    st.markdown('</div>', unsafe_allow_html=True)
    return name, type_, rank

# ==========================================
# 5. 今日のクイック統計 (ホーム用 - 改善版)
# ==========================================
def render_today_quick_stats():
    df = load_score_data_effective()
    if df.empty:
        st.markdown(
            '<div style="text-align:center;padding:1.5rem;color:var(--text-muted);'
            'background:var(--bg-card);border:1px dashed var(--border);border-radius:var(--radius);">'
            '今日の対局データはまだありません<br>'
            '<span style="font-size:0.85rem;">📝 「成績をつける」から記録を始めましょう</span>'
            '</div>',
            unsafe_allow_html=True
        )
        return

    JST = timezone(timedelta(hours=9), 'JST')
    current_dt = datetime.now(JST)
    today_logical = (current_dt - timedelta(hours=9)).date()
    mask = df["論理日付"].apply(lambda x: x == today_logical if pd.notnull(x) else False)
    df_today = df[mask]

    if df_today.empty:
        st.markdown(
            '<div style="text-align:center;padding:1.5rem;color:var(--text-muted);'
            'background:var(--bg-card);border:1px dashed var(--border);border-radius:var(--radius);">'
            '今日の対局データはまだありません<br>'
            '<span style="font-size:0.85rem;">📝 「成績をつける」から記録を始めましょう</span>'
            '</div>',
            unsafe_allow_html=True
        )
        return

    total_games = len(df_today)
    total_fee = 0
    type_counts = {"A客": 0, "B客": 0, "AS": 0, "BS": 0}
    FEE_MAP = {"A客": 3, "B客": 5, "AS": 1, "BS": 1}

    for _, row in df_today.iterrows():
        try:
            r_a, r_b, r_c = int(float(row["A着順"])), int(float(row["B着順"])), int(float(row["C着順"]))
        except:
            r_a, r_b, r_c = 0, 0, 0
        winner_type = None
        if r_a == 1: winner_type = row["Aタイプ"]
        elif r_b == 1: winner_type = row["Bタイプ"]
        elif r_c == 1: winner_type = row["Cタイプ"]
        if winner_type in type_counts:
            type_counts[winner_type] += 1
            total_fee += FEE_MAP.get(winner_type, 0)
        note = str(row["備考"])
        if note == "東１終了": total_fee -= 1
        elif note == "２人飛ばし": total_fee -= 2
        elif note == "５連勝〜": total_fee -= 5

    fee_class = "green" if total_fee >= 0 else "red"

    st.markdown(f"""
    <div class="quick-stat-bar">
        <div class="quick-stat-item blue">
            <div class="qs-label">本日 ゲーム数</div>
            <div class="qs-value">{total_games}<span style="font-size:0.8rem;color:var(--text-muted);"> 回</span></div>
        </div>
        <div class="quick-stat-item {fee_class}">
            <div class="qs-label">ゲーム代</div>
            <div class="qs-value">{total_fee}<span style="font-size:0.8rem;color:var(--text-muted);"> 枚</span></div>
        </div>
        <div class="quick-stat-item">
            <div class="qs-label">A客 / B客</div>
            <div class="qs-value" style="font-size:1.1rem;">{type_counts['A客']} / {type_counts['B客']}</div>
        </div>
        <div class="quick-stat-item green">
            <div class="qs-label">AS / BS</div>
            <div class="qs-value" style="font-size:1.1rem;">{type_counts['AS']} / {type_counts['BS']}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ==========================================
# 6. 各ページ
# ==========================================

# --- ホーム (格好いい版) ---
def page_home():
    # ヒーローヘッダー (グリーティング削除でコンパクトに)
    st.markdown("""
    <div class="hero-header">
        <div class="hero-bg-decoration">
            <div class="hero-orb hero-orb-1"></div>
            <div class="hero-orb hero-orb-2"></div>
        </div>
        <div class="hero-content">
            <div class="hero-badge">🀄 PINE RIVER</div>
            <div class="hero-title">ぱいん成績管理</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 未保存ステータスバー
    render_pending_bar(location_key="home")

    # メニュー(縦積みラベル + 説明)
    st.markdown("""
    <div style="margin:1.2rem 0 0.7rem 0;">
        <div style="font-size:0.7rem;color:var(--text-muted);letter-spacing:0.18em;
                    font-weight:700;text-transform:uppercase;">MENU</div>
    </div>
    """, unsafe_allow_html=True)

    # メニュー項目 (絵文字, ラベル, page, カラークラス)
    menu_items = [
        ("👤", "個人成績", "personal", "blue"),
        ("📊", "データ参照", "history", "green"),
        ("🏆", "ランキング", "ranking", "gold"),
        ("📅", "月間ランキングPT", "monthly", "orange"),
        ("🤝", "2人対戦データ", "versus2", "purple"),
        ("👥", "3人対戦データ", "versus3", "pink"),
    ]

    # 2列グリッド
    for i in range(0, len(menu_items), 2):
        cols = st.columns(2, gap="small")
        for j, col in enumerate(cols):
            idx = i + j
            if idx >= len(menu_items):
                continue
            icon, label, page_key, color_class = menu_items[idx]
            with col:
                # ボタンを div でラップして、その div にカラークラスを付与
                # (直下の Streamlit ボタンにCSSでスタイルを当てる)
                st.markdown(f'<div class="menu-btn-wrap menu-color-{color_class}">', unsafe_allow_html=True)
                if st.button(f"{icon}  {label}", key=f"home_{page_key}", use_container_width=True):
                    st.session_state["page"] = page_key
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

    # フッター
    st.markdown("""
    <div class="home-footer">
        <div class="home-footer-line"></div>
        <div class="home-footer-text">
            🀄 Pine River Score Manager
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- 個人成績 (改善版) ---
def page_personal():
    render_top_nav("personal")
    st.title("👤 個人成績")
    render_pending_bar(location_key="personal")

    df = load_score_data_effective()
    if df.empty:
        st.info("データがありません")
        return

    all_players = get_all_member_names()
    if not all_players:
        st.info("メンバーが登録されていません")
        return

    default_player_idx = 0
    if "personal_player" in st.session_state and st.session_state["personal_player"] in all_players:
        default_player_idx = all_players.index(st.session_state["personal_player"])

    selected_player = st.selectbox("👤 プレイヤーを選択", all_players, index=default_player_idx, key="personal_player_select")
    st.session_state["personal_player"] = selected_player

    if not selected_player:
        return

    # レーティング/段位カードを表示
    rating_info = get_player_rating(selected_player)
    if rating_info is not None:
        render_rating_card(selected_player, rating_info)

    # 直近10戦のレーティング変動履歴 (折りたたみで表示)
    with st.expander("📈 直近10戦のレーティング変動 (対戦相手・段位変化)", expanded=True):
        render_recent_rating_history(selected_player, last_n=10)

    # TOP5にランクインしている全項目を表示 (折りたたみで展開)
    with st.expander("🏆 TOP5にランクインしている項目", expanded=True):
        with st.spinner("ランキング項目を集計中..."):
            top5_items = get_player_top5_rankings(selected_player, top_n=5, min_games=30)

        if top5_items is None or len(top5_items) == 0:
            st.info(f"「{selected_player}」さんがTOP5にランクインしている項目はありません(規定打数30戦以上)")
        else:
            cat_label = "スタッフ" if top5_items[0]["カテゴリ"] == "staff" else "お客さん"
            st.caption(f"「{selected_player}」さんが**{cat_label}**部門で上位5位以内にランクインしている項目です (規定打数30戦以上)")

            # 順位でソート (1位が上)
            top5_items_sorted = sorted(top5_items, key=lambda x: (x["順位"], x["項目"]))

            # HTMLテーブルで表示
            html = '<table class="stats-table" style="width:100%;">'
            html += """<thead><tr>
                <th style="width:60px;text-align:center;">順位</th>
                <th style="text-align:left;">ランキング項目</th>
                <th style="text-align:center;">記録</th>
                <th style="width:110px;text-align:center;">エントリ数</th>
            </tr></thead><tbody>"""

            rank_medals = {1: "🥇", 2: "🥈", 3: "🥉"}
            for item in top5_items_sorted:
                pos = item["順位"]
                medal = rank_medals.get(pos, "")
                rank_color = ("var(--accent)" if pos == 1
                              else "var(--text-primary)" if pos == 2
                              else "var(--red)" if pos == 3
                              else "var(--text-muted)")
                row_bg = "rgba(240,192,64,0.08)" if pos == 1 else "transparent"
                html += f'''<tr style="background:{row_bg};">
                    <td style="text-align:center;font-weight:900;color:{rank_color};font-size:1.1rem;">
                        {medal} {pos}位
                    </td>
                    <td style="text-align:left;font-weight:600;">{item["項目"]}</td>
                    <td style="text-align:center;font-family:'Zen Kaku Gothic New';
                               font-weight:700;color:{rank_color};">{item["値"]}</td>
                    <td style="text-align:center;color:var(--text-muted);font-size:0.85rem;">
                        {item["順位"]} / {item["総エントリ数"]}
                    </td>
                </tr>'''
            html += '</tbody></table>'
            st.markdown(html, unsafe_allow_html=True)

            # サマリバッジ
            counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
            for item in top5_items:
                counts[item["順位"]] = counts.get(item["順位"], 0) + 1
            summary_parts = []
            for r, cnt in [(1, counts[1]), (2, counts[2]), (3, counts[3])]:
                if cnt > 0:
                    medal = rank_medals[r]
                    summary_parts.append(f'<span style="margin-right:1.2rem;font-size:0.95rem;">{medal} <strong>{cnt}</strong>項目</span>')
            if summary_parts:
                st.markdown(
                    f'<div style="margin-top:0.6rem;color:var(--text-muted);font-size:0.85rem;">'
                    f'合計 {len(top5_items)} 項目でTOP5入り' +
                    (f' — 内訳: {"".join(summary_parts)}' if summary_parts else '') +
                    f'</div>',
                    unsafe_allow_html=True
                )

    df_player = df[
        (df["Aさん"] == selected_player) |
        (df["Bさん"] == selected_player) |
        (df["Cさん"] == selected_player)
    ]

    if df_player.empty:
        st.warning(f"「{selected_player}」さんの対局データはありません")
        return

    df_player = df_player.copy()
    df_player["年月"] = df_player["日時Obj"].dt.to_period("M")
    available_months = sorted(df_player["年月"].dropna().unique(), reverse=True)

    if not len(available_months):
        st.warning("日時データがありません")
        return

    month_labels = ["全期間"] + [str(m) for m in available_months]

    c_filter1, c_filter2 = st.columns([1, 2])
    with c_filter1:
        selected_month_label = st.selectbox("📅 期間", month_labels, index=0, key="personal_month")
    with c_filter2:
        time_range = st.selectbox("⏰ 時間帯", ["全日", "9:00-21:00", "21:00-33:00(翌9:00)"], key="personal_time")

    df_filtered = df_player.copy()
    if selected_month_label != "全期間":
        df_filtered = df_filtered[df_filtered["年月"].astype(str) == selected_month_label]
    if time_range == "9:00-21:00":
        df_filtered = df_filtered[df_filtered["日時Obj"].dt.hour.between(9, 20)]
    elif time_range == "21:00-33:00(翌9:00)":
        df_filtered = df_filtered[~df_filtered["日時Obj"].dt.hour.between(9, 20)]

    if df_filtered.empty:
        st.warning("選択した条件のデータはありません")
        return

    period_label = selected_month_label if selected_month_label != "全期間" else "全期間"
    section_title("📊", f"{selected_player} さん — {period_label}")

    ranks = []
    played_dates = set()
    compatibility = {}
    player_seat_ranks = {"A": [], "B": [], "C": []}
    monthly_data = {}

    for _, row in df_filtered.iterrows():
        my_rank = None
        my_seat = None
        for s in ["A", "B", "C"]:
            if row[f"{s}さん"] == selected_player:
                try:
                    my_rank = int(float(row[f"{s}着順"]))
                    my_seat = s
                except:
                    pass
                break
        if my_rank:
            ranks.append(my_rank)
            played_dates.add(row["論理日付"])
            if my_seat in player_seat_ranks:
                player_seat_ranks[my_seat].append(my_rank)

            ym = str(row["年月"])
            if ym not in monthly_data:
                monthly_data[ym] = {"ranks": [], "dates": set()}
            monthly_data[ym]["ranks"].append(my_rank)
            monthly_data[ym]["dates"].add(row["論理日付"])

            for s in ["A", "B", "C"]:
                if s == my_seat:
                    continue
                opp_name = row[f"{s}さん"]
                if not opp_name:
                    continue
                try:
                    opp_rank = int(float(row[f"{s}着順"]))
                except:
                    opp_rank = 0
                if opp_rank == 0:
                    continue
                if opp_name not in compatibility:
                    compatibility[opp_name] = {"count": 0, "score": 0}
                compatibility[opp_name]["count"] += 1
                compatibility[opp_name]["score"] += opp_rank - my_rank

    if not ranks:
        st.warning("着順データが見つかりません")
        return

    games = len(ranks)
    avg = sum(ranks) / games
    c1_cnt = ranks.count(1)
    c2_cnt = ranks.count(2)
    c3_cnt = ranks.count(3)
    top_rate = c1_cnt / games * 100
    last_avoid = (games - c3_cnt) / games * 100
    unique_days = len(played_dates)

    stats_html = f"""
    <table class="stats-table">
        <thead><tr>
            <th>総回数</th><th>稼働日数</th><th>平均着順</th><th>トップ率</th><th>ラス回避率</th>
            <th>🥇 1着</th><th>🥈 2着</th><th>🥉 3着</th>
        </tr></thead>
        <tbody><tr>
            <td>{games} 回</td>
            <td>{unique_days} 日</td>
            <td style="color:var(--accent)">{avg:.3f}</td>
            <td style="color:var(--green)">{top_rate:.3f}%</td>
            <td style="color:var(--blue)">{last_avoid:.3f}%</td>
            <td>{c1_cnt}<span class="stats-sub">{c1_cnt/games*100:.2f}%</span></td>
            <td>{c2_cnt}<span class="stats-sub">{c2_cnt/games*100:.2f}%</span></td>
            <td>{c3_cnt}<span class="stats-sub">{c3_cnt/games*100:.2f}%</span></td>
        </tr></tbody>
    </table>
    """
    st.markdown(stats_html, unsafe_allow_html=True)

    # 折りたたみで席別成績
    with st.expander("🪑 席別成績", expanded=False):
        p_seat_rows = []
        for s in ["A", "B", "C"]:
            rs = player_seat_ranks[s]
            c = len(rs)
            if c > 0:
                p_seat_rows.append({
                    "席": f"{s}席", "打数": c, "平均着順": f"{sum(rs)/c:.3f}",
                    "1着": f"{rs.count(1)} ({rs.count(1)/c*100:.1f}%)",
                    "2着": f"{rs.count(2)} ({rs.count(2)/c*100:.1f}%)",
                    "3着": f"{rs.count(3)} ({rs.count(3)/c*100:.1f}%)"
                })
        if p_seat_rows:
            st.dataframe(pd.DataFrame(p_seat_rows), hide_index=True, use_container_width=True)

    # 月別成績
    if len(monthly_data) > 1 or selected_month_label == "全期間":
        with st.expander("📅 月別成績", expanded=False):
            month_rows = []
            for ym in sorted(monthly_data.keys(), reverse=True):
                md = monthly_data[ym]
                rs = md["ranks"]
                g = len(rs)
                if g == 0:
                    continue
                r1 = rs.count(1)
                r2 = rs.count(2)
                r3 = rs.count(3)
                month_rows.append({
                    "年月": ym,
                    "打数": g,
                    "稼働日数": len(md["dates"]),
                    "平均着順": f"{sum(rs)/g:.3f}",
                    "トップ率": f"{r1/g*100:.2f}%",
                    "ラス回避率": f"{(g-r3)/g*100:.2f}%",
                    "1着": f"{r1} ({r1/g*100:.1f}%)",
                    "2着": f"{r2} ({r2/g*100:.1f}%)",
                    "3着": f"{r3} ({r3/g*100:.1f}%)",
                })
            if month_rows:
                st.dataframe(pd.DataFrame(month_rows), hide_index=True, use_container_width=True)

    st.divider()
    # 着順推移
    c_graph, c_dates = st.columns([2, 1])
    with c_graph:
        chart_count = min(len(ranks), 30)
        section_title("📈", f"直近{chart_count}戦の着順推移")
        recent_ranks = ranks[-chart_count:]
        df_trend = pd.DataFrame({"戦数": range(1, len(recent_ranks) + 1), "着順": recent_ranks})
        if len(recent_ranks) >= 5:
            df_trend["移動平均(5戦)"] = df_trend["着順"].rolling(window=5, min_periods=1).mean()

        base = alt.Chart(df_trend).encode(
            x=alt.X("戦数", axis=alt.Axis(tickMinStep=1), title="直近ゲーム"),
        )
        line_main = base.mark_line(
            point=alt.OverlayMarkDef(color="#f0c040", size=80),
            color="#f0c040", strokeWidth=2
        ).encode(
            y=alt.Y("着順", scale=alt.Scale(domain=[3.3, 0.7]), title="着順"),
            tooltip=["戦数", "着順"]
        )
        chart = line_main
        if "移動平均(5戦)" in df_trend.columns:
            line_avg = base.mark_line(
                color="#5b9cf6", strokeWidth=1.5, strokeDash=[5, 3]
            ).encode(
                y=alt.Y("移動平均(5戦)"),
                tooltip=["戦数", alt.Tooltip("移動平均(5戦)", format=".3f")]
            )
            chart = alt.layer(line_main, line_avg)

        chart = chart.properties(height=280).configure_view(
            strokeWidth=0, fill="#1a1d2e"
        ).configure_axis(
            gridColor="#2a2d3e", labelColor="#8890a8", titleColor="#8890a8"
        )
        st.altair_chart(chart, use_container_width=True)
        if "移動平均(5戦)" in df_trend.columns:
            st.caption("🟡 着順  /  🔵 5戦移動平均")
    with c_dates:
        section_title("📅", "稼働日")
        date_list = sorted(list(played_dates), reverse=True)
        st.dataframe(pd.DataFrame(date_list, columns=["日付"]), hide_index=True, use_container_width=True, height=300)

    if compatibility:
        st.divider()
        section_title("🤝", "対戦相手データ (TOP5)")
        comp_data = [{"名前": n, "同卓回数": d["count"], "相性スコア": d["score"]} for n, d in compatibility.items()]
        df_comp = pd.DataFrame(comp_data)
        c_freq, c_good, c_bad = st.columns(3)
        with c_freq:
            st.markdown("**👬 同卓回数**")
            st.dataframe(df_comp.sort_values("同卓回数", ascending=False).head(5).reset_index(drop=True)[["名前", "同卓回数"]], hide_index=True, use_container_width=True)
        with c_good:
            st.markdown("**💖 相性が良い**")
            st.dataframe(df_comp.sort_values("相性スコア", ascending=False).head(5).reset_index(drop=True)[["名前", "相性スコア"]], hide_index=True, use_container_width=True)
        with c_bad:
            st.markdown("**💀 相性が悪い**")
            st.dataframe(df_comp.sort_values("相性スコア", ascending=True).head(5).reset_index(drop=True)[["名前", "相性スコア"]], hide_index=True, use_container_width=True)

    st.divider()
    with st.expander("🀄 個人記録の更新", expanded=False):
        df_mem = load_member_data()
        current_max = 0
        current_yaku = 0
        current_detail = ""
        current_date_str = ""
        target_idx = df_mem.index[df_mem["名前"] == selected_player].tolist()

        if target_idx:
            idx = target_idx[0]
            current_max = int(df_mem.at[idx, "最大飜数"])
            current_yaku = int(df_mem.at[idx, "役満回数"])
            current_detail = df_mem.at[idx, "最大飜数詳細"] if "最大飜数詳細" in df_mem.columns else ""
            current_date_str = df_mem.at[idx, "最大飜数記録日"] if "最大飜数記録日" in df_mem.columns else ""

            c_d1, c_d2, c_d3 = st.columns(3)
            c_d1.metric("最大飜数", f"{current_max} 飜", current_detail if current_detail else None)
            c_d2.metric("役満回数", f"{current_yaku} 回")
            if current_date_str:
                c_d3.metric("記録日", current_date_str)

        with st.form("update_personal_stats_page"):
            c_in1, c_in2 = st.columns(2)
            with c_in1:
                new_max = st.number_input("最大飜数", min_value=0, value=current_max, key="ps_max")
                new_detail = st.text_input("最大飜数詳細 (役名など)", value=current_detail, key="ps_detail")
                new_date_val = st.text_input("記録日 (例: 2026/02/20)", value=current_date_str, key="ps_date")
            with c_in2:
                new_yaku = st.number_input("役満回数", min_value=0, value=current_yaku, key="ps_yaku")
            if st.form_submit_button("💾 更新する", type="primary"):
                if target_idx:
                    df_mem.at[idx, "最大飜数"] = new_max
                    df_mem.at[idx, "役満回数"] = new_yaku
                    if "最大飜数詳細" not in df_mem.columns:
                        df_mem["最大飜数詳細"] = ""
                    if "最大飜数記録日" not in df_mem.columns:
                        df_mem["最大飜数記録日"] = ""
                    df_mem.at[idx, "最大飜数詳細"] = new_detail
                    df_mem.at[idx, "最大飜数記録日"] = new_date_val
                    save_member_data(df_mem)
                    st.success(f"✅ {selected_player}さんの記録を更新しました！")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("メンバー登録されていません。「メンバー管理」から登録してください。")

# --- 編集画面 (バッファ方式) ---
def page_edit():
    st.title("🔧 データ修正・削除")

    edit_id = st.session_state.get("editing_game_id")
    if not edit_id:
        st.error("編集対象が選択されていません")
        if st.button("🏠 ホームに戻る"):
            st.session_state["page"] = "home"
            st.rerun()
        return

    # 実効データ (バッファ反映後) から対象を探す
    df = load_score_data_effective()
    target_row = df[df["GameNo"] == edit_id]

    if target_row.empty:
        st.error("データが見つかりません（削除された可能性があります）")
        if st.button("🏠 ホームに戻る"):
            st.session_state["page"] = "home"
            st.rerun()
        return

    row = target_row.iloc[0]
    df_mem = load_member_data()
    member_list = get_all_member_names()
    type_map = dict(zip(df_mem["名前"], df_mem["タイプ"]))

    # 未保存データかどうかを判定 (GameNoが負なら未保存の新規追加)
    is_unsaved = edit_id < 0
    status_badge = "🆕 未保存(新規)" if is_unsaved else "💾 保存済み"

    st.markdown(f"""
    <div class="input-status-bar">
        <span class="isb-main">📝 編集中: No.{row['DailyNo']}</span>
        <span class="isb-sub">{status_badge} ／ 卓: {row['TableNo']} ／ セット: {row['SetNo']} ／ 時刻: {pd.to_datetime(row['日時']).strftime('%H:%M') if row['日時'] else '-'}</span>
    </div>
    """, unsafe_allow_html=True)

    st.info("📌 編集内容は「未保存」状態になります。入力画面の「💾 まとめて保存」ボタンで一括反映してください。")

    with st.form("edit_form"):
        p1_n, p1_t, p1_r = player_input_row_dynamic("A席", member_list, row["Aさん"], row["Aタイプ"], int(float(row["A着順"])), [1, 2, 3], "_edit", type_map)
        p2_n, p2_t, p2_r = player_input_row_dynamic("B席", member_list, row["Bさん"], row["Bタイプ"], int(float(row["B着順"])), [1, 2, 3], "_edit", type_map)
        p3_n, p3_t, p3_r = player_input_row_dynamic("C席", member_list, row["Cさん"], row["Cタイプ"], int(float(row["C着順"])), [1, 2, 3], "_edit", type_map)

        st.markdown("**📋 備考**")
        NOTE_OPTS = ["なし", "東１終了", "２人飛ばし", "５連勝〜"]
        def idx(opts, val): return opts.index(val) if val in opts else 0
        cur_note = row["備考"] if row["備考"] else "なし"
        opts = NOTE_OPTS if cur_note in NOTE_OPTS else NOTE_OPTS + [cur_note]
        note = st.radio("内容", opts, index=idx(opts, cur_note), horizontal=True)

        st.divider()
        c_up, c_del, c_can = st.columns(3)
        with c_up:
            submit_update = st.form_submit_button("🔄 更新を一時保存", type="primary", use_container_width=True)
        with c_del:
            submit_delete = st.form_submit_button("🗑 削除を一時保存", use_container_width=True)
        with c_can:
            submit_cancel = st.form_submit_button("キャンセル", use_container_width=True)

        if submit_cancel:
            st.session_state["page"] = "home"
            st.session_state["editing_game_id"] = None
            st.rerun()

        if submit_update:
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
                changes_list = []
                compare_keys = [
                    ("備考", "備考"), ("A名前", "Aさん"), ("A着順", "A着順"), ("Aタイプ", "Aタイプ"),
                    ("B名前", "Bさん"), ("B着順", "B着順"), ("Bタイプ", "Bタイプ"),
                    ("C名前", "Cさん"), ("C着順", "C着順"), ("Cタイプ", "Cタイプ"),
                ]
                for label_, key in compare_keys:
                    old_val = row[key]
                    new_val = new_data[key]
                    if str(old_val) != str(new_val):
                        changes_list.append(f"{label_}: {old_val}→{new_val}")
                diff_text = ", ".join(changes_list) if changes_list else "変更なし"

                buffer_update(edit_id, new_data, detail=diff_text)
                st.session_state["success_msg"] = f"🔄 修正を一時保存しました — 未保存: {pending_count()}件"
                st.session_state["page"] = "home"
                st.session_state["editing_game_id"] = None
                st.rerun()

        if submit_delete:
            del_info = f"{row['日時']} {row['TableNo']}卓 Set{row['SetNo']}"
            buffer_delete(edit_id, info=del_info)
            st.session_state["success_msg"] = f"🗑 削除を一時保存しました — 未保存: {pending_count()}件"
            st.session_state["page"] = "home"
            st.session_state["editing_game_id"] = None
            st.rerun()

# --- 履歴画面 (改善版) ---
def page_history():
    render_top_nav("history")
    st.title("📊 過去データ参照")
    render_pending_bar(location_key="history")

    df = load_score_data_effective()
    if df.empty:
        st.info("データがありません")
        return

    # タブで「期間統計・詳細検索」「2人対戦」「3人対戦」を切り替え
    tab1, tab2, tab3 = st.tabs(["📈 期間統計・詳細検索", "👥 2人対戦データ", "👥👤 3人対戦データ"])

    with tab1:
        _page_history_overview(df)
    with tab2:
        _page_history_versus_2(df)
    with tab3:
        _page_history_versus_3(df)

def page_versus2():
    """2人対戦データ専用ページ (ホームから直接アクセス可能)"""
    render_top_nav("versus2")
    st.title("🤝 2人対戦データ")
    render_pending_bar(location_key="versus2")

    df = load_score_data_effective()
    if df.empty:
        st.info("データがありません")
        return
    _page_history_versus_2(df)

def page_versus3():
    """3人対戦データ専用ページ (ホームから直接アクセス可能)"""
    render_top_nav("versus3")
    st.title("👥 3人対戦データ")
    render_pending_bar(location_key="versus3")

    df = load_score_data_effective()
    if df.empty:
        st.info("データがありません")
        return
    _page_history_versus_3(df)

def _page_history_versus_2(df):
    """2人を選択して、その2人が同卓した試合データを表示"""
    section_title("👥", "2人を選択")
    st.caption("選択した2人が同卓した試合のデータを表示します")

    all_players = get_all_member_names()
    if len(all_players) < 2:
        st.warning("メンバーが2人以上必要です")
        return

    c1, c2 = st.columns(2)
    with c1:
        p1 = st.selectbox("👤 プレイヤー1", ["(選択してください)"] + all_players, key="vs2_p1")
    with c2:
        p2_options = ["(選択してください)"] + [p for p in all_players if p != p1]
        p2 = st.selectbox("👤 プレイヤー2", p2_options, key="vs2_p2")

    if p1 == "(選択してください)" or p2 == "(選択してください)" or p1 == p2:
        st.info("☝️ 2人を選択してください")
        return

    # 同卓試合を抽出
    def has_both(row, a, b):
        names = [row["Aさん"], row["Bさん"], row["Cさん"]]
        return a in names and b in names

    mask = df.apply(lambda r: has_both(r, p1, p2), axis=1)
    df_vs = df[mask].copy()

    if df_vs.empty:
        st.warning(f"「{p1}」と「{p2}」が同卓した試合はありません")
        return

    # 統計を計算
    p1_ranks = []
    p2_ranks = []
    p1_wins = 0  # p1がp2より上位だった回数
    p2_wins = 0
    draws = 0  # 同じ着順はあり得ないが念のため

    for _, row in df_vs.iterrows():
        r1, r2 = None, None
        for s in ["A", "B", "C"]:
            if row[f"{s}さん"] == p1:
                try: r1 = int(float(row[f"{s}着順"]))
                except: pass
            if row[f"{s}さん"] == p2:
                try: r2 = int(float(row[f"{s}着順"]))
                except: pass
        if r1 and r2 and r1 > 0 and r2 > 0:
            p1_ranks.append(r1)
            p2_ranks.append(r2)
            if r1 < r2: p1_wins += 1
            elif r1 > r2: p2_wins += 1
            else: draws += 1

    total = len(p1_ranks)
    if total == 0:
        st.warning("有効なデータがありません")
        return

    # サマリーカード
    st.markdown(f"""
    <div class="quick-stat-bar">
        <div class="quick-stat-item blue">
            <div class="qs-label">同卓回数</div>
            <div class="qs-value">{total}<span style="font-size:0.8rem;color:var(--text-muted);"> 回</span></div>
        </div>
        <div class="quick-stat-item green">
            <div class="qs-label">{p1} 直接対決 勝</div>
            <div class="qs-value">{p1_wins}<span style="font-size:0.8rem;color:var(--text-muted);"> 回</span></div>
        </div>
        <div class="quick-stat-item red">
            <div class="qs-label">{p2} 直接対決 勝</div>
            <div class="qs-value">{p2_wins}<span style="font-size:0.8rem;color:var(--text-muted);"> 回</span></div>
        </div>
        <div class="quick-stat-item">
            <div class="qs-label">{p1} 勝率</div>
            <div class="qs-value" style="font-size:1.2rem;">{p1_wins/total*100:.1f}%</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 着順分布テーブル
    section_title("📊", "着順の分布")

    def calc_stats(ranks, name):
        c = len(ranks)
        if c == 0: return None
        r1 = ranks.count(1); r2 = ranks.count(2); r3 = ranks.count(3)
        return {
            "プレイヤー": name,
            "打数": c,
            "平均着順": f"{sum(ranks)/c:.3f}",
            "1着": f"{r1} ({r1/c*100:.1f}%)",
            "2着": f"{r2} ({r2/c*100:.1f}%)",
            "3着": f"{r3} ({r3/c*100:.1f}%)",
            "トップ率": f"{r1/c*100:.2f}%",
            "ラス回避率": f"{(c-r3)/c*100:.2f}%",
        }

    rows = []
    s1 = calc_stats(p1_ranks, p1)
    s2 = calc_stats(p2_ranks, p2)
    if s1: rows.append(s1)
    if s2: rows.append(s2)
    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)

    # 直接対決マトリックス
    section_title("⚔️", "直接対決の内訳")
    st.caption(f"{p1} の着順 × {p2} の着順 (同卓した全試合)")

    matrix = [[0]*3 for _ in range(3)]
    for a, b in zip(p1_ranks, p2_ranks):
        if 1 <= a <= 3 and 1 <= b <= 3:
            matrix[a-1][b-1] += 1

    matrix_html = f"""
    <table class="stats-table" style="width:auto;margin:0 auto;">
        <thead>
            <tr>
                <th rowspan="2" style="background:var(--bg-card2);"></th>
                <th colspan="3" style="background:var(--accent-soft);color:var(--accent);">{p2} 着順</th>
            </tr>
            <tr>
                <th>1着</th><th>2着</th><th>3着</th>
            </tr>
        </thead>
        <tbody>
    """
    rank_labels = ["1着", "2着", "3着"]
    for i in range(3):
        matrix_html += f'<tr><th style="background:var(--accent-soft);color:var(--accent);">{p1}<br>{rank_labels[i]}</th>'
        for j in range(3):
            val = matrix[i][j]
            if i == j:
                cell_color = "var(--text-muted)"  # 同着はあり得ないが念のため
                bg = "rgba(255,255,255,0.02)"
            elif i < j:
                cell_color = "var(--green)"
                bg = "var(--green-soft)"
            else:
                cell_color = "var(--red)"
                bg = "var(--red-soft)"
            matrix_html += f'<td style="background:{bg};color:{cell_color};">{val}</td>'
        matrix_html += '</tr>'
    matrix_html += '</tbody></table>'
    st.markdown(matrix_html, unsafe_allow_html=True)
    st.caption(f"🟢 緑のセル: {p1} が {p2} より上位 ／ 🔴 赤のセル: {p2} が {p1} より上位")

    # 試合一覧
    st.divider()
    section_title("📋", "同卓した試合一覧")
    df_show = df_vs.sort_values("日時Obj", ascending=False).copy()
    df_show["日付"] = df_show["日時Obj"].dt.strftime("%Y-%m-%d %H:%M")
    df_show = df_show[["日付", "TableNo", "SetNo", "Aさん", "A着順", "Bさん", "B着順", "Cさん", "C着順", "備考"]]
    df_show = df_show.rename(columns={"TableNo": "卓", "SetNo": "セット"})
    st.dataframe(df_show, hide_index=True, use_container_width=True, height=400)

def _page_history_versus_3(df):
    """3人を選択して、その3人が同卓した試合データを表示"""
    section_title("👥", "3人を選択")
    st.caption("選択した3人が同卓(=この3人が席を埋めた)試合のデータを表示します")

    all_players = get_all_member_names()
    if len(all_players) < 3:
        st.warning("メンバーが3人以上必要です")
        return

    c1, c2, c3 = st.columns(3)
    with c1:
        p1 = st.selectbox("👤 プレイヤー1", ["(選択してください)"] + all_players, key="vs3_p1")
    with c2:
        p2_opts = ["(選択してください)"] + [p for p in all_players if p != p1]
        p2 = st.selectbox("👤 プレイヤー2", p2_opts, key="vs3_p2")
    with c3:
        p3_opts = ["(選択してください)"] + [p for p in all_players if p != p1 and p != p2]
        p3 = st.selectbox("👤 プレイヤー3", p3_opts, key="vs3_p3")

    placeholders = ["(選択してください)"]
    if p1 in placeholders or p2 in placeholders or p3 in placeholders:
        st.info("☝️ 3人を選択してください")
        return
    if len({p1, p2, p3}) < 3:
        st.error("3人とも異なるプレイヤーを選択してください")
        return

    target_set = {p1, p2, p3}

    def is_same_three(row):
        names = {row["Aさん"], row["Bさん"], row["Cさん"]}
        return names == target_set

    mask = df.apply(is_same_three, axis=1)
    df_vs = df[mask].copy()

    if df_vs.empty:
        st.warning(f"「{p1}」「{p2}」「{p3}」の3人だけで同卓した試合はありません")
        return

    # 各プレイヤーの着順履歴
    ranks_map = {p1: [], p2: [], p3: []}
    win_counts = {p1: 0, p2: 0, p3: 0}  # 1着回数
    last_counts = {p1: 0, p2: 0, p3: 0}  # 3着回数

    for _, row in df_vs.iterrows():
        for s in ["A", "B", "C"]:
            name = row[f"{s}さん"]
            if name in ranks_map:
                try:
                    r = int(float(row[f"{s}着順"]))
                    if r in [1, 2, 3]:
                        ranks_map[name].append(r)
                        if r == 1: win_counts[name] += 1
                        if r == 3: last_counts[name] += 1
                except: pass

    total = len(df_vs)

    # サマリー
    st.markdown(f"""
    <div class="quick-stat-bar">
        <div class="quick-stat-item blue">
            <div class="qs-label">同卓回数</div>
            <div class="qs-value">{total}<span style="font-size:0.8rem;color:var(--text-muted);"> 回</span></div>
        </div>
        <div class="quick-stat-item green">
            <div class="qs-label">最多トップ</div>
            <div class="qs-value" style="font-size:1rem;">{max(win_counts, key=win_counts.get)}<br><span style="font-size:0.8rem;color:var(--text-muted);">{max(win_counts.values())}回</span></div>
        </div>
        <div class="quick-stat-item red">
            <div class="qs-label">最多ラス</div>
            <div class="qs-value" style="font-size:1rem;">{max(last_counts, key=last_counts.get)}<br><span style="font-size:0.8rem;color:var(--text-muted);">{max(last_counts.values())}回</span></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 統計テーブル
    section_title("📊", "3人の成績")
    rows = []
    for name in [p1, p2, p3]:
        rs = ranks_map[name]
        c = len(rs)
        if c == 0:
            continue
        r1 = rs.count(1); r2 = rs.count(2); r3_cnt = rs.count(3)
        rows.append({
            "プレイヤー": name,
            "打数": c,
            "平均着順": f"{sum(rs)/c:.3f}",
            "1着": f"{r1} ({r1/c*100:.1f}%)",
            "2着": f"{r2} ({r2/c*100:.1f}%)",
            "3着": f"{r3_cnt} ({r3_cnt/c*100:.1f}%)",
            "トップ率": f"{r1/c*100:.2f}%",
            "ラス回避率": f"{(c-r3_cnt)/c*100:.2f}%",
        })
    if rows:
        st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)

    # 着順パターン分布
    section_title("🎯", "着順パターン")
    st.caption(f"3人のうち誰が何着だったかの集計 (全{total}試合)")

    # 6パターン (3!) の組合せ
    from itertools import permutations
    pattern_counts = {}
    for perm in permutations([p1, p2, p3]):
        pattern_counts[perm] = 0

    for _, row in df_vs.iterrows():
        rank_to_name = {}
        for s in ["A", "B", "C"]:
            name = row[f"{s}さん"]
            try:
                r = int(float(row[f"{s}着順"]))
                if name in target_set and r in [1, 2, 3]:
                    rank_to_name[r] = name
            except: pass
        if len(rank_to_name) == 3:
            key = (rank_to_name[1], rank_to_name[2], rank_to_name[3])
            if key in pattern_counts:
                pattern_counts[key] += 1

    pattern_rows = []
    for (n1, n2, n3), cnt in sorted(pattern_counts.items(), key=lambda x: -x[1]):
        if total > 0:
            pattern_rows.append({
                "🥇 1着": n1, "🥈 2着": n2, "🥉 3着": n3,
                "回数": cnt,
                "割合": f"{cnt/total*100:.1f}%",
            })
    st.dataframe(pd.DataFrame(pattern_rows), hide_index=True, use_container_width=True)

    # 試合一覧
    st.divider()
    section_title("📋", "同卓した試合一覧")
    df_show = df_vs.sort_values("日時Obj", ascending=False).copy()
    df_show["日付"] = df_show["日時Obj"].dt.strftime("%Y-%m-%d %H:%M")
    df_show = df_show[["日付", "TableNo", "SetNo", "Aさん", "A着順", "Bさん", "B着順", "Cさん", "C着順", "備考"]]
    df_show = df_show.rename(columns={"TableNo": "卓", "SetNo": "セット"})
    st.dataframe(df_show, hide_index=True, use_container_width=True, height=400)


def _page_history_overview(df):
    """期間統計と詳細検索 (元のpage_historyの処理)"""
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

    section_title("📈", "期間別統計")

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
            with st.expander("💰 利益集計", expanded=False):
                cp1, cp2 = st.columns(2)
                cp1.metric("MIX差 合計", f"{sum_mix:,}")
                cp2.metric("実利益 合計", f"{sum_real:,}")

        with st.expander("📊 卓組構成・タイプ別・席別成績", expanded=False):
            st.caption(f"卓組構成の割合 ({start} 〜 {end})")
            df_pattern = pd.DataFrame({"構成": list(pattern_counts.keys()), "回数": list(pattern_counts.values())})
            total_p = df_pattern["回数"].sum()
            df_pattern["割合"] = (df_pattern["回数"] / total_p * 100).map('{:.1f}%'.format) if total_p > 0 else "0.0%"
            win_rates = []
            for k in df_pattern["構成"]:
                cnt = pattern_counts[k]
                wins_a = pattern_wins_a[k]
                if k in ["A2人B1人", "A1人B2人"] and cnt > 0:
                    win_rates.append(f"A: {wins_a/cnt*100:.1f}% / B: {(cnt-wins_a)/cnt*100:.1f}%")
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
                stats_by_type["avg"] = stats_by_type["avg"].map('{:.3f}'.format)
                stats_by_type["1着"] = stats_by_type.apply(lambda x: f"{x['r1']} ({x['r1']/x['games']*100:.2f}%)", axis=1)
                stats_by_type["2着"] = stats_by_type.apply(lambda x: f"{x['r2']} ({x['r2']/x['games']*100:.2f}%)", axis=1)
                stats_by_type["3着"] = stats_by_type.apply(lambda x: f"{x['r3']} ({x['r3']/x['games']*100:.2f}%)", axis=1)
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
                        "席": f"{s}席", "打数": c, "平均着順": f"{avg:.3f}",
                        "1着": f"{d['1']} ({d['1']/c*100:.2f}%)",
                        "2着": f"{d['2']} ({d['2']/c*100:.2f}%)",
                        "3着": f"{d['3']} ({d['3']/c*100:.2f}%)"
                    })
            if seat_rows:
                st.markdown("##### 🪑 席別成績")
                st.dataframe(pd.DataFrame(seat_rows), hide_index=True, use_container_width=True)

    st.divider()

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

    section_title("🔍", "詳細検索")
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

    section_title("📅", "選択期間の集計")
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

    with st.expander("📋 卓組構成", expanded=False):
        df_pattern = pd.DataFrame({"構成": list(pattern_counts.keys()), "回数": list(pattern_counts.values())})
        total = df_pattern["回数"].sum()
        df_pattern["割合"] = (df_pattern["回数"] / total * 100).map('{:.1f}%'.format) if total > 0 else "0.0%"
        win_rates = []
        for k in df_pattern["構成"]:
            cnt = pattern_counts[k]
            wins_a = pattern_wins_a[k]
            if k in ["A2人B1人", "A1人B2人"] and cnt > 0:
                win_rates.append(f"A: {wins_a/cnt*100:.1f}% / B: {(cnt-wins_a)/cnt*100:.1f}%")
            else:
                win_rates.append("-")
        df_pattern["勝率"] = win_rates
        st.dataframe(df_pattern, hide_index=True, use_container_width=True)
    st.divider()

    if active_player != "(指定なし)":
        section_title("👤", f"{active_player} さんの成績")
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
            top_rate = c1_cnt / games * 100
            last_avoid = (games - c3_cnt) / games * 100

            stats_html = f"""
            <table class="stats-table">
                <thead><tr>
                    <th>総回数</th><th>平均着順</th><th>トップ率</th><th>ラス回避率</th>
                    <th>🥇 1着</th><th>🥈 2着</th><th>🥉 3着</th>
                </tr></thead>
                <tbody><tr>
                    <td>{games} 回</td>
                    <td style="color:var(--accent)">{avg:.3f}</td>
                    <td style="color:var(--green)">{top_rate:.3f}%</td>
                    <td style="color:var(--blue)">{last_avoid:.3f}%</td>
                    <td>{c1_cnt}<span class="stats-sub">{c1_cnt/games*100:.2f}%</span></td>
                    <td>{c2_cnt}<span class="stats-sub">{c2_cnt/games*100:.2f}%</span></td>
                    <td>{c3_cnt}<span class="stats-sub">{c3_cnt/games*100:.2f}%</span></td>
                </tr></tbody>
            </table>
            """
            st.markdown(stats_html, unsafe_allow_html=True)

            with st.expander("🪑 席別成績", expanded=False):
                p_seat_rows = []
                for s in ["A", "B", "C"]:
                    rs = player_seat_ranks[s]
                    c = len(rs)
                    if c > 0:
                        p_seat_rows.append({
                            "席": f"{s}席", "打数": c, "平均着順": f"{sum(rs)/c:.3f}",
                            "1着": f"{rs.count(1)} ({rs.count(1)/c*100:.2f}%)",
                            "2着": f"{rs.count(2)} ({rs.count(2)/c*100:.2f}%)",
                            "3着": f"{rs.count(3)} ({rs.count(3)/c*100:.2f}%)"
                        })
                if p_seat_rows:
                    st.dataframe(pd.DataFrame(p_seat_rows), hide_index=True, use_container_width=True)

            st.divider()
            c_graph, c_dates = st.columns([2, 1])
            with c_graph:
                section_title("📈", "直近20戦の着順推移")
                recent_ranks = ranks[-20:]
                df_trend = pd.DataFrame({"戦数": range(1, len(recent_ranks) + 1), "着順": recent_ranks})
                if len(recent_ranks) >= 5:
                    df_trend["移動平均(5戦)"] = df_trend["着順"].rolling(window=5, min_periods=1).mean()

                base = alt.Chart(df_trend).encode(
                    x=alt.X("戦数", axis=alt.Axis(tickMinStep=1), title="直近ゲーム"),
                )
                line_main = base.mark_line(
                    point=alt.OverlayMarkDef(color="#f0c040", size=80),
                    color="#f0c040", strokeWidth=2
                ).encode(
                    y=alt.Y("着順", scale=alt.Scale(domain=[3.3, 0.7]), title="着順"),
                    tooltip=["戦数", "着順"]
                )
                chart = line_main
                if "移動平均(5戦)" in df_trend.columns:
                    line_avg = base.mark_line(
                        color="#5b9cf6", strokeWidth=1.5, strokeDash=[5, 3]
                    ).encode(
                        y=alt.Y("移動平均(5戦)"),
                        tooltip=["戦数", alt.Tooltip("移動平均(5戦)", format=".3f")]
                    )
                    chart = alt.layer(line_main, line_avg)

                chart = chart.properties(height=280).configure_view(
                    strokeWidth=0, fill="#1a1d2e"
                ).configure_axis(
                    gridColor="#2a2d3e", labelColor="#8890a8", titleColor="#8890a8"
                )
                st.altair_chart(chart, use_container_width=True)
                if "移動平均(5戦)" in df_trend.columns:
                    st.caption("🟡 着順  /  🔵 5戦移動平均")
            with c_dates:
                section_title("📅", "稼働日")
                date_list = sorted(list(played_dates), reverse=True)
                st.dataframe(pd.DataFrame(date_list, columns=["日付"]), hide_index=True, use_container_width=True, height=300)

        if compatibility:
            st.divider()
            section_title("🤝", "対戦相手データ (TOP5)")
            comp_data = [{"名前": n, "同卓回数": d["count"], "相性スコア": d["score"]} for n, d in compatibility.items()]
            df_comp = pd.DataFrame(comp_data)
            c_freq, c_good, c_bad = st.columns(3)
            with c_freq:
                st.markdown("**👬 同卓回数**")
                st.dataframe(df_comp.sort_values("同卓回数", ascending=False).head(5).reset_index(drop=True)[["名前", "同卓回数"]], hide_index=True, use_container_width=True)
            with c_good:
                st.markdown("**💖 相性が良い**")
                st.dataframe(df_comp.sort_values("相性スコア", ascending=False).head(5).reset_index(drop=True)[["名前", "相性スコア"]], hide_index=True, use_container_width=True)
            with c_bad:
                st.markdown("**💀 相性が悪い**")
                st.dataframe(df_comp.sort_values("相性スコア", ascending=True).head(5).reset_index(drop=True)[["名前", "相性スコア"]], hide_index=True, use_container_width=True)

        st.divider()
        with st.expander("🀄 個人記録の更新", expanded=False):
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
        section_title("📝", "集計表")
        render_paper_sheet(df_filtered)

# --- 月間成績画面 ---
def page_monthly():
    render_top_nav("monthly")
    st.title("📅 月間ランキングPT")
    render_pending_bar(location_key="monthly")

    # 集計内容を視覚的に明記するパネル
    st.markdown("""
    <div class="rankpt-info-panel">
        <div class="rankpt-section">
            <div class="rankpt-section-title">📋 集計対象の8項目 (その月だけのデータで計算)</div>
            <div class="rankpt-items">
                <span class="rankpt-item">📊 打数</span>
                <span class="rankpt-item">🥇 平均着順</span>
                <span class="rankpt-item">👑 トップ率</span>
                <span class="rankpt-item">🛡 ラス回避率</span>
                <span class="rankpt-item">🔥 最長連勝</span>
                <span class="rankpt-item">🛡️ 最長連続ラス回避</span>
                <span class="rankpt-item">⭐ 5連勝以上回数</span>
                <span class="rankpt-item">🌟 ベスト100半荘</span>
            </div>
        </div>
        <div class="rankpt-divider"></div>
        <div class="rankpt-section">
            <div class="rankpt-section-title">💎 順位別ポイント</div>
            <div class="rankpt-pts">
                <span class="rankpt-pt pt-gold">🥇 1位 <strong>10pt</strong></span>
                <span class="rankpt-pt pt-silver">🥈 2位 <strong>7pt</strong></span>
                <span class="rankpt-pt pt-bronze">🥉 3位 <strong>5pt</strong></span>
                <span class="rankpt-pt">4位 <strong>3pt</strong></span>
                <span class="rankpt-pt">5位 <strong>2pt</strong></span>
                <span class="rankpt-pt">6〜10位 <strong>1pt</strong></span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.caption("月内 **10戦以上** のプレイヤーが対象。お客さん/スタッフは別々に集計。")

    # 現在の月と過去の月を全て取得
    with st.spinner("月間ランキングPT総合を集計中..."):
        monthly_result = compute_monthly_ranking_points(min_games=10, top_n=3)

    all_months = monthly_result.get("months", [])
    monthly_data = monthly_result.get("data", {})

    if not all_months:
        st.info("集計できる対局データがありません")
        return

    # --- 今月の表示 (詳細版: TOP20) ---
    latest_month = all_months[0]
    st.markdown(f"## 🌟 今月({latest_month})のランキングPT")

    with st.spinner(f"{latest_month}の詳細ランキングを計算中..."):
        # 今月分だけTOP20まで表示
        ym_period = pd.Period(latest_month, freq="M")
        latest_full = compute_ranking_points_all(
            min_games=10,
            from_dt=pd.Timestamp(ym_period.start_time),
            until_dt=pd.Timestamp(ym_period.end_time),
        )

    c1, c2 = st.columns(2)
    for col_obj, cat_key, title, icon in [(c1, "guest", "お客さん", "🧑‍🤝‍🧑"),
                                            (c2, "staff", "スタッフ", "👔")]:
        with col_obj:
            st.markdown(f"### {icon} {title} 今月Top20")
            cat_data = latest_full.get(cat_key, [])
            if not cat_data:
                st.info("今月の対局データがありません")
                continue

            top20 = cat_data[:20]
            rank_medals = {1: "🥇", 2: "🥈", 3: "🥉"}
            for i, entry in enumerate(top20):
                pos = i + 1
                medal = rank_medals.get(pos, f"{pos}")
                label = f"{medal}　{entry['name']}　—　{entry['total_pt']}pt"
                with st.expander(label, expanded=False):
                    render_rankpt_breakdown(entry["breakdown"])

    st.divider()

    # --- 過去の月間TOP3 ---
    past_months = all_months[1:]  # 今月以外
    if not past_months:
        st.info("過去のランキングPTはまだありません(今月が最初の月です)")
        return

    st.markdown(f"## 📜 過去のランキングPT TOP3 ({len(past_months)}ヶ月分)")
    st.caption("各月のTOP3。名前をクリックすると、その月に何の項目で何位だったかの内訳が見られます。")

    # 過去月を新しい順に表示 (現在は新しい順)
    for ym_str in past_months:
        top3 = monthly_data.get(ym_str, {})
        guest_top = top3.get("guest", [])
        staff_top = top3.get("staff", [])

        # 月の表示名
        try:
            ym_period = pd.Period(ym_str, freq="M")
            month_display = ym_period.strftime("%Y年%m月")
        except:
            month_display = ym_str

        with st.container():
            st.markdown(f"### 📆 {month_display}")

            mc1, mc2 = st.columns(2)
            rank_medals = {1: "🥇", 2: "🥈", 3: "🥉"}

            for col_obj, cat_data, title, icon in [(mc1, guest_top, "お客さん", "🧑‍🤝‍🧑"),
                                                     (mc2, staff_top, "スタッフ", "👔")]:
                with col_obj:
                    st.markdown(f"**{icon} {title}**")
                    if not cat_data:
                        st.markdown('<div style="color:var(--text-muted);font-size:0.85rem;padding:0.4rem 0;">— データなし —</div>', unsafe_allow_html=True)
                        continue
                    # 各プレイヤーをexpanderで表示 (クリックで内訳)
                    for i, entry in enumerate(cat_data):
                        pos = i + 1
                        medal = rank_medals.get(pos, f"{pos}")
                        label = f"{medal}　{entry['name']}　—　{entry['total_pt']}pt"
                        with st.expander(label, expanded=False):
                            render_rankpt_breakdown(entry["breakdown"])

            st.markdown("<div style='height:0.6rem;'></div>", unsafe_allow_html=True)


# --- ランキング画面 ---
def page_ranking():
    render_top_nav("ranking")
    st.title("🏆 ランキング")
    render_pending_bar(location_key="ranking")

    df = load_score_data_effective()
    if df.empty:
        st.info("データがありません")
        return

    valid_dates = pd.to_datetime(df["論理日付"]).dropna()
    if not valid_dates.empty:
        min_date = valid_dates.min().date()
        max_date = valid_dates.max().date()
    else:
        min_date = max_date = date.today()

    df_tmp = df.copy()
    df_tmp["年月"] = df_tmp["日時Obj"].dt.to_period("M")
    available_months = sorted(df_tmp["年月"].dropna().unique(), reverse=True)
    month_labels = ["全期間", "カスタム期間"] + [str(m) for m in available_months]

    c1, c2 = st.columns([2, 1])
    with c1:
        selected_period = st.selectbox("📅 集計期間", month_labels, index=0, key="ranking_period")
    with c2:
        min_games = st.number_input("規定打数", min_value=1, value=100, help="これ未満は非表示")

    if selected_period == "カスタム期間":
        date_range = st.date_input("📅 期間を指定", value=(min_date, max_date), min_value=min_date, max_value=max_date, key="ranking_custom_date")
        if isinstance(date_range, tuple) and len(date_range) == 2:
            start_d, end_d = date_range
            mask = (df["論理日付"] >= start_d) & (df["論理日付"] <= end_d)
            df_filtered = df[mask]
        else:
            df_filtered = df
    elif selected_period == "全期間":
        df_filtered = df
    else:
        df_filtered = df_tmp[df_tmp["年月"].astype(str) == selected_period]
        df_filtered = df_filtered.drop(columns=["年月"], errors="ignore")

    if df_filtered.empty:
        st.warning("指定された期間のデータはありません")
        return

    records = []
    for _, row in df_filtered.iterrows():
        for seat in ["A", "B", "C"]:
            name = row[f"{seat}さん"]
            rank = row[f"{seat}着順"]
            player_type = row.get(f"{seat}タイプ", "")
            if name:
                try: r = int(float(rank))
                except: r = 0
                if r > 0:
                    records.append({
                        "name": name, "rank": r, "date": row["論理日付"],
                        "dt": row.get("日時Obj", pd.Timestamp("1900-01-01")),
                        "game_no": row.get("GameNo", 0),
                        "player_type": str(player_type) if player_type else "",
                        "seat": seat,  # A/B/C 席情報
                    })

    if not records:
        st.warning("集計できるデータがありません")
        return

    df_raw = pd.DataFrame(records)

    # --- 連続系ストリークを計算 (時系列で並べて算出) ---
    def compute_streaks(group):
        """1プレイヤーの時系列着順から連続系指標を算出"""
        # 時系列で並べる
        g = group.sort_values(["dt", "game_no"])
        ranks = g["rank"].tolist()

        max_win_streak = 0        # 最長連勝(1着連続)
        max_last_streak = 0       # 最長連続ラス(3着連続)
        max_second_streak = 0     # 最長連続2着
        max_last_avoid_streak = 0 # 最長連続ラス回避(1着or2着が連続)
        max_no_top_streak = 0     # 最長連続トップ無し(2着or3着が連続、= 1着を取れなかった連続)
        four_win_count = 0        # 4連勝以上の達成回数
        five_win_count = 0        # 5連勝以上の達成回数
        second_total = ranks.count(2)

        # 連勝確率(トップを取った直後の半荘でトップを取った確率)
        # 分母: トップを取った試合 (ただし最終試合を除く=直後の試合がある)
        # 分子: 直後の試合でもトップを取った数
        top_after_top_denominator = 0
        top_after_top_numerator = 0
        # 連続2着率(2着の直後の半荘で2着を取った確率)
        second_after_second_denominator = 0
        second_after_second_numerator = 0
        # 連続ラス率(3着の直後の半荘で3着を取った確率)
        last_after_last_denominator = 0
        last_after_last_numerator = 0
        for i in range(len(ranks) - 1):  # 最終試合は「次」がないので除外
            cur_r = ranks[i]
            next_r = ranks[i + 1]
            if cur_r == 1:
                top_after_top_denominator += 1
                if next_r == 1:
                    top_after_top_numerator += 1
            elif cur_r == 2:
                second_after_second_denominator += 1
                if next_r == 2:
                    second_after_second_numerator += 1
            elif cur_r == 3:
                last_after_last_denominator += 1
                if next_r == 3:
                    last_after_last_numerator += 1
        top_after_top_rate = (
            (top_after_top_numerator / top_after_top_denominator * 100)
            if top_after_top_denominator > 0 else None
        )
        second_after_second_rate = (
            (second_after_second_numerator / second_after_second_denominator * 100)
            if second_after_second_denominator > 0 else None
        )
        last_after_last_rate = (
            (last_after_last_numerator / last_after_last_denominator * 100)
            if last_after_last_denominator > 0 else None
        )

        cur_win = cur_last = cur_second = 0
        cur_last_avoid = 0  # 現在の連続ラス回避 (1 or 2)
        cur_no_top = 0      # 現在の連続トップ無し (2 or 3)

        for r in ranks:
            # --- 1着/2着/3着の連続系 ---
            if r == 1:
                cur_win += 1
                cur_last = cur_second = 0
                if cur_win == 4:  # 4連勝到達時点でカウント (1つの連勝ストリークで1回)
                    four_win_count += 1
                if cur_win == 5:  # 5連勝到達時点でカウント
                    five_win_count += 1
            elif r == 2:
                cur_second += 1
                cur_win = cur_last = 0
            elif r == 3:
                cur_last += 1
                cur_win = cur_second = 0
            else:
                cur_win = cur_last = cur_second = 0

            if cur_win > max_win_streak: max_win_streak = cur_win
            if cur_last > max_last_streak: max_last_streak = cur_last
            if cur_second > max_second_streak: max_second_streak = cur_second

            # --- 連続ラス回避 (1 or 2 が続く) ---
            if r in (1, 2):
                cur_last_avoid += 1
                if cur_last_avoid > max_last_avoid_streak:
                    max_last_avoid_streak = cur_last_avoid
            else:
                cur_last_avoid = 0

            # --- 連続トップ無し (2 or 3 が続く = 1着を取れなかった連続) ---
            if r in (2, 3):
                cur_no_top += 1
                if cur_no_top > max_no_top_streak:
                    max_no_top_streak = cur_no_top
            else:
                cur_no_top = 0

        return pd.Series({
            "max_win_streak": max_win_streak,
            "max_last_streak": max_last_streak,
            "max_second_streak": max_second_streak,
            "max_last_avoid_streak": max_last_avoid_streak,
            "max_no_top_streak": max_no_top_streak,
            "four_win_count": four_win_count,
            "five_win_count": five_win_count,
            "second_count": second_total,
            "top_after_top_rate": top_after_top_rate,
            "top_after_top_samples": top_after_top_denominator,
            "second_after_second_rate": second_after_second_rate,
            "second_after_second_samples": second_after_second_denominator,
            "last_after_last_rate": last_after_last_rate,
            "last_after_last_samples": last_after_last_denominator,
        })

    streaks = df_raw.groupby("name", group_keys=False).apply(compute_streaks).reset_index()

    # --- 連続100半荘の最高成績を計算 (スライディングウィンドウ) ---
    WINDOW_SIZE = 100
    def compute_best_window(group):
        """1プレイヤーの時系列着順から、連続100半荘の最良成績ウィンドウを算出"""
        g = group.sort_values(["dt", "game_no"]).reset_index(drop=True)
        n = len(g)
        if n < WINDOW_SIZE:
            return pd.Series({
                "best100_avg": None,
                "best100_first": 0,
                "best100_second": 0,
                "best100_third": 0,
                "best100_top_rate": None,
                "best100_start_dt": None,
                "best100_end_dt": None,
                "best100_start_idx": 0,  # プレイヤー内での通し番号 (何戦目〜何戦目か)
                "best100_end_idx": 0,
            })
        ranks = g["rank"].tolist()
        dts = g["dt"].tolist()

        # スライディングウィンドウで平均着順を計算
        # 累積和で高速化 (O(n))
        window_sum = sum(ranks[:WINDOW_SIZE])
        best_avg = window_sum / WINDOW_SIZE
        best_start = 0
        for i in range(1, n - WINDOW_SIZE + 1):
            window_sum += ranks[i + WINDOW_SIZE - 1] - ranks[i - 1]
            avg = window_sum / WINDOW_SIZE
            if avg < best_avg:  # 平均着順は小さいほど良い
                best_avg = avg
                best_start = i

        best_end = best_start + WINDOW_SIZE - 1
        window_ranks = ranks[best_start:best_end + 1]
        return pd.Series({
            "best100_avg": best_avg,
            "best100_first": window_ranks.count(1),
            "best100_second": window_ranks.count(2),
            "best100_third": window_ranks.count(3),
            "best100_top_rate": window_ranks.count(1) / WINDOW_SIZE * 100,
            "best100_start_dt": dts[best_start],
            "best100_end_dt": dts[best_end],
            "best100_start_idx": best_start + 1,  # 1-indexed
            "best100_end_idx": best_end + 1,
        })

    best_windows = df_raw.groupby("name", group_keys=False).apply(compute_best_window).reset_index()

    stats = df_raw.groupby("name").agg(
        games=("rank", "count"),
        avg_rank=("rank", "mean"),
        first_count=("rank", lambda x: (x==1).sum()),
        third_count=("rank", lambda x: (x==3).sum()),
        days=("date", "nunique")
    ).reset_index()
    # ストリーク統計をマージ
    stats = stats.merge(streaks, on="name", how="left")
    # 連続100半荘最高成績をマージ
    stats = stats.merge(best_windows, on="name", how="left")

    # --- タイプ別平均着順(A客/AS/B客/BS)を集計してマージ ---
    for target_type in ["A客", "AS", "B客", "BS"]:
        df_type = df_raw[df_raw["player_type"] == target_type]
        if not df_type.empty:
            type_stats = df_type.groupby("name").agg(
                **{
                    f"avg_rank_{target_type}": ("rank", "mean"),
                    f"games_{target_type}": ("rank", "count"),
                }
            ).reset_index()
            stats = stats.merge(type_stats, on="name", how="left")
        else:
            stats[f"avg_rank_{target_type}"] = None
            stats[f"games_{target_type}"] = 0

    # --- 席別平均着順(A/B/C席)を集計してマージ ---
    for seat_key in ["A", "B", "C"]:
        df_seat = df_raw[df_raw["seat"] == seat_key]
        if not df_seat.empty:
            seat_stats = df_seat.groupby("name").agg(
                **{
                    f"avg_rank_seat_{seat_key}": ("rank", "mean"),
                    f"games_seat_{seat_key}": ("rank", "count"),
                }
            ).reset_index()
            stats = stats.merge(seat_stats, on="name", how="left")
        else:
            stats[f"avg_rank_seat_{seat_key}"] = None
            stats[f"games_seat_{seat_key}"] = 0

    stats["games_per_day"] = stats["games"] / stats["days"]
    stats["top_rate"] = (stats["first_count"] / stats["games"]) * 100
    stats["second_rate"] = (stats["second_count"] / stats["games"]) * 100
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
                st.markdown(f"#### {icon} {title} Top20")
                if not df_r.empty:
                    # 同率順位で順位付けしてから上位20を抽出
                    ranked = assign_competition_rank(df_r, sort_col, ascending=asc)
                    res = ranked[ranked["順位"] <= 20].reset_index(drop=True)
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
                                "avg_rank": "平均着順", "top_rate": "トップ率",
                                "second_rate": "2着率", "last_avoid_rate": "ラス回避率",
                                "max_win_streak": "最長連勝",
                                "max_last_streak": "最長連続ラス",
                                "max_second_streak": "最長連続2着",
                                "max_last_avoid_streak": "最長連続ラス回避",
                                "max_no_top_streak": "最長連続トップ無し",
                                "four_win_count": "4連勝以上回数",
                                "five_win_count": "5連勝以上回数",
                                "top_after_top_rate": "連勝確率",
                                "avg_rank_A客": "平均着順(A客)",
                                "avg_rank_AS": "平均着順(AS)",
                                "avg_rank_B客": "平均着順(B客)",
                                "avg_rank_BS": "平均着順(BS)",
                                "avg_rank_seat_A": "平均着順(A席)",
                                "avg_rank_seat_B": "平均着順(B席)",
                                "avg_rank_seat_C": "平均着順(C席)"}
                    st.dataframe(res[cols].rename(columns=rmap), hide_index=True, use_container_width=True)
                else:
                    st.info("データなし")

    t1, t2, t3, t4, t5, t6, t7, t8, t9, t10, t11, t12, t13, t14, t15, t16, t17, t18, t19, t20, t21, t22, t23 = st.tabs([
        "🏆 ランキングPT総合",
        "🏅 レーティング", "🎖️ 段位",
        "📊 打数", "🥇 平均着順", "🎯 平均着順(ルール別)", "💺 平均着順(席別)",
        "👑 トップ率", "🥈 2着率", "🛡 ラス回避率",
        "🔥 最長連勝", "💀 最長連続ラス", "😐 最長連続2着",
        "🛡️ 最長連続ラス回避", "😑 最長連続トップ無し",
        "✨ 4連勝以上回数", "⭐ 5連勝以上回数",
        "🔁 連勝確率", "🔄 連続2着率", "☠️ 連続ラス率",
        "🌟 ベスト100半荘",
        "💥 最大飜数", "🀅 役満回数"
    ])

    # ---- レーティング/段位用の統計データを準備 (全期間版・キャプション用) ----
    # 実際の表示は各タブ内で期間指定に応じて再計算する

    def build_rating_stats(until_dt_iso=None, from_dt_iso=None):
        """指定期間のレーティングデータを準備し、guest/staffに分けて返す"""
        df_r = load_ratings_effective(until_dt_iso=until_dt_iso, from_dt_iso=from_dt_iso)
        if df_r.empty:
            return pd.DataFrame(), pd.DataFrame()
        df_r_clean = df_r.copy()
        df_r_clean["name"] = df_r_clean["名前"].astype(str).str.replace(r'[（\(].*?[）\)]', '', regex=True)
        st_r = df_r_clean[["name", "レート", "対局数", "段位名", "段位色", "段位Index", "段位pt", "昇段まで"]].copy()
        st_r = st_r.rename(columns={"対局数": "games"})
        st_r["type"] = st_r["name"].apply(lambda x: "staff" if str(x).lower().endswith("s") else "guest")
        g = st_r[(st_r["type"] == "guest") & (st_r["games"] >= min_games)]
        s = st_r[(st_r["type"] == "staff") & (st_r["games"] >= min_games)]
        return g, s

    def rating_period_selector(key_suffix):
        """
        期間指定UI: 3モード
          1. 全期間 (現時点までの累積) - デフォルト
          2. ある月末時点までの累積レート
          3. 選択した月(複数選択可)の対局だけを集計 (その月/月々の成績)
        Returns: (until_dt_iso, from_dt_iso) のタプル
        """
        # スコアデータから利用可能な年月を取得
        df_all = load_score_data_effective()
        available_months_list = []
        if not df_all.empty and "日時Obj" in df_all.columns:
            df_tmp = df_all[df_all["日時Obj"].notna() & (df_all["日時Obj"] != pd.Timestamp("1900-01-01"))].copy()
            df_tmp["年月"] = df_tmp["日時Obj"].dt.to_period("M")
            available_months_list = sorted(df_tmp["年月"].dropna().unique(), reverse=True)

        c1_, c2_ = st.columns([1, 2])
        with c1_:
            mode = st.radio(
                "📅 集計モード",
                ["全期間 (累積)", "月末時点 (累積)", "月別 (選択月のみ)"],
                key=f"rating_mode_{key_suffix}",
                horizontal=False,
                label_visibility="collapsed",
            )
            st.caption(
                "**全期間**: 現時点までの累積レート\n\n"
                "**月末時点**: 選んだ月末までの累積レート\n\n"
                "**月別**: 選んだ月(複数選択可)の対局だけで再計算"
            )

        with c2_:
            if mode == "全期間 (累積)":
                st.markdown("_全期間の累積で計算します_")
                return (None, None)

            elif mode == "月末時点 (累積)":
                if not available_months_list:
                    st.info("対局データがありません")
                    return (None, None)
                month_labels = [f"{m}" for m in available_months_list]
                selected = st.selectbox(
                    "🕐 何月末時点までを集計するか",
                    month_labels,
                    key=f"rating_month_end_{key_suffix}",
                )
                try:
                    period = pd.Period(selected, freq="M")
                    until_iso = period.end_time.isoformat()
                    return (until_iso, None)
                except:
                    return (None, None)

            elif mode == "月別 (選択月のみ)":
                if not available_months_list:
                    st.info("対局データがありません")
                    return (None, None)
                month_labels = [f"{m}" for m in available_months_list]
                selected_months = st.multiselect(
                    "📆 集計する月を選択 (複数可)",
                    month_labels,
                    default=[month_labels[0]] if month_labels else [],
                    key=f"rating_months_multi_{key_suffix}",
                    help="複数選択した場合、それらの月に絞ったデータで再計算します。連続していない月でもOKです。",
                )
                if not selected_months:
                    st.warning("月を1つ以上選択してください")
                    return (None, None)

                # 選ばれた月をPeriodに変換
                selected_periods = []
                for lbl in selected_months:
                    try:
                        selected_periods.append(pd.Period(lbl, freq="M"))
                    except:
                        pass
                if not selected_periods:
                    return (None, None)

                # 選んだ月群の最も古い月の初日〜最新月の月末を「範囲」として指定
                # ただし途中の月を除外する場合、単純な from/until では絞りきれない
                # → 特別な戻り値 (list of periods) にして、compute側で判定する
                # ここでは代替として、範囲だけを返し、途中の月除外は compute 側で対応することにする
                sorted_periods = sorted(selected_periods)
                from_iso = sorted_periods[0].start_time.isoformat()
                until_iso = sorted_periods[-1].end_time.isoformat()

                # 選択月が「連続」しているかチェック。連続なら普通に区間指定でOK。
                # 不連続なら「選択月のみ」フィルタが必要になるので別処理
                all_between = pd.period_range(sorted_periods[0], sorted_periods[-1], freq="M")
                if len(all_between) == len(sorted_periods):
                    # 連続している - 単純な区間指定
                    st.markdown(f"📊 **{sorted_periods[0]} 〜 {sorted_periods[-1]}** の期間で計算")
                    return (until_iso, from_iso)
                else:
                    # 不連続 - 特別処理: 選択月をセッションに保存して build 側で使う
                    st.markdown(f"📊 選択された **{len(selected_periods)}ヶ月分** で計算 (不連続選択)")
                    st.session_state[f"_rating_selected_periods_{key_suffix}"] = [str(p) for p in sorted_periods]
                    return ("__MULTI__", key_suffix)

        return (None, None)

    def build_rating_stats_with_periods(period_result):
        """
        period_result: rating_period_selector の戻り値 (until_iso, from_iso)
                       until_iso="__MULTI__" の場合は from_iso が key_suffix となる
        """
        until_iso, from_iso = period_result
        if until_iso == "__MULTI__":
            # 不連続月選択: セッションから選択月リストを取得し、それらの月のデータだけで計算
            key_suffix = from_iso
            selected_period_strs = st.session_state.get(f"_rating_selected_periods_{key_suffix}", [])
            if not selected_period_strs:
                return pd.DataFrame(), pd.DataFrame()

            # 対局データを月フィルタしてから計算
            df_all = load_score_data_effective()
            if df_all.empty or "日時Obj" not in df_all.columns:
                return pd.DataFrame(), pd.DataFrame()

            df_all = df_all[df_all["日時Obj"].notna()]
            df_all = df_all.copy()
            df_all["_ym"] = df_all["日時Obj"].dt.to_period("M").astype(str)
            df_filtered = df_all[df_all["_ym"].isin(selected_period_strs)]

            if df_filtered.empty:
                return pd.DataFrame(), pd.DataFrame()

            ratings = compute_ratings_from_scratch(df_filtered)
            df_r = ratings_dict_to_df(ratings)
            if df_r.empty:
                return pd.DataFrame(), pd.DataFrame()

            df_r_clean = df_r.copy()
            df_r_clean["name"] = df_r_clean["名前"].astype(str).str.replace(r'[（\(].*?[）\)]', '', regex=True)
            st_r = df_r_clean[["name", "レート", "対局数", "段位名", "段位色", "段位Index", "段位pt", "昇段まで"]].copy()
            st_r = st_r.rename(columns={"対局数": "games"})
            st_r["type"] = st_r["name"].apply(lambda x: "staff" if str(x).lower().endswith("s") else "guest")
            g = st_r[(st_r["type"] == "guest") & (st_r["games"] >= min_games)]
            s = st_r[(st_r["type"] == "staff") & (st_r["games"] >= min_games)]
            return g, s
        else:
            return build_rating_stats(until_dt_iso=until_iso, from_dt_iso=from_iso)

    def show_rating_ranking(df_g, df_s):
        """レーティングランキング (段位バッジ + レートの見せ方)"""
        c1_, c2_ = st.columns(2)
        for col_obj, df_r, title, icon in [(c1_, df_g, "お客さん", "🧑‍🤝‍🧑"), (c2_, df_s, "スタッフ", "👔")]:
            with col_obj:
                st.markdown(f"#### {icon} {title} Top20")
                if not df_r.empty:
                    # レートは表示精度(小数1桁)で同率判定
                    tmp = df_r.copy()
                    tmp["_レート丸め"] = tmp["レート"].round(1)
                    ranked = assign_competition_rank(tmp, "_レート丸め", ascending=False)
                    res = ranked[ranked["順位"] <= 20].reset_index(drop=True)
                    html = '<table class="stats-table" style="width:100%;">'
                    html += """<thead><tr>
                        <th style="width:50px;">順位</th>
                        <th style="text-align:left;">名前</th>
                        <th style="width:70px;">段位</th>
                        <th style="width:90px;">レート</th>
                        <th style="width:60px;">打数</th>
                    </tr></thead><tbody>"""
                    for _, r in res.iterrows():
                        rank_num = int(r["順位"])
                        if rank_num == 1: rank_disp = "🥇 1"
                        elif rank_num == 2: rank_disp = "🥈 2"
                        elif rank_num == 3: rank_disp = "🥉 3"
                        else: rank_disp = str(rank_num)
                        dan_html = render_dan_badge(r["段位名"], r["段位色"], size="small")
                        rate_col = "var(--accent)" if rank_num <= 3 else "var(--text-primary)"
                        html += f'''<tr>
                            <td style="text-align:center;font-weight:800;">{rank_disp}</td>
                            <td style="text-align:left;font-weight:600;">{r["name"]}</td>
                            <td style="text-align:center;">{dan_html}</td>
                            <td style="text-align:center;font-family:'Zen Kaku Gothic New';font-weight:900;color:{rate_col};font-size:1.0rem;">R{r["レート"]:.1f}</td>
                            <td style="text-align:center;color:var(--text-muted);">{int(r["games"])}</td>
                        </tr>'''
                    html += '</tbody></table>'
                    st.markdown(html, unsafe_allow_html=True)
                else:
                    st.info("データなし")

    def show_dan_ranking(df_g, df_s):
        """段位ランキング (段位Index高い順、同段位は段位pt多い順)"""
        c1_, c2_ = st.columns(2)
        for col_obj, df_r, title, icon in [(c1_, df_g, "お客さん", "🧑‍🤝‍🧑"), (c2_, df_s, "スタッフ", "👔")]:
            with col_obj:
                st.markdown(f"#### {icon} {title} Top20")
                if not df_r.empty:
                    # 段位Index・段位pt の複合キーで同率判定
                    # (段位Index, 段位pt) が完全一致なら同順位
                    tmp = df_r.copy()
                    # 複合ソートキーを作る (段位Index * 大きな係数 + 段位pt)
                    # 段位ptが負でも比較できるよう十分大きなオフセット
                    tmp["_段位キー"] = tmp["段位Index"] * 1000000 + tmp["段位pt"]
                    ranked = assign_competition_rank(tmp, "_段位キー", ascending=False)
                    res = ranked[ranked["順位"] <= 20].reset_index(drop=True)
                    html = '<table class="stats-table" style="width:100%;">'
                    html += """<thead><tr>
                        <th style="width:50px;">順位</th>
                        <th style="text-align:left;">名前</th>
                        <th style="width:80px;">段位</th>
                        <th style="width:90px;">段位pt</th>
                        <th style="width:60px;">打数</th>
                    </tr></thead><tbody>"""
                    for _, r in res.iterrows():
                        rank_num = int(r["順位"])
                        if rank_num == 1: rank_disp = "🥇 1"
                        elif rank_num == 2: rank_disp = "🥈 2"
                        elif rank_num == 3: rank_disp = "🥉 3"
                        else: rank_disp = str(rank_num)
                        dan_html = render_dan_badge(r["段位名"], r["段位色"], size="small")
                        up_needed = int(r["昇段まで"])
                        pt_disp = f'{r["段位pt"]:.1f} / {up_needed if up_needed < 999999 else "—"}'
                        html += f'''<tr>
                            <td style="text-align:center;font-weight:800;">{rank_disp}</td>
                            <td style="text-align:left;font-weight:600;">{r["name"]}</td>
                            <td style="text-align:center;">{dan_html}</td>
                            <td style="text-align:center;color:{r["段位色"]};font-weight:700;">{pt_disp}</td>
                            <td style="text-align:center;color:var(--text-muted);">{int(r["games"])}</td>
                        </tr>'''
                    html += '</tbody></table>'
                    st.markdown(html, unsafe_allow_html=True)
                else:
                    st.info("データなし")

    # --- t1: ランキングPT総合 ---
    with t1:
        # 集計内容を視覚的に明記するパネル
        st.markdown("""
        <div class="rankpt-info-panel">
            <div class="rankpt-section">
                <div class="rankpt-section-title">📋 集計対象の8項目</div>
                <div class="rankpt-items">
                    <span class="rankpt-item">📊 打数</span>
                    <span class="rankpt-item">🥇 平均着順</span>
                    <span class="rankpt-item">👑 トップ率</span>
                    <span class="rankpt-item">🛡 ラス回避率</span>
                    <span class="rankpt-item">🔥 最長連勝</span>
                    <span class="rankpt-item">🛡️ 最長連続ラス回避</span>
                    <span class="rankpt-item">⭐ 5連勝以上回数</span>
                    <span class="rankpt-item">🌟 ベスト100半荘</span>
                </div>
            </div>
            <div class="rankpt-divider"></div>
            <div class="rankpt-section">
                <div class="rankpt-section-title">💎 順位別ポイント</div>
                <div class="rankpt-pts">
                    <span class="rankpt-pt pt-gold">🥇 1位 <strong>10pt</strong></span>
                    <span class="rankpt-pt pt-silver">🥈 2位 <strong>7pt</strong></span>
                    <span class="rankpt-pt pt-bronze">🥉 3位 <strong>5pt</strong></span>
                    <span class="rankpt-pt">4位 <strong>3pt</strong></span>
                    <span class="rankpt-pt">5位 <strong>2pt</strong></span>
                    <span class="rankpt-pt">6〜10位 <strong>1pt</strong></span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.caption("上の10項目それぞれで順位を判定し、獲得ポイントを合計します。お客さん/スタッフは別々に集計。")

        with st.spinner("全ランキング項目のポイントを集計中..."):
            pt_result = compute_ranking_points_all(min_games=min_games)

        c1_pt, c2_pt = st.columns(2)
        for col_obj, cat_key, title, icon in [(c1_pt, "guest", "お客さん", "🧑‍🤝‍🧑"),
                                                (c2_pt, "staff", "スタッフ", "👔")]:
            with col_obj:
                st.markdown(f"#### {icon} {title} Top20")
                cat_data = pt_result.get(cat_key, [])
                if not cat_data:
                    st.info("データなし")
                    continue

                # 上位20位を expander で表示 (クリックで内訳展開)
                top20 = cat_data[:20]
                rank_medals = {1: "🥇", 2: "🥈", 3: "🥉"}
                for i, entry in enumerate(top20):
                    pos = i + 1
                    medal = rank_medals.get(pos, f"{pos}")
                    # expander のラベル: 順位 名前 合計pt
                    label = f"{medal}　{entry['name']}　—　{entry['total_pt']}pt"
                    # 上位3位はデフォルトで展開
                    with st.expander(label, expanded=False):
                        render_rankpt_breakdown(entry["breakdown"])

        # 集計条件の補足説明
        with st.expander("ℹ️ 集計条件の詳細", expanded=False):
            st.markdown(f"""
            **各項目の集計条件**:

            | 項目 | ソート | 集計条件 |
            |---|---|---|
            | 📊 打数 | 多い順 | 1戦以上 |
            | 🥇 平均着順 | 良い順(小さい順) | **{min_games}戦以上** |
            | 👑 トップ率 | 高い順 | **{min_games}戦以上** |
            | 🛡 ラス回避率 | 高い順 | **{min_games}戦以上** |
            | 🔥 最長連勝 | 多い順 | 制限なし |
            | 🛡️ 最長連続ラス回避 | 多い順 | 制限なし |
            | ⭐ 5連勝以上回数 | 多い順 | 制限なし |
            | 🌟 ベスト100半荘 | 良い順(小さい順) | **100戦以上** |

            ※ レーティング・段位は専用タブがあるため、ランキングPTの集計には含めません。

            **その他**:
            - 11位以下は 0pt (ポイントなし)
            - **お客さん / スタッフ** は別カテゴリで集計 (混ざりません)
            - 規定打数はページ上部のスライダーで変更できます (現在: **{min_games}戦**)
            - 1項目で獲得できる最大は 10pt、8項目すべて1位なら理論値 **80pt**
            """)

    with t2:
        st.caption("勝つほど、そして強い人に勝つほど大きく上がります。1着 +15 / 2着 −4 / 3着 −9 が基本pt。")
        period_result_t1 = rating_period_selector("t1")
        rating_guest_t1, rating_staff_t1 = build_rating_stats_with_periods(period_result_t1)
        show_rating_ranking(rating_guest_t1, rating_staff_t1)
    with t3:
        st.caption("段位が高い順で表示。同段位内は段位ptの多い順です。")
        period_result_t2 = rating_period_selector("t2")
        rating_guest_t2, rating_staff_t2 = build_rating_stats_with_periods(period_result_t2)
        show_dan_ranking(rating_guest_t2, rating_staff_t2)
    with t4: show_ranking_split(stats_guest, stats_staff, "games", False, None, "games")
    with t5: show_ranking_split(stats_guest, stats_staff, "avg_rank", True, '{:.3f}'.format, "avg_rank")

    # --- t5: 平均着順(ルール別) - サブタブで A客/AS/B客/BS を切り替え ---
    with t6:
        st.caption("プレイヤーが打った時のルール(タイプ)別の平均着順。各タイプで規定打数以上のプレイヤーのみ表示。")
        sub_t1, sub_t2, sub_t3, sub_t4 = st.tabs(["🟦 A客", "🟪 AS", "🟨 B客", "🟩 BS"])

        def show_type_ranking(sub_tab, type_key, min_type_games=10):
            """タイプ別平均着順ランキング (規定打数はタイプ内での打数)"""
            with sub_tab:
                st.markdown(f"**「{type_key}」として打った時の平均着順ランキング** (このタイプで{min_type_games}戦以上)")
                col_avg = f"avg_rank_{type_key}"
                col_games = f"games_{type_key}"

                # 各グループでフィルタして表示
                c1_, c2_ = st.columns(2)
                for col_obj, df_r, title, icon in [(c1_, stats_guest, "お客さん", "🧑‍🤝‍🧑"),
                                                    (c2_, stats_staff, "スタッフ", "👔")]:
                    with col_obj:
                        st.markdown(f"#### {icon} {title} Top20")
                        if not df_r.empty and col_avg in df_r.columns:
                            df_filtered = df_r[df_r[col_games].fillna(0) >= min_type_games].copy()
                            if not df_filtered.empty:
                                ranked = assign_competition_rank(df_filtered, col_avg, ascending=True)
                                res = ranked[ranked["順位"] <= 20].reset_index(drop=True)
                                display_df = pd.DataFrame({
                                    "順位": res["順位"],
                                    "名前": res["name"],
                                    f"平均着順({type_key})": res[col_avg].map('{:.3f}'.format),
                                    f"{type_key}打数": res[col_games].astype(int),
                                })
                                st.dataframe(display_df, hide_index=True, use_container_width=True)
                            else:
                                st.info(f"「{type_key}」で{min_type_games}戦以上のプレイヤーがいません")
                        else:
                            st.info("データなし")

        show_type_ranking(sub_t1, "A客")
        show_type_ranking(sub_t2, "AS")
        show_type_ranking(sub_t3, "B客")
        show_type_ranking(sub_t4, "BS")

    # --- t6: 席別平均着順 (A/B/C席のサブタブ) ---
    with t7:
        st.caption("プレイヤーがどの席に座ったかで平均着順を集計。各席で10戦以上のプレイヤーのみ表示。")
        sub_s_a, sub_s_b, sub_s_c = st.tabs(["🅰️ A席", "🅱️ B席", "🇨 C席"])

        def show_seat_ranking(sub_tab, seat_key, min_seat_games=10):
            """席別平均着順ランキング"""
            with sub_tab:
                st.markdown(f"**「{seat_key}席」に座った時の平均着順ランキング** (この席で{min_seat_games}戦以上)")
                col_avg = f"avg_rank_seat_{seat_key}"
                col_games = f"games_seat_{seat_key}"

                c1_, c2_ = st.columns(2)
                for col_obj, df_r, title, icon in [(c1_, stats_guest, "お客さん", "🧑‍🤝‍🧑"),
                                                    (c2_, stats_staff, "スタッフ", "👔")]:
                    with col_obj:
                        st.markdown(f"#### {icon} {title} Top20")
                        if not df_r.empty and col_avg in df_r.columns:
                            df_filtered = df_r[df_r[col_games].fillna(0) >= min_seat_games].copy()
                            if not df_filtered.empty:
                                ranked = assign_competition_rank(df_filtered, col_avg, ascending=True)
                                res = ranked[ranked["順位"] <= 20].reset_index(drop=True)
                                display_df = pd.DataFrame({
                                    "順位": res["順位"],
                                    "名前": res["name"],
                                    f"平均着順({seat_key}席)": res[col_avg].map('{:.3f}'.format),
                                    f"{seat_key}席打数": res[col_games].astype(int),
                                })
                                st.dataframe(display_df, hide_index=True, use_container_width=True)
                            else:
                                st.info(f"「{seat_key}席」で{min_seat_games}戦以上のプレイヤーがいません")
                        else:
                            st.info("データなし")

        show_seat_ranking(sub_s_a, "A")
        show_seat_ranking(sub_s_b, "B")
        show_seat_ranking(sub_s_c, "C")

    with t8: show_ranking_split(stats_guest, stats_staff, "top_rate", False, '{:.3f}%'.format, "top_rate")
    with t9: show_ranking_split(stats_guest, stats_staff, "second_rate", False, '{:.3f}%'.format, "second_rate")
    with t10: show_ranking_split(stats_guest, stats_staff, "last_avoid_rate", False, '{:.3f}%'.format, "last_avoid_rate")
    with t11:
        st.caption("時系列で1着を連続で取った歴代最長回数。")
        show_ranking_split(stats_guest, stats_staff, "max_win_streak", False, '{:.0f}'.format, "max_win_streak")
    with t12:
        st.caption("時系列で3着(ラス)を連続で取った歴代最長回数。少ないほど良い指標ですが、多いと目立ちます。")
        show_ranking_split(stats_guest, stats_staff, "max_last_streak", False, '{:.0f}'.format, "max_last_streak")
    with t13:
        st.caption("時系列で2着を連続で取った歴代最長回数。")
        show_ranking_split(stats_guest, stats_staff, "max_second_streak", False, '{:.0f}'.format, "max_second_streak")
    with t14:
        st.caption("1着または2着を連続で取った歴代最長回数(=ラスを回避し続けた連続回数)。安定感の指標。")
        show_ranking_split(stats_guest, stats_staff, "max_last_avoid_streak", False, '{:.0f}'.format, "max_last_avoid_streak")
    with t15:
        st.caption("2着または3着を連続で取った歴代最長回数(=1着を取れなかった連続回数)。多いほど「トップ運が無い期間」があったことを表す。")
        show_ranking_split(stats_guest, stats_staff, "max_no_top_streak", False, '{:.0f}'.format, "max_no_top_streak")
    with t16:
        st.caption("4連勝以上を達成した回数(1つの連勝ストリークにつき1回カウント)。5連勝も1回カウント。")
        show_ranking_split(stats_guest, stats_staff, "four_win_count", False, '{:.0f}'.format, "four_win_count")
    with t17:
        st.caption("5連勝以上を達成した回数(1つの連勝ストリークにつき1回カウント)。")
        show_ranking_split(stats_guest, stats_staff, "five_win_count", False, '{:.0f}'.format, "five_win_count")

    # --- 「Xの次にX」系ランキングの共通表示関数 ---
    def show_streak_prob_ranking(rate_col, samples_col, label, empty_label, min_samples=10):
        """
        「Xの次にX」の連続確率ランキング (連勝確率/連続2着率/連続ラス率で共通)
        rate_col: 確率列名 (例: top_after_top_rate)
        samples_col: サンプル数列名 (例: top_after_top_samples)
        label: 表示ラベル (例: "連勝確率")
        empty_label: 該当なし時のメッセージ (例: "トップ数")
        """
        c1_, c2_ = st.columns(2)
        for col_obj, df_r, title, icon in [(c1_, stats_guest, "お客さん", "🧑‍🤝‍🧑"),
                                            (c2_, stats_staff, "スタッフ", "👔")]:
            with col_obj:
                st.markdown(f"#### {icon} {title} Top20")
                if not df_r.empty and rate_col in df_r.columns:
                    df_filtered = df_r[
                        df_r[rate_col].notna() &
                        (df_r[samples_col].fillna(0) >= min_samples)
                    ].copy()
                    if not df_filtered.empty:
                        ranked = assign_competition_rank(df_filtered, rate_col, ascending=False)
                        res = ranked[ranked["順位"] <= 20].reset_index(drop=True)
                        display_df = pd.DataFrame({
                            "順位": res["順位"],
                            "名前": res["name"],
                            label: res[rate_col].map('{:.2f}%'.format),
                            "分子/分母": res.apply(
                                lambda r: f"{int(r[rate_col]/100 * r[samples_col] + 0.5)}/{int(r[samples_col])}",
                                axis=1
                            ),
                            "打数": res["games"].astype(int),
                        })
                        st.dataframe(display_df, hide_index=True, use_container_width=True)
                    else:
                        st.info(f"{empty_label}が{min_samples}以上のプレイヤーがいません")
                else:
                    st.info("データなし")

    # --- t16: 連勝確率 ---
    with t18:
        st.caption("トップを取った直後の半荘で再度トップを取った確率(サンプル数10以上のプレイヤーのみ表示)。")
        show_streak_prob_ranking(
            "top_after_top_rate", "top_after_top_samples",
            "連勝確率", "トップ数"
        )

    # --- t17: 連続2着率 ---
    with t19:
        st.caption("2着を取った直後の半荘で再度2着を取った確率(サンプル数10以上のプレイヤーのみ表示)。")
        show_streak_prob_ranking(
            "second_after_second_rate", "second_after_second_samples",
            "連続2着率", "2着数"
        )

    # --- t18: 連続ラス率 ---
    with t20:
        st.caption("ラス(3着)を取った直後の半荘で再度ラスを取った確率(サンプル数10以上のプレイヤーのみ表示)。多いと「連ラス」しがちなプレイヤー。")
        show_streak_prob_ranking(
            "last_after_last_rate", "last_after_last_samples",
            "連続ラス率", "ラス数"
        )

    # --- ベスト100半荘表示関数 ---
    def show_best100_ranking(df_g, df_s):
        """連続100半荘の最高成績を表示 (期間明記付き)"""
        c1_, c2_ = st.columns(2)
        for col_obj, df_r, title, icon in [(c1_, df_g, "お客さん", "🧑‍🤝‍🧑"), (c2_, df_s, "スタッフ", "👔")]:
            with col_obj:
                st.markdown(f"#### {icon} {title} Top20")
                # 100半荘に達していない (best100_avgがNaN) は除外
                df_valid = df_r[df_r["best100_avg"].notna()].copy() if not df_r.empty else pd.DataFrame()
                if df_valid.empty:
                    st.info("100半荘以上打っているプレイヤーがいません")
                    continue
                # 平均着順が小さい順 (=良い順)、同率は同順位
                ranked = assign_competition_rank(df_valid, "best100_avg", ascending=True)
                res = ranked[ranked["順位"] <= 20].reset_index(drop=True)

                # HTMLテーブル (期間・成績を分かりやすく)
                html = '<table class="stats-table" style="width:100%;">'
                html += """<thead><tr>
                    <th style="width:50px;">順位</th>
                    <th style="text-align:left;">名前</th>
                    <th style="width:75px;">平均着順</th>
                    <th style="width:75px;">1着数</th>
                    <th style="width:75px;">トップ率</th>
                    <th style="text-align:left;">期間 (対局番号 / 日時)</th>
                </tr></thead><tbody>"""
                for _, r in res.iterrows():
                    rank_num = int(r["順位"])
                    if rank_num == 1: rank_disp = "🥇 1"
                    elif rank_num == 2: rank_disp = "🥈 2"
                    elif rank_num == 3: rank_disp = "🥉 3"
                    else: rank_disp = str(rank_num)

                    avg_color = "var(--accent)" if rank_num <= 3 else "var(--text-primary)"
                    first_cnt = int(r["best100_first"])
                    second_cnt = int(r["best100_second"])
                    third_cnt = int(r["best100_third"])
                    top_rate = r["best100_top_rate"]

                    # 期間表示
                    try:
                        start_str = pd.to_datetime(r["best100_start_dt"]).strftime("%Y/%m/%d")
                    except:
                        start_str = "?"
                    try:
                        end_str = pd.to_datetime(r["best100_end_dt"]).strftime("%Y/%m/%d")
                    except:
                        end_str = "?"
                    start_idx = int(r["best100_start_idx"])
                    end_idx = int(r["best100_end_idx"])
                    total_games = int(r["games"])
                    period_html = f'''
                        <div style="font-size:0.85rem;line-height:1.35;">
                            <div style="color:var(--text-primary);font-weight:600;">
                                📅 {start_str} 〜 {end_str}
                            </div>
                            <div style="color:var(--text-muted);font-size:0.75rem;">
                                第{start_idx}戦目 〜 第{end_idx}戦目 / 全{total_games}戦中
                            </div>
                        </div>
                    '''
                    html += f'''<tr>
                        <td style="text-align:center;font-weight:800;">{rank_disp}</td>
                        <td style="text-align:left;font-weight:600;">{r["name"]}</td>
                        <td style="text-align:center;color:{avg_color};font-weight:900;
                                   font-family:'Zen Kaku Gothic New';">{r["best100_avg"]:.3f}</td>
                        <td style="text-align:center;">{first_cnt}
                            <span style="color:var(--text-muted);font-size:0.7rem;"> / 2着{second_cnt} / 3着{third_cnt}</span>
                        </td>
                        <td style="text-align:center;color:var(--green);font-weight:700;">{top_rate:.1f}%</td>
                        <td style="text-align:left;">{period_html}</td>
                    </tr>'''
                html += '</tbody></table>'
                st.markdown(html, unsafe_allow_html=True)

    with t21:
        st.caption("各プレイヤーが**連続100半荘**でもっとも良い平均着順を出した期間を抽出。100半荘未満のプレイヤーは非表示です。")
        show_best100_ranking(stats_guest, stats_staff)

    df_mem = load_member_data()
    df_mem["type"] = df_mem["名前"].apply(lambda x: "staff" if str(x).lower().endswith("s") else "guest")
    df_mem["名前"] = df_mem["名前"].astype(str).str.replace(r'[(\(].*?[)\)]', '', regex=True)
    mem_g = df_mem[df_mem["type"] == "guest"]
    mem_s = df_mem[df_mem["type"] == "staff"]

    def show_mem_ranking(df_g, df_s, col):
        c1, c2 = st.columns(2)
        for col_obj, df_r, title, icon in [(c1, df_g, "お客さん", "🧑‍🤝‍🧑"), (c2, df_s, "スタッフ", "👔")]:
            with col_obj:
                st.markdown(f"#### {icon} {title} Top20")
                if not df_r.empty:
                    # 0より大きいものだけ残してから同率順位付け
                    df_valid = df_r[df_r[col] > 0].copy()
                    if not df_valid.empty:
                        ranked = assign_competition_rank(df_valid, col, ascending=False)
                        res = ranked[ranked["順位"] <= 20].reset_index(drop=True)
                        cols = ["順位", "名前", col]
                        if col == "最大飜数":
                            for extra in ["最大飜数詳細", "最大飜数記録日"]:
                                if extra in res.columns: cols.append(extra)
                        st.dataframe(res[cols], hide_index=True, use_container_width=True)
                    else: st.info("データなし")
                else: st.info("データなし")

    with t22: show_mem_ranking(mem_g, mem_s, "最大飜数")
    with t23: show_mem_ranking(mem_g, mem_s, "役満回数")

    # 段位システム詳細を折りたたみで表示
    with st.expander("📖 レーティング・段位システムの詳細", expanded=False):
        st.markdown("""
        #### 📐 レーティング計算式
        - **1着**: +15 pt / **2着**: −4 pt / **3着**: −9 pt (基本)
        - **卓平均補正**: `(他プレイヤー平均レート − 自レート) ÷ 40`
          - 強い相手に勝つと大幅アップ、弱い相手に負けると大幅ダウン
          - 3人麻雀では自分を除いた2人の平均を使うので、真のゼロサム性が保たれます
        - **調整係数**: 対局数400戦までは徐々に0.2に近づく (安定期は0.2固定)
        - 初期レート **R1500** から始まります

        #### 🏅 段位表
        """)
        st.caption(f"着順ポイント: 1着 **+{DAN_POINTS_1}** / 2着 **{DAN_POINTS_2:+d}** / 3着 **{DAN_POINTS_3:+d}** (全段位共通)")
        dan_table_html = '<table class="stats-table" style="width:100%;">'
        dan_table_html += """<thead><tr>
            <th>段位</th><th style="text-align:center;">到達pt (累積)</th>
        </tr></thead><tbody>"""
        for i, dan in enumerate(DAN_TABLE):
            dname, threshold, col = dan
            badge = render_dan_badge(dname, col, size="small")
            th_display = f"{threshold:+d}" if threshold > -9999 else "初期"
            dan_table_html += f'''<tr>
                <td>{badge}</td>
                <td style="text-align:center;color:{col};font-weight:700;">{th_display} pt</td>
            </tr>'''
        dan_table_html += '</tbody></table>'
        st.markdown(dan_table_html, unsafe_allow_html=True)

    # 手動再計算ボタン
    with st.expander("⚙️ レーティング再計算 (管理用)", expanded=False):
        st.caption("何らかの理由でレーティングがズレた場合、全対局データから再計算できます。通常は「まとめて保存」時に自動再計算されます。")
        if st.button("🔄 レーティングを再計算する", key="btn_recompute_rating_ranking"):
            with st.spinner("再計算中..."):
                try:
                    recompute_and_save_ratings()
                    load_ratings_effective.clear()
                    st.success("✅ レーティングを再計算しました")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"再計算に失敗: {e}")

# ==========================================
# 7. メインルーティング
# ==========================================
if "page" not in st.session_state:
    st.session_state["page"] = "home"

page = st.session_state["page"]
if page == "home":       page_home()
elif page == "personal": page_personal()
elif page == "history":  page_history()
elif page == "versus2":  page_versus2()
elif page == "versus3":  page_versus3()
elif page == "edit":     page_edit()
elif page == "ranking":  page_ranking()
elif page == "monthly":  page_monthly()
else:                    page_home()
