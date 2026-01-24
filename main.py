import streamlit as st
import pandas as pd
import altair as alt
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
    
    /* --- スコアシート風スタイル --- */
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

    /* --- 個人成績表スタイル --- */
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
# 2. パスワード認証 (2026)
# ==========================================
def check_password():
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False
    if st.session_state["password_correct"]:
        return True
    
    st.title("🔒 ログイン")
    password = st.text_input("パスワードを入力してください", type="password")
    if st.button("ログイン"):
        if password == "2026":
            st.session_state["password_correct"] = True
            st.rerun()
        else:
            st.error("パスワードが違います")
    return False

if not check_password():
    st.stop()

# ==========================================
# 3. データ管理関数 (Google Sheets版)
# ==========================================
SHEET_SCORE = "score"
SHEET_MEMBER = "members"

def get_conn():
    return st.connection("gsheets", type=GSheetsConnection)

def load_score_data():
    conn = get_conn()
    try:
        df = conn.read(worksheet=SHEET_SCORE, ttl=0).fillna("")
    except:
        cols = ["GameNo", "TableNo", "SetNo", "日時", "備考", "Aさん", "Aタイプ", "A着順", "Bさん", "Bタイプ", "B着順", "Cさん", "Cタイプ", "C着順"]
        return pd.DataFrame(columns=cols)

    if "SetNo" not in df.columns and not df.empty:
        df["SetNo"] = (df["GameNo"] - 1) // 10 + 1
    elif "SetNo" not in df.columns:
        df["SetNo"] = []
    if "TableNo" not in df.columns:
        df["TableNo"] = 1 if not df.empty else []
    
    if not df.empty:
        df["日時Obj"] = pd.to_datetime(df["日時"])
        df["論理日付"] = (df["日時Obj"] - timedelta(hours=9)).dt.date
        df = df.sort_values(["論理日付", "TableNo", "日時Obj"])
        df["DailyNo"] = df.groupby(["論理日付", "TableNo"]).cumcount() + 1
    else:
        df["DailyNo"] = []
        
    return df

def save_score_data(df):
    conn = get_conn()
    save_cols = ["GameNo", "TableNo", "SetNo", "日時", "備考", "Aさん", "Aタイプ", "A着順", "Bさん", "Bタイプ", "B着順", "Cさん", "Cタイプ", "C着順"]
    existing_cols = [c for c in save_cols if c in df.columns]
    df_to_save = df[existing_cols]
    conn.update(worksheet=SHEET_SCORE, data=df_to_save)

def load_member_data():
    conn = get_conn()
    try:
        df = conn.read(worksheet=SHEET_MEMBER, ttl=0).fillna("")
        if df.empty:
             return pd.DataFrame({"名前": ["内山", "野田", "豊村"], "登録日": [date.today()]*3})
        return df
    except:
        return pd.DataFrame({"名前": ["内山", "野田", "豊村"], "登録日": [date.today()]*3})

def save_member_data(df):
    conn = get_conn()
    conn.update(worksheet=SHEET_MEMBER, data=df)

def get_all_member_names():
    df_mem = load_member_data()
    registered = df_mem["名前"].tolist() if not df_mem.empty else []
    df_score = load_score_data()
    history = []
    if not df_score.empty:
        history = pd.concat([df_score["Aさん"], df_score["Bさん"], df_score["Cさん"]]).unique().tolist()
    all_names = sorted(list(set(registered + [x for x in history if x != ""])))
    return all_names

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
        if row["A着順"] == 1: w_type = row["Aタイプ"]
        elif row["B着順"] == 1: w_type = row["Bタイプ"]
        elif row["C着順"] == 1: w_type = row["Cタイプ"]
        
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
        
        SPECIAL_NOTES = ["東１終了", "２人飛ばし", "５連勝〜"]
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
                if p_name == last_names[p_char]:
                    display_text = ""
                else:
                    display_text = p_name
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

# --- 共通パーツ: プレイヤー入力行 ---
def player_input_row(label, member_list, def_n, def_t, def_r):
    st.markdown(f"**▼ {label}**")
    TYPE_OPTS = ["A客", "B客", "AS", "BS"]
    def idx(opts, val): return opts.index(val) if val in opts else 0
    def get_idx_in_list(lst, val): return lst.index(val) if val in lst else None
    
    c1, c2 = st.columns([1, 2])
    with c1:
        idx_val = get_idx_in_list(member_list, def_n) if def_n else None
        name = st.selectbox("名前", member_list, index=idx_val, key=f"n_{label}")
    with c2:
        rank = st.radio("着順", [1, 2, 3], index=idx([1, 2, 3], def_r), horizontal=True, key=f"r_{label}")
        type_ = st.radio("タイプ", TYPE_OPTS, index=idx(TYPE_OPTS, def_t), horizontal=True, key=f"t_{label}")
    st.markdown("---")
    return name, type_, rank

# --- ホーム画面 ---
def page_home():
    st.title("🀄 ぱいん成績管理")
    st.write("")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("📝 成績をつける", type="primary", use_container_width=True):
            st.session_state["page"] = "input"
            st.rerun()
    with col2:
        if st.button("📊 データを見る", use_container_width=True):
            st.session_state["page"] = "history"
            st.rerun()
    with col3:
        if st.button("👥 メンバー管理", use_container_width=True):
            st.session_state["page"] = "members"
            st.rerun()

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
                new_row = {"名前": new_name, "登録日": date.today()}
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

# --- 編集専用画面 (NEW) ---
def page_edit():
    st.title("🔧 データの修正・削除")
    
    # セッションから編集対象IDを取得
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
        # 名前、タイプ、着順の入力欄
        p1_n, p1_t, p1_r = player_input_row("A席", member_list, row["Aさん"], row["Aタイプ"], int(float(row["A着順"])))
        p2_n, p2_t, p2_r = player_input_row("B席", member_list, row["Bさん"], row["Bタイプ"], int(float(row["B着順"])))
        p3_n, p3_t, p3_r = player_input_row("C席", member_list, row["Cさん"], row["Cタイプ"], int(float(row["C着順"])))

        # 備考
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
            if not p1_n or not p2_n or not p3_n:
                st.error("名前を選択してください")
            elif sorted([p1_r, p2_r, p3_r]) != [1, 2, 3]:
                st.error("着順が重複しています")
            else:
                # データを更新
                new_data = {
                    "GameNo": row["GameNo"], "TableNo": row["TableNo"], "SetNo": row["SetNo"],
                    "日時": row["日時"], "備考": ("" if note == "なし" else note),
                    "Aさん": p1_n, "Aタイプ": p1_t, "A着順": p1_r,
                    "Bさん": p2_n, "Bタイプ": p2_t, "B着順": p2_r,
                    "Cさん": p3_n, "Cタイプ": p3_t, "C着順": p3_r
                }
                # DataFrameの該当行を上書き
                idx = df[df["GameNo"] == edit_id].index[0]
                df.loc[idx, list(new_data.keys())] = list(new_data.values())
                
                save_score_data(df)
                st.session_state["success_msg"] = "✅ 修正しました！"
                st.session_state["page"] = "input"
                st.session_state["editing_game_id"] = None
                st.rerun()
        
        if submit_delete:
            df = df[df["GameNo"] != edit_id]
            save_score_data(df)
            st.session_state["success_msg"] = "🗑 削除しました"
            st.session_state["page"] = "input"
            st.session_state["editing_game_id"] = None
            st.rerun()

# --- 入力画面 ---
def page_input():
    st.title("📝 成績入力")
    if "success_msg" in st.session_state and st.session_state.get("success_msg"):
        st.success(st.session_state["success_msg"])
        st.session_state["success_msg"] = None 
    if st.button("🏠 ホームに戻る"):
        st.session_state["page"] = "home"
        st.rerun()

    df = load_score_data()
    member_list = get_all_member_names()
    JST = timezone(timedelta(hours=9), 'JST')
    
    # --- 卓と日付の選択 ---
    c_top1, c_top2 = st.columns(2)
    with c_top1:
        current_table = st.selectbox("入力する卓を選択してください", [1, 2, 3], index=0)
    with c_top2:
        current_dt = datetime.now(JST)
        default_date_obj = (current_dt - timedelta(hours=9)).date()
        input_date = st.date_input("日付 (朝9時切替)", value=default_date_obj)

    # --- 今日のデータの抽出 ---
    df_table = df[df["TableNo"] == current_table]
    if not df_table.empty:
        df_today = df_table[df_table["論理日付"] == input_date]
    else:
        df_today = pd.DataFrame()

    # --- 本日の履歴リスト (クリックで編集へ遷移) ---
    if not df_today.empty:
        st.markdown("### 📋 本日の履歴")
        st.caption("👇 修正したい行をクリックすると、編集画面に移動します")
        
        # 表示用のデータ作成
        df_display = df_today.sort_values("DailyNo", ascending=False)[["DailyNo", "SetNo", "日時", "Aさん", "Bさん", "Cさん"]].copy()
        df_display["日時"] = pd.to_datetime(df_display["日時"]).dt.strftime('%H:%M')
        
        # クリック可能なテーブル
        event = st.dataframe(
            df_display, 
            use_container_width=True, 
            hide_index=True,
            on_select="rerun",
            selection_mode="single-row"
        )
        
        # 選択されたら編集ページへ遷移
        if len(event.selection.rows) > 0:
            selected_idx = event.selection.rows[0]
            target_daily_no = df_display.iloc[selected_idx]["DailyNo"]
            target_row = df_today[df_today["DailyNo"] == target_daily_no].iloc[0]
            
            # ステートをセットしてリロード
            st.session_state["editing_game_id"] = target_row["GameNo"]
            st.session_state["page"] = "edit"
            st.rerun()

        # HTML成績表の表示 (リストのすぐ下に配置)
        render_paper_sheet(df_today)
        st.divider()

    else:
        st.info("今日のデータはまだありません")
        st.divider()

    # --- 新規入力フォーム ---
    st.subheader("🆕 新しい対局の入力")
    
    current_set_no = int(df_today["SetNo"].max()) if not df_today.empty else 1
    if not df_today.empty:
        next_display_no = int(df_today["DailyNo"].max()) + 1
    else:
        next_display_no = 1
    
    if not df.empty:
        next_internal_game_no = df["GameNo"].max() + 1
    else:
        next_internal_game_no = 1
    
    defaults = {
        "n1": None, "t1": "A客", "r1": 2,
        "n2": None, "t2": "B客", "r2": 1,
        "n3": None, "t3": "AS", "r3": 3,
        "note": "なし",
        "internal_game_no": next_internal_game_no,
        "display_game_no": next_display_no,
        "set_no": current_set_no,
        "table_no": current_table
    }

    with st.form("input_form"):
        st.write(f"**次の記録: No.{defaults['display_game_no']}**")
        st.caption(f"【{defaults['table_no']}卓】 第 {defaults['set_no']} セット")
        start_new_set = st.checkbox(f"🆕 ここから新しいセットにする ({defaults['table_no']}卓の第{defaults['set_no']+1}セットへ)")
        
        st.divider()

        # 入力行 (共通関数を使用)
        p1_n, p1_t, p1_r = player_input_row("A席", member_list, defaults["n1"], defaults["t1"], defaults["r1"])
        p2_n, p2_t, p2_r = player_input_row("B席", member_list, defaults["n2"], defaults["t2"], defaults["r2"])
        p3_n, p3_t, p3_r = player_input_row("C席", member_list, defaults["n3"], defaults["t3"], defaults["r3"])

        st.markdown("**▼ 備考**")
        NOTE_OPTS = ["なし", "東１終了", "２人飛ばし", "５連勝〜"]
        def idx(opts, val): return opts.index(val) if val in opts else 0
        note = st.radio("内容を選択", NOTE_OPTS, index=0, horizontal=True)
        
        st.divider()
        submitted = st.form_submit_button("📝 記録する", type="primary", use_container_width=True)

        if submitted:
            if not p1_n or not p2_n or not p3_n:
                st.error("⚠️ 名前が選択されていません！")
            elif sorted([p1_r, p2_r, p3_r]) != [1, 2, 3]:
                st.error("⚠️ 着順が重複しています！")
            else:
                save_date_str = input_date.strftime("%Y-%m-%d") + " " + datetime.now(JST).strftime("%H:%M")
                final_set_no = defaults['set_no']
                if start_new_set: final_set_no += 1
                
                new_row = {
                    "GameNo": defaults["internal_game_no"], "TableNo": defaults["table_no"], "SetNo": final_set_no,
                    "日時": save_date_str, "備考": ("" if note == "なし" else note),
                    "Aさん": p1_n, "Aタイプ": p1_t, "A着順": p1_r,
                    "Bさん": p2_n, "Bタイプ": p2_t, "B着順": p2_r,
                    "Cさん": p3_n, "Cタイプ": p3_t, "C着順": p3_r
                }
                
                # 新しいデータを後ろに追加
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                save_score_data(df)
                
                st.session_state["success_msg"] = f"✅ 記録しました！ (No.{defaults['display_game_no']})"
                st.rerun()

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

    unique_dates = sorted(df["論理日付"].unique(), reverse=True)
    all_players = get_all_member_names()

    st.markdown("### 🔍 日付と人物で絞り込み")
    
    with st.form("history_search_form"):
        c1, c2 = st.columns(2)
        with c1: sel_date = st.selectbox("📅 日付を選択", ["(指定なし)"] + list(unique_dates))
        with c2: sel_player = st.selectbox("👤 プレイヤーを選択", ["(指定なし)"] + list(all_players))
        
        submitted = st.form_submit_button("🔍 絞り込み表示")

    if submitted:
        is_filtered = False
        if sel_date != "(指定なし)":
            df = df[df["論理日付"] == sel_date]
            is_filtered = True
        if sel_player != "(指定なし)":
            df = df[(df["Aさん"] == sel_player) | (df["Bさん"] == sel_player) | (df["Cさん"] == sel_player)]
            is_filtered = True

        st.divider()

        if is_filtered and not df.empty:
            if sel_player != "(指定なし)":
                st.markdown(f"#### 👤 {sel_player} さんの成績")
                ranks = []
                played_dates = set()
                for _, row in df.iterrows():
                    rank = None
                    if row["Aさん"] == sel_player: rank = int(float(row["A着順"]))
                    elif row["Bさん"] == sel_player: rank = int(float(row["B着順"]))
                    elif row["Cさん"] == sel_player: rank = int(float(row["C着順"]))
                    if rank:
                        ranks.append(rank)
                        played_dates.add(row["論理日付"])
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
                    c_graph, c_dates = st.columns([2, 1])
                    with c_graph:
                        st.markdown("##### 📊 着順分布 (円グラフ)")
                        source = pd.DataFrame({
                            "着順": ["1着", "2着", "3着"],
                            "回数": [c1, c2_cnt, c3]
                        })
                        base = alt.Chart(source).encode(
                            theta=alt.Theta("回数", stack=True)
                        )
                        pie = base.mark_arc(outerRadius=100).encode(
                            color=alt.Color("着順"),
                            order=alt.Order("着順"),
                            tooltip=["着順", "回数"]
                        )
                        st.altair_chart(pie, use_container_width=True)

                    with c_dates:
                        st.markdown("##### 📅 稼働日リスト")
                        date_list = sorted(list(played_dates), reverse=True)
                        st.dataframe(pd.DataFrame(date_list, columns=["日付"]), hide_index=True, use_container_width=True)
            else:
                st.markdown(f"#### 📝 集計表")
                render_paper_sheet(df)
        elif is_filtered and df.empty:
            st.warning("条件に一致するデータが見つかりませんでした")
        else:
            st.info("☝️ 上のボックスから条件を選択し、「絞り込み表示」ボタンを押してください")
    else:
        st.info("☝️ 上のボックスから条件を選択し、「絞り込み表示」ボタンを押してください")

# ==========================================
# 6. メインルーティング
# ==========================================
if "page" not in st.session_state:
    st.session_state["page"] = "home"

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
