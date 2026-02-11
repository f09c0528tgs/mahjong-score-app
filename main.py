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
st.set_page_config(page_title="ぱいん成績管理", layout="wide")

hide_style = """
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    
    .score-sheet {
        border-collapse: collapse;
        width: 100%;
        max_width: 1000px;
        margin-bottom: 20px;
        font-family: "Hiragino Kaku Gothic ProN", Meiryo, sans-serif;
        color: #000;
        background-color: #fff;
    }
    .score-sheet th, .score-sheet td {
        border: 1px solid #333;
        padding: 6px 4px;
        text-align: center;
        font-size: 14px;
        vertical-align: middle;
    }
    .score-sheet th {
        background-color: #f2f2f2;
        font-weight: bold;
    }
    .score-sheet .set-header {
        background-color: #d9edf7;
        text-align: left;
        padding-left: 10px;
        font-weight: bold;
        font-size: 15px;
    }
    .rank-num {
        font-weight: bold;
        font-size: 16px;
        margin-left: 5px;
        display: inline-block;
        width: 20px;
        text-align: center;
    }
    .cell-top {
        background-color: #e6f7ff !important; 
    }
    .rank-special {
        background-color: #333;
        color: #fff;
        border-radius: 50%;
        width: 22px;
        height: 22px;
        line-height: 22px;
        font-size: 13px;
    }
    .score-sheet .summary-row td {
        background-color: #fffbe6;
        font-weight: bold;
        border-top: 2px double #333;
    }

    .stats-table {
        border-collapse: collapse;
        width: 100%;
        max_width: 800px;
        margin-bottom: 20px;
        font-family: "Hiragino Kaku Gothic ProN", Meiryo, sans-serif;
    }
    .stats-table th {
        background-color: #333;
        color: #fff;
        padding: 10px;
        border: 1px solid #333;
        text-align: center;
        font-weight: normal;
    }
    .stats-table td {
        background-color: #fff;
        color: #000;
        padding: 15px;
        border: 1px solid #ccc;
        text-align: center;
        font-weight: bold;
        font-size: 18px;
    }
    .stats-sub {
        font-size: 12px;
        color: #666;
        display: block;
        margin-top: 4px;
    }
    </style>
"""
st.markdown(hide_style, unsafe_allow_html=True)

# ==========================================
# 2. パスワード認証
# ==========================================


# ==========================================
# 3. データ管理関数 (安全装置付き)
# ==========================================
SHEET_SCORE = "score"
SHEET_MEMBER = "members"
SHEET_LOG = "logs"
SHEET_PROFIT = "daily_profits"

# 期待する列定義
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

# --- データ補正ロジック ---
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
    new_log = pd.DataFrame([{
        "日時": jst_now,
        "操作": action,
        "GameNo": game_no,
        "詳細": detail
    }])
    
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
            
        df["最大飜数"] = pd.to_numeric(df["最大飜数"], errors='coerce').fillna(0).astype(int)
        df["役満回数"] = pd.to_numeric(df["役満回数"], errors='coerce').fillna(0).astype(int)
        
        return df
    except:
        return pd.DataFrame({"名前": [], "登録日": [], "最大飜数": [], "役満回数": []})

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

# --- 利益データ管理関数 ---
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
            st.error(f"エラー: スプレッドシートに '{SHEET_PROFIT}' という名前のシートが見つかりません。")
            st.info("スプレッドシートの下にある「＋」ボタンで新しいシートを追加し、名前を 'daily_profits' に変更してください。")
        else:
            st.error(f"保存エラー: {e}")
        st.stop()

# ==========================================
# 4. 集計 & レンダリングロジック
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
                <tr class="set-header"><td colspan="6">📄 第 {int(set_no)} セット (卓: {int(table_no)})</td></tr>
                <tr>
                    <th style="width:5%">No</th>
                    <th style="width:10%">時刻</th>
                    <th style="width:23%">A席</th>
                    <th style="width:23%">B席</th>
                    <th style="width:23%">C席</th>
                    <th style="width:16%">備考</th>
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
                    rank_span = f'<span class="rank-num rank-special">❶</span>'
                else:
                    char_map = {"1":"①", "2":"②", "3":"③"}
                    d_char = char_map.get(rank_val, rank_val)
                    color_style = "color:#000;"
                    rank_span = f'<span class="rank-num" style="{color_style}">{d_char}</span>'
                
                p_name = row[f"{p_char}さん"]
                p_type = row[f"{p_char}タイプ"] 
                
                if p_name == last_names[p_char]:
                    display_text = ""
                else:
                    display_text = f"{p_name}<span style='font-size:11px; color:#555; margin-left:3px;'>({p_type})</span>"
                    last_names[p_char] = p_name
                
                cell_content = f'<div style="display:flex; justify-content:space-between; align-items:center; padding:0 5px;"><span>{display_text}</span>{rank_span}</div>'
                ranks_html_list.append(f'<td{td_class}>{cell_content}</td>')

            note_txt = row["備考"] if row["備考"] else ""
            html += f'<tr><td>{row["DailyNo"]}</td><td>{time_str}</td>{ranks_html_list[0]}{ranks_html_list[1]}{ranks_html_list[2]}<td style="color:red; font-size:12px;">{note_txt}</td></tr>'

        html += f'<tr class="summary-row"><td colspan="2" style="text-align:right;">合計</td><td>ゲーム代: <span style="font-size:16px; color:#d9534f;">{fee}</span> 枚</td><td colspan="3" style="font-size:12px; text-align:left;">A客:{stats["A客"]} / B客:{stats["B客"]} / AS:{stats["AS"]} / BS:{stats["BS"]}</td></tr></tbody></table>'
        
        st.markdown(html, unsafe_allow_html=True)

# ==========================================
# 5. 各ページ画面
# ==========================================

def player_input_row_dynamic(label, member_list, def_n, def_t, def_r, available_ranks, key_suffix=""):
    st.markdown(f"**▼ {label}**")
    TYPE_OPTS = ["A客", "B客", "AS", "BS"]
    
    def get_idx_in_list(lst, val): return lst.index(val) if val in lst else None
    def get_idx_in_opts(opts, val): return opts.index(val) if val in opts else 0

    c1, c2 = st.columns([1, 2])
    with c1:
        idx_val = get_idx_in_list(member_list, def_n) if def_n else None
        name = st.selectbox("名前", member_list, index=idx_val, key=f"n_{label}{key_suffix}")
    with c2:
        final_idx = 0
        if def_r in available_ranks:
            final_idx = available_ranks.index(def_r)
        
        rank = st.radio("着順", available_ranks, index=final_idx, horizontal=True, key=f"r_{label}{key_suffix}")
        type_ = st.radio("タイプ", TYPE_OPTS, index=get_idx_in_opts(TYPE_OPTS, def_t), horizontal=True, key=f"t_{label}{key_suffix}")
    
    st.markdown("---")
    return name, type_, rank

# --- ホーム画面 (Adminのみ) ---
def page_home():
    st.title("🀄 ぱいん成績管理")
    st.write("")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("📝 成績をつける", type="primary", use_container_width=True):
            st.session_state["page"] = "input"
            st.rerun()
        st.write("")
        if st.button("🏆 ランキング", use_container_width=True):
            st.session_state["page"] = "ranking"
            st.rerun()
    with c2:
        if st.button("📊 データを見る", use_container_width=True):
            st.session_state["page"] = "history"
            st.rerun()
        st.write("")
        if st.button("👥 メンバー管理", use_container_width=True):
            st.session_state["page"] = "members"
            st.rerun()
    
    st.write("")
    if st.button("📜 操作ログ", use_container_width=True):
        st.session_state["page"] = "logs"
        st.rerun()

    # QRコード表示削除

# --- メンバー管理画面 ---
def page_members():
    st.title("👥 メンバー管理")
    if st.button("🏠 ホームに戻る"):
        st.session_state["page"] = "home"
        st.rerun()
    st.info("同姓同名の場合は「田中（A）」「田中（B）」のように区別して登録してください。")
    df_mem = load_member_data()
    with st.form("add_member_form"):
        new_name = st.text_input("新しいメンバーの名前を入力")
        submitted = st.form_submit_button("追加する")
        if submitted and new_name:
            if new_name in df_mem["名前"].values:
                st.error(f"「{new_name}」は既に登録されています")
            else:
                new_row = {"名前": new_name, "登録日": date.today(), "最大飜数": 0, "役満回数": 0}
                df_mem = pd.concat([df_mem, pd.DataFrame([new_row])], ignore_index=True)
                save_member_data(df_mem)
                st.success(f"「{new_name}」を追加しました")
                st.rerun()
    st.divider()
    st.markdown("### 登録済みメンバー一覧")
    if not df_mem.empty:
        for i, row in df_mem.iterrows():
            c1, c2 = st.columns([4, 1])
            c1.write(f"👤 **{row['名前']}**")
            if c2.button("削除", key=f"del_{i}"):
                df_mem = df_mem.drop(i)
                save_member_data(df_mem)
                st.warning(f"「{row['名前']}」を削除しました")
                st.rerun()
    else:
        st.write("登録メンバーはいません")

# --- 編集専用画面 ---
def page_edit():
    st.title("🔧 データの修正・削除")
    
    edit_id = st.session_state.get("editing_game_id")
    if not edit_id:
        st.error("編集対象が選択されていません")
        if st.button("戻る"):
            st.session_state["page"] = "input"
            st.rerun()
        return

    df = load_score_data()
    target_row = df[df["GameNo"] == edit_id]
    
    if target_row.empty:
        st.error("データが見つかりません（削除された可能性があります）")
        if st.button("戻る"):
            st.session_state["page"] = "input"
            st.rerun()
        return

    row = target_row.iloc[0]
    member_list = get_all_member_names()
    
    st.info(f"編集中: No.{row['DailyNo']} (卓: {row['TableNo']}, セット: {row['SetNo']})")

    with st.form("edit_form"):
        p1_n, p1_t, p1_r = player_input_row_dynamic("A席", member_list, row["Aさん"], row["Aタイプ"], int(float(row["A着順"])), [1, 2, 3], "_edit")
        p2_n, p2_t, p2_r = player_input_row_dynamic("B席", member_list, row["Bさん"], row["Bタイプ"], int(float(row["B着順"])), [1, 2, 3], "_edit")
        p3_n, p3_t, p3_r = player_input_row_dynamic("C席", member_list, row["Cさん"], row["Cタイプ"], int(float(row["C着順"])), [1, 2, 3], "_edit")

        st.markdown("**▼ 備考**")
        NOTE_OPTS = ["なし", "東１終了", "２人飛ばし", "５連勝〜"]
        def idx(opts, val): return opts.index(val) if val in opts else 0
        cur_note = row["備考"] if row["備考"] else "なし"
        opts = NOTE_OPTS if cur_note in NOTE_OPTS else NOTE_OPTS + [cur_note]
        note = st.radio("内容を選択", opts, index=idx(opts, cur_note), horizontal=True)
        
        st.divider()
        
        c_up, c_del, c_can = st.columns(3)
        with c_up:
            submit_update = st.form_submit_button("🔄 更新して保存", type="primary", use_container_width=True)
        with c_del:
            submit_delete = st.form_submit_button("🗑 このデータを削除", type="secondary", use_container_width=True)
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
                        ("備考", "備考"),
                        ("A名前", "Aさん"), ("A着順", "A着順"), ("Aタイプ", "Aタイプ"),
                        ("B名前", "Bさん"), ("B着順", "B着順"), ("Bタイプ", "Bタイプ"),
                        ("C名前", "Cさん"), ("C着順", "C着順"), ("Cタイプ", "Cタイプ"),
                    ]
                    for label, key in compare_keys:
                        old_val = row[key]
                        new_val = new_data[key]
                        if str(old_val) != str(new_val):
                            changes.append(f"{label}: {old_val}→{new_val}")
                    
                    diff_text = ", ".join(changes) if changes else "変更なし"
                    
                    idx = df_latest[df_latest["GameNo"] == edit_id].index[0]
                    df_latest.loc[idx, list(new_data.keys())] = list(new_data.values())
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
                
                del_info = f"{row['日時']} {row['TableNo']}卓 Set{row['SetNo']} (A:{row['Aさん']}, B:{row['Bさん']}, C:{row['Cさん']})"
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
        components.html("""<script>try{var main=window.parent.document.querySelector('section.main');if(main){main.scrollTo(0,0);}window.parent.scrollTo(0,0);}catch(e){console.log(e);}</script>""", height=0)
        st.session_state["success_msg"] = None 
    if st.button("🏠 ホームに戻る"):
        st.session_state["page"] = "home"
        st.rerun()

    df = load_score_data()
    member_list = get_all_member_names()
    JST = timezone(timedelta(hours=9), 'JST')
    
    c_top1, c_top2 = st.columns(2)
    with c_top1:
        current_table = st.selectbox("入力する卓を選択してください", [1, 2, 3], index=0)
    with c_top2:
        current_dt = datetime.now(JST)
        default_date_obj = (current_dt - timedelta(hours=9)).date()
        input_date = st.date_input("日付 (朝9時切替)", value=default_date_obj)

    df_table = df[df["TableNo"] == current_table]
    if not df_table.empty:
        mask = df_table["論理日付"].apply(lambda x: x == input_date if pd.notnull(x) else False)
        df_today = df_table[mask]
    else:
        df_today = pd.DataFrame()

    st.subheader("🆕 新しい対局の入力")
    
    # 既存データの最大値を取得（表示用）
    if not df_today.empty and "SetNo" in df_today.columns:
        current_set_no = int(df_today["SetNo"].max())
    else:
        current_set_no = 1

    if not df_today.empty and "DailyNo" in df_today.columns:
        next_display_no = int(df_today["DailyNo"].max()) + 1
    else:
        next_display_no = 1
    
    if not df.empty and "GameNo" in df.columns:
        next_internal_game_no = df["GameNo"].max() + 1
    else:
        next_internal_game_no = 1
    
    last_n1, last_t1 = None, "A客"
    last_n2, last_t2 = None, "B客"
    last_n3, last_t3 = None, "AS"

    if not df_today.empty:
        last_game = df_today.iloc[-1]
        last_n1 = last_game["Aさん"]
        last_t1 = last_game["Aタイプ"]
        last_n2 = last_game["Bさん"]
        last_t2 = last_game["Bタイプ"]
        last_n3 = last_game["Cさん"]
        last_t3 = last_game["Cタイプ"]

    st.markdown(f"**▼ A席**")
    c1, c2 = st.columns([1, 2])
    with c1:
        idx1 = member_list.index(last_n1) if last_n1 in member_list else None
        n1 = st.selectbox("名前", member_list, index=idx1, key="p1_name_input")
    with c2:
        r1 = st.radio("着順", [1, 2, 3], index=1, horizontal=True, key="p1_rank_input")
        TYPE_OPTS = ["A客", "B客", "AS", "BS"]
        t_idx1 = TYPE_OPTS.index(last_t1) if last_t1 in TYPE_OPTS else 0
        t1 = st.radio("タイプ", TYPE_OPTS, index=t_idx1, horizontal=True, key="p1_type_input")
    st.markdown("---")

    st.markdown(f"**▼ B席**")
    c1, c2 = st.columns([1, 2])
    ranks_for_2 = [x for x in [1, 2, 3] if x != r1]
    with c1:
        idx2 = member_list.index(last_n2) if last_n2 in member_list else None
        n2 = st.selectbox("名前", member_list, index=idx2, key="p2_name_input")
    with c2:
        r2 = st.radio("着順", ranks_for_2, index=0, horizontal=True, key="p2_rank_input")
        t_idx2 = TYPE_OPTS.index(last_t2) if last_t2 in TYPE_OPTS else 1
        t2 = st.radio("タイプ", TYPE_OPTS, index=t_idx2, horizontal=True, key="p2_type_input")
    st.markdown("---")

    st.markdown(f"**▼ C席**")
    c1, c2 = st.columns([1, 2])
    ranks_for_3 = [x for x in ranks_for_2 if x != r2]
    with c1:
        idx3 = member_list.index(last_n3) if last_n3 in member_list else None
        n3 = st.selectbox("名前", member_list, index=idx3, key="p3_name_input")
    with c2:
        r3 = st.radio("着順", ranks_for_3, index=0, horizontal=True, key="p3_rank_input")
        t_idx3 = TYPE_OPTS.index(last_t3) if last_t3 in TYPE_OPTS else 2
        t3 = st.radio("タイプ", TYPE_OPTS, index=t_idx3, horizontal=True, key="p3_type_input")
    st.markdown("---")

    st.markdown("**▼ 備考**")
    NOTE_OPTS = ["なし", "東１終了", "２人飛ばし", "５連勝〜"]
    note = st.radio("内容を選択", NOTE_OPTS, index=0, horizontal=True)
    st.write(f"**次の記録: No.{next_display_no}**")
    
    st.caption(f"【{current_table}卓】 第 {current_set_no} セット")
    start_new_set = st.checkbox(f"🆕 ここから新しいセットにする ({current_table}卓の第{current_set_no+1}セットへ)")
    
    st.divider()
    
    if st.button("📝 記録する", type="primary", use_container_width=True):
        if not n1 or not n2 or not n3:
            st.error("⚠️ 名前が選択されていません！")
        else:
            with st.spinner("サーバーに書き込み中..."):
                fetch_data_cached.clear()
                
                try:
                    df_latest = load_score_data_fresh()
                except:
                    st.error("データの読み込みに失敗しました。再試行してください。")
                    st.stop()
                
                if not df.empty and df_latest.empty:
                    st.error("🚨 エラー：最新データの取得に失敗しました。データ消失を防ぐため保存を中止しました。")
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
                
                final_set_no = current_set_no
                if start_new_set: final_set_no += 1
                
                new_row = {
                    "GameNo": next_internal_game_no, "TableNo": current_table, "SetNo": final_set_no,
                    "日時": save_date_str, "備考": ("" if note == "なし" else note),
                    "Aさん": n1, "Aタイプ": t1, "A着順": r1,
                    "Bさん": n2, "Bタイプ": t2, "B着順": r2,
                    "Cさん": n3, "Cタイプ": t3, "C着順": r3
                }
                
                df_final = pd.concat([df_latest, pd.DataFrame([new_row])], ignore_index=True)
                save_score_data(df_final)
                
                log_detail = f"新規: {current_table}卓 No.{next_display_no}"
                save_action_log("新規登録", next_internal_game_no, log_detail)
                
            time_str = now_jst.strftime("%H:%M")
            st.session_state["success_msg"] = f"✅ 記録しました！ ({time_str} / No.{next_display_no})"
            st.rerun()

    st.divider()

    # --- 利益管理フォーム ---
    st.markdown("### 💰 本日の利益管理")
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
        st.write(f"日付: **{input_date}**")
        col_d, col_n = st.columns(2)
        
        with col_d:
            st.info("🌞 9:00 - 21:00")
            d_mix = st.number_input("MIX差", value=init_day_mix, key="d_mix")
            d_real = st.number_input("実利益", value=init_day_real, key="d_real")
            
        with col_n:
            st.success("🌙 21:00 - 33:00")
            n_mix = st.number_input("MIX差", value=init_night_mix, key="n_mix")
            n_real = st.number_input("実利益", value=init_night_real, key="n_real")
            
        st.markdown("---")
        profit_pass = st.text_input("🔒 保存用パスワード", type="password", help="利益データを更新するにはパスワードが必要です")
        
        if st.form_submit_button("利益を保存"):
            if profit_pass == "7777":
                df_new = df_profit[df_profit["Date"] != search_date_str].copy()
                new_rows = [
                    {"Date": search_date_str, "TimeSlot": "Day", "MixDiff": d_mix, "RealProfit": d_real},
                    {"Date": search_date_str, "TimeSlot": "Night", "MixDiff": n_mix, "RealProfit": n_real}
                ]
                df_new = pd.concat([df_new, pd.DataFrame(new_rows)], ignore_index=True)
                save_profit_data(df_new)
                st.success("利益データを保存しました")
                time.sleep(1)
                st.rerun()
            else:
                st.error("パスワードが違います。権限がありません。")

    st.divider()

    if not df_today.empty:
        st.markdown("### 📋 本日の履歴")

        total_fee_today = 0
        type_counts = {"A客": 0, "B客": 0, "AS": 0, "BS": 0}
        total_back_a = 0
        total_back_b = 0
        FEE_MAP = {"A客": 3, "B客": 5, "AS": 1, "BS": 1}

        for _, row in df_today.iterrows():
            w_type = None
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

            if r_a == 1: w_type = row["Aタイプ"]
            elif r_b == 1: w_type = row["Bタイプ"]
            elif r_c == 1: w_type = row["Cタイプ"]

            if w_type in type_counts:
                type_counts[w_type] += 1
                total_fee_today += FEE_MAP[w_type]

            note = str(row["備考"])
            discount = 0
            if note == "東１終了": discount = 1
            elif note == "２人飛ばし": discount = 2
            elif note == "５連勝〜": discount = 5
            
            total_fee_today -= discount
            
            if discount > 0 and winner_type:
                if winner_type == "A客": total_back_a += discount
                elif winner_type == "B客": total_back_b += discount

        st.info(f"💰 **本日の合計:** ゲーム代 **{total_fee_today}** 枚  \n"
                f"🎁 **バック:** A客: **{total_back_a}** 枚 / B客: **{total_back_b}** 枚  \n"
                f"📊 **内訳:** A客:{type_counts['A客']} / B客:{type_counts['B客']} / AS:{type_counts['AS']} / BS:{type_counts['BS']}")
        
        render_paper_sheet(df_today)
        st.write("")
        
        st.caption("👇 修正したい行をクリックすると、編集画面に移動します")
        df_display = df_today.sort_values("DailyNo", ascending=True)[["DailyNo", "SetNo", "日時", "Aさん", "Bさん", "Cさん"]].copy()
        
        def safe_strftime(x):
            try: return pd.to_datetime(x).strftime('%H:%M')
            except: return ""
        df_display["日時"] = df_display["日時"].apply(safe_strftime)
        
        event = st.dataframe(
            df_display, 
            use_container_width=True, 
            hide_index=True,
            on_select="rerun",
            selection_mode="single-row"
        )
        
        if len(event.selection.rows) > 0:
            selected_idx = event.selection.rows[0]
            target_daily_no = df_display.iloc[selected_idx]["DailyNo"]
            target_rows = df_today[df_today["DailyNo"] == target_daily_no]
            if not target_rows.empty:
                target_row = target_rows.iloc[0]
                st.session_state["editing_game_id"] = target_row["GameNo"]
                st.session_state["page"] = "edit"
                st.rerun()

    else:
        st.info("今日のデータはまだありません")

# --- 履歴画面 ---
def page_history():
    st.title("📊 過去データ参照")
    if st.button("🏠 ホームに戻る"):
        st.session_state["page"] = "home"
        st.rerun()
        
    df = load_score_data()
    if df.empty:
        st.info("データがありません")
        return

    # --- 期間別統計 (集計) ---
    st.markdown("### 📈 期間別統計 (集計)")
    
    if "論理日付" in df.columns:
        min_date = df["論理日付"].min()
        max_date = df["論理日付"].max()
    else:
        min_date = date.today()
        max_date = date.today()

    c1, c2 = st.columns([2, 1])
    with c1:
        stats_range = st.date_input("集計期間", value=(min_date, max_date))
    with c2:
        stats_time_range = st.selectbox("時間帯", ["全日", "9:00-21:00", "21:00-33:00(翌9:00)"], key="stats_time")
    
    # フィルタリング
    df_target = df.copy()
    
    if isinstance(stats_range, tuple) and len(stats_range) == 2:
        start, end = stats_range
        df_target = df_target[(df_target["論理日付"] >= start) & (df_target["論理日付"] <= end)]
    elif isinstance(stats_range, tuple) and len(stats_range) == 1:
        start = stats_range[0]
        end = start 
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
        
        # --- ★追加: 席別集計 (全体) ---
        seat_counts = {s: {"1":0, "2":0, "3":0, "sum":0, "count":0} for s in ["A", "B", "C"]}
        
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
            except:
                pass
                
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
            
            # --- タイプ別・席別データ収集 ---
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
        c2.metric("平均ゲーム数/日", f"{avg_games_day:.1f} 回")
        c3.metric("総バック (A)", f"{total_back_a} 枚", f"平均 {avg_back_a:.1f} 枚/日")
        c4.metric("総バック (B)", f"{total_back_b} 枚", f"平均 {avg_back_b:.1f} 枚/日")

        # --- 利益データの表示 ---
        df_profit = load_profit_data()
        if not df_profit.empty:
            df_profit["MixDiff"] = pd.to_numeric(df_profit["MixDiff"], errors='coerce').fillna(0)
            df_profit["RealProfit"] = pd.to_numeric(df_profit["RealProfit"], errors='coerce').fillna(0)
            df_profit["DateObj"] = pd.to_datetime(df_profit["Date"]).dt.date

            # 日付フィルタ
            df_p_target = df_profit.copy()
            if isinstance(stats_range, tuple) and len(stats_range) == 2:
                df_p_target = df_p_target[(df_p_target["DateObj"] >= start) & (df_p_target["DateObj"] <= end)]
            elif isinstance(stats_range, tuple) and len(stats_range) == 1:
                df_p_target = df_p_target[df_p_target["DateObj"] == start]
            
            # 時間帯フィルタ
            if stats_time_range == "9:00-21:00":
                df_p_target = df_p_target[df_p_target["TimeSlot"] == "Day"]
            elif stats_time_range == "21:00-33:00(翌9:00)":
                df_p_target = df_p_target[df_p_target["TimeSlot"] == "Night"]
                
            sum_mix = int(df_p_target["MixDiff"].sum())
            sum_real = int(df_p_target["RealProfit"].sum())
            
            st.markdown("##### 💰 利益集計")
            cp1, cp2 = st.columns(2)
            cp1.metric("MIX差 (合計)", f"{sum_mix:,}")
            cp2.metric("実利益 (合計)", f"{sum_real:,}")

        st.caption(f"卓組構成の割合 ({start} 〜 {end})")
        df_pattern = pd.DataFrame({
            "構成": list(pattern_counts.keys()),
            "回数": list(pattern_counts.values())
        })
        total_p = df_pattern["回数"].sum()
        if total_p > 0:
            df_pattern["割合"] = (df_pattern["回数"] / total_p * 100).map('{:.1f}%'.format)
        else:
            df_pattern["割合"] = "0.0%"
        
        win_rates = []
        for k in df_pattern["構成"]:
            cnt = pattern_counts[k]
            wins_a = pattern_wins_a[k]
            wins_b = cnt - wins_a
            if k in ["A2人B1人", "A1人B2人"] and cnt > 0:
                rate_a = (wins_a / cnt) * 100
                rate_b = (wins_b / cnt) * 100
                win_rates.append(f"A: {rate_a:.0f}% / B: {rate_b:.0f}%")
            else:
                win_rates.append("-")
        
        df_pattern["勝率データ"] = win_rates
        st.dataframe(df_pattern, hide_index=True, use_container_width=True)

        # --- タイプ別成績 ---
        if type_data:
            st.markdown("##### 📊 タイプ別成績")
            df_type_raw = pd.DataFrame(type_data)
            stats_by_type = df_type_raw.groupby("Type")["Rank"].agg(
                games="count",
                avg="mean",
                r1=lambda x: (x==1).sum(),
                r2=lambda x: (x==2).sum(),
                r3=lambda x: (x==3).sum()
            ).reset_index()

            stats_by_type["avg"] = stats_by_type["avg"].map('{:.2f}'.format)
            stats_by_type["r1_rate"] = (stats_by_type["r1"] / stats_by_type["games"] * 100).map('{:.1f}%'.format)
            stats_by_type["r2_rate"] = (stats_by_type["r2"] / stats_by_type["games"] * 100).map('{:.1f}%'.format)
            stats_by_type["r3_rate"] = (stats_by_type["r3"] / stats_by_type["games"] * 100).map('{:.1f}%'.format)

            display_cols = {
                "Type": "タイプ", "games": "打数", "avg": "平均着順",
                "r1_rate": "トップ率", "r2_rate": "2着率", "r3_rate": "ラス率"
            }
            type_order = {"A客": 0, "B客": 1, "AS": 2, "BS": 3}
            stats_by_type["order"] = stats_by_type["Type"].map(lambda x: type_order.get(x, 99))
            stats_by_type = stats_by_type.sort_values("order").drop("order", axis=1)

            st.dataframe(stats_by_type.rename(columns=display_cols)[["タイプ", "打数", "平均着順", "トップ率", "2着率", "ラス率"]],
                         hide_index=True, use_container_width=True)
        
        # --- ★追加: 席別成績テーブル ---
        seat_rows = []
        for s in ["A", "B", "C"]:
            d = seat_counts[s]
            c = d["count"]
            if c > 0:
                avg = d["sum"] / c
                r1_r = d["1"]/c*100
                r2_r = d["2"]/c*100
                r3_r = d["3"]/c*100
                seat_rows.append({
                    "席": f"{s}席",
                    "打数": c,
                    "平均着順": f"{avg:.2f}",
                    "1着": f"{d['1']} ({r1_r:.1f}%)",
                    "2着": f"{d['2']} ({r2_r:.1f}%)",
                    "3着": f"{d['3']} ({r3_r:.1f}%)"
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

    st.markdown("### 🔍 日付・人物ごとの詳細")
    with st.form("history_search_form"):
        c1, c2, c3 = st.columns(3)
        with c1: 
            sel_date = st.selectbox("📅 日付を選択", ["(指定なし)"] + list(unique_dates))
        with c2:
            sel_time = st.selectbox("⏰ 時間帯", ["全日", "9:00-21:00", "21:00-33:00(翌9:00)"], key="search_time")
        with c3: 
            sel_player = st.selectbox("👤 プレイヤーを選択", ["(指定なし)"] + list(all_players))
        submitted = st.form_submit_button("🔍 絞り込み表示")
    
    st.divider()

    if submitted:
        if sel_date == "(指定なし)" and sel_player == "(指定なし)":
            st.warning("⚠️ 日付またはプレイヤーを選択して「絞り込み表示」ボタンを押してください")
            return

        df_filtered = df.copy()
        
        if sel_date != "(指定なし)":
            df_filtered = df_filtered[df_filtered["論理日付"] == sel_date]
        if sel_player != "(指定なし)":
            df_filtered = df_filtered[
                (df_filtered["Aさん"] == sel_player) | 
                (df_filtered["Bさん"] == sel_player) | 
                (df_filtered["Cさん"] == sel_player)
            ]
        
        if sel_time == "9:00-21:00":
            df_filtered = df_filtered[df_filtered["日時Obj"].dt.hour.between(9, 20)]
        elif sel_time == "21:00-33:00(翌9:00)":
            df_filtered = df_filtered[~df_filtered["日時Obj"].dt.hour.between(9, 20)]

        if df_filtered.empty:
            st.warning("条件に一致するデータが見つかりませんでした")
        else:
            if not df_filtered.empty:
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
                    except:
                        pass

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
                
                st.caption("卓組構成の割合")
                df_pattern = pd.DataFrame({
                    "構成": list(pattern_counts.keys()),
                    "回数": list(pattern_counts.values())
                })
                total = df_pattern["回数"].sum()
                if total > 0:
                    df_pattern["割合"] = (df_pattern["回数"] / total * 100).map('{:.1f}%'.format)
                else:
                    df_pattern["割合"] = "0.0%"

                win_rates = []
                for k in df_pattern["構成"]:
                    cnt = pattern_counts[k]
                    wins_a = pattern_wins_a[k]
                    wins_b = cnt - wins_a
                    if k in ["A2人B1人", "A1人B2人"] and cnt > 0:
                        rate_a = (wins_a / cnt) * 100
                        rate_b = (wins_b / cnt) * 100
                        win_rates.append(f"A: {rate_a:.0f}% / B: {rate_b:.0f}%")
                    else:
                        win_rates.append("-")
                
                df_pattern["勝率データ"] = win_rates
                st.dataframe(df_pattern, hide_index=True, use_container_width=True)
                st.divider()

            if sel_player != "(指定なし)":
                st.markdown(f"#### 👤 {sel_player} さんの成績")
                ranks = []
                played_dates = set()
                compatibility = {}
                
                # ★追加: 個人用席別集計
                player_seat_ranks = {"A": [], "B": [], "C": []}

                for _, row in df_filtered.iterrows():
                    my_rank = None
                    my_seat = None
                    seats = ["A", "B", "C"]
                    
                    for s in seats:
                        if row[f"{s}さん"] == sel_player:
                            try:
                                my_rank = int(float(row[f"{s}着順"]))
                                my_seat = s
                            except: pass
                            break
                    
                    if my_rank:
                        ranks.append(my_rank)
                        played_dates.add(row["論理日付"])
                        
                        # ★追加: 席別リストに追加
                        if my_seat in player_seat_ranks:
                            player_seat_ranks[my_seat].append(my_rank)
                        
                        for s in seats:
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
                            score = opp_rank - my_rank
                            compatibility[opp_name]["score"] += score

                if ranks:
                    games = len(ranks)
                    avg = sum(ranks)/games
                    c1 = ranks.count(1)
                    c2_cnt = ranks.count(2)
                    c3 = ranks.count(3)
                    r1_rate = (c1 / games) * 100
                    r2_rate = (c2_cnt / games) * 100
                    r3_rate = (c3 / games) * 100
                    
                    stats_html = f"""
                    <table class="stats-table"><thead><tr><th>総回数</th><th>平均着順</th><th>1着回数</th><th>2着回数</th><th>3着回数</th></tr></thead>
                    <tbody><tr><td>{games} 回</td><td>{avg:.2f}</td><td>{c1} 回<span class="stats-sub">({r1_rate:.1f}%)</span></td><td>{c2_cnt} 回<span class="stats-sub">({r2_rate:.1f}%)</span></td><td>{c3} 回<span class="stats-sub">({r3_rate:.1f}%)</span></td></tr></tbody></table>
                    """
                    st.markdown(stats_html, unsafe_allow_html=True)
                    st.divider()
                    
                    # --- ★追加: 個人席別成績表示 ---
                    p_seat_rows = []
                    for s in ["A", "B", "C"]:
                        rs = player_seat_ranks[s]
                        c = len(rs)
                        if c > 0:
                            r1 = rs.count(1)
                            r2 = rs.count(2)
                            r3 = rs.count(3)
                            avg = sum(rs)/c
                            p_seat_rows.append({
                                "席": f"{s}席",
                                "打数": c,
                                "平均着順": f"{avg:.2f}",
                                "1着": f"{r1} ({r1/c*100:.1f}%)",
                                "2着": f"{r2} ({r2/c*100:.1f}%)",
                                "3着": f"{r3} ({r3/c*100:.1f}%)"
                            })
                    if p_seat_rows:
                        st.markdown("##### 🪑 席別成績")
                        st.dataframe(pd.DataFrame(p_seat_rows), hide_index=True, use_container_width=True)
                    
                    st.divider()
                    
                    c_graph, c_dates = st.columns([2, 1])
                    with c_graph:
                        st.markdown("##### 📈 直近50戦の着順推移")
                        recent_ranks = ranks[-50:]
                        df_trend = pd.DataFrame({
                            "戦数": range(1, len(recent_ranks) + 1),
                            "着順": recent_ranks
                        })
                        line_chart = alt.Chart(df_trend).mark_line(point=True).encode(
                            x=alt.X("戦数", axis=alt.Axis(tickMinStep=1), title="直近ゲーム"),
                            y=alt.Y("着順", scale=alt.Scale(domain=[3, 1]), title="着順"),
                            tooltip=["戦数", "着順"]
                        ).properties(height=300)
                        st.altair_chart(line_chart, use_container_width=True)

                    with c_dates:
                        st.markdown("##### 📅 稼働日リスト")
                        date_list = sorted(list(played_dates), reverse=True)
                        st.dataframe(pd.DataFrame(date_list, columns=["日付"]), hide_index=True, use_container_width=True)
                
                if compatibility:
                    st.divider()
                    st.subheader("🤝 対戦相手データ (TOP3)")
                    comp_data = []
                    for name, data in compatibility.items():
                        comp_data.append({"名前": name, "同卓回数": data["count"], "相性スコア": data["score"]})
                    
                    df_comp = pd.DataFrame(comp_data)
                    c_freq, c_good, c_bad = st.columns(3)
                    with c_freq:
                        st.markdown("**👬 同卓回数が多い**")
                        df_freq = df_comp.sort_values("同卓回数", ascending=False).head(3).reset_index(drop=True)
                        st.dataframe(df_freq[["名前", "同卓回数"]], hide_index=True, use_container_width=True)
                    with c_good:
                        st.markdown("**💖 相性が良い (カモ)**")
                        df_good = df_comp.sort_values("相性スコア", ascending=False).head(3).reset_index(drop=True)
                        st.dataframe(df_good[["名前", "相性スコア"]], hide_index=True, use_container_width=True)
                    with c_bad:
                        st.markdown("**💀 相性が悪い (天敵)**")
                        df_bad = df_comp.sort_values("相性スコア", ascending=True).head(3).reset_index(drop=True)
                        st.dataframe(df_bad[["名前", "相性スコア"]], hide_index=True, use_container_width=True)

                st.divider()
                st.markdown("#### 🀄 個人記録の更新")
                df_mem = load_member_data()
                
                current_max = 0
                current_yaku = 0
                target_idx = df_mem.index[df_mem["名前"] == sel_player].tolist()
                
                if target_idx:
                    idx = target_idx[0]
                    current_max = int(df_mem.at[idx, "最大飜数"])
                    current_yaku = int(df_mem.at[idx, "役満回数"])
                
                with st.form("update_personal_stats"):
                    c_in1, c_in2 = st.columns(2)
                    with c_in1:
                        new_max = st.number_input("最大飜数", min_value=0, value=current_max)
                    with c_in2:
                        new_yaku = st.number_input("役満回数", min_value=0, value=current_yaku)
                    
                    if st.form_submit_button("更新する"):
                        if target_idx:
                            df_mem.at[idx, "最大飜数"] = new_max
                            df_mem.at[idx, "役満回数"] = new_yaku
                            save_member_data(df_mem)
                            st.success(f"{sel_player}さんの記録を更新しました！")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("メンバー登録されていません。「メンバー管理」から登録してください。")

            else:
                st.markdown(f"#### 📝 集計表")
                render_paper_sheet(df_filtered)
    else:
        st.info("☝️ 上のボックスから条件を選択し、「絞り込み表示」ボタンを押してください")

# --- ランキング画面 ---
def page_ranking():
    st.title("🏆 ランキング (通算)")
    
    is_admin = (st.session_state.get("user_role") == "admin")
    if is_admin:
        if st.button("🏠 ホームに戻る"):
            st.session_state["page"] = "home"
            st.rerun()

    df = load_score_data()
    if df.empty:
        st.info("データがありません")
        return

    # 日付範囲フィルター
    valid_dates = pd.to_datetime(df["論理日付"]).dropna()
    if not valid_dates.empty:
        min_date = valid_dates.min().date()
        max_date = valid_dates.max().date()
    else:
        min_date = date.today()
        max_date = date.today()

    c1, c2 = st.columns(2)
    with c1:
        date_range = st.date_input(
            "📅 集計期間",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date
        )
    
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
    
    # 統計計算 (1日あたりの打数を追加)
    stats = df_raw.groupby("name").agg(
        games=("rank", "count"),
        avg_rank=("rank", "mean"),
        first_count=("rank", lambda x: (x==1).sum()),
        third_count=("rank", lambda x: (x==3).sum()),
        days=("date", "nunique") # ユニークな日付数
    ).reset_index()

    stats["games_per_day"] = stats["games"] / stats["days"]
    stats["top_rate"] = (stats["first_count"] / stats["games"]) * 100
    stats["last_avoid_rate"] = ((stats["games"] - stats["third_count"]) / stats["games"]) * 100
    
    # ゲスト/スタッフ分類
    stats["type"] = stats["name"].apply(lambda x: "staff" if str(x).lower().endswith("s") else "guest")
    stats_guest = stats[stats["type"] == "guest"]
    stats_staff = stats[stats["type"] == "staff"]
    
    min_games = st.slider("規定打数 (これ以下の人はランキングに表示しません)", 1, 50, 5)
    
    # フィルタリング
    stats_guest = stats_guest[stats_guest["games"] >= min_games]
    stats_staff = stats_staff[stats_staff["games"] >= min_games]
    
    if stats_guest.empty and stats_staff.empty:
        st.warning(f"打数が {min_games} 回以上のプレイヤーがいません。")
        return

    st.write("---")
    
    t1, t2, t3, t4, t5, t6 = st.tabs(["📊 打数", "🥇 平均着順", "👑 トップ率", "🛡 ラス回避率", "💥 最大飜数", "🀅 役満回数"])
    
    # 共通表示関数 (修正版)
    def show_ranking_split(df_g, df_s, sort_col, asc=False, format_func=None, val_col=None):
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("### 🧑‍🤝‍🧑 お客さん Top10")
            if not df_g.empty:
                res = df_g.sort_values(sort_col, ascending=asc).reset_index(drop=True).head(10)
                res["順位"] = res.index + 1
                if format_func and val_col and val_col != "games":
                    res[val_col] = res[val_col].map(format_func)
                
                # 表示カラムの調整
                cols = ["順位", "name"]
                if val_col == "games":
                    cols.extend(["games", "games_per_day"])
                    rename_map = {"name":"名前", "games":"打数", "games_per_day":"平均打数/日"}
                    res["games_per_day"] = res["games_per_day"].map('{:.1f}'.format)
                else:
                    cols.extend([val_col, "games"])
                    rename_map = {"name":"名前", "games":"打数"}
                    if val_col == "avg_rank": rename_map["avg_rank"] = "平均着順"
                    elif val_col == "top_rate": rename_map["top_rate"] = "トップ率"
                    elif val_col == "last_avoid_rate": rename_map["last_avoid_rate"] = "ラス回避率"
                
                st.dataframe(res[cols].rename(columns=rename_map), hide_index=True, use_container_width=True)
            else:
                st.info("データなし")

        with c2:
            st.markdown("### 👔 スタッフ Top10")
            if not df_s.empty:
                res = df_s.sort_values(sort_col, ascending=asc).reset_index(drop=True).head(10)
                res["順位"] = res.index + 1
                if format_func and val_col and val_col != "games":
                    res[val_col] = res[val_col].map(format_func)
                
                # 表示カラムの調整
                cols = ["順位", "name"]
                if val_col == "games":
                    cols.extend(["games", "games_per_day"])
                    rename_map = {"name":"名前", "games":"打数", "games_per_day":"平均打数/日"}
                    res["games_per_day"] = res["games_per_day"].map('{:.1f}'.format)
                else:
                    cols.extend([val_col, "games"])
                    rename_map = {"name":"名前", "games":"打数"}
                    if val_col == "avg_rank": rename_map["avg_rank"] = "平均着順"
                    elif val_col == "top_rate": rename_map["top_rate"] = "トップ率"
                    elif val_col == "last_avoid_rate": rename_map["last_avoid_rate"] = "ラス回避率"
                
                st.dataframe(res[cols].rename(columns=rename_map), hide_index=True, use_container_width=True)
            else:
                st.info("データなし")

    with t1:
        show_ranking_split(stats_guest, stats_staff, "games", False, None, "games")
    with t2:
        show_ranking_split(stats_guest, stats_staff, "avg_rank", True, '{:.2f}'.format, "avg_rank")
    with t3:
        show_ranking_split(stats_guest, stats_staff, "top_rate", False, '{:.1f}%'.format, "top_rate")
    with t4:
        show_ranking_split(stats_guest, stats_staff, "last_avoid_rate", False, '{:.1f}%'.format, "last_avoid_rate")

    # --- メンバーデータのランキング ---
    df_mem = load_member_data()
    df_mem["type"] = df_mem["名前"].apply(lambda x: "staff" if str(x).lower().endswith("s") else "guest")
    mem_g = df_mem[df_mem["type"] == "guest"]
    mem_s = df_mem[df_mem["type"] == "staff"]
    
    def show_mem_ranking(df_g, df_s, col, label):
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("### 🧑‍🤝‍🧑 お客さん Top10")
            if not df_g.empty:
                res = df_g.sort_values(col, ascending=False).reset_index(drop=True).head(10)
                res = res[res[col] > 0]
                if not res.empty:
                    res["順位"] = res.index + 1
                    st.dataframe(res[["順位", "名前", col]], hide_index=True, use_container_width=True)
                else: st.info("データなし")
            else: st.info("データなし")
        with c2:
            st.markdown("### 👔 スタッフ Top10")
            if not df_s.empty:
                res = df_s.sort_values(col, ascending=False).reset_index(drop=True).head(10)
                res = res[res[col] > 0]
                if not res.empty:
                    res["順位"] = res.index + 1
                    st.dataframe(res[["順位", "名前", col]], hide_index=True, use_container_width=True)
                else: st.info("データなし")
            else: st.info("データなし")

    with t5:
        show_mem_ranking(mem_g, mem_s, "最大飜数", "最大飜数")
    with t6:
        show_mem_ranking(mem_g, mem_s, "役満回数", "役満回数")

# --- ログ閲覧画面 ---
def page_logs():
    st.title("📜 修正・削除ログ")
    if st.button("🏠 ホームに戻る"):
        st.session_state["page"] = "home"
        st.rerun()
    
    df_logs = load_log_data()
    
    if not df_logs.empty and "操作" in df_logs.columns:
        target_actions = ["修正", "削除"]
        df_logs = df_logs[df_logs["操作"].isin(target_actions)]
    
    if not df_logs.empty and "GameNo" in df_logs.columns:
        df_logs = df_logs.rename(columns={"GameNo": "DailyNo"})

    if df_logs.empty:
        st.info("修正・削除の履歴はありません")
    else:
        st.dataframe(df_logs, use_container_width=True, hide_index=True)

# ==========================================
# 6. メインルーティング
# ==========================================
if "page" not in st.session_state:
    st.session_state["page"] = "home"

user_role = st.session_state.get("user_role")

if user_role == "guest":
    page_ranking()
else:
    if st.session_state["page"] == "home":
        page_home()
    elif st.session_state["page"] == "members":
        page_members()
    elif st.session_state["page"] == "input":
        page_input()
    elif st.session_state["page"] == "history":
        page_history()
    elif st.session_state["page"] == "edit":
        page_edit()
    elif st.session_state["page"] == "ranking":
        page_ranking()
    elif st.session_state["page"] == "logs":
        page_logs()
