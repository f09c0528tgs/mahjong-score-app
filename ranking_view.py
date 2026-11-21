"""
ぱいんりばー 成績入力・着順表 専用アプリ
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
3画面のシンプルな入力・閲覧アプリ:
  1. 📝 成績を付ける    - 対局結果を入力 (名前→タイプ自動選択・連続入力対応)
  2. 📋 今日の着順表    - 今日の対局を紙の着順表風に表示
  3. 📆 過去の着順表    - 日付を選んで過去の着順表を表示
"""

import bisect
import re
import time
import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta, timezone

JST = timezone(timedelta(hours=9), 'JST')


def now_jst():
    """JST の現在時刻 (タイムゾーン情報なし)。サーバーがUTCでもずれないようにする。"""
    return datetime.now(JST).replace(tzinfo=None)


def _html(s):
    """
    st.markdown に渡す HTML を安全化する (メインアプリと同じ)。
    行頭4スペース以上はコードブロック扱いになるので、改行とインデントを除去する。
    """
    if not s:
        return ""
    return re.sub(r"\n\s*", "", s)

# ==========================================
# 1. ページ設定
# ==========================================
st.set_page_config(
    page_title="ぱいんりばー 成績入力",
    layout="centered",
    initial_sidebar_state="collapsed",
)

CUSTOM_CSS = """
<style>
/* ==========================================================
   デザイン: 「平らなキー」(温かいベージュ × フラットな白いキー × こげ茶のアクセント)
   - Streamlit のテーマ (config.toml はメインアプリと共通のダーク) に左右されないよう、
     画面に出る部品の色はすべてここで固定している。
   - 文字と背景のコントラスト比は 4.5 以上を目安にする。
   ========================================================== */
:root {
    --bg-main: #e9e4e2;      /* 画面の背景 */
    --bg-card: #f1edec;      /* カード */
    --key: #f8f6f5;          /* 平らなキー */
    --key-press: #efe9e6;
    --border: #dcd5d2;
    --text-primary: #2b2422; /* 本文 (背景とのコントラスト比 約13) */
    --text-muted: #62574f;   /* 補足 (約5.6) */
    --brown: #6e5236;        /* 主ボタン「保存して次へ」 */
    --brown-active: #8a6642; /* 選ばれているキー・チップ */
    --brown-ring: #caa073;
    --taupe: #d9d0ca;        /* 控えめなボタン */
    --accent: #8a6642;
    --radius: 12px;
    --mono: "SF Mono", "Menlo", "Roboto Mono", "Consolas", monospace;
}
html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
    background: var(--bg-main) !important;
}
.stApp {
    color: var(--text-primary) !important;
    font-family: "Zen Kaku Gothic New", "Hiragino Sans", "Hiragino Kaku Gothic ProN", "Noto Sans JP", Meiryo, sans-serif !important;
}
#MainMenu, header, footer {visibility: hidden;}
.stDeployButton {display: none;}
h1, h2, h3, h4 { color: var(--text-primary) !important; font-weight: 800 !important; letter-spacing: 0.02em !important; }
.stApp p, .stApp li, .stApp label, .stApp span { color: inherit; }
[data-testid="stMarkdownContainer"] { color: var(--text-primary); }

/* ---------- タブ: 平らな丸いピル ---------- */
[data-baseweb="tab-list"] { gap: 6px !important; border-bottom: none !important; }
[data-baseweb="tab-highlight"], [data-baseweb="tab-border"] { display: none !important; }
button[role="tab"] {
    background: var(--key) !important;
    color: var(--text-primary) !important;
    border: 1px solid var(--border) !important;
    border-radius: 999px !important;
    font-weight: 700 !important;
    padding: 0.45rem 1rem !important;
    transition: none !important;   /* 背景だけ遅れて切り替わると一瞬読めなくなる */
}
button[role="tab"] * { color: inherit !important; }
button[role="tab"][aria-selected="true"] {
    background: var(--brown) !important;
    color: #ffffff !important;
    border-color: var(--brown) !important;
}

/* ---------- ボタン: 平らなキー ---------- */
.stButton button {
    background: var(--key) !important;
    color: var(--text-primary) !important;
    border: 1px solid transparent !important;
    border-radius: var(--radius) !important;
    font-weight: 700 !important;
    box-shadow: 0 1px 0 rgba(60,40,30,0.06) !important;
    transition: background 0.1s !important;
    min-height: 48px !important;
}
.stButton button * { color: inherit !important; }
.stButton button:hover { background: #ffffff !important; border-color: var(--border) !important; }
.stButton button:active { background: var(--key-press) !important; }
.stButton button[kind="primary"] {
    background: var(--brown) !important;
    color: #ffffff !important;
    font-weight: 800 !important;
}
.stButton button[kind="primary"]:hover { background: #5f462e !important; }
/* 使えない状態: 読める濃さを保ちつつ、点線枠で「まだ押せない」と分かるように */
.stButton button:disabled, .stButton button[kind="primary"]:disabled {
    background: var(--taupe) !important;
    color: #4f4540 !important;
    border: 1px dashed #a89b93 !important;
    box-shadow: none !important; cursor: not-allowed !important;
}
.stButton button:disabled * { color: #4f4540 !important; }

/* ---------- タイプ・着順のボタン (segmented control) を「離れた平らなキー」に ---------- */
[data-testid="stElementContainer"]:has(> [data-testid="stButtonGroup"]) { width: 100% !important; }
[data-testid="stButtonGroup"], [data-testid="stButtonGroup"] > div {
    width: 100% !important; max-width: none !important; gap: 8px !important; flex-wrap: wrap !important;
}
button[data-testid^="stBaseButton-segmented_control"] {
    flex: 1 1 auto !important;
    min-height: 46px !important;
    padding: 0 0.5rem !important;
    border-radius: var(--radius) !important;
    margin: 0 !important;
    font-size: 0.95rem !important;
    transition: none !important;
}
button[data-testid="stBaseButton-segmented_control"] {
    background: var(--key) !important;
    color: var(--text-primary) !important;
    border: 1px solid transparent !important;
    box-shadow: 0 1px 0 rgba(60,40,30,0.06) !important;
}
button[data-testid="stBaseButton-segmented_control"] * { color: var(--text-primary) !important; }
button[data-testid="stBaseButton-segmented_controlActive"] {
    background: var(--brown-active) !important;
    border: 2px solid var(--brown-ring) !important;
    color: #ffffff !important;
    font-weight: 800 !important;
}
button[data-testid="stBaseButton-segmented_controlActive"] * { color: #ffffff !important; }
button[data-testid^="stBaseButton-segmented_control"]:disabled {
    background: var(--taupe) !important; border: 1px dashed #a89b93 !important; opacity: 1 !important;
}
button[data-testid^="stBaseButton-segmented_control"]:disabled * { color: #4f4540 !important; }
/* 備考の選択 (st.pills): 平らなキー。選んだものはこげ茶 */
button[data-testid^="stBaseButton-pills"] {
    border-radius: 999px !important; min-height: 40px !important; padding: 0 0.9rem !important;
    transition: none !important;
}
button[data-testid="stBaseButton-pills"] {
    background: var(--key) !important; color: var(--text-primary) !important;
    border: 1px solid var(--border) !important;
}
button[data-testid="stBaseButton-pills"] * { color: var(--text-primary) !important; }
button[data-testid="stBaseButton-pillsActive"] {
    background: var(--brown-active) !important; border: 2px solid var(--brown-ring) !important;
    color: #ffffff !important; font-weight: 800 !important;
}
button[data-testid="stBaseButton-pillsActive"] * { color: #ffffff !important; }

/* 着順のキーはさらに大きく (テンキーのような押しやすさ) */
.st-key-rank_area button[data-testid^="stBaseButton-segmented_control"],
.st-key-fix_rank_area button[data-testid^="stBaseButton-segmented_control"] { min-height: 64px !important; }
.st-key-rank_area button[data-testid^="stBaseButton-segmented_control"] p {
    font-size: 1.1rem !important; font-weight: 800 !important;
}

/* ---------- 入力欄 (名前・卓番・日付・備考) ---------- */
[data-baseweb="select"] > div, [data-baseweb="input"], [data-baseweb="base-input"],
[data-baseweb="input"] input, [data-baseweb="textarea"], textarea,
.stNumberInput > div, .stTextInput > div {
    background: var(--key) !important;
    color: var(--text-primary) !important;
    border-color: var(--border) !important;
    border-radius: 10px !important;
}
[data-baseweb="select"] *, [data-baseweb="input"] input, textarea {
    color: var(--text-primary) !important;
    -webkit-text-fill-color: var(--text-primary) !important;
}
[data-baseweb="select"] svg { fill: var(--text-muted) !important; color: var(--text-muted) !important; }
input::placeholder, textarea::placeholder {
    color: #6d625c !important; -webkit-text-fill-color: #6d625c !important; opacity: 1 !important;
}
[data-baseweb="select"] [id$="placeholder"], [data-baseweb="select"] div[aria-hidden="true"] {
    color: #6d625c !important; -webkit-text-fill-color: #6d625c !important;
}
input:disabled, textarea:disabled {
    color: #5a504a !important; -webkit-text-fill-color: #5a504a !important; opacity: 1 !important;
}
button[data-testid^="stNumberInputStep"] {
    background: var(--bg-card) !important; color: var(--text-primary) !important; border: none !important;
}
button[data-testid^="stNumberInputStep"] svg { color: inherit !important; fill: currentColor !important; }
button[data-testid^="stNumberInputStep"]:disabled { color: #9a8f88 !important; }
/* 入力欄の見出し */
[data-testid="stWidgetLabel"], [data-testid="stWidgetLabel"] * {
    color: var(--text-muted) !important; opacity: 1 !important; font-weight: 700 !important;
}
/* プルダウンの候補一覧 (画面の外側に出る部品なので個別に) */
[data-baseweb="popover"] ul, [data-baseweb="popover"] [role="listbox"], [data-baseweb="menu"] {
    background: #fbf9f8 !important;
}
[data-baseweb="popover"] li, [data-baseweb="popover"] [role="option"] {
    background: #fbf9f8 !important; color: var(--text-primary) !important;
}
[data-baseweb="popover"] li *, [data-baseweb="popover"] [role="option"] * { color: var(--text-primary) !important; }
[data-baseweb="popover"] li:hover, [data-baseweb="popover"] [role="option"][aria-selected="true"],
[data-baseweb="popover"] li[aria-selected="true"] { background: #efe4d8 !important; }
/* カレンダー (日付) */
[data-baseweb="calendar"], [data-baseweb="calendar"] > div, [data-baseweb="datepicker"] {
    background: #fbf9f8 !important; color: var(--text-primary) !important;
}
[data-baseweb="calendar"] * { color: var(--text-primary) !important; }
[data-baseweb="calendar"] [aria-selected="true"], [data-baseweb="calendar"] [aria-selected="true"] * {
    color: #ffffff !important;
}
[data-baseweb="calendar"] [aria-selected="true"]::after { background: var(--brown) !important; border-color: var(--brown) !important; }

/* 折りたたみ (日時・備考) */
[data-testid="stExpander"] details {
    background: var(--bg-card) !important; border: 1px solid var(--border) !important; border-radius: var(--radius) !important;
}
[data-testid="stExpander"] summary { background: transparent !important; color: var(--text-primary) !important; }
[data-testid="stExpander"] summary *, [data-testid="stExpander"] summary svg {
    color: var(--text-primary) !important; fill: var(--text-primary) !important;
}
[data-testid="stCheckbox"] *, [data-testid="stRadio"] label * { color: var(--text-primary) !important; }

/* 補足文字 */
.stCaption, [data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] * {
    color: var(--text-muted) !important; opacity: 1 !important;
}

/* お知らせ枠: 淡い色の背景 × 濃い文字 (テーマに関係なく固定) */
.stAlert { border-radius: var(--radius) !important; }
[data-testid="stAlertContainer"] { opacity: 1 !important; border-radius: var(--radius) !important; border: 1px solid var(--border) !important; }
[data-testid="stAlertContainer"]:has([data-testid="stAlertContentInfo"])    { background: #e4ebf2 !important; }
[data-testid="stAlertContainer"]:has([data-testid="stAlertContentSuccess"]) { background: #e3eee5 !important; }
[data-testid="stAlertContainer"]:has([data-testid="stAlertContentWarning"]) { background: #f5ead2 !important; }
[data-testid="stAlertContainer"]:has([data-testid="stAlertContentError"])   { background: #f5e0dd !important; }
[data-testid="stAlertContentInfo"], [data-testid="stAlertContentInfo"] * { color: #1f3a55 !important; }
[data-testid="stAlertContentSuccess"], [data-testid="stAlertContentSuccess"] * { color: #1c4a31 !important; }
[data-testid="stAlertContentWarning"], [data-testid="stAlertContentWarning"] * { color: #573f0c !important; }
[data-testid="stAlertContentError"], [data-testid="stAlertContentError"] * { color: #74221c !important; }
hr { border-color: var(--border) !important; }

/* ---------- 上のカード (モックの「合計」の枠) ---------- */
.sum-card {
    display: flex; justify-content: space-between; align-items: baseline; gap: 0.5rem;
    background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--radius);
    padding: 0.7rem 1rem; margin-bottom: 0.6rem;
}
.sum-label { font-size: 0.85rem; color: var(--text-muted); font-weight: 700; }
.sum-value { font-family: var(--mono); font-size: 1.15rem; color: var(--text-primary); font-weight: 600; white-space: nowrap; }
.sum-value small { font-size: 0.72rem; color: var(--text-muted); }

/* ---------- 選手チップ ---------- */
.chips { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; margin: 0.15rem 0 0.5rem; }
.chip {
    position: relative; background: var(--key); border-radius: var(--radius);
    padding: 0.5rem 0.3rem 0.45rem; text-align: center; min-height: 58px;
    box-shadow: 0 1px 0 rgba(60,40,30,0.06); border: 2px solid transparent;
}
.chip-seat { font-size: 0.66rem; color: var(--text-muted); font-weight: 700; letter-spacing: 0.05em; }
.chip-name { font-size: 0.92rem; font-weight: 800; color: var(--text-primary); line-height: 1.25;
             overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.chip-sub { font-family: var(--mono); font-size: 0.78rem; color: var(--text-muted); margin-top: 1px; }
.chip.empty .chip-name { color: #6d625c; font-weight: 700; }
.chip.done { background: #e2dcd9; }
.chip.active { background: var(--brown-active); border-color: var(--brown-ring); }
.chip.active .chip-seat, .chip.active .chip-name, .chip.active .chip-sub { color: #ffffff; }
.chip .chip-check { position: absolute; top: 4px; right: 8px; font-size: 0.75rem; color: var(--text-muted); }
.chip.active .chip-check { color: #ffffff; }
.chip.active::before {
    content: ""; position: absolute; top: -5px; left: 50%; transform: translateX(-50%);
    width: 8px; height: 8px; border-radius: 50%; background: var(--brown-ring);
}

/* ---------- 卓 (2卓以上のとき) ---------- */
.stApp .tbl-tag, .stApp .tbl-tag * { color: #ffffff !important; }
.tbl-tag {
    display: inline-block; color: #ffffff; font-weight: 800; font-size: 0.8rem;
    padding: 0.1rem 0.55rem; border-radius: 999px; line-height: 1.5; white-space: nowrap;
}
.table-now { display: flex; align-items: center; gap: 0.4rem; height: 100%; padding-top: 1.9rem; }
.table-now span { font-size: 0.85rem; color: var(--text-muted); font-weight: 700; }
.sum-others { margin-top: 0.3rem; font-size: 0.72rem; color: var(--text-muted); }
.sum-others .tbl-tag { font-size: 0.68rem; padding: 0 0.45rem; }
.bar-target { display: flex; align-items: center; gap: 0.4rem; margin-bottom: 0.35rem;
              font-size: 0.78rem; color: var(--text-muted); font-weight: 700; }
.bar-target span:last-child { color: var(--text-muted); }
.st-key-table_pick_area button[data-testid^="stBaseButton-segmented_control"] { min-height: 44px !important; }
.tbl-cards { display: grid; grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); gap: 8px; margin-bottom: 0.6rem; }
.tbl-card { background: var(--key); border: 1px solid var(--border); border-radius: var(--radius); padding: 0.5rem 0.7rem; }
.tbl-card-name { font-weight: 800; font-size: 0.9rem; color: var(--text-primary); }
.tbl-card-num { font-family: var(--mono); font-size: 1.3rem; font-weight: 700; color: var(--text-primary); }
.tbl-card-sub { font-size: 0.72rem; color: var(--text-muted); }

/* 小さな見出し (モックの「うえの の素点  3ケタで自動送り」) */
.step-label { display: flex; justify-content: space-between; align-items: baseline; margin: 0.35rem 0 0.1rem; }
.step-label b { font-size: 0.9rem; color: var(--text-primary); }
.step-label span { font-size: 0.75rem; color: var(--text-muted); }

/* ---------- 下に固定する操作ボタン ---------- */
/* Streamlit は st.container を同じ高さの stLayoutWrapper で包むので、固定 (sticky) はその外側に付ける */
[data-testid="stLayoutWrapper"]:has(> .st-key-action_bar) {
    position: sticky !important; bottom: 0; z-index: 50;
}
.st-key-action_bar {
    background: var(--bg-main);
    padding: 0.5rem 0 0.6rem;
    box-shadow: 0 -8px 12px -8px rgba(60,40,30,0.18);
}
.st-key-action_bar [data-testid="stHorizontalBlock"] { flex-wrap: nowrap !important; gap: 8px !important; }
.st-key-action_bar [data-testid="stColumn"] { min-width: 0 !important; }
.st-key-action_bar .stButton button { min-height: 52px !important; padding: 0 0.25rem !important; }
.st-key-action_bar .stButton button p {
    font-size: 0.9rem !important; line-height: 1.2 !important; white-space: nowrap !important;
}

/* ---------- サマリバッジ (着順表タブ) ---------- */
.summary-badge {
    display: inline-flex; align-items: center; gap: 0.4rem;
    background: var(--key); border: 1px solid var(--border);
    padding: 0.35rem 0.8rem; border-radius: 999px;
    font-size: 0.82rem; color: var(--text-primary); margin: 0.2rem 0.4rem 0.2rem 0;
}
.summary-badge strong { color: var(--brown); font-weight: 900; font-family: var(--mono); }

/* ===== 紙の着順表 (paper-sheet) ===== */
.paper-wrap {
    background: var(--key);
    border-radius: var(--radius);
    padding: 0.35rem;
    overflow-x: auto;
    margin: 0 0 0.8rem;
    border: 1px solid var(--border);
}
.paper-table {
    border-collapse: collapse;
    width: 100%;
    max-width: 460px;
    font-family: "Zen Kaku Gothic New", sans-serif;
    background: #fffdf9;
}
.paper-table th, .paper-table td {
    border: 1px solid #d8cfc6;
    text-align: center;
    color: #1f1a18;
    padding: 1px 4px;
    font-size: 0.82rem;
    line-height: 1.5;
}
.paper-table thead th {
    background: #ede6df;
    font-weight: 800;
    font-size: 0.72rem;
    color: #3a302b;
    padding: 2px 4px;
}
.paper-table .col-no {
    background: #f1ebe5; font-weight: 700; width: 28px; color: #4a403b;
    font-size: 0.68rem;
}
.paper-table .seat-head-A, .paper-table .seat-head-B, .paper-table .seat-head-C { width: 33%; }
.paper-table .name-row td {
    font-weight: 800; font-size: 0.8rem; background: #f7f2ec;
    border-top: 2px solid #9b8a7a;
    padding: 3px 4px;
    line-height: 1.2;
}
.paper-table .name-type {
    font-size: 0.6rem; color: #4f3f2c; margin-left: 2px; white-space: nowrap;
    background: #ece2d6; padding: 0 3px; border-radius: 3px;
    vertical-align: middle;
}
.paper-table .rank1 { color: #a6362a; font-weight: 900; }
.paper-table .rank-cell { font-weight: 700; font-size: 0.9rem; font-family: var(--mono); }
.paper-table .gamecount-row td {
    background: #f1ebe5; font-weight: 700; font-size: 0.74rem; color: #4a403b;
    padding: 3px 4px;
}
.paper-table .empty-cell { color: #a99d95; }
/* ゲーム代の区切り行 */
.paper-table .fee-row td {
    background: #f6eee3; text-align: left; padding: 5px 8px;
    border-top: 2px dashed #a67c52; border-bottom: 3px double #a67c52;
}
.paper-table .fee-head { font-size: 0.85rem; font-weight: 800; color: #3b2a1a; }
.paper-table .fee-total { color: #a6362a; font-size: 1.05rem; font-family: var(--mono); }
.paper-table .fee-games { font-size: 0.72rem; color: #5a4632; font-weight: 700; margin-left: 2px; }
.paper-table .fee-status {
    float: right; font-size: 0.7rem; font-weight: 800; padding: 1px 6px; border-radius: 4px;
}
.paper-table .fee-status.done { background: #dcebdf; color: #1d5233; }
.paper-table .fee-status.open { background: #f7dfc9; color: #8a3c13; }
.paper-table .fee-detail { font-size: 0.74rem; color: #46382a; line-height: 1.45; margin-top: 2px; clear: both; }

.paper-title {
    font-weight: 800; font-size: 0.9rem; color: #2b2422;
    padding: 0.25rem 0.7rem; background: var(--key); border-radius: 8px 8px 0 0;
    border: 1px solid var(--border); border-bottom: none;
    display: inline-block; margin-top: 0.5rem;
}

/* ---------- ゲーム代の欄 ---------- */
.fee-box {
    background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--radius);
    padding: 0.7rem 1rem; margin-bottom: 0.6rem;
}
.fee-box-title { font-size: 0.92rem; margin-bottom: 0.35rem; color: var(--text-primary); }
.fee-box-total { color: var(--brown); font-size: 1.3rem; font-family: var(--mono); }
.fee-line {
    display: flex; justify-content: space-between; gap: 0.5rem;
    font-size: 0.86rem; padding: 0.2rem 0; border-bottom: 1px dotted var(--border); color: var(--text-primary);
}
.fee-line b { font-family: var(--mono); }
.fee-rule { font-size: 0.72rem; color: var(--text-muted); margin-top: 0.4rem; }
/* 値引き (備考) */
.fee-line.fee-disc, .fee-line.fee-disc * { color: #9a2f2f !important; }
.paper-table .fee-disc { color: #9a2f2f; }
.paper-table .memo-tag {
    display: block; font-size: 0.55rem; font-weight: 800; line-height: 1.2; color: #ffffff;
    background: #9a2f2f; border-radius: 3px; padding: 0 2px; margin: 1px auto 0; width: fit-content;
    font-family: "Zen Kaku Gothic New", sans-serif;
}
.memo-total {
    font-size: 0.8rem; color: #9a2f2f; font-weight: 700; margin-top: -0.2rem;
}

/* ---------- まちがいを直す ---------- */
.st-key-fix_box {
    background: var(--bg-card); border: 2px solid var(--brown); border-radius: var(--radius);
    padding: 0.6rem 0.8rem 0.8rem;
}
.fix-head { font-weight: 900; font-size: 1rem; color: var(--text-primary); display: flex; justify-content: space-between; }
.fix-head span { font-size: 0.78rem; color: var(--text-muted); font-weight: 700; }

/* ---------- 中間締め・1日締め (タイプ別のトップ回数) ---------- */
.close-card {
    background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--radius);
    padding: 0.6rem 0.8rem 0.7rem; margin-bottom: 0.6rem;
}
.close-card.done { border-left: 6px solid var(--brown); }
.close-head { display: flex; justify-content: space-between; align-items: baseline; gap: 0.5rem; flex-wrap: wrap; margin-bottom: 0.4rem; }
.close-title { font-weight: 900; font-size: 1.05rem; color: var(--text-primary); }
.close-status { font-size: 0.78rem; color: var(--text-muted); font-weight: 700; }
.close-table { width: 100%; border-collapse: collapse; table-layout: fixed; }
.close-table th, .close-table td { padding: 0.35rem 0.3rem; border-bottom: 1px solid var(--border); color: var(--text-primary); }
.close-table thead th { font-size: 0.72rem; color: var(--text-muted); font-weight: 700; text-align: right; }
.close-table thead th:first-child { text-align: left; }
.close-table tbody th { text-align: left; font-size: 0.95rem; font-weight: 800; white-space: nowrap; }
.close-table td { text-align: right; white-space: nowrap; }
.close-table td b { font-family: var(--mono); font-size: 1.35rem; font-weight: 800; }
.close-table td small { font-size: 0.7rem; margin-left: 2px; color: var(--text-muted); }
.close-table td.close-main b { color: var(--brown); font-size: 1.6rem; }
.close-table thead th.close-main { color: var(--brown); }
.close-table td.close-zero b { color: var(--text-muted); font-weight: 500; }
.close-table tr.close-sum th, .close-table tr.close-sum td { border-bottom: none; border-top: 2px solid var(--text-primary); }

/* ---------- 余白・見出し ---------- */
[data-testid="stMainBlockContainer"] { padding-top: 1rem !important; padding-bottom: 2rem !important; max-width: 560px !important; }
h1 { font-size: 1.35rem !important; line-height: 1.3 !important; margin: 0.1rem 0 0.4rem !important; padding: 0 !important; }
h3 { font-size: 1rem !important; line-height: 1.35 !important; margin-top: 0.6rem !important; padding-bottom: 0 !important; color: var(--text-muted) !important; }
.brand-bar { display: flex; justify-content: space-between; font-size: 0.75rem; color: var(--text-muted); margin-bottom: 0.4rem; }

/* タッチ端末: 押した後もボタンの色が変わったまま残る (hover が残る) のを防ぐ */
@media (hover: none) {
    .stButton button:hover { background: var(--key) !important; border-color: transparent !important; }
    .stButton button[kind="primary"]:hover { background: var(--brown) !important; }
}

@media (max-width: 640px) {
    [data-testid="stMainBlockContainer"] {
        padding-top: 0.6rem !important; padding-left: 0.8rem !important; padding-right: 0.8rem !important;
    }
    [data-testid="stVerticalBlock"] { gap: 0.55rem !important; }
    h1 { font-size: 1.2rem !important; }
    /* 卓番・セット、下の操作ボタンは横に並べたまま */
    .st-key-table_set [data-testid="stHorizontalBlock"],
    .st-key-action_bar [data-testid="stHorizontalBlock"],
    .st-key-fee_confirm [data-testid="stHorizontalBlock"],
    .st-key-fix_btns [data-testid="stHorizontalBlock"],
    .st-key-fix_del_btns [data-testid="stHorizontalBlock"],
    .st-key-close_confirm [data-testid="stHorizontalBlock"],
    .st-key-close_btns [data-testid="stHorizontalBlock"] { flex-wrap: nowrap !important; gap: 8px !important; }
    .st-key-table_set [data-testid="stColumn"],
    .st-key-action_bar [data-testid="stColumn"],
    .st-key-fee_confirm [data-testid="stColumn"],
    .st-key-fix_btns [data-testid="stColumn"],
    .st-key-fix_del_btns [data-testid="stColumn"],
    .st-key-close_confirm [data-testid="stColumn"],
    .st-key-close_btns [data-testid="stColumn"] { flex: 1 1 0 !important; width: auto !important; min-width: 0 !important; }
    button[role="tab"] { padding: 0.4rem 0.75rem !important; }
}

/* ---------- 着順表の段組み (iPad・PC) ----------
   着順表は紙と同じく20回ずつの列 (.paper-block) に分けてある。1列目の上→下→2列目の上→下…の順。
   スマホでは縦1本につなげて (2つ目からの見出しは隠す)、幅のある画面では同じ幅の列を左から右へ並べる。
   入力画面 (.st-key-page_input) はスマホ幅のまま真ん中に置く。 */
.paper-wrap .paper-table { max-width: none; margin: 0 !important; }
@media (max-width: 699px) {
    .paper-block + .paper-block thead { display: none; }
}
@media (min-width: 700px) {
    [data-testid="stMainBlockContainer"] { max-width: 1240px !important; }
    .st-key-page_input { max-width: 560px; width: 100%; margin: 0 auto; }
    .st-key-close_area_today, .st-key-close_area_past { max-width: 600px; }
    .paper-cols { display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); align-items: start; gap: 12px; margin-bottom: 10px; }
    .paper-wrap .paper-foot { max-width: 560px; }
}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ==========================================
# 2. 定数
# ==========================================
SHEET_SCORE = "score"
SHEET_MEMBER = "members"
# ゲーム代の集金記録 (着順表の区切り)。1行 = 1回の集金。
# LastGameNo = その集金に含めた最後の対局の GameNo。卓ごとに、前回の集金の次の局からここまでが1区切り。
SHEET_FEE = "fee_collections"
FEE_COLS = ["日時", "TableNo", "LastGameNo", "枚数", "内訳"]
# 中間締め・1日締めの記録。1行 = 1回の締め。種類は CLOSE_MID / CLOSE_DAY。
# LastGameNo = 締めた時点でのその日の最後の対局の GameNo (全卓共通)。それ以下の GameNo の対局が締めに入る。
# トップ回数は画面では毎回対局データから計算し直す。シートの「回数」「A客」… は記録用。
SHEET_CLOSE = "day_closings"
# 操作の記録 (メインアプリと共通)。入力アプリでは回の訂正・削除を書く
SHEET_LOG = "logs"
LOG_COLS = ["日時", "操作", "GameNo", "詳細"]
CLOSE_COLS = ["日時", "論理日付", "種類", "LastGameNo", "回数", "A客", "B客", "AS", "BS", "不明"]
CLOSE_MID = "中間締め"
CLOSE_DAY = "1日締め"

# ゲーム代: トップを取った人が、自分のタイプに応じた枚数を払う (メインアプリの GAME_FEE_TABLE と同じ値)
GAME_FEE_TABLE = {"A客": 3, "B客": 4, "AS": 1, "BS": 1}

# 備考と、それによるゲーム代の値引き (枚)。備考は複数選べる。保存するときは「、」でつなぐ (例: "東１終了、５連勝〜")。
# 複数あれば値引きは足し算。文字 (全角数字・「〜」) を変えないこと。
# ※ メインアプリ (main.py) の NOTE_DISCOUNTS / _normalize_note / note_tags / note_discount と同じ。片方を直したらもう片方も直すこと。
NOTE_DISCOUNTS = {"東１終了": 1, "２人飛ばし": 2, "５連勝〜": 5}
MEMO_OPTIONS = list(NOTE_DISCOUNTS)
MEMO_SEP = "、"
# 着順表の印に使う短い名前
NOTE_SHORT = {"東１終了": "東１", "２人飛ばし": "２飛", "５連勝〜": "５連"}


def _normalize_note(note):
    """備考の表記ゆれをそろえる (半角数字→全角、「~」「～」→「〜」、「東発終了」「東初終了」→「東１終了」)"""
    text = str(note or "")
    text = text.translate(str.maketrans("0123456789~～", "０１２３４５６７８９〜〜"))
    return text.replace("東発終了", "東１終了").replace("東初終了", "東１終了")


def note_tags(note):
    """備考に含まれている値引きの項目 (NOTE_DISCOUNTS の順)"""
    text = _normalize_note(note)
    return [t for t in NOTE_DISCOUNTS if t in text]


def note_discount(note):
    """備考による値引きの合計 (枚。複数あれば足す)"""
    return sum(NOTE_DISCOUNTS[t] for t in note_tags(note))

EXPECTED_COLS = [
    "GameNo", "TableNo", "SetNo", "日時", "備考",
    "Aさん", "Aタイプ", "A着順",
    "Bさん", "Bタイプ", "B着順",
    "Cさん", "Cタイプ", "C着順"
]

TYPE_OPTIONS = ["A客", "AS", "B客", "BS"]
# 入力画面のボタンの並びと表示名 (保存する値は A客/B客/AS/BS のまま)
TYPE_BUTTON_ORDER = ["A客", "B客", "AS", "BS"]
TYPE_LABELS = {"A客": "A客", "B客": "B客", "AS": "Aスタッフ", "BS": "Bスタッフ"}
RANK_OPTIONS = [1, 2, 3]

# ==========================================
# 3. データ読み書き
# ==========================================
# --- 接続 ---
# st-gsheets-connection (st.connection) は、読み書きのたびに「スプレッドシートを開く → シートを探す → 読む」で
# 3回通信し、保存はシート全体を消して書き直す。遅いので、このアプリは gspread を直接使う。
#   - 接続とシート情報は使い回す (st.cache_resource)
#   - 表示用の読み込みは score / members / fee_collections を1回の通信でまとめて取る (values_batch_get)
#   - 成績の保存は「末尾に1行追記」(append_row)。他の行には触らないので、他端末の入力を消すこともない
# 接続情報は今までどおり .streamlit/secrets.toml の [connections.gsheets] を使う。

class SheetMissing(Exception):
    """シートが存在しない"""


def _is_sheet_missing(err):
    """gspread の WorksheetNotFound はメッセージがシート名だけなので、例外の型で判定する"""
    if isinstance(err, SheetMissing):
        return True
    return any(c.__name__ == "WorksheetNotFound" for c in type(err).__mro__)


def _status_code(err):
    resp = getattr(err, "response", None)
    return getattr(resp, "status_code", None)


def _with_retry(fn, write=False):
    """
    通信が混み合ったとき (429) や Google 側の一時エラー (5xx) なら、少し待ってやり直す。
    書き込みは「実は成功していた」のに二重に書くのを避けるため、確実に受け付けられていない 429 のときだけやり直す。
    """
    for i in range(3):
        try:
            return fn()
        except Exception as e:
            code = _status_code(e)
            retryable = code == 429 or (not write and code is not None and code >= 500)
            if i < 2 and retryable:
                time.sleep(1.0 * (i + 1))
                continue
            raise


@st.cache_resource(show_spinner=False)
def _get_spreadsheet():
    """スプレッドシートへの接続 (アプリ全体で使い回す)"""
    import gspread
    info = dict(st.secrets["connections"]["gsheets"])
    target = info.pop("spreadsheet", None)
    folder_id = info.pop("worksheet", None)
    if info.get("type") != "service_account":
        raise RuntimeError("secrets.toml の [connections.gsheets] にサービスアカウントの設定が必要です（保存に必要）")
    client = gspread.service_account_from_dict(info)
    if str(target).startswith("http"):
        return client.open_by_url(target)
    return client.open(target, folder_id=folder_id) if folder_id else client.open(target)


@st.cache_resource(show_spinner=False)
def _sheet_meta():
    """シート (Worksheet) と、各シートの見出し行の使い回し用"""
    return {"ws": {}, "titles": None, "header": {}}


def _sheet_titles(refresh=False):
    meta = _sheet_meta()
    if refresh or meta["titles"] is None:
        wss = _with_retry(lambda: _get_spreadsheet().worksheets())
        meta["titles"] = [w.title for w in wss]
        meta["ws"].update({w.title: w for w in wss})
    return meta["titles"]


def _get_ws(name):
    """シートを返す。無ければ (他端末で作られた可能性があるので一度だけ確認し直してから) SheetMissing"""
    meta = _sheet_meta()
    if name not in meta["ws"]:
        if name not in _sheet_titles(refresh=True):
            raise SheetMissing(name)
    return meta["ws"][name]


def _values_to_df(values, keep_row=False):
    """シートの値 (2次元リスト) を DataFrame に。1行目が見出し。空行は除く。keep_row なら _row (シート上の行番号) を付ける"""
    if not values:
        return pd.DataFrame()
    header = [str(h).strip() for h in values[0]]
    width = len(header)
    rows, row_nos = [], []
    for n, r in enumerate(values[1:], start=2):
        r = (list(r) + [""] * width)[:width]
        if any(str(c).strip() for c in r):
            rows.append(r)
            row_nos.append(n)
    df = pd.DataFrame(rows, columns=header)
    df = df.loc[:, [c != "" for c in df.columns]]
    df = df.loc[:, ~df.columns.duplicated()]
    if keep_row:
        df["_row"] = row_nos
    return df


def _batch_read(names, keep_row=False):
    """複数のシートを1回の通信で読む。存在しないシートは空の DataFrame。"""
    titles = _sheet_titles()
    exist = [n for n in names if n in titles]
    out = {n: pd.DataFrame() for n in names}
    if exist:
        res = _with_retry(lambda: _get_spreadsheet().values_batch_get([f"'{n}'" for n in exist]))
        for n, vr in zip(exist, res.get("valueRanges", [])):
            out[n] = _values_to_df(vr.get("values", []), keep_row=keep_row)
    return out


@st.cache_data(ttl=60, show_spinner=False)
def _fetch_all():
    """表示用: 成績・メンバー・集金記録をまとめて読む (60秒キャッシュ)"""
    return _batch_read([SHEET_SCORE, SHEET_MEMBER, SHEET_FEE, SHEET_CLOSE])


def clear_cache():
    _fetch_all.clear()


def _get_all_or_stop():
    try:
        return _fetch_all()
    except Exception as e:
        st.error(f"スプレッドシートを読み込めませんでした。少し待ってから「再読み込み」を押してください。（{type(e).__name__}: {e}）")
        if st.button("🔄 再読み込み", key="reload_err"):
            clear_cache()
            st.rerun()
        st.stop()


def parse_datetime_mixed(s):
    """
    「日時」の列を日時に変換する。1件ずつ形を判断する。
    pd.to_datetime は列の最初の値で形を決めるので、「2026-11-09 22:00」(分まで) と
    「2026-11-21 18:53:54」(秒まで。入力アプリが保存する形) が混ざると、形の違う方が読めず
    NaT になる (= その対局がどの日にも入らず、画面から消える)。format="mixed" で避ける。
    ※ メインアプリ (main.py) と入力アプリ (ranking_view.py) に同じ関数がある。片方を直したらもう片方も直すこと。
    """
    try:
        return pd.to_datetime(s, errors="coerce", format="mixed")
    except (TypeError, ValueError):
        # format="mixed" が使えない古い pandas のとき: 1件ずつ変換する
        return pd.Series([pd.to_datetime(x, errors="coerce") for x in s], index=s.index)


def process_score_df(df):
    if df is None or df.empty:
        return pd.DataFrame(columns=EXPECTED_COLS + ["日時Obj", "論理日付"])
    df = df.copy()
    df.columns = df.columns.astype(str).str.strip()
    missing = [c for c in EXPECTED_COLS if c not in df.columns]
    if missing:
        return None
    numeric_cols = ["GameNo", "TableNo", "SetNo", "A着順", "B着順", "C着順"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
    df = df.fillna("")
    if "日時" in df.columns:
        df["日時Obj"] = parse_datetime_mixed(df["日時"])
        df["日時Obj"] = df["日時Obj"].fillna(pd.Timestamp("1900-01-01"))
        df["論理日付"] = (df["日時Obj"] - timedelta(hours=9)).dt.date
    return df


def load_score_data():
    processed = process_score_df(_get_all_or_stop()[SHEET_SCORE])
    if processed is None:
        clear_cache()
        processed = process_score_df(_get_all_or_stop()[SHEET_SCORE])
    if processed is None:
        st.error("スプレッドシートの列名が想定と異なります。管理者に連絡してください。")
        st.stop()
    return processed

_ZEN2HAN = str.maketrans("ＡＢＣＳａｂｃｓ０１２３４５６７８９", "ABCSabcs0123456789")


def _normalize_play_type(tp):
    """
    タイプ表記のゆれを吸収して A客 / AS / B客 / BS のいずれかに正規化する。該当しなければ None。
    メインアプリ (main.py) の同名関数と同じルール。片方を直したらもう片方も直すこと。
    """
    if tp is None:
        return None
    s = str(tp).strip()
    if not s:
        return None
    s = s.translate(_ZEN2HAN).replace(" ", "").replace("　", "").upper()
    s = re.sub(r"[（(].*?[)）]", "", s)
    if not s:
        return None
    if s in ("A客", "A", "AK", "ACLIENT"):
        return "A客"
    if s in ("B客", "B", "BK", "BCLIENT"):
        return "B客"
    if s in ("AS", "ASTAFF", "Aスタッフ".upper()):
        return "AS"
    if s in ("BS", "BSTAFF", "Bスタッフ".upper()):
        return "BS"
    if s.startswith("A") and s.endswith("S"):
        return "AS"
    if s.startswith("B") and s.endswith("S"):
        return "BS"
    if s.startswith("A"):
        return "A客"
    if s.startswith("B"):
        return "B客"
    return None


def _guess_type_from_name(name):
    """
    名前末尾の記号からタイプを推測する (最後の手段)。
    末尾 'BS' → BS、末尾 's'/'S' → AS (スタッフ扱い)、末尾 'B' → B客、それ以外 → A客
    """
    n = str(name).strip().translate(_ZEN2HAN).upper()
    if n.endswith("BS"):
        return "BS"
    if n.endswith("S"):
        return "AS"
    if n.endswith("B"):
        return "B客"
    return "A客"


def load_members():
    """
    メンバー一覧と、メンバーシートに書かれたタイプ (正規化済み) を取得。
    Returns: (names: list, member_type: dict 名前→タイプ。タイプ欄が空・読めない人は入らない)
    """
    df = _get_all_or_stop()[SHEET_MEMBER]
    if df.empty or "名前" not in df.columns:
        return [], {}
    df = df.fillna("")
    names = []
    member_type = {}
    has_type_col = "タイプ" in df.columns
    for _, row in df.iterrows():
        name = str(row["名前"]).strip()
        if not name or name in names:
            continue
        names.append(name)
        if has_type_col:
            t = _normalize_play_type(row["タイプ"])
            if t:
                member_type[name] = t
    return names, member_type


def get_last_played_types(df_score):
    """成績データから、各プレイヤーが最後の対局で使ったタイプを返す (名前→タイプ)"""
    if df_score is None or df_score.empty:
        return {}
    parts = []
    for seat in ["A", "B", "C"]:
        parts.append(pd.DataFrame({
            "t": df_score["日時Obj"] if "日時Obj" in df_score.columns else range(len(df_score)),
            "g": df_score["GameNo"],
            "name": df_score[f"{seat}さん"].astype(str).str.strip(),
            "type": df_score[f"{seat}タイプ"].astype(str),
        }))
    long = pd.concat(parts, ignore_index=True)
    norm = {v: _normalize_play_type(v) for v in long["type"].unique()}
    long["type"] = long["type"].map(norm)
    long = long[(long["name"] != "") & long["type"].notna()]
    long = long.sort_values(["t", "g"]).drop_duplicates("name", keep="last")
    return dict(zip(long["name"], long["type"]))


def resolve_player_type(name, member_type, last_types):
    """
    名前からタイプを決める。優先順: メンバーシートのタイプ → 前回の対局のタイプ → 名前から推測
    Returns: (type, 出どころの説明)
    """
    if name in member_type:
        return member_type[name], "メンバー登録"
    if name in last_types:
        return last_types[name], "前回の対局"
    return _guess_type_from_name(name), "名前から推測"

def _header(name, refresh=False):
    """シートの見出し行 (使い回す)"""
    meta = _sheet_meta()
    if refresh or name not in meta["header"]:
        ws = _get_ws(name)
        meta["header"][name] = [str(h).strip() for h in _with_retry(lambda: ws.row_values(1))]
    return meta["header"][name]


def _append(name, row_dict, cols):
    """シートの末尾に1行追記する (見出しの並びに合わせる)。日付などはスプレッドシートの手入力と同じ扱い (USER_ENTERED)"""
    ws = _get_ws(name)
    header = _header(name)
    if any(c not in header for c in cols):
        header = _header(name, refresh=True)
        missing = [c for c in cols if c not in header]
        if missing:
            raise RuntimeError(f"'{name}' シートに列が見つかりません: {missing}")
    values = [row_dict.get(h, "") for h in header]
    _with_retry(lambda: ws.append_row(values, value_input_option="USER_ENTERED", table_range="A1"),
                write=True)


def append_score_row(row_dict):
    """
    score シートの末尾に1行追記する。GameNo は保存直前に GameNo 列だけ読んで (最大値+1) 決める。
    シート全体を書き直さないので、他端末で入力された行を消すことはない。
    Returns: (ok, game_no or None, err or None)
    """
    try:
        ws = _get_ws(SHEET_SCORE)
        header = _header(SHEET_SCORE)
        if "GameNo" not in header:
            header = _header(SHEET_SCORE, refresh=True)
        col = header.index("GameNo") + 1
        nos = pd.to_numeric(pd.Series(_with_retry(lambda: ws.col_values(col))[1:], dtype=object), errors="coerce")
        game_no = int(nos.max()) + 1 if nos.notna().any() else 1
        new_row = dict(row_dict)
        new_row["GameNo"] = game_no
        _append(SHEET_SCORE, new_row, EXPECTED_COLS)
        clear_cache()
        return True, game_no, None
    except Exception as e:
        return False, None, f"{type(e).__name__}: {e}"


def _write_log(action, game_no, detail):
    """logs シートに1行追記する (メインアプリと同じ形)。失敗しても本体の処理は止めない"""
    try:
        _append(SHEET_LOG, {"日時": now_jst().strftime("%Y-%m-%d %H:%M:%S"), "操作": action,
                            "GameNo": int(game_no), "詳細": detail}, LOG_COLS)
    except Exception:
        pass


def _find_score_row(game_no):
    """score シートで GameNo が game_no の行番号 (1始まり) を最新の状態から探す。1行だけ見つかったときだけ返す"""
    ws = _get_ws(SHEET_SCORE)
    header = _header(SHEET_SCORE, refresh=True)
    col = header.index("GameNo") + 1
    nos = pd.to_numeric(pd.Series(_with_retry(lambda: ws.col_values(col))[1:], dtype=object), errors="coerce")
    hits = [i + 2 for i, v in enumerate(nos) if v == int(game_no)]
    if len(hits) != 1:
        raise RuntimeError(f"GameNo {game_no} の行が{'見つかりません' if not hits else '2つ以上あります'}"
                           "（ほかの端末やメインアプリで変更された可能性があります。再読み込みしてください）")
    return ws, header, hits[0]


def update_score_row(game_no, changes, detail):
    """
    score シートの1回分を、変わった列のセルだけ書き換える (行全体やシート全体は書き直さない)。
    changes = {列名: 新しい値}。Returns: (ok, err)
    """
    try:
        from gspread.utils import rowcol_to_a1
        ws, header, r = _find_score_row(game_no)
        missing = [c for c in changes if c not in header]
        if missing:
            raise RuntimeError(f"'{SHEET_SCORE}' シートに列が見つかりません: {missing}")
        data = [{"range": rowcol_to_a1(r, header.index(c) + 1), "values": [[v]]} for c, v in changes.items()]
        if data:
            _with_retry(lambda: ws.batch_update(data, value_input_option="USER_ENTERED"), write=True)
        _write_log("修正", game_no, detail)
        clear_cache()
        return True, None
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"


def delete_score_row(game_no, detail):
    """score シートから1回分 (1行) を消す。Returns: (ok, err)"""
    try:
        ws, _, r = _find_score_row(game_no)
        _with_retry(lambda: ws.delete_rows(r), write=True)
        _write_log("削除", game_no, detail)
        clear_cache()
        return True, None
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"


def _clean_fee_df(df):
    """集金記録を整形 (列をそろえ、数値化)"""
    if df is None or df.empty:
        return pd.DataFrame(columns=FEE_COLS)
    df = df.copy()
    df.columns = df.columns.astype(str).str.strip()
    for c in FEE_COLS:
        if c not in df.columns:
            df[c] = ""
    keep = FEE_COLS + (["_row"] if "_row" in df.columns else [])
    df = df[keep]
    df["TableNo"] = pd.to_numeric(df["TableNo"], errors="coerce")
    df["LastGameNo"] = pd.to_numeric(df["LastGameNo"], errors="coerce")
    df = df.dropna(subset=["TableNo", "LastGameNo"])
    df["TableNo"] = df["TableNo"].astype(int)
    df["LastGameNo"] = df["LastGameNo"].astype(int)
    df["枚数"] = pd.to_numeric(df["枚数"], errors="coerce").fillna(0).astype(int)
    df["日時"] = df["日時"].fillna("").astype(str)
    df["内訳"] = df["内訳"].fillna("").astype(str)
    return df.reset_index(drop=True)


def load_fee_collections():
    """集金記録 (表示用、60秒キャッシュ)。シートがまだ無ければ空。"""
    return _clean_fee_df(_get_all_or_stop()[SHEET_FEE])


def _read_score_and_fee_fresh():
    """保存直前用: 成績と集金記録を最新で (1回の通信で) 読む。fee には _row (シート上の行番号) が付く"""
    _sheet_titles(refresh=True)   # 他端末で fee_collections が作られていても拾えるように
    got = _batch_read([SHEET_SCORE, SHEET_FEE], keep_row=True)
    df_score = process_score_df(got[SHEET_SCORE].drop(columns="_row", errors="ignore"))
    if df_score is None:
        raise RuntimeError("成績シートの列名が想定と異なります")
    return df_score, _clean_fee_df(got[SHEET_FEE])


def _ensure_sheet(name, cols):
    """シートが無ければ作る (見出し行つき)。fee_collections / day_closings で使う"""
    try:
        return _get_ws(name)
    except SheetMissing:
        pass
    try:
        ws = _with_retry(lambda: _get_spreadsheet().add_worksheet(title=name, rows=200, cols=len(cols)),
                         write=True)
    except Exception as e:
        # 同時に他端末が作った場合など
        if name in _sheet_titles(refresh=True):
            return _get_ws(name)
        raise RuntimeError(
            f"'{name}' シートを自動で作れませんでした。スプレッドシートに '{name}' シートを作り、"
            f"1行目に [{', '.join(cols)}] と入れてください。（{type(e).__name__}: {e}）")
    _with_retry(lambda: ws.update([cols], "A1"), write=True)
    meta = _sheet_meta()
    meta["ws"][name] = ws
    meta["header"][name] = list(cols)
    if meta["titles"] is not None and name not in meta["titles"]:
        meta["titles"].append(name)
    return ws


def _ensure_fee_sheet():
    return _ensure_sheet(SHEET_FEE, FEE_COLS)


def collect_game_fee(table_no):
    """
    指定卓のゲーム代を集める (= 着順表に区切りを入れる)。
    他の端末の入力を取りこぼさないよう、成績も集金記録も最新を読み直してから計算し、集金記録に1行追記する。
    Returns: (ok, message, fee_info or None)
    """
    try:
        df_score, fees = _read_score_and_fee_fresh()
        df_open = get_open_section_games(df_score, fees, table_no, get_today_logical_date())
        if df_open.empty:
            return False, "前回の集金のあとの対局がありません", None
        info = calc_game_fee(df_open)
        new_row = {
            "日時": now_jst().strftime("%Y-%m-%d %H:%M:%S"),
            "TableNo": int(table_no),
            "LastGameNo": int(df_open["GameNo"].max()),
            "枚数": info["total"],
            "内訳": fee_breakdown_text(info),
        }
        _ensure_fee_sheet()
        _append(SHEET_FEE, new_row, FEE_COLS)
        clear_cache()
        return True, None, info
    except Exception as e:
        return False, f"{type(e).__name__}: {e}", None


def undo_last_fee_collection(table_no, target_date):
    """指定卓の、指定日の最後の集金 (区切り) を1行削除して取り消す。対局データには触らない。"""
    try:
        df_score, fees = _read_score_and_fee_fresh()
        day_nos = set(df_score.loc[(df_score["論理日付"] == target_date)
                                   & (df_score["TableNo"] == int(table_no)), "GameNo"])
        cand = fees[(fees["TableNo"] == int(table_no)) & fees["LastGameNo"].isin(day_nos)]
        if cand.empty:
            return False, "取り消せる集金がありません"
        row_no = int(cand.loc[cand["LastGameNo"].idxmax(), "_row"])
        ws = _get_ws(SHEET_FEE)
        _with_retry(lambda: ws.delete_rows(row_no), write=True)
        clear_cache()
        return True, None
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"


def _clean_close_df(df):
    """締めの記録を整形。論理日付は date に、LastGameNo は int に"""
    if df is None or df.empty:
        return pd.DataFrame(columns=CLOSE_COLS)
    df = df.copy()
    df.columns = df.columns.astype(str).str.strip()
    for c in CLOSE_COLS:
        if c not in df.columns:
            df[c] = ""
    keep = CLOSE_COLS + (["_row"] if "_row" in df.columns else [])
    df = df[keep]
    df["LastGameNo"] = pd.to_numeric(df["LastGameNo"], errors="coerce")
    df["論理日付"] = pd.to_datetime(df["論理日付"].astype(str).str.strip().str.lstrip("'"), errors="coerce").dt.date
    df["種類"] = df["種類"].fillna("").astype(str).str.strip()
    df = df.dropna(subset=["LastGameNo", "論理日付"])
    df = df[df["種類"].isin([CLOSE_MID, CLOSE_DAY])]
    df["LastGameNo"] = df["LastGameNo"].astype(int)
    df["日時"] = df["日時"].fillna("").astype(str)
    return df.reset_index(drop=True)


def load_closings():
    """締めの記録 (表示用、60秒キャッシュ)。シートがまだ無ければ空。"""
    return _clean_close_df(_get_all_or_stop()[SHEET_CLOSE])


def get_day_closings(closings, target_date):
    """指定日の締め {種類: 記録(dict)}。同じ種類が2行あれば後のもの"""
    out = {}
    if closings is None or closings.empty:
        return out
    for rec in closings[closings["論理日付"] == target_date].to_dict("records"):
        out[rec["種類"]] = rec
    return out


def count_tops(df_games):
    """対局群で、各タイプが何回トップ (1着) を取ったか。Returns: {"games", "tops": {タイプ: 回数}, "unknown"}"""
    tops = {t: 0 for t in TYPE_BUTTON_ORDER}
    unknown = 0
    for _, row in df_games.iterrows():
        for seat in ["A", "B", "C"]:
            try:
                rk = int(float(row.get(f"{seat}着順", 0)))
            except (TypeError, ValueError):
                rk = 0
            if rk != 1:
                continue
            t = _normalize_play_type(row.get(f"{seat}タイプ", ""))
            if t in tops:
                tops[t] += 1
            else:
                unknown += 1
    return {"games": len(df_games), "tops": tops, "unknown": unknown}


def _read_score_and_close_fresh():
    """保存直前用: 成績と締めの記録を最新で読む。締めには _row (シート上の行番号) が付く"""
    _sheet_titles(refresh=True)
    got = _batch_read([SHEET_SCORE, SHEET_CLOSE], keep_row=True)
    df_score = process_score_df(got[SHEET_SCORE].drop(columns="_row", errors="ignore"))
    if df_score is None:
        raise RuntimeError("成績シートの列名が想定と異なります")
    return df_score, _clean_close_df(got[SHEET_CLOSE])


def do_closing(kind):
    """
    今日の中間締め / 1日締めを記録する (day_closings に1行追記)。
    他の端末の入力を取りこぼさないよう、成績も締めの記録も最新を読み直してから決める。
    Returns: (ok, message, counts or None)
    """
    try:
        today = get_today_logical_date()
        df_score, closings = _read_score_and_close_fresh()
        done = get_day_closings(closings, today)
        if kind in done:
            return False, f"今日の{kind}はもう済んでいます（ほかの端末で押された可能性があります）", None
        if kind == CLOSE_MID and CLOSE_DAY in done:
            return False, "今日はもう1日締めが済んでいます", None
        df_day = get_games_by_date(df_score, today)
        if df_day.empty:
            return False, "今日の対局がまだありません", None
        last_no = int(df_day["GameNo"].max())
        c = count_tops(df_day)
        new_row = {
            "日時": now_jst().strftime("%Y-%m-%d %H:%M:%S"),
            "論理日付": "'" + today.isoformat(),   # 文字のまま保存する (日付に変換されないように)
            "種類": kind,
            "LastGameNo": last_no,
            "回数": c["games"],
            **{t: c["tops"][t] for t in TYPE_BUTTON_ORDER},
            "不明": c["unknown"],
        }
        _ensure_sheet(SHEET_CLOSE, CLOSE_COLS)
        _append(SHEET_CLOSE, new_row, CLOSE_COLS)
        clear_cache()
        return True, None, c
    except Exception as e:
        return False, f"{type(e).__name__}: {e}", None


def undo_closing(kind, target_date):
    """指定日の締めを1行削除して取り消す。対局データには触らない。"""
    try:
        _, closings = _read_score_and_close_fresh()
        cand = closings[(closings["論理日付"] == target_date) & (closings["種類"] == kind)]
        if cand.empty:
            return False, "取り消せる締めがありません"
        row_no = int(cand["_row"].max())
        ws = _get_ws(SHEET_CLOSE)
        _with_retry(lambda: ws.delete_rows(row_no), write=True)
        clear_cache()
        return True, None
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"


# ==========================================
# 4. 日付・集計ヘルパー
# ==========================================
def get_today_logical_date():
    return (now_jst() - timedelta(hours=9)).date()

def get_games_by_date(df, target_date):
    """指定した論理日付の対局を返す (卓・SetNo・GameNo順)"""
    if df is None or df.empty:
        return pd.DataFrame()
    df_day = df[df["論理日付"] == target_date].copy()
    if df_day.empty:
        return df_day
    sort_keys = [k for k in ["TableNo", "SetNo", "GameNo"] if k in df_day.columns]
    if sort_keys:
        df_day = df_day.sort_values(sort_keys).reset_index(drop=True)
    return df_day

def calc_game_fee(df_games):
    """
    対局群のゲーム代を計算する。トップ (1着) を取った人が、自分のタイプの枚数を払う。
    備考 (東１終了・２人飛ばし・５連勝〜) があれば、その局の分を値引きする (メインアプリと同じ)。
    Returns: {"games": 対局数, "lines": [(タイプ, トップ回数, 1回の枚数, 小計)],
              "discounts": [(備考, 回数, 1回の値引き, 値引き小計)], "gross": 値引き前, "discount": 値引き合計,
              "total": 値引き後の合計枚数, "unknown": タイプ不明のトップ回数}
    """
    tops = {t: 0 for t in TYPE_BUTTON_ORDER}
    unknown = 0
    disc_count = {t: 0 for t in NOTE_DISCOUNTS}
    for _, row in df_games.iterrows():
        for tag in note_tags(row.get("備考", "")):
            disc_count[tag] += 1
        for seat in ["A", "B", "C"]:
            try:
                rk = int(float(row.get(f"{seat}着順", 0)))
            except (TypeError, ValueError):
                rk = 0
            if rk != 1:
                continue
            t = _normalize_play_type(row.get(f"{seat}タイプ", ""))
            if t in tops:
                tops[t] += 1
            else:
                unknown += 1
    lines = [(t, tops[t], GAME_FEE_TABLE[t], tops[t] * GAME_FEE_TABLE[t])
             for t in TYPE_BUTTON_ORDER if tops[t] > 0]
    discounts = [(t, disc_count[t], NOTE_DISCOUNTS[t], disc_count[t] * NOTE_DISCOUNTS[t])
                 for t in NOTE_DISCOUNTS if disc_count[t] > 0]
    gross = sum(l[3] for l in lines)
    discount = sum(d[3] for d in discounts)
    return {"games": len(df_games), "lines": lines, "discounts": discounts,
            "gross": gross, "discount": discount, "total": gross - discount, "unknown": unknown}


def fee_breakdown_text(info, sep="、"):
    """例: 'A客トップ 2回×3枚=6枚、Aスタッフトップ 1回×1枚=1枚'"""
    parts = [f"{TYPE_LABELS[t]}トップ {n}回×{unit}枚={sub}枚" for t, n, unit, sub in info["lines"]]
    parts += [f"値引き {t} {n}回×{unit}枚=−{sub}枚" for t, n, unit, sub in info.get("discounts", [])]
    if info.get("unknown"):
        parts.append(f"タイプ不明のトップ {info['unknown']}回（0枚で計算）")
    return sep.join(parts)


def get_fee_cuts(fees, table_no):
    """指定卓の区切り (集金) を LastGameNo の昇順で返す"""
    if fees is None or fees.empty:
        return []
    f = fees[fees["TableNo"] == int(table_no)].sort_values("LastGameNo")
    return f.to_dict("records")


def get_open_section_games(df_score, fees, table_no, target_date):
    """指定卓・指定日の対局のうち、まだゲーム代を集めていないもの (最後の区切りより後)"""
    df_day = get_games_by_date(df_score, target_date)
    if df_day.empty:
        return df_day
    df_tbl = df_day[df_day["TableNo"] == int(table_no)]
    cuts = get_fee_cuts(fees, table_no)
    if cuts:
        df_tbl = df_tbl[df_tbl["GameNo"] > cuts[-1]["LastGameNo"]]
    return df_tbl.sort_values("GameNo").reset_index(drop=True)


def get_next_game_no(df):
    if df is None or df.empty or "GameNo" not in df.columns:
        return 1
    max_no = pd.to_numeric(df["GameNo"], errors='coerce').fillna(0).max()
    return int(max_no) + 1

def get_available_dates(df):
    """対局が存在する論理日付のリストを新しい順で返す"""
    if df is None or df.empty or "論理日付" not in df.columns:
        return []
    dates = sorted([d for d in df["論理日付"].unique() if d and d != date(1900, 1, 1)], reverse=True)
    return dates


# ==========================================
# 5. 紙の着順表を描画する (写真の形式を再現)
# ==========================================
def render_paper_sheet(df_day, target_date, fees=None):
    """
    指定日の対局を「紙の着順表」風に表示する。
    卓ごとに、各局の実際の着席メンバーを正確に表示。
    メンバーが変わったタイミングで名前行を挿入する。
    ゲーム代を集めたところで区切り、区切りごとにゲーム代の枚数と内訳を出す。
    """
    if df_day.empty:
        st.info("この日の対局データはありません。")
        return

    tables = sorted(df_day["TableNo"].unique()) if "TableNo" in df_day.columns else [1]

    for table_no in tables:
        df_tbl = df_day[df_day["TableNo"] == table_no].copy()
        if df_tbl.empty:
            continue
        st.markdown(_html(f'<div class="paper-title" style="border-top: 4px solid {table_color(table_no)};">'
                          f'{table_mark(table_no)} {int(table_no)}卓</div>'), unsafe_allow_html=True)
        _render_table(df_tbl, get_fee_cuts(fees, table_no))


def _fee_row_html(info, cut):
    """区切りの最後に入れる「ゲーム代」の行"""
    if cut is not None:
        t = str(cut.get("日時", ""))
        hhmm = t[11:16] if len(t) >= 16 else ""
        status = f'<span class="fee-status done">✅ 集金済 {hhmm}</span>'
    else:
        status = '<span class="fee-status open">⏳ 未集金（ここまでの分）</span>'
    detail = "".join(
        f'<div>{TYPE_LABELS[t]}のトップ <b>{n}回</b> × {unit}枚 = <b>{sub}枚</b></div>'
        for t, n, unit, sub in info["lines"]
    )
    detail += "".join(
        f'<div class="fee-disc">値引き {t} <b>{n}回</b> × {unit}枚 = <b>−{sub}枚</b></div>'
        for t, n, unit, sub in info.get("discounts", [])
    )
    if info.get("unknown"):
        detail += f'<div>タイプ不明のトップ {info["unknown"]}回（0枚で計算）</div>'
    return (
        '<tr class="fee-row"><td colspan="4">'
        f'<div class="fee-head">💰 ゲーム代 <b class="fee-total">{info["total"]}枚</b>'
        f'<span class="fee-games">（{info["games"]}回）</span>{status}</div>'
        f'<div class="fee-detail">{detail}</div>'
        '</td></tr>'
    )


PAPER_CHUNK = 20   # 着順表の1列の回数。紙の着順表と同じく、左の列を上から下まで埋めてから次の列へ進む


def _split_chunks(items, size=PAPER_CHUNK):
    """items を先頭から size 個ずつの列に分ける (最後の列だけ短くなる)。入力が増えても前の列は動かない"""
    return [items[i:i + size] for i in range(0, len(items), size)]


def _paper_html(blocks, foot=""):
    """
    着順表の列を並べる。幅のある画面 (iPad・PC) では左から右へ同じ幅で並べ (CSS の .paper-cols)、
    スマホでは縦に1本につなげて見せる。どちらも 1列目の上 → 下 → 2列目の上 → 下 … の順に読む。
    """
    inner = "".join(f'<div class="paper-block">{b}</div>' for b in blocks)
    return f'<div class="paper-wrap"><div class="paper-cols">{inner}</div>{foot}</div>'


def _sheet_order(df_tbl, cuts=None):
    """
    着順表に出す順に並べる。_sec = 区切り番号 (この回より前にある集金の数)、_no = 表の「回」の番号。
    同じ区切り・同じセットの中は時刻順 (後から日時を指定して入れた回も正しい位置に)。同じ時刻なら入力順 (GameNo)
    """
    cut_nos = [int(c["LastGameNo"]) for c in (cuts or [])]
    df_tbl = df_tbl.copy()
    df_tbl["_sec"] = [bisect.bisect_left(cut_nos, int(g)) for g in df_tbl["GameNo"]]
    sort_keys = ["_sec"] + [k for k in ["SetNo", "日時Obj", "GameNo"] if k in df_tbl.columns]
    df_tbl = df_tbl.sort_values(sort_keys, kind="stable").reset_index(drop=True)
    df_tbl["_no"] = range(1, len(df_tbl) + 1)
    return df_tbl


def _render_table(df_tbl, cuts=None):
    """
    1卓分の着順表を描画。
    各局の実際のメンバーを表示し、メンバーが変わったら名前行を差し込む。
    名前抜けを防ぐため、局ごとに実データを参照する。
    cuts (集金の区切り) があれば、区切りごとにゲーム代の行を入れる。
    """
    cuts = cuts or []
    cut_nos = [int(c["LastGameNo"]) for c in cuts]

    df_tbl = _sheet_order(df_tbl, cuts)

    thead = ('<thead><tr><th class="col-no">回</th><th class="seat-head-A">A席</th>'
             '<th class="seat-head-B">B席</th><th class="seat-head-C">C席</th></tr></thead>')

    # 1回ごとに (区切り番号, メンバー, 名前行, 着順行, この回のあとに入れるゲーム代の行) を作り、20回ずつの列に分ける
    totals = {"done": 0, "open": 0}
    entries = []
    game_idx = 0
    for sec, df_sec in df_tbl.groupby("_sec", sort=True):
        n_sec = len(df_sec)
        for i, (_, row) in enumerate(df_sec.iterrows()):
            game_idx += 1
            cur_names, cur_types, cur_ranks = {}, {}, {}
            for seat in ["A", "B", "C"]:
                cur_names[seat] = str(row.get(f"{seat}さん", "")).strip()
                cur_types[seat] = str(row.get(f"{seat}タイプ", "")).strip()
                try:
                    cur_ranks[seat] = int(float(row.get(f"{seat}着順", 0)))
                except (TypeError, ValueError):
                    cur_ranks[seat] = 0

            # 名前かタイプが前の回と変わったら名前行を出し直す (同じ人でも途中でタイプを変えたら分かるように)
            members = tuple(cur_names[x] for x in "ABC") + tuple(cur_types[x] for x in "ABC")
            name_html = '<tr class="name-row"><td class="col-no"></td>'
            for seat in ["A", "B", "C"]:
                nm = cur_names[seat] or "-"
                tp = cur_types[seat]
                type_disp = f'<span class="name-type">{tp}</span>' if tp else ""
                name_html += f'<td>{nm}{type_disp}</td>'
            name_html += '</tr>'

            # 着順行 (回の番号はその日・その卓での連番。内部用の GameNo は出さない)
            row_html = f'<tr><td class="col-no">{game_idx}</td>'
            for seat in ["A", "B", "C"]:
                rk = cur_ranks[seat]
                if rk == 1:
                    tags = note_tags(row.get("備考", ""))
                    mark = "".join(f'<span class="memo-tag">{NOTE_SHORT[t]}−{NOTE_DISCOUNTS[t]}</span>' for t in tags)
                    row_html += f'<td class="rank-cell rank1">1{mark}</td>'
                elif rk in [2, 3]:
                    row_html += f'<td class="rank-cell">{rk}</td>'
                else:
                    row_html += '<td class="empty-cell">·</td>'
            row_html += '</tr>'

            fee_html = ""
            if i == n_sec - 1:   # 区切りの最後の回のあとにゲーム代の行
                info = calc_game_fee(df_sec)
                cut = cuts[sec] if sec < len(cuts) else None
                totals["done" if cut is not None else "open"] += info["total"]
                fee_html = _fee_row_html(info, cut)
            entries.append((sec, members, name_html, row_html, fee_html))

    blocks = []
    for col in _split_chunks(entries):
        body, prev_sec, prev_members = "", None, None   # 列の最初と区切りのあとは名前行を出し直す
        for sec, members, name_html, row_html, fee_html in col:
            if sec != prev_sec:
                prev_members = None
                prev_sec = sec
            if members != prev_members:
                body += name_html
                prev_members = members
            body += row_html + fee_html
        blocks.append(f'<table class="paper-table">{thead}<tbody>{body}</tbody></table>')

    # この日の合計
    total = totals["done"] + totals["open"]
    foot = (f'<table class="paper-table paper-foot"><tbody><tr class="gamecount-row"><td class="col-no">計</td>'
            f'<td colspan="3" style="text-align:left;padding-left:8px;">この卓のゲーム代 合計 <strong>{total}枚</strong>')
    if totals["open"]:
        foot += f'（集金済 {totals["done"]}枚・未集金 {totals["open"]}枚）'
    foot += '</td></tr></tbody></table>'

    html = _paper_html(blocks, foot)
    st.markdown(html, unsafe_allow_html=True)


# ==========================================
# 6. 成績を付けるページ
# ==========================================
SEATS = ["A", "B", "C"]
SEAT_LABELS = {"A": "A席", "B": "B席", "C": "C席"}
TYPE_SHORT = {"A客": "A客", "B客": "B客", "AS": "AS", "BS": "BS"}

# 卓ごとの色 (2卓以上立ったとき、どの卓に入力しているか一目で分かるように)。
# 印の色と、カード・着順表の見出しの色をそろえている。文字色(白)とのコントラスト比 4.5 以上。
TABLE_MARKS = ["🔵", "🟠", "🟢", "🟣", "🔴", "🟤", "⚫", "🟡"]
TABLE_COLORS = ["#3f6597", "#a85a1f", "#2f7449", "#7c4593", "#a83a3a", "#6b4a2f", "#3d3d3d", "#8a6d00"]


def table_mark(t):
    return TABLE_MARKS[(int(t) - 1) % len(TABLE_MARKS)]


def table_color(t):
    return TABLE_COLORS[(int(t) - 1) % len(TABLE_COLORS)]


def table_tag_html(t, extra=""):
    return f'<span class="tbl-tag" style="background:{table_color(t)}">{int(t)}卓{extra}</span>'


def _seat_key(table_no, seat):
    """名前欄のキー。卓ごとに別にして、卓を切り替えても各卓のメンバーを覚えておく"""
    return f"sel_name_{int(table_no)}_{seat}"


def _table_mem(table_no):
    """
    卓ごとの入力内容 (名前・セット・手で変えたタイプ) の控え。
    Streamlit は画面に出ていない入力欄の値を捨てるので、別の卓に切り替えて戻ってきたときに、ここから戻す。
    """
    mem = st.session_state.setdefault("table_mem", {})
    return mem.setdefault(int(table_no), {"names": {}, "set": None, "types": {}})


def _clear_seats(table_no):
    """
    その卓を全員空席にする (ボタンの on_click、またはウィジェットを描く前に呼ぶ)。
    キーを del するだけだとブラウザ側の表示が残るので、値を None に明示的にセットする。
    """
    for seat in SEATS:
        st.session_state[_seat_key(table_no, seat)] = None
    _table_mem(table_no)["names"] = {}
    st.session_state["input_round"] = st.session_state.get("input_round", 0) + 1


def _rank_key(mkey, seat):
    return f"rank_{mkey}_{seat}"


def _on_rank_change(mkey, seat):
    """
    ある席の着順を選んだとき (on_change):
    - 同じ着順がほかの席に付いていたら、その席と入れ替える (重複でエラーにしない)
    - 2人の着順が決まったら、残りの1人に残りの着順を自動で入れる
    """
    ss = st.session_state
    prev = ss.setdefault("rank_prev", {}).get(mkey, {})
    new = ss.get(_rank_key(mkey, seat))
    if new is not None:
        for t in SEATS:
            if t != seat and ss.get(_rank_key(mkey, t)) == new:
                ss[_rank_key(mkey, t)] = prev.get(seat)   # この席の元の着順と入れ替え
    vals = {x: ss.get(_rank_key(mkey, x)) for x in SEATS}
    filled = [x for x in SEATS if vals[x] is not None]
    if len(filled) == 2 and len({vals[x] for x in filled}) == 2:
        empty = next(x for x in SEATS if vals[x] is None)
        ss[_rank_key(mkey, empty)] = ({1, 2, 3} - {vals[x] for x in filled}).pop()
    ss["rank_prev"][mkey] = {x: ss.get(_rank_key(mkey, x)) for x in SEATS}


def _step_label(left, right=""):
    """小さな見出し (左に何をするか、右に補足)"""
    st.markdown(_html(f'<div class="step-label"><b>{left}</b><span>{right}</span></div>'),
                unsafe_allow_html=True)


def _chips_html(seat_info, ranks):
    """
    上に並べる選手チップ。
    - 着順が決まったら「1着」などを表示し、トップの人をこげ茶で強調 (トップがゲーム代を払うので)
    - まだ着順が無いうちは、次に名前を入れる席をこげ茶で強調
    """
    top = next((s for s, r in ranks.items() if r == 1), None)
    first_empty = next((s for s in SEATS if not seat_info[s]["name"]), None)
    active = top or first_empty
    html = '<div class="chips">'
    for s in SEATS:
        nm, tp = seat_info[s]["name"], seat_info[s]["type"]
        if nm:
            sub = f"{ranks[s]}着" if s in ranks else "---"
            sub += f"・{TYPE_SHORT.get(tp, '')}" if tp else ""
            cls = "active" if s == active else "done"
            check = '<span class="chip-check">✓</span>'
            name_html = nm
        else:
            sub, cls, check, name_html = "---", ("active" if s == active else "empty"), "", "未選択"
        html += (f'<div class="chip {cls}">{check}<div class="chip-seat">{SEAT_LABELS[s]}</div>'
                 f'<div class="chip-name">{name_html}</div><div class="chip-sub">{sub}</div></div>')
    return html + "</div>"


def get_table_status(df_today, fees, today):
    """
    今日の卓ごとの状況。{卓番: {"games": 局数, "last_set": 最後のセット, "open_fee": 未集金枚数,
    "last_members": 最後の局の3人, "last_time": 最後の局の時刻}}
    """
    status = {}
    if df_today is None or df_today.empty:
        return status
    for t, g in df_today.groupby("TableNo"):
        g = g.sort_values(["日時Obj", "GameNo"])
        last = g.iloc[-1]
        df_open = get_open_section_games(df_today, fees, int(t), today)
        status[int(t)] = {
            "games": len(g),
            "last_set": int(last["SetNo"]) if str(last["SetNo"]).strip() else 1,
            "open_fee": calc_game_fee(df_open)["total"] if not df_open.empty else 0,
            "last_members": {str(last[f"{s}さん"]).strip() for s in SEATS} - {""},
            "last_time": last["日時Obj"],
        }
    return status


def page_input():
    with st.spinner("データ読込中..."):
        df_all = load_score_data()
        member_names, member_type = load_members()
    last_types = get_last_played_types(df_all)

    if not member_names:
        st.warning("メンバーが登録されていません。管理画面から先にメンバー登録をしてください。")
        return

    ss = st.session_state
    ss.setdefault("input_round", 0)   # 保存のたびに+1 → 着順ボタンをリセット
    ss.setdefault("cur_table", 1)

    today = get_today_logical_date()
    fees = load_fee_collections()
    df_today = get_games_by_date(df_all, today)
    tstat = get_table_status(df_today, fees, today)

    # 保存後のリセット (ウィジェットを描く前でないと値を書き換えられないので、ここで行う)
    pending = ss.pop("input_pending_reset", None)
    if pending:
        # 「日時を指定する」は1局ごと。付けたままだと次の局も同じ時刻で記録されてしまうので外す
        ss["input_use_custom_dt"] = False
        if pending.get("seats"):
            _clear_seats(pending["table"])

    # 直前の保存結果 (rerun後に表示する)
    flash = ss.pop("input_flash", None)
    if flash:
        st.success(flash)

    # 上のカードと選手チップは、下で名前・着順が決まってから中身を入れる
    sum_slot = st.empty()
    chips_slot = st.empty()

    # --- 卓を選ぶ (今日立っている卓 + 新しい卓) ---
    active_tables = sorted(set(tstat) | {int(ss["cur_table"])})
    new_table = max(active_tables) + 1
    options = active_tables + [new_table]

    def _table_label(t):
        if t == new_table:
            return f"＋ {t}卓"
        n = tstat.get(t, {}).get("games", 0)
        return f"{table_mark(t)} {t}卓 {n}回" if n else f"{table_mark(t)} {t}卓"

    running = len(tstat)
    _step_label("卓", f"今日 {running}卓 立っています" if running >= 2 else "2卓以上立ったら、ここで切り替えます")
    with st.container(key="table_pick_area"):
        picked_table = st.segmented_control(
            "入力する卓", options, default=int(ss["cur_table"]), format_func=_table_label,
            key="table_pick", label_visibility="collapsed",
        )
    table_no = int(picked_table) if picked_table is not None else int(ss["cur_table"])
    ss["cur_table"] = table_no
    color = table_color(table_no)

    tmem = _table_mem(table_no)

    # --- セット (卓ごと。初めて開いたときは、その卓の今日最後のセット) ---
    set_key = f"input_set_no_{table_no}"
    if set_key not in ss:
        ss[set_key] = tmem["set"] or tstat.get(table_no, {}).get("last_set", 1)
    with st.container(key="table_set"):
        col_s, col_info = st.columns(2)
        with col_s:
            set_no = st.number_input("セット", min_value=1, step=1, key=set_key)
            tmem["set"] = int(set_no)
        with col_info:
            st.markdown(_html(f'<div class="table-now">{table_tag_html(table_no)}'
                              f'<span>に入力します</span></div>'), unsafe_allow_html=True)

    # --- メンバー (卓ごとに覚えておく) ---
    _step_label("メンバー", "文字を打つと絞り込めます")
    seat_info = {}
    for seat in SEATS:
        k = _seat_key(table_no, seat)
        if k not in ss and tmem["names"].get(seat) in member_names:
            ss[k] = tmem["names"][seat]      # 別の卓から戻ってきたとき
        sel_name = st.selectbox(
            SEAT_LABELS[seat], member_names, index=None,
            placeholder="名前を選択", key=k,
        )
        tmem["names"][seat] = sel_name
        sel_type = None
        if sel_name:
            auto_type, source = resolve_player_type(sel_name, member_type, last_types)
            # 名前ごとに別キーにすることで、名前を変えたらタイプも自動で切り替わる
            tkey = f"sel_type_{table_no}_{seat}_{sel_name}"
            if tkey not in ss and (seat, sel_name) in tmem["types"]:
                ss[tkey] = tmem["types"][(seat, sel_name)]   # 手で変えたタイプも戻す
            # 控えから値を戻したときに default も渡すと、Streamlit が画面に警告を出すので渡さない
            picked = st.segmented_control(
                f"{seat}席のタイプ", TYPE_BUTTON_ORDER,
                default=None if tkey in ss else auto_type,
                format_func=lambda t: TYPE_LABELS[t],
                key=tkey, label_visibility="collapsed",
            )
            sel_type = picked or auto_type
            if sel_type != auto_type:
                tmem["types"][(seat, sel_name)] = sel_type
            else:
                tmem["types"].pop((seat, sel_name), None)
            note = source if sel_type == auto_type else "手動で変更"
            st.caption(f"タイプ: {TYPE_LABELS[sel_type]}（{note}）")
        seat_info[seat] = {"name": sel_name, "type": sel_type}

    names_sel = [seat_info[s]["name"] for s in SEATS]
    members_ready = all(names_sel) and len(set(names_sel)) == 3

    # --- 他の卓にも入っている人がいないか (卓の選び間違い防止) ---
    elsewhere = []
    for nm in [n for n in names_sel if n]:
        for t, info in tstat.items():
            if t != table_no and nm in info["last_members"]:
                elsewhere.append(f"{nm}さんは {t}卓の最後の回（{info['last_time'].strftime('%H:%M')}）にも入っています")
        for t in active_tables:
            if t != table_no and nm in set(_table_mem(t)["names"].values()):
                elsewhere.append(f"{nm}さんは {t}卓の入力欄にも入っています")
    if elsewhere:
        st.warning("入力する卓が合っているか確認してください。\n\n" + "\n\n".join(dict.fromkeys(elsewhere)))

    # --- 着順 (席ごとに何着かをタップ。2人決めると残りは自動) ---
    ranks = {}
    rank_area = st.container(key="rank_area")  # 着順のキーは大きくする (CSS は .st-key-rank_area)
    with rank_area:
        if not all(names_sel):
            _step_label("着順", "3人とも名前を選ぶと入力できます")
        elif not members_ready:
            _step_label("着順")
            st.error("同じ人が複数の席にいます")
        else:
            mkey = f"{table_no}_{ss['input_round']}_{'|'.join(names_sel)}"
            n_set = sum(ss.get(_rank_key(mkey, x)) is not None for x in SEATS)
            hint = ("各席の着順をタップ（2人決めると残りは自動）" if n_set < 2
                    else "変えるときは、その席の着順をタップ（入れ替わります）")
            _step_label("着順", hint)
            for seat in SEATS:
                val = st.segmented_control(
                    f"{SEAT_LABELS[seat]}　{seat_info[seat]['name']}", [1, 2, 3],
                    format_func=lambda r: f"{r}着", key=_rank_key(mkey, seat),
                    on_change=_on_rank_change, args=(mkey, seat),
                )
                if val is not None:
                    ranks[seat] = int(val)
            if len(ranks) == 3 and sorted(ranks.values()) != [1, 2, 3]:
                st.error("着順が重複しています")
                ranks = {}

    can_save = members_ready and len(ranks) == 3 and sorted(ranks.values()) == [1, 2, 3]

    # --- 備考 (タップで選ぶ。複数選べる。保存すると空に戻る) ---
    memo_sel = st.pills(
        "備考（あれば）", MEMO_OPTIONS, selection_mode="multi",
        format_func=lambda m: f"{m}（−{NOTE_DISCOUNTS[m]}枚）",
        key=f"memo_{table_no}_{ss['input_round']}",
    ) or []
    memo = MEMO_SEP.join(m for m in MEMO_OPTIONS if m in memo_sel)
    if memo_sel:
        st.markdown(_html(
            f'<div class="memo-total">この回のゲーム代から <b>−{note_discount(memo)}枚</b> 値引き'
            f'（{"・".join(f"{m} −{NOTE_DISCOUNTS[m]}" for m in MEMO_OPTIONS if m in memo_sel)}）</div>'),
            unsafe_allow_html=True)

    # --- 日時 (通常は保存した時刻。後から付けるときだけ指定) ---
    with st.expander("日時（後から付けるときだけ）"):
        use_custom_dt = st.checkbox("日時を指定する", key="input_use_custom_dt")
        col_dt, col_time = st.columns(2)
        with col_dt:
            input_date = st.date_input("日付", value=now_jst().date(), key="input_date",
                                       disabled=not use_custom_dt)
        with col_time:
            input_time = st.time_input("時刻", value=now_jst().time().replace(second=0, microsecond=0),
                                       key="input_time", disabled=not use_custom_dt)

    # --- 操作ボタン (画面の下に固定。CSS は .st-key-action_bar) ---
    games_here = tstat.get(table_no, {}).get("games", 0)
    with st.container(key="action_bar"):
        st.markdown(_html(f'<div class="bar-target">入力先 {table_tag_html(table_no)}'
                          f'<span>セット{int(set_no)}・{games_here + 1}回目</span></div>'),
                    unsafe_allow_html=True)
        c_clear, c_next, c_end = st.columns([1, 1.45, 1.45])
        with c_clear:
            st.button("クリア", use_container_width=True, on_click=_clear_seats, args=(table_no,),
                      disabled=not any(names_sel), help="この卓を全員空席に戻します", key="btn_clear")
        with c_next:
            save_continue = st.button("保存して次へ", type="primary", disabled=not can_save,
                                      use_container_width=True, key="btn_save_next",
                                      help="同じメンバーのまま次の回へ")
        with c_end:
            save_reset = st.button("保存して空席に", disabled=not can_save,
                                   use_container_width=True, key="btn_save_reset",
                                   help="保存して、この卓を空席に戻します")

    if (save_continue or save_reset) and can_save:
        if use_custom_dt:
            dt_str = f"{input_date.strftime('%Y-%m-%d')} {input_time.strftime('%H:%M:%S')}"
        else:
            dt_str = now_jst().strftime("%Y-%m-%d %H:%M:%S")

        signature = (int(table_no), int(set_no), tuple(names_sel), tuple(ranks[s] for s in SEATS))
        last = ss.get("input_last_saved")
        if last and last[0] == signature and time.time() - last[1] < 15:
            # ボタンの二度押し対策
            st.warning("同じ内容を保存したばかりなので、二重登録を防ぐため保存しませんでした。")
        else:
            row = {
                "TableNo": int(table_no), "SetNo": int(set_no),
                "日時": dt_str, "備考": memo,
            }
            for s in SEATS:
                row[f"{s}さん"] = seat_info[s]["name"]
                row[f"{s}タイプ"] = seat_info[s]["type"]
                row[f"{s}着順"] = int(ranks[s])
            with st.spinner("保存中..."):
                ok, saved_no, err = append_score_row(row)
            if ok:
                ss["input_last_saved"] = (signature, time.time())
                order = sorted(SEATS, key=lambda s: ranks[s])
                result = " → ".join(seat_info[s]["name"] for s in order)
                ss["input_flash"] = f"{table_mark(table_no)} {int(table_no)}卓に保存しました：{result}"
                ss["input_round"] += 1
                ss["input_pending_reset"] = {"table": int(table_no), "seats": bool(save_reset)}
                st.rerun()
            else:
                st.error(f"保存に失敗しました（もう一度押してください）: {err}")

    # --- ゲーム代 (集めると着順表に区切りが入る) ---
    open_fee = render_fee_collect_section(df_all, fees, int(table_no), today)

    # --- この卓の今日の記録 (入力の確認用) ---
    df_tbl = df_today[df_today["TableNo"] == int(table_no)] if not df_today.empty else df_today
    if not df_tbl.empty:
        _step_label(f"{table_mark(table_no)} {int(table_no)}卓の今日の記録", f"{len(df_tbl)}回")
        _render_table(df_tbl.reset_index(drop=True), get_fee_cuts(fees, table_no))
        render_fix_section(df_tbl, fees, closings_today=get_day_closings(load_closings(), today),
                           table_no=int(table_no), member_names=member_names)

    # --- 上のカード・選手チップの中身 (ここまでで分かった内容で描く) ---
    fee_txt = f"未集金 {open_fee}枚" if open_fee else "未集金なし"
    others = [t for t in sorted(tstat) if t != table_no]
    others_html = ""
    if others:
        others_html = '<div class="sum-others">ほかの卓: ' + " ".join(
            table_tag_html(t, f" {tstat[t]['games']}回") for t in others) + "</div>"
    sum_slot.markdown(_html(f"""
        <div class="sum-card" style="border-left: 6px solid {color};">
          <div>
            <span class="sum-label">{table_tag_html(table_no)} セット{int(set_no)}</span>
            {others_html}
          </div>
          <span class="sum-value">{len(df_tbl) + 1}回目 <small>/ {fee_txt}</small></span>
        </div>
    """), unsafe_allow_html=True)
    chips_slot.markdown(_html(_chips_html(seat_info, ranks)), unsafe_allow_html=True)


def _game_text(row, ranks=None, names=None, types=None, memo=None):
    """1回分を文字にする (ログ用)。例: 'A席 田中(A客) 1着 / B席 … / 備考 東１終了'"""
    parts = []
    for s in SEATS:
        nm = (names or {}).get(s, str(row.get(f"{s}さん", "")).strip())
        tp = (types or {}).get(s, _normalize_play_type(row.get(f"{s}タイプ", "")) or str(row.get(f"{s}タイプ", "")))
        rk = (ranks or {}).get(s, _int_rank(row.get(f"{s}着順")))
        parts.append(f"{SEAT_LABELS[s]} {nm}({tp}) {rk}着")
    m = memo if memo is not None else str(row.get("備考", "") or "")
    if m:
        parts.append(f"備考 {m}")
    return " / ".join(parts)


def _int_rank(v):
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return None


def render_fix_section(df_tbl, fees, closings_today, table_no, member_names):
    """
    「まちがいを直す」: この卓の今日の回を選んで、着順 (と名前・タイプ・備考) を直す、または消す。
    シートは、その回の行の変わったセルだけを書き換える (GameNo で行を探す)。
    """
    ss = st.session_state
    cuts = get_fee_cuts(fees, table_no)
    df_o = _sheet_order(df_tbl, cuts)
    rows = {int(r["GameNo"]): r for r in df_o.to_dict("records")}

    def _label(g):
        r = rows[g]
        order = sorted(SEATS, key=lambda s: _int_rank(r.get(f"{s}着順")) or 9)
        tops = " → ".join(str(r.get(f"{s}さん", "")).strip() for s in order)
        t = r.get("日時Obj")
        hhmm = t.strftime("%H:%M") if pd.notna(t) else ""
        return f"{r['_no']}回目（{hhmm}）{tops}"

    _step_label("まちがいを直す", "着順・名前・備考を直せます")
    pick_key = f"fix_pick_{table_no}"

    def _cleanup(g):
        """直す欄を閉じる。ウィジェットを描く前でないと値を変えられないので、次の実行の最初に呼ぶ"""
        for k in [k for k in ss.keys() if str(k).startswith(f"fix_{g}_") or str(k).startswith(f"rank_fix{g}_")]:
            del ss[k]
        ss.get("rank_prev", {}).pop(f"fix{g}", None)
        ss[pick_key] = None
        ss.pop("fix_del_confirm", None)

    done = ss.pop("fix_pending_close", None)
    if done is not None:
        _cleanup(done)
    if ss.get(pick_key) is not None and ss[pick_key] not in rows:
        ss[pick_key] = None   # 消した回など
    gno = st.selectbox("直す回", sorted(rows, key=lambda g: -rows[g]["_no"]), index=None,
                       placeholder="直す回を選ぶ（新しい順）", format_func=_label, key=pick_key,
                       label_visibility="collapsed")
    if gno is None:
        return
    row = rows[gno]
    cur_rank = {s: _int_rank(row.get(f"{s}着順")) for s in SEATS}
    cur_name = {s: str(row.get(f"{s}さん", "")).strip() for s in SEATS}
    cur_type = {s: _normalize_play_type(row.get(f"{s}タイプ", "")) or "A客" for s in SEATS}
    cur_memo = [t for t in note_tags(row.get("備考", ""))]

    # ウィジェットの初めの値は session_state に入れておく (default と同時に使うと警告が出るため)
    mkey = f"fix{gno}"
    for s in SEATS:
        ss.setdefault(_rank_key(mkey, s), cur_rank[s] if cur_rank[s] in (1, 2, 3) else None)
        ss.setdefault(f"fix_{gno}_name_{s}", cur_name[s])
        ss.setdefault(f"fix_{gno}_type_{s}", cur_type[s])
    ss.setdefault(f"fix_{gno}_memo", cur_memo)
    ss.setdefault("rank_prev", {}).setdefault(mkey, {s: ss[_rank_key(mkey, s)] for s in SEATS})

    with st.container(key="fix_box"):
        st.markdown(_html(f'<div class="fix-head">{row["_no"]}回目を直す'
                          f'<span>セット{int(row.get("SetNo", 0) or 0)}</span></div>'), unsafe_allow_html=True)
        if row["_sec"] < len(cuts):
            st.caption("⚠️ この回はゲーム代を集金済みの区切りに入っています。直すと、その区切りの枚数も変わります。")
        if closings_today:
            st.caption("⚠️ 今日はもう締めをしています。直すと、締めのトップ回数の一覧も変わります。")

        new_name, new_type, new_rank = {}, {}, {}
        with st.expander("名前・タイプを直す"):
            for s in SEATS:
                opts = list(member_names)
                if cur_name[s] and cur_name[s] not in opts:
                    opts = [cur_name[s]] + opts
                new_name[s] = st.selectbox(SEAT_LABELS[s], opts, key=f"fix_{gno}_name_{s}")
                new_type[s] = st.segmented_control(
                    f"{s}席のタイプ", TYPE_BUTTON_ORDER, format_func=lambda t: TYPE_LABELS[t],
                    key=f"fix_{gno}_type_{s}", label_visibility="collapsed") or cur_type[s]
        with st.container(key="fix_rank_area"):
            for s in SEATS:
                v = st.segmented_control(
                    f"{SEAT_LABELS[s]}　{new_name[s]}", [1, 2, 3], format_func=lambda r: f"{r}着",
                    key=_rank_key(mkey, s), on_change=_on_rank_change, args=(mkey, s))
                new_rank[s] = int(v) if v is not None else None
        memo_sel = st.pills("備考", MEMO_OPTIONS, selection_mode="multi",
                            format_func=lambda m: f"{m}（−{NOTE_DISCOUNTS[m]}枚）", key=f"fix_{gno}_memo") or []
        # 備考は選べる項目だけを入れ直す (それ以外の書き込みがあれば残す)
        other = _normalize_note(row.get("備考", ""))
        for t in MEMO_OPTIONS:
            other = other.replace(t, "")
        other = other.strip(" 、,・")
        new_memo = MEMO_SEP.join([m for m in MEMO_OPTIONS if m in memo_sel] + ([other] if other else []))

        names_ok = all(new_name.values()) and len(set(new_name.values())) == 3
        ranks_ok = sorted(r for r in new_rank.values() if r) == [1, 2, 3]
        if not names_ok:
            st.error("同じ人が複数の席にいます")
        elif not ranks_ok:
            st.error("着順を3人ぶん選んでください")

        changes = {}
        for s in SEATS:
            if new_name[s] != cur_name[s]:
                changes[f"{s}さん"] = new_name[s]
            if new_type[s] != cur_type[s]:
                changes[f"{s}タイプ"] = new_type[s]
            if new_rank[s] != cur_rank[s]:
                changes[f"{s}着順"] = new_rank[s]
        if new_memo != str(row.get("備考", "") or ""):
            changes["備考"] = new_memo

        with st.container(key="fix_btns"):
            c1, c2 = st.columns([1, 1.6])
            with c1:
                st.button("やめる", use_container_width=True, key="fix_cancel", on_click=_cleanup, args=(gno,))
            with c2:
                do_fix = st.button("この内容で直す", type="primary", use_container_width=True, key="fix_do",
                                   disabled=not (names_ok and ranks_ok and changes))
        if do_fix:
            detail = (f"入力アプリ {table_no}卓 {row['_no']}回目: {_game_text(row)} → "
                      f"{_game_text(row, new_rank, new_name, new_type, new_memo)}")
            with st.spinner("保存中..."):
                ok, err = update_score_row(gno, changes, detail)
            if ok:
                order = sorted(SEATS, key=lambda s: new_rank[s])
                ss["input_flash"] = (f"{table_no}卓の{row['_no']}回目を直しました："
                                     + " → ".join(new_name[s] for s in order))
                ss["fix_pending_close"] = gno
                st.rerun()
            else:
                st.error(f"直せませんでした: {err}")

        # 消す (確認つき)
        if ss.get("fix_del_confirm") == gno:
            st.warning(f"{row['_no']}回目（{_game_text(row)}）を消します。元に戻せません。よろしいですか？")
            with st.container(key="fix_del_btns"):
                d1, d2 = st.columns(2)
                with d1:
                    if st.button("やめる", use_container_width=True, key="fix_del_cancel"):
                        ss.pop("fix_del_confirm", None)
                        st.rerun()
                with d2:
                    do_del = st.button("消す", type="primary", use_container_width=True, key="fix_del_do")
            if do_del:
                with st.spinner("保存中..."):
                    ok, err = delete_score_row(gno, f"入力アプリ {table_no}卓 {row['_no']}回目: {_game_text(row)}")
                if ok:
                    ss["input_flash"] = f"{table_no}卓の{row['_no']}回目を消しました"
                    ss["fix_pending_close"] = gno
                    st.rerun()
                else:
                    st.error(f"消せませんでした: {err}")
        else:
            if st.button("この回を消す", use_container_width=True, key="fix_del_start",
                         help="入力のしすぎなど、この回そのものが無かったとき"):
                ss["fix_del_confirm"] = gno
                st.rerun()


FEE_RULE_TEXT = ("ゲーム代はトップ（1着）を取った人が払います。1回につき " + "・".join(
    f"{TYPE_LABELS[t]} {GAME_FEE_TABLE[t]}枚" for t in TYPE_BUTTON_ORDER)
    + "。備考があればその回は値引き（" + "・".join(f"{t} −{n}枚" for t, n in NOTE_DISCOUNTS.items()) + "）")


def render_fee_collect_section(df_all, fees, table_no, today):
    """成績入力ページの「ゲーム代を集める」欄。まだ集めていない枚数を返す"""
    ss = st.session_state
    df_open = get_open_section_games(df_all, fees, table_no, today)
    open_total = 0

    if df_open.empty:
        _step_label(f"{table_no}卓のゲーム代", "前回の集金のあとの対局はまだありません")
    else:
        info = calc_game_fee(df_open)
        open_total = info["total"]
        _step_label(f"{table_no}卓のゲーム代", "集めると着順表に区切りが入ります")
        lines = "".join(
            f'<div class="fee-line"><span>{TYPE_LABELS[t]}のトップ</span>'
            f'<span><b>{n}回</b> × {unit}枚 = <b>{sub}枚</b></span></div>'
            for t, n, unit, sub in info["lines"]
        )
        lines += "".join(
            f'<div class="fee-line fee-disc"><span>値引き（{t}）</span>'
            f'<span><b>{n}回</b> × {unit}枚 = <b>−{sub}枚</b></span></div>'
            for t, n, unit, sub in info["discounts"]
        )
        if info["unknown"]:
            lines += (f'<div class="fee-line"><span>タイプ不明のトップ</span>'
                      f'<span><b>{info["unknown"]}回</b>（0枚で計算）</span></div>')
        st.markdown(_html(f"""
            <div class="fee-box">
              <div class="fee-box-title">前回の集金から <b>{info["games"]}回</b>：ゲーム代 <b class="fee-box-total">{info["total"]}枚</b></div>
              {lines}
              <div class="fee-rule">{FEE_RULE_TEXT}</div>
            </div>
        """), unsafe_allow_html=True)

        if ss.get("fee_confirm_table") == table_no:
            st.warning(f"{table_no}卓の {info['games']}回分、ゲーム代 {info['total']}枚 を集めて、着順表に区切りを入れます。よろしいですか？")
            with st.container(key="fee_confirm"):
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("やめる", use_container_width=True, key="fee_cancel"):
                        ss.pop("fee_confirm_table", None)
                        st.rerun()
                with c2:
                    do_collect = st.button("集める", type="primary", use_container_width=True, key="fee_do")
            if do_collect:
                with st.spinner("保存中..."):
                    ok, err, done = collect_game_fee(table_no)
                ss.pop("fee_confirm_table", None)
                if ok:
                    ss["input_flash"] = (f"{table_no}卓のゲーム代 {done['total']}枚 を集めました"
                                         f"（{done['games']}回分：{fee_breakdown_text(done)}）")
                    st.rerun()
                else:
                    st.error(f"集金を記録できませんでした: {err}")
        else:
            if st.button(f"ゲーム代を集める（{info['total']}枚）", use_container_width=True, key="fee_start"):
                ss["fee_confirm_table"] = table_no
                st.rerun()

    # 今日この卓で集金していれば、直前の集金を取り消せる
    df_today = get_games_by_date(df_all, today)
    day_nos = set(df_today.loc[df_today["TableNo"] == table_no, "GameNo"]) if not df_today.empty else set()
    has_cut_today = any(int(c["LastGameNo"]) in day_nos for c in get_fee_cuts(fees, table_no))
    if has_cut_today:
        if st.button("直前の集金を取り消す（区切りを消す）", key="fee_undo", use_container_width=True,
                     help="押し間違えたときに。対局の記録は消えません。"):
            with st.spinner("保存中..."):
                ok, err = undo_last_fee_collection(table_no, today)
            if ok:
                ss["input_flash"] = f"{table_no}卓の直前の集金を取り消しました"
                st.rerun()
            else:
                st.error(f"取り消せませんでした: {err}")
    return open_total


def _hhmm(text):
    t = str(text or "")
    return t[11:16] if len(t) >= 16 else ""


def _close_table_html(cols):
    """トップ回数の一覧表。cols = [(列の見出し, count_tops の結果)]。最後の列を強調する"""
    show_unknown = any(c["unknown"] for _, c in cols)
    head = "".join(f'<th class="{"close-main" if i == len(cols) - 1 else ""}">{lbl}</th>'
                   for i, (lbl, _) in enumerate(cols))

    def _cells(values):
        out = ""
        for i, v in enumerate(values):
            cls = ("close-main " if i == len(values) - 1 else "") + ("close-zero" if v == 0 else "")
            out += f'<td class="{cls}"><b>{v}</b><small>回</small></td>'
        return out

    body = ""
    for t in TYPE_BUTTON_ORDER:
        body += f'<tr><th>{TYPE_LABELS[t]}</th>{_cells([c["tops"][t] for _, c in cols])}</tr>'
    if show_unknown:
        body += f'<tr><th>タイプ不明</th>{_cells([c["unknown"] for _, c in cols])}</tr>'
    body += f'<tr class="close-sum"><th>合計</th>{_cells([c["games"] for _, c in cols])}</tr>'
    return (f'<table class="close-table"><thead><tr><th>トップ回数</th>{head}</tr></thead>'
            f'<tbody>{body}</tbody></table>')


def _close_card_html(title, status, cols, done):
    return _html(f"""
        <div class="close-card {'done' if done else 'open'}">
          <div class="close-head"><span class="close-title">{title}</span><span class="close-status">{status}</span></div>
          {_close_table_html(cols)}
        </div>
    """)


def render_closing_section(df_day, closings, target_date, editable=True):
    """
    中間締め・1日締めの欄。締めた時点までの対局で、各タイプのトップ回数を一覧にする。
    締めの区切りは GameNo (全卓共通)。editable=False (過去の着順表) なら、締めの記録があるときだけ表示する。
    """
    ss = st.session_state
    done = get_day_closings(closings, target_date)
    mid, day = done.get(CLOSE_MID), done.get(CLOSE_DAY)
    if not editable and not done:
        return
    if df_day.empty and not done:
        return

    game_nos = pd.to_numeric(df_day["GameNo"], errors="coerce") if not df_day.empty else pd.Series(dtype=float)

    def part(lo=None, hi=None):
        m = pd.Series(True, index=df_day.index)
        if lo is not None:
            m &= game_nos > lo
        if hi is not None:
            m &= game_nos <= hi
        return count_tops(df_day[m])

    mid_no = int(mid["LastGameNo"]) if mid else None
    day_no = int(day["LastGameNo"]) if day else None

    _step_label("締め（タイプ別のトップ回数）", "全卓の合計")
    msg = ss.pop("close_flash", None)
    if msg and editable:
        st.success(msg)

    if day:
        status = f"✅ 1日締め {_hhmm(day['日時'])}"
        if mid:
            status = f"✅ 中間締め {_hhmm(mid['日時'])} ／ 1日締め {_hhmm(day['日時'])}"
            cols = [("中間締めまで", part(hi=mid_no)), ("中間締めのあと", part(lo=mid_no, hi=day_no)),
                    ("1日合計", part(hi=day_no))]
        else:
            cols = [("1日合計", part(hi=day_no))]
        st.markdown(_close_card_html("1日締め", status, cols, True), unsafe_allow_html=True)
        later = part(lo=day_no)["games"]
        if editable and later:
            st.warning(f"1日締めのあとに {later}回 記録されています（上の表には入っていません）。"
                       "入れて数え直すときは「1日締めを取り消す」を押してから、もう一度締めてください。")
        undo_kind = CLOSE_DAY
    elif mid:
        now_after = part(lo=mid_no)
        st.markdown(_close_card_html("中間締め", f"✅ 済 {_hhmm(mid['日時'])}",
                                     [("中間締めまで", part(hi=mid_no)), ("そのあと（いま）", now_after)], True),
                    unsafe_allow_html=True)
        undo_kind = CLOSE_MID
    else:
        st.markdown(_close_card_html("今日ここまで", "⏳ まだ締めていません", [("いまの時点", part())], False),
                    unsafe_allow_html=True)
        undo_kind = None

    if not editable:
        return

    # --- 締めるボタン (押すと確認を出す) ---
    choices = []
    if not mid and not day:
        choices.append(CLOSE_MID)
    if not day:
        choices.append(CLOSE_DAY)

    confirm = ss.get("close_confirm")
    if confirm in choices:
        n_games = len(df_day)
        note = ""
        if confirm == CLOSE_DAY and not mid:
            note = "（今日はまだ中間締めをしていません）"
        st.warning(f"今日のここまでの {n_games}回分で「{confirm}」をします。よろしいですか？{note}")
        with st.container(key="close_confirm"):
            c1, c2 = st.columns(2)
            with c1:
                if st.button("やめる", use_container_width=True, key="close_cancel"):
                    ss.pop("close_confirm", None)
                    st.rerun()
            with c2:
                do_it = st.button("締める", type="primary", use_container_width=True, key="close_do")
        if do_it:
            with st.spinner("保存中..."):
                ok, err, c = do_closing(confirm)
            ss.pop("close_confirm", None)
            if ok:
                ss["close_flash"] = f"{confirm}をしました（{c['games']}回分）"
                st.rerun()
            else:
                st.error(f"締めを記録できませんでした: {err}")
    elif choices:
        with st.container(key="close_btns"):
            cs = st.columns(len(choices))
            for col, kind in zip(cs, choices):
                with col:
                    label = "中間締めをする" if kind == CLOSE_MID else "1日を締める"
                    if st.button(label, use_container_width=True, key=f"close_start_{kind}",
                                 type="primary" if kind == CLOSE_DAY and mid else "secondary"):
                        ss["close_confirm"] = kind
                        st.rerun()

    if undo_kind:
        if st.button(f"{undo_kind}を取り消す", key="close_undo", use_container_width=True,
                     help="押し間違えたときに。対局の記録は消えません。"):
            with st.spinner("保存中..."):
                ok, err = undo_closing(undo_kind, target_date)
            if ok:
                ss["close_flash"] = f"{undo_kind}を取り消しました"
                st.rerun()
            else:
                st.error(f"取り消せませんでした: {err}")


# ==========================================
# 7. 今日の着順表ページ
# ==========================================
def page_today():
    st.title("今日の着順表")
    today = get_today_logical_date()
    st.caption(f"論理日付: **{today.strftime('%Y年%m月%d日')}** (午前9時までは前日扱い)")

    with st.spinner("データ読込中..."):
        df = load_score_data()
    df_day = get_games_by_date(df, today)

    if df_day.empty:
        st.info("今日の対局データはまだありません。")
        if st.button("再読み込み", use_container_width=True):
            clear_cache()
            st.rerun()
        return

    fees = load_fee_collections()
    _render_day_summary(df_day)
    with st.container(key="close_area_today"):
        render_closing_section(df_day, load_closings(), today, editable=True)
    tstat = get_table_status(df_day, fees, today)
    if len(tstat) >= 2:
        _step_label("卓ごとの状況", f"{len(tstat)}卓")
        cards = "".join(
            f'<div class="tbl-card" style="border-top: 4px solid {table_color(t)};">'
            f'<div class="tbl-card-name">{table_mark(t)} {t}卓</div>'
            f'<div class="tbl-card-num">{v["games"]}回</div>'
            f'<div class="tbl-card-sub">{"未集金 " + str(v["open_fee"]) + "枚" if v["open_fee"] else "未集金なし"}'
            f' ・最後 {v["last_time"].strftime("%H:%M")}</div></div>'
            for t, v in sorted(tstat.items()))
        st.markdown(_html(f'<div class="tbl-cards">{cards}</div>'), unsafe_allow_html=True)
    render_paper_sheet(df_day, today, fees)

    if st.button("データを再読み込み", use_container_width=True):
        clear_cache()
        st.rerun()


# ==========================================
# 8. 過去の着順表ページ
# ==========================================
def page_past():
    st.title("過去の着順表")
    st.caption("過去の日付を選ぶと、その日の着順表が見られます。")

    with st.spinner("データ読込中..."):
        df = load_score_data()

    dates = get_available_dates(df)
    if not dates:
        st.info("対局データがありません。")
        return

    # 日付選択
    date_labels = []
    for d in dates:
        weekday = ["月", "火", "水", "木", "金", "土", "日"][d.weekday()]
        date_labels.append(f"{d.strftime('%Y年%m月%d日')} ({weekday})")

    sel_idx = st.selectbox(
        "日付を選択",
        range(len(dates)),
        format_func=lambda i: date_labels[i],
        key="past_date_select",
    )
    selected_date = dates[sel_idx]

    df_day = get_games_by_date(df, selected_date)

    _step_label(f"{date_labels[sel_idx]} の着順表")
    _render_day_summary(df_day)
    with st.container(key="close_area_past"):
        render_closing_section(df_day, load_closings(), selected_date, editable=False)
    render_paper_sheet(df_day, selected_date, load_fee_collections())


def _render_day_summary(df_day):
    """その日のサマリバッジを表示"""
    total_games = len(df_day)
    total_tables = df_day["TableNo"].nunique() if "TableNo" in df_day.columns else 0
    all_players = set()
    for _, row in df_day.iterrows():
        for seat in ["A", "B", "C"]:
            nm = str(row.get(f"{seat}さん", "")).strip()
            if nm:
                all_players.add(nm)
    st.markdown(_html(f"""
    <div style="margin-bottom:0.5rem;">
        <span class="summary-badge">対局 <strong>{total_games}</strong></span>
        <span class="summary-badge">卓 <strong>{total_tables}</strong></span>
        <span class="summary-badge">参加 <strong>{len(all_players)}</strong>人</span>
    </div>
    """), unsafe_allow_html=True)


# ==========================================
# 9. メイン
# ==========================================
def main():
    st.markdown(
        f'<div class="brand-bar"><span>ぱいんりばー 成績入力</span>'
        f'<span>更新 {now_jst().strftime("%H:%M")}</span></div>',
        unsafe_allow_html=True
    )

    tab_input, tab_today, tab_past = st.tabs(["成績を付ける", "今日の着順表", "過去の着順表"])
    with tab_input:
        with st.container(key="page_input"):
            page_input()
    with tab_today:
        page_today()
    with tab_past:
        page_past()


if __name__ == '__main__':
    main()
