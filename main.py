import streamlit as st
import pandas as pd
import os
from datetime import datetime, date, timedelta

# ==========================================
# 1. ページ設定 & デザイン調整
# ==========================================
st.set_page_config(page_title="ぱいん成績管理", layout="wide")

hide_style = """
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* スコアシート風のスタイル定義 */
    .score-sheet {
        border-collapse: collapse;
        width: 100%;
        max_width: 800px;
        margin-bottom: 20px;
        font-family: "Hiragino Kaku Gothic ProN", Meiryo, sans-serif;
        color: #000;
        background-color: #fff;
    }
    .score-sheet th, .score-sheet td {
        border: 1px solid #333;
        padding: 4px 8px;
        text-align: center;
        font-size: 14px;
    }
    .score-sheet th {
        background-color: #f0f0f0;
        font-weight: bold;
    }
    .score-sheet .set-header {
        background-color: #d9edf7;
        text-align: left;
        padding-left: 10px;
        font-weight: bold;
    }
    .score-sheet .rank-circle {
        display: inline-block;
        width: 20px;
        height: 20px;
        line-height: 20px;
        border-radius: 50%;
        border: 1px solid #333;
        margin-left: 5px;
        font-size: 12px;
    }
    .score-sheet .rank-1 { background-color: #fff; color: #000; font-weight:bold; }
    .score-sheet .rank-special { background-color: #333; color: #fff; } /* ❶用 */
    
    .score-sheet .summary-row td {
        background-color: #fffbe6;
        font-weight: bold;
        border-top: 2px double #333;
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
# 3. データ管理関数
# ==========================================
SCORE_FILE = "sanma_score.csv"
MEMBER_FILE = "members.csv"

def load_score_data():
    if os.path.exists(SCORE_FILE):
        df = pd.read_csv(SCORE_FILE).fillna("")
        if "SetNo" not in df.columns and not df.empty:
            df["SetNo"] = (df["GameNo"] - 1) // 10 + 1
        elif "SetNo" not in df.columns:
            df["SetNo"] = []
        if "TableNo" not in df.columns:
            df["TableNo"] = 1 if not df.empty else []
        return df
    else:
        cols = ["GameNo", "TableNo", "SetNo", "日時", "備考", "Aさん", "Aタイプ", "A着順", "Bさん", "Bタイプ", "B着順", "Cさん", "Cタイプ", "C着順"]
        return pd.DataFrame(columns=cols)

def save_score_data(df):
    df.to_csv(SCORE_FILE, index=False)

def load_member_data():
    if os.path.exists(MEMBER_FILE):
        return pd.read_csv(MEMBER_FILE)
    else:
        return pd.DataFrame({"名前": ["内山", "野田", "豊村"], "登録日": [date.today()]*3})

def save_member_data(df):
    df.to_csv(MEMBER_FILE, index=False)

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

# --- 集計関数 (1セット分) ---
def calculate_set_summary(subset_df):
    target_types = ["A客", "B客", "AS", "BS"]
    type_stats = {t: 0 for t in target_types}
    FEE_MAP = {"A客": 3, "B客": 5, "AS": 1, "BS": 1}
    total_fee = 0
    
    for _, row in subset_df.iterrows():
        # 1着のタイプを集計
        w_type = None
        if row["A着順"] == 1: w_type = row["Aタイプ"]
        elif row["B着順"] == 1: w_type = row["Bタイプ"]
        elif row["C着順"] == 1: w_type = row["Cタイプ"]
        
        if w_type in target_types:
            type_stats[w_type] += 1
            if w_type in FEE_MAP: total_fee += FEE_MAP[w_type]
        
        # 備考による割引
        note = str(row["備考"])
        if note == "東１終了": total_fee -= 1
        elif note == "２人飛ばし": total_fee -= 2
        elif note == "５連勝〜": total_fee -= 5

    return total_fee, type_stats

# --- 紙の集計表風 HTMLレンダリング (修正版) ---
def render_paper_sheet(df):
    if df.empty:
        st.info("データがありません")
        return

    unique_sets = sorted(df["SetNo"].unique())

    for set_no in unique_sets:
        subset = df[df["SetNo"] == set_no].sort_values("GameNo")
        if subset.empty: continue
        
        fee, stats = calculate_set_summary(subset)
        
        # HTMLのインデントを削除して構築
        html = f"""
<table class="score-sheet">
    <thead>
        <tr class="set-header">
            <td colspan="5">📄 第 {int(set_no)} セット</td>
        </tr>
        <tr>
            <th style="width:5%">No</th>
            <th style="width:20%">備考</th>
            <th style="width:25%">A席</th>
            <th style="width:25%">B席</th>
            <th style="width:25%">C席</th>
        </tr>
    </thead>
    <tbody>
"""
        
        SPECIAL_NOTES = ["東１終了", "２人飛ばし", "５連勝〜"]
        
        for _, row in subset.iterrows():
            ranks_html = []
            for p_char in ["A", "B", "C"]:
                try:
                    rank_val = str(int(float(row[f"{p_char}着順"])))
                except:
                    rank_val = "0"

                is_special = (row["備考"] in SPECIAL_NOTES) and (rank_val == "1")
                
                if is_special:
                    rank_display = f'<span class="rank-circle rank-special">❶</span>'
                else:
                    char_map = {"1":"①", "2":"②", "3":"③"}
                    display_char = char_map.get(rank_val, rank_val)
                    rank_display = f'<span style="font-weight:bold; margin-left:4px;">{display_char}</span>'
                
                name = row[f"{p_char}さん"]
                ranks_html.append(f"{name} {rank_display}")

            note = row["備考"] if row["備考"] else ""
            
            html += f"""
        <tr>
            <td>{row['GameNo']}</td>
            <td style="color:red; font-size:12px;">{note}</td>
            <td>{ranks_html[0]}</td>
            <td>{ranks_html[1]}</td>
            <td>{ranks_html[2]}</td>
        </tr>
"""
            
        html += f"""
        <tr class="summary-row">
            <td colspan="2" style="text-align:right;">合計</td>
            <td>ゲーム代: <span style="font-size:16px; color:#d9534f;">{fee}</span> 枚</td>
            <td colspan="2" style="font-size:12px; text-align:left;">
                A客:{stats['A客']}回 / B客:{stats['B客']}回 / AS:{stats['AS']}回 / BS:{stats['BS']}回
            </td>
        </tr>
    </tbody>
</table>
"""
        st.markdown(html, unsafe_allow_html=True)

# ==========================================
# 5. 各ページ画面
# ==========================================

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

# --- 入力画面 ---
def page_input():
    st.title("📝 成績入力")
    
    if "success_msg" in st.session_state and st.session_state["success_msg"]:
        st.success(st.session_state["success_msg"])
        st.session_state["success_msg"] = None 
    
    if st.button("🏠 ホームに戻る"):
        st.session_state["page"] = "home"
        st.rerun()

    df = load_score_data()
    member_list = get_all_member_names()
    
    c_top1, c_top2 = st.columns(2)
    with c_top1:
        current_table = st.selectbox("入力する卓を選択してください", [1, 2, 3], index=0)
    with c_top2:
        current_dt = datetime.now()
        default_date_obj = (current_dt - timedelta(hours=9)).date()
        input_date = st.date_input("日付 (朝9時切替)", value=default_date_obj)

    # セット番号計算
    df_table = df[df["TableNo"] == current_table]
    if not df_table.empty:
        df_table["日時Obj"] = pd.to_datetime(df_table["日時"])
        df_table["論理日付"] = (df_table["日時Obj"] - timedelta(hours=9)).dt.date
        df_today = df_table[df_table["論理日付"] == input_date]
    else:
        df_today = pd.DataFrame()

    if not df_today.empty:
        current_set_no = int(df_today["SetNo"].max())
    else:
        current_set_no = 1

    is_edit_mode = st.checkbox("🔧 過去の記録を修正・削除する")
    
    defaults = {
        "n1": None, "t1": "A客", "r1": 2,
        "n2": None, "t2": "B客", "r2": 1,
        "n3": None, "t3": "AS", "r3": 3,
        "note": "なし",
        "game_no": df["GameNo"].max() + 1 if not df.empty else 1,
        "set_no": current_set_no,
        "table_no": current_table
    }
    
    selected_game_id = None
    if is_edit_mode:
        if not df.empty:
            ids = df["GameNo"].sort_values(ascending=False).tolist()
            selected_game_id = st.selectbox("修正するゲームNo", ids)
            row = df[df["GameNo"] == selected_game_id].iloc[0]
            
            defaults.update({
                "n1": row["Aさん"], "t1": row["Aタイプ"], "r1": int(float(row["A着順"])),
                "n2": row["Bさん"], "t2": row["Bタイプ"], "r2": int(float(row["B着順"])),
                "n3": row["Cさん"], "t3": row["Cタイプ"], "r3": int(float(row["C着順"])),
                "note": row["備考"] if row["備考"] else "なし",
                "game_no": selected_game_id, 
                "set_no": int(row["SetNo"]), "table_no": int(row["TableNo"])
            })
            if current_table != defaults["table_no"]:
                st.info(f"※ 選択中のゲームは「{defaults['table_no']}卓」のデータです")
        else:
            st.warning("データがありません")
            return

    with st.form("input_form"):
        st.write(f"**Game No: {defaults['game_no']}**")
        if not is_edit_mode:
            st.caption(f"【{defaults['table_no']}卓】 第 {defaults['set_no']} セット")
            start_new_set = st.checkbox(f"🆕 ここから新しいセットにする ({defaults['table_no']}卓の第{defaults['set_no']+1}セットへ)")

        st.divider()

        TYPE_OPTS = ["A客", "B客", "AS", "BS"]
        def idx(opts, val): return opts.index(val) if val in opts else 0
        def get_idx_in_list(lst, val): return lst.index(val) if val in lst else None
        
        def player_input_row(label, placeholder_text, def_n, def_t, def_r):
            st.markdown(f"**▼ {label}**")
            c1, c2 = st.columns([1, 2])
            with c1:
                idx_val = get_idx_in_list(member_list, def_n) if def_n else None
                name = st.selectbox("名前", member_list, index=idx_val, placeholder=placeholder_text, key=f"n_{label}")
            with c2:
                rank = st.radio("着順", [1, 2, 3], index=idx([1, 2, 3], def_r), horizontal=True, key=f"r_{label}")
                type_ = st.radio("タイプ", TYPE_OPTS, index=idx(TYPE_OPTS, def_t), horizontal=True, key=f"t_{label}")
            st.markdown("---")
            return name, type_, rank

        p1_n, p1_t, p1_r = player_input_row("A席", "name1", defaults["n1"], defaults["t1"], defaults["r1"])
        p2_n, p2_t, p2_r = player_input_row("B席", "name2", defaults["n2"], defaults["t2"], defaults["r2"])
        p3_n, p3_t, p3_r = player_input_row("C席", "name3", defaults["n3"], defaults["t3"], defaults["r3"])

        st.markdown("**▼ 備考**")
        NOTE_OPTS = ["なし", "東１終了", "２人飛ばし", "５連勝〜"]
        cur_note = defaults["note"]
        opts = NOTE_OPTS if cur_note in NOTE_OPTS else NOTE_OPTS + [cur_note]
        note = st.radio("内容を選択", opts, index=idx(opts, cur_note), horizontal=True)
        
        st.divider()

        if not is_edit_mode:
            submitted = st.form_submit_button("📝 記録する", type="primary", use_container_width=True)
        else:
            c_btn1, c_btn2 = st.columns(2)
            with c_btn1: submitted = st.form_submit_button("🔄 更新する", type="primary", use_container_width=True)
            with c_btn2: submitted = False; delete = st.form_submit_button("🗑 削除する", type="secondary", use_container_width=True)

        if submitted:
            if not p1_n or not p2_n or not p3_n:
                st.error("⚠️ 名前が選択されていません！")
            elif sorted([p1_r, p2_r, p3_r]) != [1, 2, 3]:
                st.error("⚠️ 着順が重複しています！")
            else:
                save_date_str = input_date.strftime("%Y-%m-%d") + " " + datetime.now().strftime("%H:%M")
                final_set_no = defaults['set_no']
                if not is_edit_mode and start_new_set:
                    final_set_no += 1
                
                new_row = {
                    "GameNo": defaults["game_no"], 
                    "TableNo": defaults["table_no"],
                    "SetNo": final_set_no,
                    "日時": save_date_str, "備考": ("" if note == "なし" else note),
                    "Aさん": p1_n, "Aタイプ": p1_t, "A着順": p1_r,
                    "Bさん": p2_n, "Bタイプ": p2_t, "B着順": p2_r,
                    "Cさん": p3_n, "Cタイプ": p3_t, "C着順": p3_r
                }
                
                if not is_edit_mode:
                    df = pd.concat([pd.DataFrame([new_row]), df], ignore_index=True)
                    st.session_state["success_msg"] = f"✅ {defaults['table_no']}卓に記録しました！"
                else:
                    idx_list = df[df["GameNo"] == selected_game_id].index
                    if len(idx_list) > 0: df.loc[idx_list[0]] = new_row
                    st.session_state["success_msg"] = "✅ 更新しました！"
                
                save_score_data(df)
                st.rerun()
        
        if is_edit_mode and 'delete' in locals() and delete and selected_game_id:
            df = df[df["GameNo"] != selected_game_id]
            save_score_data(df)
            st.session_state["success_msg"] = "🗑 削除しました"
            st.rerun()

    # --- 履歴表示（当日・対象卓のみ・紙風） ---
    if not df.empty and not df_today.empty:
        st.markdown(f"### 📋 {input_date.strftime('%Y/%m/%d')} の集計表 ({current_table}卓)")
        render_paper_sheet(df_today)
    elif not df.empty:
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

    df["日時Obj"] = pd.to_datetime(df["日時"])
    df["論理日付"] = (df["日時Obj"] - timedelta(hours=9)).dt.date
    unique_dates = sorted(df["論理日付"].unique(), reverse=True)
    unique_tables = sorted(df["TableNo"].unique())
    all_players = get_all_member_names()

    st.markdown("### 🔍 日付と卓を選択")
    c1, c2, c3 = st.columns(3)
    with c1: sel_date = st.selectbox("📅 日付を選択", ["(指定なし)"] + list(unique_dates))
    with c2: sel_table = st.selectbox("🀄 卓を選択", ["(指定なし)"] + list(unique_tables))
    with c3: sel_player = st.selectbox("👤 プレイヤーを選択", ["(指定なし)"] + list(all_players))

    is_filtered = False
    
    # フィルタリング
    if sel_date != "(指定なし)":
        df = df[df["論理日付"] == sel_date]
        is_filtered = True
        
    if sel_table != "(指定なし)":
        df = df[df["TableNo"] == sel_table]
        is_filtered = True

    if sel_player != "(指定なし)":
        df = df[(df["Aさん"] == sel_player) | (df["Bさん"] == sel_player) | (df["Cさん"] == sel_player)]
        is_filtered = True

    st.divider()

    if is_filtered and not df.empty:
        # 1. プレイヤー選択があれば個人成績サマリーを表示
        if sel_player != "(指定なし)":
            st.markdown(f"#### 👤 {sel_player} さんの成績 (表示範囲内)")
            ranks = []
            for _, row in df.iterrows():
                if row["Aさん"] == sel_player: ranks.append(int(float(row["A着順"])))
                elif row["Bさん"] == sel_player: ranks.append(int(float(row["B着順"])))
                elif row["Cさん"] == sel_player: ranks.append(int(float(row["C着順"])))
            
            if ranks:
                games = len(ranks)
                avg = sum(ranks)/games
                counts = {1: ranks.count(1), 2: ranks.count(2), 3: ranks.count(3)}
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("回数", f"{games}回")
                m2.metric("平均着順", f"{avg:.2f}")
                m3.metric("1着", f"{counts[1]}回")
                m4.metric("3着", f"{counts[3]}回")
            st.divider()

        # 2. 紙風スコアシートを表示
        st.markdown(f"#### 📝 集計表")
        render_paper_sheet(df)
        
    elif is_filtered and df.empty:
        st.warning("条件に一致するデータが見つかりませんでした")
    else:
        st.info("☝️ 上のボックスから「日付」などを選択すると、集計表が表示されます")

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
