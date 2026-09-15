"""
ぱいんりばー 成績入力・着順表 専用アプリ
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
3画面のシンプルな入力・閲覧アプリ:
  1. 📝 成績を付ける    - 対局結果を入力 (名前→タイプ自動選択・連続入力対応)
  2. 📋 今日の着順表    - 今日の対局を紙の着順表風に表示
  3. 📆 過去の着順表    - 日付を選んで過去の着順表を表示
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from streamlit_gsheets import GSheetsConnection

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
    --text-muted: #8b90a5;
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
.stCaption, [data-testid="stCaptionContainer"] { color: var(--text-muted) !important; }
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
    background: #ede8da; font-weight: 700; width: 28px; color: #777;
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
    font-size: 0.6rem; color: #8a7a55; margin-left: 2px;
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

.paper-title {
    font-weight: 900; font-size: 0.92rem; color: #2a2a2a;
    padding: 0.25rem 0.5rem; background: #e8e2d0; border-radius: 6px 6px 0 0;
    border: 1px solid #c2bba5; border-bottom: none;
    display: inline-block; margin-top: 0.5rem;
}

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

EXPECTED_COLS = [
    "GameNo", "TableNo", "SetNo", "日時", "備考",
    "Aさん", "Aタイプ", "A着順",
    "Bさん", "Bタイプ", "B着順",
    "Cさん", "Cタイプ", "C着順"
]

TYPE_OPTIONS = ["A客", "AS", "B客", "BS"]
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

def _guess_type_from_name(name):
    """
    名前末尾の記号からタイプを推測する。
    末尾 'B' → B客、末尾 'BS' → BS、末尾 'S' → AS、それ以外 → A客
    (メンバーシートにタイプ列がない場合のフォールバック)
    """
    n = str(name).strip()
    if n.endswith("BS"):
        return "BS"
    if n.endswith("B"):
        return "B客"
    if n.endswith("S"):
        return "AS"
    return "A客"

@st.cache_data(ttl=60, show_spinner=False)
def load_members(_conn):
    """
    メンバー一覧と名前→タイプの対応辞書を取得。
    Returns: (names: list, name_to_type: dict)
    """
    df = _fetch_sheet(_conn, SHEET_MEMBER)
    if df.empty or "名前" not in df.columns:
        return [], {}
    df = df.fillna("")
    names = []
    name_to_type = {}
    has_type_col = "タイプ" in df.columns
    for _, row in df.iterrows():
        name = str(row["名前"]).strip()
        if not name:
            continue
        if name in name_to_type:
            continue
        names.append(name)
        # タイプ列があればそれを使う、なければ名前から推測
        if has_type_col:
            t = str(row["タイプ"]).strip()
            if t not in TYPE_OPTIONS:
                t = _guess_type_from_name(name)
        else:
            t = _guess_type_from_name(name)
        name_to_type[name] = t
    return names, name_to_type

def append_score_row(row_dict):
    """scoreシートに1行追加する。"""
    conn = get_conn()
    try:
        current = _fetch_sheet(conn, SHEET_SCORE)
        if current is None or current.empty:
            current = pd.DataFrame(columns=EXPECTED_COLS)
        new_row_df = pd.DataFrame([row_dict])
        for c in EXPECTED_COLS:
            if c not in new_row_df.columns:
                new_row_df[c] = ""
        new_row_df = new_row_df[EXPECTED_COLS]
        for c in EXPECTED_COLS:
            if c not in current.columns:
                current[c] = ""
        current = current[EXPECTED_COLS]
        merged = pd.concat([current, new_row_df], ignore_index=True)
        conn.update(worksheet=SHEET_SCORE, data=merged)
        _fetch_sheet.clear()
        return True, None
    except Exception as e:
        return False, str(e)

# ==========================================
# 4. 日付・集計ヘルパー
# ==========================================
def get_today_logical_date():
    now = datetime.now()
    return (now - timedelta(hours=9)).date()

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
def render_paper_sheet(df_day, target_date):
    """
    指定日の対局を「紙の着順表」風に表示する。
    卓ごとに、各局の実際の着席メンバーを正確に表示。
    メンバーが変わったタイミングで名前行を挿入する。
    """
    if df_day.empty:
        st.info("この日の対局データはありません。")
        return

    tables = sorted(df_day["TableNo"].unique()) if "TableNo" in df_day.columns else [1]

    for table_no in tables:
        df_tbl = df_day[df_day["TableNo"] == table_no].copy()
        if df_tbl.empty:
            continue
        sort_keys = [k for k in ["SetNo", "GameNo"] if k in df_tbl.columns]
        if sort_keys:
            df_tbl = df_tbl.sort_values(sort_keys).reset_index(drop=True)

        st.markdown(f'<div class="paper-title">🎲 {int(table_no)}卓</div>', unsafe_allow_html=True)
        _render_table(df_tbl)


def _render_table(df_tbl):
    """
    1卓分の着順表を描画。
    各局の実際のメンバーを表示し、メンバーが変わったら名前行を差し込む。
    名前抜けを防ぐため、局ごとに実データを参照する。
    """
    # タイプ別の打数集計 (卓全体)
    type_counts = {"A客": 0, "AS": 0, "B客": 0, "BS": 0}

    html = '<div class="paper-wrap"><table class="paper-table">'
    # ヘッダー
    html += '<thead><tr>'
    html += '<th class="col-no">局</th>'
    html += '<th class="seat-head-A">A席</th>'
    html += '<th class="seat-head-B">B席</th>'
    html += '<th class="seat-head-C">C席</th>'
    html += '</tr></thead><tbody>'

    prev_members = None  # 直前の (A名, B名, C名)

    for _, row in df_tbl.iterrows():
        # この局の各席の名前・タイプ・着順を取得
        cur_names = {}
        cur_types = {}
        cur_ranks = {}
        for seat in ["A", "B", "C"]:
            nm = str(row.get(f"{seat}さん", "")).strip()
            tp = str(row.get(f"{seat}タイプ", "")).strip()
            try:
                rk = int(float(row.get(f"{seat}着順", 0)))
            except:
                rk = 0
            cur_names[seat] = nm
            cur_types[seat] = tp
            cur_ranks[seat] = rk
            # タイプ別打数集計
            if rk in [1, 2, 3] and tp in type_counts:
                type_counts[tp] += 1

        members = (cur_names["A"], cur_names["B"], cur_names["C"])

        # メンバーが前局と変わった (または最初) なら名前行を挿入
        if members != prev_members:
            html += '<tr class="name-row">'
            html += '<td class="col-no"></td>'
            for seat in ["A", "B", "C"]:
                nm = cur_names[seat] if cur_names[seat] else "-"
                tp = cur_types[seat]
                type_disp = f'<span class="name-type">{tp}</span>' if tp else ""
                html += f'<td>{nm}{type_disp}</td>'
            html += '</tr>'
            prev_members = members

        # 着順行
        try:
            game_no = int(float(row.get("GameNo", 0)))
        except:
            game_no = ""
        html += '<tr>'
        html += f'<td class="col-no">{game_no}</td>'
        for seat in ["A", "B", "C"]:
            rk = cur_ranks[seat]
            if rk == 1:
                html += '<td class="rank-cell rank1">1</td>'
            elif rk in [2, 3]:
                html += f'<td class="rank-cell">{rk}</td>'
            else:
                html += '<td class="empty-cell">·</td>'
        html += '</tr>'

    # ゲーム代枚数行 (タイプ別打数)
    total_games = len(df_tbl)
    html += '<tr class="gamecount-row">'
    html += '<td class="col-no">代</td>'
    html += '<td colspan="3" style="text-align:left;padding-left:8px;">'
    parts = []
    for t in ["A客", "AS", "B客", "BS"]:
        if type_counts[t] > 0:
            parts.append(f'{t} <strong>{type_counts[t]}</strong>')
    html += "　".join(parts) if parts else f'計 {total_games} 戦'
    html += '</td>'
    html += '</tr>'

    html += '</tbody></table></div>'
    st.markdown(html, unsafe_allow_html=True)


# ==========================================
# 6. 成績を付けるページ
# ==========================================
def page_input():
    st.title("📝 成績を付ける")

    conn = get_conn()
    with st.spinner("データ読込中..."):
        df_all = load_score_data()
        member_names, name_to_type = load_members(conn)

    if not member_names:
        st.warning("メンバーが登録されていません。管理画面から先にメンバー登録をしてください。")
        return

    # --- セッション状態の初期化 ---
    ss = st.session_state
    if "input_table_no" not in ss:
        ss["input_table_no"] = 1
    if "input_set_no" not in ss:
        ss["input_set_no"] = 1
    # 着席中のメンバー (連続入力用)
    if "seated" not in ss:
        ss["seated"] = {"A": None, "B": None, "C": None}

    next_game_no = get_next_game_no(df_all)

    # --- 対局情報 ---
    st.markdown("### ⚙️ 卓・局の設定")
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        game_no = st.number_input("GameNo", value=next_game_no, min_value=1, step=1, key="input_game_no")
    with col_b:
        table_no = st.number_input("卓番", value=ss["input_table_no"], min_value=1, step=1, key="input_table_widget")
        ss["input_table_no"] = table_no
    with col_c:
        set_no = st.number_input("セット", value=ss["input_set_no"], min_value=1, step=1, key="input_set_widget")
        ss["input_set_no"] = set_no

    col_dt, col_time = st.columns(2)
    with col_dt:
        input_date = st.date_input("日付", value=date.today(), key="input_date")
    with col_time:
        input_time = st.time_input("時刻", value=datetime.now().time().replace(microsecond=0), key="input_time")
    memo = st.text_input("備考 (任意)", value="", key="input_memo")

    # --- 着席メンバーの選択 ---
    st.markdown("### 🪑 メンバーを着席させる")
    st.caption("名前を選ぶとタイプ(A客/AS/B客/BS)が自動でセットされます。着席させると連続入力できます。")

    name_opts = ["--空席--"] + member_names
    seat_colors = {"A": "🟦 A席", "B": "🟧 B席", "C": "🟩 C席"}
    seat_types = {}

    for seat in ["A", "B", "C"]:
        st.markdown(f'<div class="seat-card seat-{seat}"><div class="seat-label">{seat_colors[seat]}</div></div>',
                    unsafe_allow_html=True)
        c1, c2 = st.columns([3, 1])
        with c1:
            # 現在着席中のメンバーをデフォルト選択
            cur = ss["seated"].get(seat)
            default_idx = name_opts.index(cur) if cur in name_opts else 0
            sel_name = st.selectbox(
                f"{seat}席の名前", name_opts, index=default_idx,
                key=f"sel_name_{seat}", label_visibility="collapsed"
            )
        with c2:
            # タイプ自動判定 (手動上書きも可)
            auto_type = name_to_type.get(sel_name, "A客") if sel_name != "--空席--" else "A客"
            type_idx = TYPE_OPTIONS.index(auto_type) if auto_type in TYPE_OPTIONS else 0
            sel_type = st.selectbox(
                f"{seat}席のタイプ", TYPE_OPTIONS, index=type_idx,
                key=f"sel_type_{seat}", label_visibility="collapsed"
            )
        seat_types[seat] = {"name": sel_name, "type": sel_type}

    # --- 着順入力 ---
    st.markdown("### 🎯 着順を入力")
    rc1, rc2, rc3 = st.columns(3)
    ranks = {}
    for seat, col in [("A", rc1), ("B", rc2), ("C", rc3)]:
        with col:
            nm = seat_types[seat]["name"]
            label = nm if nm != "--空席--" else f"{seat}席"
            ranks[seat] = st.selectbox(
                f"{label} の着順", RANK_OPTIONS, key=f"rank_{seat}"
            )

    st.divider()

    # --- バリデーション ---
    errors = []
    names_sel = [seat_types[s]["name"] for s in ["A", "B", "C"]]
    ranks_sel = [ranks[s] for s in ["A", "B", "C"]]
    if any(n == "--空席--" for n in names_sel):
        errors.append("全ての席にメンバーを着席させてください")
    else:
        if len(set(names_sel)) != 3:
            errors.append("同じ人が複数の席にいます")
    if sorted(ranks_sel) != [1, 2, 3]:
        errors.append("着順は 1・2・3 が1つずつ必要です")

    if errors:
        for e in errors:
            st.error(f"⚠️ {e}")

    can_save = len(errors) == 0

    # --- 保存ボタン (2種類) ---
    col_save1, col_save2 = st.columns(2)
    with col_save1:
        save_continue = st.button(
            "💾 保存して次の局へ", type="primary",
            disabled=not can_save, use_container_width=True,
            help="同じメンバーのまま次の局を入力できます"
        )
    with col_save2:
        save_only = st.button(
            "✅ 保存のみ",
            disabled=not can_save, use_container_width=True
        )

    if save_continue or save_only:
        dt_str = f"{input_date.strftime('%Y-%m-%d')} {input_time.strftime('%H:%M:%S')}"
        row = {
            "GameNo": int(game_no), "TableNo": int(table_no), "SetNo": int(set_no),
            "日時": dt_str, "備考": memo,
            "Aさん": seat_types["A"]["name"], "Aタイプ": seat_types["A"]["type"], "A着順": int(ranks["A"]),
            "Bさん": seat_types["B"]["name"], "Bタイプ": seat_types["B"]["type"], "B着順": int(ranks["B"]),
            "Cさん": seat_types["C"]["name"], "Cタイプ": seat_types["C"]["type"], "C着順": int(ranks["C"]),
        }
        with st.spinner("保存中..."):
            ok, err = append_score_row(row)
        if ok:
            st.success(f"✅ 保存しました (GameNo {game_no})")
            if save_continue:
                # メンバーを着席したまま保持、GameNoだけ進める
                for seat in ["A", "B", "C"]:
                    ss["seated"][seat] = seat_types[seat]["name"]
                # 着順選択だけリセット
                for seat in ["A", "B", "C"]:
                    if f"rank_{seat}" in ss:
                        del ss[f"rank_{seat}"]
                st.rerun()
            else:
                # 全リセット
                ss["seated"] = {"A": None, "B": None, "C": None}
                for seat in ["A", "B", "C"]:
                    for k in [f"sel_name_{seat}", f"rank_{seat}"]:
                        if k in ss:
                            del ss[k]
                st.balloons()
                st.rerun()
        else:
            st.error(f"❌ 保存に失敗しました: {err}")

    # --- 着席クリアボタン ---
    if any(ss["seated"].get(s) for s in ["A", "B", "C"]):
        seated_names = "・".join([ss["seated"][s] for s in ["A", "B", "C"] if ss["seated"].get(s)])
        st.markdown(
            f'<div class="seated-banner">🪑 着席中: <strong>{seated_names}</strong>（連続入力モード）</div>',
            unsafe_allow_html=True
        )
        if st.button("🔄 全員を空席にする", use_container_width=True):
            ss["seated"] = {"A": None, "B": None, "C": None}
            for seat in ["A", "B", "C"]:
                for k in [f"sel_name_{seat}", f"rank_{seat}"]:
                    if k in ss:
                        del ss[k]
            st.rerun()


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
    render_paper_sheet(df_day, today)

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
    render_paper_sheet(df_day, selected_date)


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
    st.markdown(f"""
    <div style="margin-bottom:0.5rem;">
        <span class="summary-badge">🀄 対局数: <strong>{total_games}</strong></span>
        <span class="summary-badge">🎲 卓数: <strong>{total_tables}</strong></span>
        <span class="summary-badge">👥 参加者: <strong>{len(all_players)}</strong>人</span>
    </div>
    """, unsafe_allow_html=True)


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
