"""
ぱいんりばー 成績入力・今日の着順表 専用アプリ
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
2画面のみのシンプルな入力・閲覧アプリ:
  1. 📝 成績を付ける  - 対局結果を入力してスプレッドシートに直接保存
  2. 📋 今日の着順表  - 今日の対局を集計表形式で表示
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

# ダークテーマ + 金アクセントCSS
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
    --radius: 12px;
}

/* 全体背景 */
.stApp {
    background: linear-gradient(180deg, #1a1d2e 0%, #232739 100%) !important;
    color: var(--text-primary) !important;
    font-family: "Zen Kaku Gothic New", "Noto Sans JP", "Hiragino Kaku Gothic ProN", Meiryo, sans-serif !important;
}

/* Streamlit標準要素の非表示 */
#MainMenu, header, footer {visibility: hidden;}
.stDeployButton {display: none;}

/* タイトル */
h1, h2, h3 {
    color: var(--text-primary) !important;
    font-weight: 900 !important;
    letter-spacing: 0.02em !important;
}

/* タブ */
button[role="tab"] {
    background: #2f3550 !important;
    color: #ffffff !important;
    border: 1px solid rgba(255,255,255,0.15) !important;
    border-radius: 10px 10px 0 0 !important;
    font-weight: 700 !important;
    padding: 0.6rem 1.2rem !important;
    margin-right: 4px !important;
}
button[role="tab"] * { color: inherit !important; }
button[role="tab"][aria-selected="true"] {
    background: var(--accent) !important;
    color: #000000 !important;
    border-color: var(--accent) !important;
}
button[role="tab"][aria-selected="true"] * { color: #000000 !important; }

/* ボタン (通常) */
.stButton > button {
    background: linear-gradient(135deg, var(--bg-card) 0%, #2f3550 100%) !important;
    color: var(--text-primary) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    font-weight: 700 !important;
    padding: 0.6rem 1.2rem !important;
    transition: transform 0.15s, box-shadow 0.15s !important;
}
.stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 12px rgba(0,0,0,0.3) !important;
    border-color: var(--accent) !important;
}

/* プライマリボタン (保存など) */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, var(--accent) 0%, #e0a828 100%) !important;
    color: #000000 !important;
    font-weight: 900 !important;
    border: none !important;
}
.stButton > button[kind="primary"]:hover {
    box-shadow: 0 6px 20px rgba(240,192,64,0.4) !important;
}

/* 入力フィールド */
.stTextInput input, .stNumberInput input, .stSelectbox select,
.stTextInput > div, .stNumberInput > div, .stSelectbox > div {
    background: var(--bg-card) !important;
    color: var(--text-primary) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
}
.stTextInput input:focus, .stNumberInput input:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 2px rgba(240,192,64,0.2) !important;
}

/* Selectbox の中身 */
[data-baseweb="select"] > div {
    background: var(--bg-card) !important;
    border-color: var(--border) !important;
    color: var(--text-primary) !important;
}

/* ラジオボタン */
[data-baseweb="radio"] {
    color: var(--text-primary) !important;
}

/* Alert (info/success/warning) */
.stAlert {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    color: var(--text-primary) !important;
}

/* Caption */
.stCaption, [data-testid="stCaptionContainer"] {
    color: var(--text-muted) !important;
}

/* Divider */
hr {
    border-color: var(--border) !important;
    opacity: 0.4 !important;
}

/* 着順表 (paper-sheet) */
.paper-sheet {
    background: #232739;
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1rem;
    overflow-x: auto;
    margin: 1rem 0;
}
.paper-table {
    border-collapse: collapse;
    width: 100%;
    font-family: "Zen Kaku Gothic New", "Noto Sans JP", sans-serif;
}
.paper-table th {
    background: #2f3550;
    color: var(--text-primary);
    padding: 0.5rem 0.7rem;
    border: 1px solid var(--border);
    text-align: center;
    font-weight: 700;
    font-size: 0.85rem;
}
.paper-table td {
    background: #1e2130;
    color: var(--text-primary);
    padding: 0.6rem 0.7rem;
    border: 1px solid var(--border);
    text-align: center;
    font-weight: 600;
    font-size: 0.9rem;
}
.paper-table td.rank-1 { color: var(--accent); font-weight: 900; }
.paper-table td.rank-2 { color: var(--accent2); font-weight: 900; }
.paper-table td.rank-3 { color: var(--red); font-weight: 900; }
.paper-table tr:nth-child(even) td { background: #232739; }

/* 席入力カード */
.seat-card {
    background: linear-gradient(135deg, var(--bg-card) 0%, #2a2f45 100%);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 0.9rem 1.1rem;
    margin-bottom: 0.7rem;
}
.seat-card.seat-A { border-left: 4px solid var(--accent2); }
.seat-card.seat-B { border-left: 4px solid #e07b39; }
.seat-card.seat-C { border-left: 4px solid var(--green); }
.seat-label {
    font-size: 0.75rem;
    color: var(--text-muted);
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin-bottom: 0.3rem;
}

/* サマリバッジ */
.summary-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    background: var(--bg-card);
    border: 1px solid var(--border);
    padding: 0.5rem 0.9rem;
    border-radius: 999px;
    font-size: 0.85rem;
    color: var(--text-primary);
    margin: 0.2rem 0.4rem 0.2rem 0;
}
.summary-badge strong {
    color: var(--accent);
    font-weight: 900;
}
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
        # 論理日付: 午前9時までは前日として扱う (深夜営業対応)
        df["論理日付"] = (df["日時Obj"] - timedelta(hours=9)).dt.date
    return df

def load_score_data():
    conn = get_conn()
    df = _fetch_sheet(conn, SHEET_SCORE)
    processed = process_score_df(df)
    if processed is None:
        # 列名不一致 → キャッシュクリアして再読込
        _fetch_sheet.clear()
        df = _fetch_sheet(conn, SHEET_SCORE)
        processed = process_score_df(df)
    if processed is None:
        st.error("スプレッドシートの列名が想定と異なります。管理者に連絡してください。")
        st.stop()
    return processed

def load_member_names():
    """メンバー名の一覧を取得 (namesのみ、括弧内は削除)"""
    conn = get_conn()
    df = _fetch_sheet(conn, SHEET_MEMBER)
    if df.empty or "名前" not in df.columns:
        return []
    names = df["名前"].fillna("").astype(str).tolist()
    # 括弧内を削除
    names = [str(n).strip() for n in names if str(n).strip()]
    # 重複除去 (順序保持)
    seen = set()
    unique_names = []
    for n in names:
        if n not in seen:
            seen.add(n)
            unique_names.append(n)
    return unique_names

def append_score_row(row_dict):
    """
    scoreシートに1行追加する。
    row_dict: EXPECTED_COLS の全列を持つ辞書
    """
    conn = get_conn()
    try:
        # 既存データを取得
        current = _fetch_sheet(conn, SHEET_SCORE)
        if current is None or current.empty:
            current = pd.DataFrame(columns=EXPECTED_COLS)

        # 新しい行を追加
        new_row_df = pd.DataFrame([row_dict])
        # 列を揃える
        for c in EXPECTED_COLS:
            if c not in new_row_df.columns:
                new_row_df[c] = ""
        new_row_df = new_row_df[EXPECTED_COLS]

        # 既存に append
        for c in EXPECTED_COLS:
            if c not in current.columns:
                current[c] = ""
        current = current[EXPECTED_COLS]
        merged = pd.concat([current, new_row_df], ignore_index=True)

        # スプレッドシートに更新
        conn.update(worksheet=SHEET_SCORE, data=merged)
        # キャッシュクリアで即反映
        _fetch_sheet.clear()
        return True, None
    except Exception as e:
        return False, str(e)

# ==========================================
# 4. 今日の対局を取得 (論理日付ベース)
# ==========================================
def get_today_logical_date():
    """現在時刻から論理日付を返す (午前9時までは前日扱い)"""
    now = datetime.now()
    return (now - timedelta(hours=9)).date()

def get_today_games(df, today=None):
    """今日 (論理日付) の対局を返す。日時順にソート済"""
    if df is None or df.empty:
        return pd.DataFrame()
    if today is None:
        today = get_today_logical_date()
    df_today = df[df["論理日付"] == today].copy()
    if df_today.empty:
        return df_today
    # 卓ごと・SetNo・GameNoでソート
    sort_keys = []
    if "TableNo" in df_today.columns: sort_keys.append("TableNo")
    if "SetNo" in df_today.columns: sort_keys.append("SetNo")
    if "GameNo" in df_today.columns: sort_keys.append("GameNo")
    if sort_keys:
        df_today = df_today.sort_values(sort_keys).reset_index(drop=True)
    return df_today

def get_next_game_no(df):
    """次のGameNoを返す (現在の最大値+1)"""
    if df is None or df.empty or "GameNo" not in df.columns:
        return 1
    max_no = pd.to_numeric(df["GameNo"], errors='coerce').fillna(0).max()
    return int(max_no) + 1

# ==========================================
# 5. 成績入力ページ
# ==========================================
def page_input():
    st.title("📝 成績を付ける")
    st.caption("対局結果を入力してスプレッドシートに直接保存します。")

    # 全データ取得 (GameNo決定用)
    with st.spinner("データ読込中..."):
        df_all = load_score_data()
        member_names = load_member_names()

    if not member_names:
        st.warning("メンバーが登録されていません。管理画面から先にメンバー登録をしてください。")
        return

    next_game_no = get_next_game_no(df_all)

    # --- 全体情報 ---
    st.markdown("### ⚙️ 対局情報")
    col_a, col_b, col_c = st.columns([1, 1, 1])
    with col_a:
        game_no = st.number_input("GameNo", value=next_game_no, min_value=1, step=1)
    with col_b:
        table_no = st.number_input("卓番", value=1, min_value=1, step=1)
    with col_c:
        set_no = st.number_input("SetNo", value=1, min_value=1, step=1)

    col_dt, col_memo = st.columns([1, 1])
    with col_dt:
        input_date = st.date_input("日付", value=date.today())
        input_time = st.time_input("時刻", value=datetime.now().time().replace(microsecond=0))
    with col_memo:
        memo = st.text_input("備考 (任意)", value="")

    st.markdown("### 🪑 席と着順")
    st.caption("A/B/C の3席それぞれに名前・タイプ・着順を選択してください")

    # 名前選択のオプション (未選択も含める)
    name_opts = ["--選択--"] + member_names

    # 3席の入力カード
    seat_inputs = {}
    for seat, color_label in [("A", "🟦 A席"), ("B", "🟧 B席"), ("C", "🟩 C席")]:
        st.markdown(f'<div class="seat-card seat-{seat}"><div class="seat-label">{color_label}</div></div>', unsafe_allow_html=True)
        c1, c2, c3 = st.columns([2, 1, 1])
        with c1:
            name = st.selectbox(f"名前 ({seat}席)", name_opts, key=f"name_{seat}",
                                 label_visibility="collapsed")
        with c2:
            ptype = st.selectbox(f"タイプ ({seat}席)", TYPE_OPTIONS, key=f"type_{seat}",
                                  label_visibility="collapsed")
        with c3:
            rank = st.selectbox(f"着順 ({seat}席)", RANK_OPTIONS, key=f"rank_{seat}",
                                 label_visibility="collapsed")
        seat_inputs[seat] = {"name": name, "type": ptype, "rank": rank}

    st.divider()

    # --- 保存ボタン ---
    st.markdown("### 💾 保存")

    # バリデーション
    errors = []
    names_selected = [seat_inputs[s]["name"] for s in ["A", "B", "C"]]
    ranks_selected = [seat_inputs[s]["rank"] for s in ["A", "B", "C"]]

    if any(n == "--選択--" for n in names_selected):
        errors.append("全ての席の名前を選択してください")
    else:
        # 重複チェック
        if len(set(names_selected)) != 3:
            errors.append("同じ人が2つ以上の席にいます")

    # 着順チェック (1,2,3が揃っているか)
    if sorted(ranks_selected) != [1, 2, 3]:
        errors.append("着順は 1・2・3 が1つずつ必要です")

    if errors:
        for e in errors:
            st.error(f"⚠️ {e}")

    # ボタン
    can_save = len(errors) == 0
    col_btn1, col_btn2 = st.columns([1, 3])
    with col_btn1:
        if st.button("💾 スプレッドシートに保存", type="primary", disabled=not can_save, use_container_width=True):
            # 日時を組み立て
            dt_str = f"{input_date.strftime('%Y-%m-%d')} {input_time.strftime('%H:%M:%S')}"

            row = {
                "GameNo": int(game_no),
                "TableNo": int(table_no),
                "SetNo": int(set_no),
                "日時": dt_str,
                "備考": memo,
                "Aさん": seat_inputs["A"]["name"],
                "Aタイプ": seat_inputs["A"]["type"],
                "A着順": int(seat_inputs["A"]["rank"]),
                "Bさん": seat_inputs["B"]["name"],
                "Bタイプ": seat_inputs["B"]["type"],
                "B着順": int(seat_inputs["B"]["rank"]),
                "Cさん": seat_inputs["C"]["name"],
                "Cタイプ": seat_inputs["C"]["type"],
                "C着順": int(seat_inputs["C"]["rank"]),
            }
            with st.spinner("保存中..."):
                ok, err = append_score_row(row)
            if ok:
                st.success(f"✅ 保存しました (GameNo {game_no})")
                st.balloons()
                # フォームをクリア(再rerun)
                # 選択状態をリセットするため、キーを削除
                for seat in ["A", "B", "C"]:
                    for k in [f"name_{seat}", f"rank_{seat}"]:
                        if k in st.session_state:
                            del st.session_state[k]
                st.rerun()
            else:
                st.error(f"❌ 保存に失敗しました: {err}")

# ==========================================
# 6. 今日の着順表ページ
# ==========================================
def page_today():
    st.title("📋 今日の着順表")

    today = get_today_logical_date()
    st.caption(f"論理日付: **{today.strftime('%Y年%m月%d日')}** (午前9時までは前日扱い)")

    with st.spinner("データ読込中..."):
        df = load_score_data()

    df_today = get_today_games(df, today)

    if df_today.empty:
        st.info("今日の対局データはまだありません。")
        return

    # --- サマリ ---
    total_games = len(df_today)
    total_tables = df_today["TableNo"].nunique() if "TableNo" in df_today.columns else 0
    # 参加プレイヤー数 (ユニーク)
    all_players = set()
    for _, row in df_today.iterrows():
        for seat in ["A", "B", "C"]:
            name = str(row.get(f"{seat}さん", "")).strip()
            if name:
                all_players.add(name)

    summary_html = f"""
    <div style="margin-bottom:1rem;">
        <span class="summary-badge">🀄 対局数: <strong>{total_games}</strong></span>
        <span class="summary-badge">🎲 卓数: <strong>{total_tables}</strong></span>
        <span class="summary-badge">👥 参加者: <strong>{len(all_players)}</strong>人</span>
    </div>
    """
    st.markdown(summary_html, unsafe_allow_html=True)

    st.divider()

    # --- 卓ごとに集計表を表示 ---
    tables = sorted(df_today["TableNo"].unique()) if "TableNo" in df_today.columns else [1]

    for table_no in tables:
        df_tbl = df_today[df_today["TableNo"] == table_no].copy()
        if df_tbl.empty:
            continue

        st.markdown(f"### 🎲 {int(table_no)}卓")

        # このテーブルの各プレイヤーの成績を集計
        player_ranks = {}  # name -> [rank1, rank2, ...]
        for _, row in df_tbl.iterrows():
            for seat in ["A", "B", "C"]:
                name = str(row.get(f"{seat}さん", "")).strip()
                if not name:
                    continue
                try:
                    r = int(float(row.get(f"{seat}着順", 0)))
                except:
                    r = 0
                if r not in [1, 2, 3]:
                    continue
                if name not in player_ranks:
                    player_ranks[name] = []
                player_ranks[name].append(r)

        # ゲーム時系列のテーブル (詳細)
        # 「対局番号 / 時間 / A席 / B席 / C席」の形式
        game_rows_html = []
        for _, row in df_tbl.iterrows():
            game_no = row.get("GameNo", "")
            try:
                game_no = int(float(game_no))
            except:
                pass
            # 時刻
            dt_obj = row.get("日時Obj", None)
            time_str = ""
            if pd.notna(dt_obj) and dt_obj != pd.Timestamp("1900-01-01"):
                try:
                    time_str = dt_obj.strftime("%H:%M")
                except:
                    time_str = ""

            # 各席の内容
            seat_cells = []
            for seat in ["A", "B", "C"]:
                name = str(row.get(f"{seat}さん", "")).strip()
                try:
                    rk = int(float(row.get(f"{seat}着順", 0)))
                except:
                    rk = 0
                rank_class = f"rank-{rk}" if rk in [1, 2, 3] else ""
                medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(rk, "")
                cell = f'<td class="{rank_class}">{medal} {name}</td>' if name else '<td>-</td>'
                seat_cells.append(cell)

            game_rows_html.append(
                f'<tr><td>{game_no}</td><td>{time_str}</td>{"".join(seat_cells)}</tr>'
            )

        detail_html = f"""
        <div class="paper-sheet">
            <table class="paper-table">
                <thead><tr>
                    <th style="width:60px;">局</th>
                    <th style="width:70px;">時間</th>
                    <th>A席 🥇=1位</th>
                    <th>B席</th>
                    <th>C席</th>
                </tr></thead>
                <tbody>{''.join(game_rows_html)}</tbody>
            </table>
        </div>
        """
        st.markdown(detail_html, unsafe_allow_html=True)

        # プレイヤー別集計
        if player_ranks:
            summary_data = []
            for name, ranks_list in player_ranks.items():
                total = len(ranks_list)
                cnt1 = ranks_list.count(1)
                cnt2 = ranks_list.count(2)
                cnt3 = ranks_list.count(3)
                avg = sum(ranks_list) / total if total > 0 else 0
                summary_data.append({
                    "名前": name,
                    "打数": total,
                    "🥇": cnt1,
                    "🥈": cnt2,
                    "🥉": cnt3,
                    "平均": f"{avg:.2f}",
                })
            summary_data.sort(key=lambda x: (float(x["平均"]), -x["🥇"]))

            # HTMLテーブル
            summary_rows_html = []
            for i, s in enumerate(summary_data):
                highlight = "background:rgba(240,192,64,0.08);" if i == 0 else ""
                summary_rows_html.append(
                    f'<tr style="{highlight}">'
                    f'<td>{i+1}</td>'
                    f'<td style="text-align:left;">{s["名前"]}</td>'
                    f'<td>{s["打数"]}</td>'
                    f'<td class="rank-1">{s["🥇"]}</td>'
                    f'<td class="rank-2">{s["🥈"]}</td>'
                    f'<td class="rank-3">{s["🥉"]}</td>'
                    f'<td><strong>{s["平均"]}</strong></td>'
                    f'</tr>'
                )
            summary_html = f"""
            <div class="paper-sheet" style="margin-top:0.5rem;">
                <table class="paper-table">
                    <thead><tr>
                        <th>順位</th>
                        <th style="text-align:left;">名前</th>
                        <th>打数</th>
                        <th>🥇</th>
                        <th>🥈</th>
                        <th>🥉</th>
                        <th>平均着順</th>
                    </tr></thead>
                    <tbody>{''.join(summary_rows_html)}</tbody>
                </table>
            </div>
            """
            with st.expander(f"📊 {int(table_no)}卓のプレイヤー別集計", expanded=False):
                st.markdown(summary_html, unsafe_allow_html=True)

        st.markdown("<div style='height:1rem;'></div>", unsafe_allow_html=True)

    # --- 手動更新ボタン ---
    if st.button("🔄 データを再読み込み", use_container_width=True):
        _fetch_sheet.clear()
        st.rerun()

# ==========================================
# 7. メイン (タブで2画面を切り替え)
# ==========================================
def main():
    # ヘッダー
    st.markdown(
        f'<div style="margin-bottom:0.5rem;">'
        f'<span style="color:var(--text-muted);font-size:0.75rem;">🀄 ぱいんりばー</span>'
        f'<span style="float:right;color:var(--text-muted);font-size:0.75rem;">'
        f'最終更新: {datetime.now().strftime("%H:%M:%S")}'
        f'</span></div>',
        unsafe_allow_html=True
    )

    # 2つのタブで切り替え
    tab_input, tab_today = st.tabs(["📝 成績を付ける", "📋 今日の着順表"])

    with tab_input:
        page_input()
    with tab_today:
        page_today()


if __name__ == '__main__':
    main()
