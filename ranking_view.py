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
from streamlit_gsheets import GSheetsConnection

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
:root {
    --bg-main: #1a1d2e;
    --bg-card: #232739;
    --border: rgba(255,255,255,0.10);
    --text-primary: #f5f5f7;
    --text-muted: #b8bdd0;   /* 補足文字。背景(#1a1d2e)とのコントラスト比 約9 */
    --accent: #f0c040;
    --accent2: #5b9cf6;
    --green: #4caf87;
    --red: #e05c5c;
    --orange: #e07b39;
    --radius: 12px;
}
.stApp {
    background: linear-gradient(180deg, #1a1d2e 0%, #232739 100%) !important;
    color: var(--text-primary) !important;
    font-family: "Zen Kaku Gothic New", "Noto Sans JP", "Hiragino Kaku Gothic ProN", Meiryo, sans-serif !important;
}
#MainMenu, header, footer {visibility: hidden;}
.stDeployButton {display: none;}
h1, h2, h3 { color: var(--text-primary) !important; font-weight: 900 !important; letter-spacing: 0.02em !important; }

/* タブ */
button[role="tab"] {
    background: #2f3550 !important;
    color: #ffffff !important;
    border: 1px solid rgba(255,255,255,0.15) !important;
    border-radius: 10px 10px 0 0 !important;
    font-weight: 700 !important;
    padding: 0.6rem 1rem !important;
    margin-right: 4px !important;
    /* 背景だけ遅れて切り替わると、一瞬「白文字×金背景」になって読めないので、アニメーションを切る */
    transition: none !important;
}
button[role="tab"] * { color: inherit !important; }
button[role="tab"][aria-selected="true"] {
    background: var(--accent) !important;
    color: #000000 !important;
    border-color: var(--accent) !important;
}
button[role="tab"][aria-selected="true"] * { color: #000000 !important; }

/* ボタン */
.stButton > button {
    background: linear-gradient(135deg, var(--bg-card) 0%, #2f3550 100%) !important;
    color: var(--text-primary) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    font-weight: 700 !important;
    transition: transform 0.15s, box-shadow 0.15s !important;
}
.stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 12px rgba(0,0,0,0.3) !important;
    border-color: var(--accent) !important;
}
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, var(--accent) 0%, #e0a828 100%) !important;
    color: #000000 !important;
    font-weight: 900 !important;
    border: none !important;
}
.stButton > button[kind="primary"]:hover {
    box-shadow: 0 6px 20px rgba(240,192,64,0.4) !important;
}

/* タイプ・着順のボタン: 選ばれているものを金色で塗りつぶして一目で分かるように */
button[data-testid="stBaseButton-segmented_controlActive"] {
    background: var(--accent) !important;
    border-color: var(--accent) !important;
    color: #000000 !important;
    font-weight: 900 !important;
}
button[data-testid="stBaseButton-segmented_controlActive"] * { color: #000000 !important; }

/* 入力 */
.stTextInput input, .stNumberInput input, .stSelectbox select,
.stTextInput > div, .stNumberInput > div, .stSelectbox > div {
    background: var(--bg-card) !important;
    color: var(--text-primary) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
}
[data-baseweb="select"] > div {
    background: var(--bg-card) !important;
    border-color: var(--border) !important;
    color: var(--text-primary) !important;
}
.stAlert {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    color: var(--text-primary) !important;
}
/* 補足文字 (st.caption)。Streamlit 既定は暗く半透明で背景に溶けるので、明るく不透明にする */
.stCaption, [data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] * {
    color: var(--text-muted) !important; opacity: 1 !important;
}

/* お知らせ枠 (st.info / success / warning / error)。既定の文字色は背景と同系色で読みにくいので、明るい色にする */
[data-testid="stAlertContentInfo"], [data-testid="stAlertContentInfo"] * { color: #b9dcff !important; }
[data-testid="stAlertContentSuccess"], [data-testid="stAlertContentSuccess"] * { color: #b4f0cc !important; }
[data-testid="stAlertContentWarning"], [data-testid="stAlertContentWarning"] * { color: #ffe7a3 !important; }
[data-testid="stAlertContentError"], [data-testid="stAlertContentError"] * { color: #ffc9c9 !important; }

/* 入力欄の見出し (卓番・日付 など)。使えない状態でも読めるようにする */
[data-testid="stWidgetLabel"], [data-testid="stWidgetLabel"] * {
    color: var(--text-primary) !important; opacity: 1 !important;
}

/* 使えない状態の入力欄の中身 (日付・時刻など) */
input:disabled, textarea:disabled {
    color: #c5c8d4 !important; -webkit-text-fill-color: #c5c8d4 !important; opacity: 1 !important;
}

/* 使えない状態のボタン: 読める明るさを保ちつつ、点線枠と灰色で「まだ押せない」と分かるようにする */
.stButton > button:disabled,
.stButton > button[kind="primary"]:disabled {
    background: #2a2e42 !important;
    color: #c5c8d4 !important;
    border: 1px dashed rgba(255,255,255,0.35) !important;
    box-shadow: none !important; transform: none !important; cursor: not-allowed !important;
}
.stButton > button:disabled * { color: #c5c8d4 !important; }
button[data-testid^="stBaseButton-segmented_control"]:disabled {
    color: #c5c8d4 !important; border-style: dashed !important; opacity: 1 !important;
}
button[data-testid^="stBaseButton-segmented_control"]:disabled * { color: #c5c8d4 !important; }
button[data-testid^="stNumberInputStep"]:disabled { color: rgba(255,255,255,0.6) !important; }
hr { border-color: var(--border) !important; opacity: 0.4 !important; }

/* 席カード */
.seat-card {
    background: linear-gradient(135deg, var(--bg-card) 0%, #2a2f45 100%);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 0.7rem 1rem;
    margin-bottom: 0.5rem;
}
.seat-card.seat-A { border-left: 4px solid var(--accent2); }
.seat-card.seat-B { border-left: 4px solid var(--orange); }
.seat-card.seat-C { border-left: 4px solid var(--green); }
.seat-label {
    font-size: 0.8rem; color: var(--text-muted); letter-spacing: 0.06em;
    font-weight: 700; margin-bottom: 0.3rem;
}
.seat-type-badge {
    display: inline-block; padding: 0.1rem 0.5rem; border-radius: 6px;
    font-size: 0.7rem; font-weight: 800; margin-left: 0.5rem;
    background: rgba(240,192,64,0.15); color: var(--accent);
    border: 1px solid rgba(240,192,64,0.3);
}

/* サマリバッジ */
.summary-badge {
    display: inline-flex; align-items: center; gap: 0.4rem;
    background: var(--bg-card); border: 1px solid var(--border);
    padding: 0.4rem 0.8rem; border-radius: 999px;
    font-size: 0.82rem; color: var(--text-primary); margin: 0.2rem 0.4rem 0.2rem 0;
}
.summary-badge strong { color: var(--accent); font-weight: 900; }

/* ===== 紙の着順表 (paper-sheet) ===== */
.paper-wrap {
    background: #f8f6f0;
    border-radius: 8px;
    padding: 0.3rem;
    overflow-x: auto;
    margin: 0 0 0.8rem;
    box-shadow: 0 3px 12px rgba(0,0,0,0.3);
}
.paper-table {
    border-collapse: collapse;
    width: 100%;
    max-width: 420px;
    font-family: "Zen Kaku Gothic New", sans-serif;
    background: #fffdf7;
}
.paper-table th, .paper-table td {
    border: 1px solid #c2bba5;
    text-align: center;
    color: #1a1a1a;
    padding: 1px 4px;
    font-size: 0.82rem;
    line-height: 1.5;
}
.paper-table thead th {
    background: #e8e2d0;
    font-weight: 800;
    font-size: 0.72rem;
    color: #333;
    padding: 2px 4px;
}
.paper-table .col-no {
    background: #ede8da; font-weight: 700; width: 28px; color: #4a4a4a;
    font-size: 0.68rem;
}
.paper-table .seat-head-A { background: #d4e4f7; width: 33%; }
.paper-table .seat-head-B { background: #f7e0cc; width: 33%; }
.paper-table .seat-head-C { background: #d4f0e0; width: 33%; }
.paper-table .name-row td {
    font-weight: 800; font-size: 0.8rem; background: #fbf8ee;
    border-top: 2px solid #8a8268;
    padding: 3px 4px;
    line-height: 1.2;
}
.paper-table .name-type {
    font-size: 0.6rem; color: #4f3f14; margin-left: 2px;
    background: #efe8d2; padding: 0 3px; border-radius: 3px;
    vertical-align: middle;
}
.paper-table .rank1 { color: #c0392b; font-weight: 900; }
.paper-table .rank-cell { font-weight: 700; font-size: 0.9rem; }
.paper-table .gamecount-row td {
    background: #f0ebd8; font-weight: 700; font-size: 0.72rem; color: #555;
    padding: 3px 4px;
}
.paper-table .empty-cell { color: #ccc; }
/* ゲーム代の区切り行 */
.paper-table .fee-row td {
    background: #fff4d6; text-align: left; padding: 5px 8px;
    border-top: 2px dashed #b8860b; border-bottom: 3px double #b8860b;
}
.paper-table .fee-head { font-size: 0.85rem; font-weight: 800; color: #3a2a00; }
.paper-table .fee-total { color: #c0392b; font-size: 1.05rem; }
.paper-table .fee-games { font-size: 0.72rem; color: #5a4a22; font-weight: 700; margin-left: 2px; }
.paper-table .fee-status {
    float: right; font-size: 0.7rem; font-weight: 800; padding: 1px 6px; border-radius: 4px;
}
.paper-table .fee-status.done { background: #d4f0e0; color: #1e6b45; }
.paper-table .fee-status.open { background: #fde2c8; color: #a0471a; }
.paper-table .fee-detail { font-size: 0.74rem; color: #4a3d20; line-height: 1.45; margin-top: 2px; }

.paper-title {
    font-weight: 900; font-size: 0.92rem; color: #2a2a2a;
    padding: 0.25rem 0.5rem; background: #e8e2d0; border-radius: 6px 6px 0 0;
    border: 1px solid #c2bba5; border-bottom: none;
    display: inline-block; margin-top: 0.5rem;
}

/* 成績入力ページのゲーム代欄 */
.fee-box {
    background: linear-gradient(135deg, rgba(240,192,64,0.14) 0%, rgba(240,192,64,0.04) 100%);
    border: 1px solid rgba(240,192,64,0.45); border-radius: var(--radius);
    padding: 0.7rem 1rem; margin-bottom: 0.6rem;
}
.fee-box-title { font-size: 0.95rem; margin-bottom: 0.35rem; }
.fee-box-total { color: var(--accent); font-size: 1.3rem; }
.fee-line {
    display: flex; justify-content: space-between; gap: 0.5rem;
    font-size: 0.88rem; padding: 0.15rem 0; border-bottom: 1px dotted rgba(255,255,255,0.12);
}
.fee-rule { font-size: 0.72rem; color: #ddd6be; margin-top: 0.4rem; }

/* 着席中バナー */
.seated-banner {
    background: linear-gradient(135deg, rgba(76,175,135,0.15) 0%, rgba(76,175,135,0.05) 100%);
    border: 1px solid rgba(76,175,135,0.4);
    border-radius: var(--radius);
    padding: 0.6rem 1rem;
    margin-bottom: 0.7rem;
    font-size: 0.85rem;
}
.seated-banner strong { color: var(--green); }
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

# ゲーム代: トップを取った人が、自分のタイプに応じた枚数を払う (メインアプリの GAME_FEE_TABLE と同じ値)
GAME_FEE_TABLE = {"A客": 3, "B客": 4, "AS": 1, "BS": 1}

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
def get_conn():
    return st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=60, show_spinner=False)
def _fetch_sheet(_conn, sheet_name):
    """シート読み込み (60秒キャッシュ、エラー時は空DF)"""
    try:
        return _conn.read(worksheet=sheet_name, ttl=0)
    except Exception:
        return pd.DataFrame()

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
        df["日時Obj"] = pd.to_datetime(df["日時"], errors='coerce')
        df["日時Obj"] = df["日時Obj"].fillna(pd.Timestamp("1900-01-01"))
        df["論理日付"] = (df["日時Obj"] - timedelta(hours=9)).dt.date
    return df

def load_score_data():
    conn = get_conn()
    df = _fetch_sheet(conn, SHEET_SCORE)
    processed = process_score_df(df)
    if processed is None:
        _fetch_sheet.clear()
        df = _fetch_sheet(conn, SHEET_SCORE)
        processed = process_score_df(df)
    if processed is None:
        st.error("スプレッドシートの列名が想定と異なります。管理者に連絡してください。")
        st.stop()
    return processed

_ZEN2HAN = str.maketrans("ＡＢＣＳａｂｃｓ０１２３４５６７８９", "ABCSabcs0123456789")


def _normalize_play_type(tp):
    """
    タイプ表記のゆれを吸収して A客 / AS / B客 / BS のいずれかに正規化する。該当しなければ None。
    メインアプリ (pine_score_manager_v2.py) の同名関数と同じルール。片方を直したらもう片方も直すこと。
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


@st.cache_data(ttl=60, show_spinner=False)
def load_members(_conn):
    """
    メンバー一覧と、メンバーシートに書かれたタイプ (正規化済み) を取得。
    Returns: (names: list, member_type: dict 名前→タイプ。タイプ欄が空・読めない人は入らない)
    """
    df = _fetch_sheet(_conn, SHEET_MEMBER)
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

def _fetch_sheet_fresh(conn, sheet_name):
    """保存直前用: キャッシュを使わずに読む。失敗時は最大3回リトライし、それでも駄目なら例外。"""
    for i in range(3):
        try:
            return conn.read(worksheet=sheet_name, ttl=0)
        except Exception:
            if i < 2:
                time.sleep(2)
                continue
            raise


def append_score_row(row_dict):
    """
    scoreシートに1行追加する。GameNo はここで最新データから採番する。
    シート全体を上書き保存するため、必ずキャッシュを使わず最新を読んでから追記する
    (他端末で入力された行を消さないため)。読み込みに失敗したら保存しない。
    Returns: (ok, game_no or None, err or None)
    """
    conn = get_conn()
    try:
        _fetch_sheet.clear()
        raw = _fetch_sheet_fresh(conn, SHEET_SCORE)
        if raw is None:
            return False, None, "スプレッドシートを読み込めませんでした"
        current = raw.copy()
        current.columns = current.columns.astype(str).str.strip()
        if not current.empty:
            missing = [c for c in EXPECTED_COLS if c not in current.columns]
            if missing:
                return False, None, f"列が見つかりません: {missing}"
        for c in EXPECTED_COLS:
            if c not in current.columns:
                current[c] = ""
        current = current[EXPECTED_COLS]

        game_no = get_next_game_no(current)
        new_row = dict(row_dict)
        new_row["GameNo"] = game_no
        new_row_df = pd.DataFrame([new_row])
        for c in EXPECTED_COLS:
            if c not in new_row_df.columns:
                new_row_df[c] = ""
        new_row_df = new_row_df[EXPECTED_COLS]

        merged = pd.concat([current, new_row_df], ignore_index=True)
        conn.update(worksheet=SHEET_SCORE, data=merged)
        _fetch_sheet.clear()
        return True, game_no, None
    except Exception as e:
        return False, None, str(e)

def _is_sheet_missing(err):
    msg = str(err)
    return "WorksheetNotFound" in msg or "not found" in msg.lower()


def _clean_fee_df(df):
    """集金記録を整形 (列をそろえ、数値化)"""
    if df is None or df.empty:
        return pd.DataFrame(columns=FEE_COLS)
    df = df.copy()
    df.columns = df.columns.astype(str).str.strip()
    for c in FEE_COLS:
        if c not in df.columns:
            df[c] = ""
    df = df[FEE_COLS]
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
    return _clean_fee_df(_fetch_sheet(get_conn(), SHEET_FEE))


def _read_fee_fresh(conn):
    """保存直前用に集金記録を最新で読む。シートが無いだけなら空を返し、それ以外の失敗は例外。"""
    try:
        return _clean_fee_df(_fetch_sheet_fresh(conn, SHEET_FEE))
    except Exception as e:
        if _is_sheet_missing(e):
            return _clean_fee_df(None)
        raise


def _write_fee(conn, df):
    """集金記録を上書き保存。シートが無ければ作成する。"""
    out = df[FEE_COLS].copy()
    try:
        conn.update(worksheet=SHEET_FEE, data=out)
    except Exception as e:
        if not _is_sheet_missing(e):
            raise
        try:
            conn.create(worksheet=SHEET_FEE, data=out)
        except Exception as e2:
            raise RuntimeError(
                f"'{SHEET_FEE}' シートが見つからず、自動作成にも失敗しました。"
                f"スプレッドシートに列 [{', '.join(FEE_COLS)}] を持つ '{SHEET_FEE}' シートを作ってください。({e2})"
            )
    _fetch_sheet.clear()


def collect_game_fee(table_no):
    """
    指定卓のゲーム代を集める (= 着順表に区切りを入れる)。
    他の端末の入力を取りこぼさないよう、成績も集金記録も最新を読み直してから計算・保存する。
    Returns: (ok, message, fee_info or None)
    """
    conn = get_conn()
    try:
        _fetch_sheet.clear()
        df_score = process_score_df(_fetch_sheet_fresh(conn, SHEET_SCORE))
        if df_score is None:
            return False, "成績シートの列名が想定と異なります", None
        fees = _read_fee_fresh(conn)
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
        _write_fee(conn, pd.concat([fees, pd.DataFrame([new_row])], ignore_index=True))
        return True, None, info
    except Exception as e:
        return False, str(e), None


def undo_last_fee_collection(table_no, target_date):
    """指定卓の、指定日の最後の集金 (区切り) を取り消す。対局データには触らない。"""
    conn = get_conn()
    try:
        _fetch_sheet.clear()
        df_score = process_score_df(_fetch_sheet_fresh(conn, SHEET_SCORE))
        fees = _read_fee_fresh(conn)
        day_nos = set(df_score.loc[(df_score["論理日付"] == target_date)
                                   & (df_score["TableNo"] == int(table_no)), "GameNo"])
        cand = fees[(fees["TableNo"] == int(table_no)) & fees["LastGameNo"].isin(day_nos)]
        if cand.empty:
            return False, "取り消せる集金がありません"
        drop_idx = cand["LastGameNo"].idxmax()
        _write_fee(conn, fees.drop(index=drop_idx))
        return True, None
    except Exception as e:
        return False, str(e)


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
    Returns: {"games": 対局数, "lines": [(タイプ, トップ回数, 1回の枚数, 小計)], "total": 合計枚数, "unknown": タイプ不明のトップ回数}
    """
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
    lines = [(t, tops[t], GAME_FEE_TABLE[t], tops[t] * GAME_FEE_TABLE[t])
             for t in TYPE_BUTTON_ORDER if tops[t] > 0]
    return {"games": len(df_games), "lines": lines,
            "total": sum(l[3] for l in lines), "unknown": unknown}


def fee_breakdown_text(info, sep="、"):
    """例: 'A客トップ 2回×3枚=6枚、Aスタッフトップ 1回×1枚=1枚'"""
    parts = [f"{TYPE_LABELS[t]}トップ {n}回×{unit}枚={sub}枚" for t, n, unit, sub in info["lines"]]
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
        st.markdown(f'<div class="paper-title">🎲 {int(table_no)}卓</div>', unsafe_allow_html=True)
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
    if info.get("unknown"):
        detail += f'<div>タイプ不明のトップ {info["unknown"]}回（0枚で計算）</div>'
    return (
        '<tr class="fee-row"><td colspan="4">'
        f'<div class="fee-head">💰 ゲーム代 <b class="fee-total">{info["total"]}枚</b>'
        f'<span class="fee-games">（{info["games"]}局）</span>{status}</div>'
        f'<div class="fee-detail">{detail}</div>'
        '</td></tr>'
    )


def _render_table(df_tbl, cuts=None):
    """
    1卓分の着順表を描画。
    各局の実際のメンバーを表示し、メンバーが変わったら名前行を差し込む。
    名前抜けを防ぐため、局ごとに実データを参照する。
    cuts (集金の区切り) があれば、区切りごとにゲーム代の行を入れる。
    """
    cuts = cuts or []
    cut_nos = [int(c["LastGameNo"]) for c in cuts]

    df_tbl = df_tbl.copy()
    # 区切り番号: この局より前にある区切りの数 (GameNo が区切りの LastGameNo 以下なら、その区切りに入る)
    df_tbl["_sec"] = [bisect.bisect_left(cut_nos, int(g)) for g in df_tbl["GameNo"]]
    sort_keys = ["_sec"] + [k for k in ["SetNo", "GameNo"] if k in df_tbl.columns]
    df_tbl = df_tbl.sort_values(sort_keys).reset_index(drop=True)

    html = '<div class="paper-wrap"><table class="paper-table">'
    html += '<thead><tr>'
    html += '<th class="col-no">局</th>'
    html += '<th class="seat-head-A">A席</th>'
    html += '<th class="seat-head-B">B席</th>'
    html += '<th class="seat-head-C">C席</th>'
    html += '</tr></thead><tbody>'

    totals = {"done": 0, "open": 0}
    game_idx = 0
    for sec, df_sec in df_tbl.groupby("_sec", sort=True):
        prev_members = None  # 区切りのあとは名前行を出し直す
        for _, row in df_sec.iterrows():
            game_idx += 1
            cur_names, cur_types, cur_ranks = {}, {}, {}
            for seat in ["A", "B", "C"]:
                cur_names[seat] = str(row.get(f"{seat}さん", "")).strip()
                cur_types[seat] = str(row.get(f"{seat}タイプ", "")).strip()
                try:
                    cur_ranks[seat] = int(float(row.get(f"{seat}着順", 0)))
                except (TypeError, ValueError):
                    cur_ranks[seat] = 0

            members = (cur_names["A"], cur_names["B"], cur_names["C"])
            # メンバーが前局と変わった (または区切りの最初) なら名前行を挿入
            if members != prev_members:
                html += '<tr class="name-row"><td class="col-no"></td>'
                for seat in ["A", "B", "C"]:
                    nm = cur_names[seat] or "-"
                    tp = cur_types[seat]
                    type_disp = f'<span class="name-type">{tp}</span>' if tp else ""
                    html += f'<td>{nm}{type_disp}</td>'
                html += '</tr>'
                prev_members = members

            # 着順行 (局番号はその日・その卓での連番。内部用の GameNo は出さない)
            html += f'<tr><td class="col-no">{game_idx}</td>'
            for seat in ["A", "B", "C"]:
                rk = cur_ranks[seat]
                if rk == 1:
                    html += '<td class="rank-cell rank1">1</td>'
                elif rk in [2, 3]:
                    html += f'<td class="rank-cell">{rk}</td>'
                else:
                    html += '<td class="empty-cell">·</td>'
            html += '</tr>'

        info = calc_game_fee(df_sec)
        cut = cuts[sec] if sec < len(cuts) else None
        totals["done" if cut is not None else "open"] += info["total"]
        html += _fee_row_html(info, cut)

    # この日の合計
    total = totals["done"] + totals["open"]
    html += '<tr class="gamecount-row"><td class="col-no">計</td>'
    html += f'<td colspan="3" style="text-align:left;padding-left:8px;">この日のゲーム代 合計 <strong>{total}枚</strong>'
    if totals["open"]:
        html += f'（集金済 {totals["done"]}枚・未集金 {totals["open"]}枚）'
    html += '</td></tr>'

    html += '</tbody></table></div>'
    st.markdown(html, unsafe_allow_html=True)


# ==========================================
# 6. 成績を付けるページ
# ==========================================
SEATS = ["A", "B", "C"]
SEAT_LABELS = {"A": "🟦 A席", "B": "🟧 B席", "C": "🟩 C席"}


def _clear_seats():
    """
    全員を空席にする (ボタンの on_click、またはウィジェットを描く前に呼ぶ)。
    キーを del するだけだとブラウザ側の表示が残るので、値を None に明示的にセットする。
    """
    for seat in SEATS:
        st.session_state[f"sel_name_{seat}"] = None
    st.session_state["input_round"] = st.session_state.get("input_round", 0) + 1


def page_input():
    st.title("📝 成績を付ける")

    conn = get_conn()
    with st.spinner("データ読込中..."):
        df_all = load_score_data()
        member_names, member_type = load_members(conn)
    last_types = get_last_played_types(df_all)

    if not member_names:
        st.warning("メンバーが登録されていません。管理画面から先にメンバー登録をしてください。")
        return

    ss = st.session_state
    ss.setdefault("input_table_no", 1)
    ss.setdefault("input_set_no", 1)
    ss.setdefault("input_round", 0)   # 保存のたびに+1 → 着順ボタンをリセット

    # 保存後のリセット (ウィジェットを描く前でないと値を書き換えられないので、ここで行う)
    pending = ss.pop("input_pending_reset", None)
    if pending:
        ss["input_memo"] = ""
        if pending == "seats":
            _clear_seats()

    # 直前の保存結果 (rerun後に表示する)
    flash = ss.pop("input_flash", None)
    if flash:
        st.success(flash)

    # --- 卓・セット ---
    col_b, col_c = st.columns(2)
    with col_b:
        table_no = st.number_input("卓番", min_value=1, step=1, key="input_table_no")
    with col_c:
        set_no = st.number_input("セット", min_value=1, step=1, key="input_set_no")

    # --- メンバー ---
    st.markdown("### 🪑 メンバー")
    st.caption("名前は文字を打つと絞り込めます。名前を選ぶとタイプ（A客・B客・Aスタッフ・Bスタッフ）が自動で選ばれます。違うときはタップで変更できます。")

    seat_info = {}
    for seat in SEATS:
        sel_name = st.selectbox(
            SEAT_LABELS[seat], member_names, index=None,
            placeholder="名前を選択", key=f"sel_name_{seat}",
        )
        sel_type = None
        if sel_name:
            auto_type, source = resolve_player_type(sel_name, member_type, last_types)
            c1, c2 = st.columns([4, 1.4], vertical_alignment="center")
            with c1:
                # 名前ごとに別キーにすることで、名前を変えたらタイプも自動で切り替わる
                picked = st.segmented_control(
                    f"{seat}席のタイプ", TYPE_BUTTON_ORDER, default=auto_type,
                    format_func=lambda t: TYPE_LABELS[t],
                    key=f"sel_type_{seat}_{sel_name}", label_visibility="collapsed",
                )
            sel_type = picked or auto_type
            with c2:
                note = source if sel_type == auto_type else "手動で変更"
                st.caption(f"（{note}）")
        seat_info[seat] = {"name": sel_name, "type": sel_type}

    names_sel = [seat_info[s]["name"] for s in SEATS]
    members_ready = all(names_sel) and len(set(names_sel)) == 3

    # --- 着順 (1着→2着をタップ、3着は自動) ---
    st.markdown("### 🎯 着順")
    ranks = {}
    if not all(names_sel):
        st.info("3人とも名前を選ぶと着順を入力できます。")
    elif not members_ready:
        st.error("⚠️ 同じ人が複数の席にいます")
    else:
        fmt = lambda s: f"{s} {seat_info[s]['name']}"
        mkey = f"{ss['input_round']}_{'|'.join(names_sel)}"
        first = st.segmented_control(
            "🥇 1着", SEATS, format_func=fmt, key=f"rank1_{mkey}",
        )
        remain = [s for s in SEATS if s != first]
        second = st.segmented_control(
            "🥈 2着", remain if first else SEATS, format_func=fmt,
            key=f"rank2_{mkey}_{first}", disabled=first is None,
        )
        if first and second:
            third = [s for s in SEATS if s not in (first, second)][0]
            ranks = {first: 1, second: 2, third: 3}
            st.markdown(f"🥉 3着: **{fmt(third)}**")

    can_save = members_ready and len(ranks) == 3

    # --- 日時 (通常は保存した時刻。後から付けるときだけ指定) ---
    with st.expander("🕒 日時・備考（後から付けるときだけ）"):
        use_custom_dt = st.checkbox("日時を指定する", key="input_use_custom_dt")
        col_dt, col_time = st.columns(2)
        with col_dt:
            input_date = st.date_input("日付", value=now_jst().date(), key="input_date",
                                       disabled=not use_custom_dt)
        with col_time:
            input_time = st.time_input("時刻", value=now_jst().time().replace(second=0, microsecond=0),
                                       key="input_time", disabled=not use_custom_dt)
        memo = st.text_input("備考", value="", key="input_memo")

    # --- 保存ボタン ---
    col_save1, col_save2 = st.columns(2)
    with col_save1:
        save_continue = st.button(
            "💾 保存（同じメンバーで次へ）", type="primary",
            disabled=not can_save, use_container_width=True,
        )
    with col_save2:
        save_reset = st.button(
            "✅ 保存して空席に戻す",
            disabled=not can_save, use_container_width=True,
        )

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
                ss["input_flash"] = f"✅ {int(table_no)}卓に保存しました：{result}"
                ss["input_round"] += 1
                ss["input_pending_reset"] = "seats" if save_reset else "memo"
                st.rerun()
            else:
                st.error(f"❌ 保存に失敗しました（もう一度押してください）: {err}")

    if any(names_sel):
        st.button("🔄 全員を空席にする", use_container_width=True, on_click=_clear_seats)

    # --- ゲーム代 (集めると着順表に区切りが入る) ---
    today = get_today_logical_date()
    fees = load_fee_collections()
    render_fee_collect_section(df_all, fees, int(table_no), today)

    # --- この卓の今日の記録 (入力の確認用) ---
    df_today = get_games_by_date(df_all, today)
    if not df_today.empty:
        df_tbl = df_today[df_today["TableNo"] == int(table_no)]
        if not df_tbl.empty:
            st.markdown(f"### 📋 {int(table_no)}卓の今日の記録（{len(df_tbl)}局）")
            _render_table(df_tbl.reset_index(drop=True), get_fee_cuts(fees, table_no))


FEE_RULE_TEXT = "ゲーム代はトップ（1着）を取った人が払います。1回につき " + "・".join(
    f"{TYPE_LABELS[t]} {GAME_FEE_TABLE[t]}枚" for t in TYPE_BUTTON_ORDER)


def render_fee_collect_section(df_all, fees, table_no, today):
    """成績入力ページの「ゲーム代を集める」欄"""
    ss = st.session_state
    st.markdown(f"### 💰 {table_no}卓のゲーム代")
    df_open = get_open_section_games(df_all, fees, table_no, today)

    if df_open.empty:
        st.caption("前回ゲーム代を集めたあとの対局は、まだありません。")
    else:
        info = calc_game_fee(df_open)
        lines = "".join(
            f'<div class="fee-line"><span>{TYPE_LABELS[t]}のトップ</span>'
            f'<span><b>{n}回</b> × {unit}枚 = <b>{sub}枚</b></span></div>'
            for t, n, unit, sub in info["lines"]
        )
        if info["unknown"]:
            lines += (f'<div class="fee-line"><span>タイプ不明のトップ</span>'
                      f'<span><b>{info["unknown"]}回</b>（0枚で計算）</span></div>')
        st.markdown(_html(f"""
            <div class="fee-box">
              <div class="fee-box-title">前回の集金から <b>{info["games"]}局</b>：ゲーム代 <b class="fee-box-total">{info["total"]}枚</b></div>
              {lines}
              <div class="fee-rule">{FEE_RULE_TEXT}</div>
            </div>
        """), unsafe_allow_html=True)

        if ss.get("fee_confirm_table") == table_no:
            st.warning(f"{table_no}卓の {info['games']}局分、ゲーム代 {info['total']}枚 を集めて、着順表に区切りを入れます。よろしいですか？")
            c1, c2 = st.columns(2)
            with c1:
                do_collect = st.button("💰 集める", type="primary", use_container_width=True, key="fee_do")
            with c2:
                if st.button("やめる", use_container_width=True, key="fee_cancel"):
                    ss.pop("fee_confirm_table", None)
                    st.rerun()
            if do_collect:
                with st.spinner("保存中..."):
                    ok, err, done = collect_game_fee(table_no)
                ss.pop("fee_confirm_table", None)
                if ok:
                    ss["input_flash"] = (f"💰 {table_no}卓のゲーム代 {done['total']}枚 を集めました"
                                         f"（{done['games']}局分：{fee_breakdown_text(done)}）")
                    st.rerun()
                else:
                    st.error(f"❌ 集金を記録できませんでした: {err}")
        else:
            if st.button(f"💰 ゲーム代を集める（{info['total']}枚）", use_container_width=True, key="fee_start"):
                ss["fee_confirm_table"] = table_no
                st.rerun()

    # 今日この卓で集金していれば、直前の集金を取り消せる
    df_today = get_games_by_date(df_all, today)
    day_nos = set(df_today.loc[df_today["TableNo"] == table_no, "GameNo"]) if not df_today.empty else set()
    has_cut_today = any(int(c["LastGameNo"]) in day_nos for c in get_fee_cuts(fees, table_no))
    if has_cut_today:
        if st.button("↩️ 直前の集金を取り消す（区切りを消す）", key="fee_undo",
                     help="押し間違えたときに。対局の記録は消えません。"):
            with st.spinner("保存中..."):
                ok, err = undo_last_fee_collection(table_no, today)
            if ok:
                ss["input_flash"] = f"↩️ {table_no}卓の直前の集金を取り消しました"
                st.rerun()
            else:
                st.error(f"❌ 取り消せませんでした: {err}")


# ==========================================
# 7. 今日の着順表ページ
# ==========================================
def page_today():
    st.title("📋 今日の着順表")
    today = get_today_logical_date()
    st.caption(f"論理日付: **{today.strftime('%Y年%m月%d日')}** (午前9時までは前日扱い)")

    with st.spinner("データ読込中..."):
        df = load_score_data()
    df_day = get_games_by_date(df, today)

    if df_day.empty:
        st.info("今日の対局データはまだありません。")
        if st.button("🔄 再読み込み", use_container_width=True):
            _fetch_sheet.clear()
            st.rerun()
        return

    _render_day_summary(df_day)
    render_paper_sheet(df_day, today, load_fee_collections())

    if st.button("🔄 データを再読み込み", use_container_width=True):
        _fetch_sheet.clear()
        st.rerun()


# ==========================================
# 8. 過去の着順表ページ
# ==========================================
def page_past():
    st.title("📆 過去の着順表")
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
        "📅 日付を選択",
        range(len(dates)),
        format_func=lambda i: date_labels[i],
        key="past_date_select",
    )
    selected_date = dates[sel_idx]

    df_day = get_games_by_date(df, selected_date)

    st.markdown(f"### 🗓️ {date_labels[sel_idx]} の着順表")
    _render_day_summary(df_day)
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
        <span class="summary-badge">🀄 対局数: <strong>{total_games}</strong></span>
        <span class="summary-badge">🎲 卓数: <strong>{total_tables}</strong></span>
        <span class="summary-badge">👥 参加者: <strong>{len(all_players)}</strong>人</span>
    </div>
    """), unsafe_allow_html=True)


# ==========================================
# 9. メイン
# ==========================================
def main():
    st.markdown(
        f'<div style="margin-bottom:0.5rem;">'
        f'<span style="color:var(--text-muted);font-size:0.75rem;">🀄 ぱいんりばー</span>'
        f'<span style="float:right;color:var(--text-muted);font-size:0.75rem;">'
        f'最終更新: {datetime.now().strftime("%H:%M:%S")}</span></div>',
        unsafe_allow_html=True
    )

    tab_input, tab_today, tab_past = st.tabs([
        "📝 成績を付ける", "📋 今日の着順表", "📆 過去の着順表"
    ])
    with tab_input:
        page_input()
    with tab_today:
        page_today()
    with tab_past:
        page_past()


if __name__ == '__main__':
    main()
