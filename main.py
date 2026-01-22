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
        # 初期メンバーは空でも良いが、例として入れておく
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
# 4. 集計 & 表示ロジック
# ==========================================
def calculate_summary(subset_df):
    player_cols = ["Aさん", "Bさん", "Cさん"]
    rank_cols = ["A着順", "B着順", "C着順"]
    
    all_players = pd.concat([subset_df[col] for col in player_cols]).unique()
    all_players = [p for p in all_players if p != ""]
    
    player_stats = []
    for player in all_players:
        counts = {1: 0, 2: 0, 3: 0}
        for p_col, r_col in zip(player_cols, rank_cols):
            for _, row in subset_df.iterrows():
                if row[p_col] == player:
                    try:
                        r = int(float(row[r_col]))
                        if 1 <= r <= 3: counts[r] += 1
                    except: pass
        
        total_games = sum(counts.values())
        if total_games > 0:
            total_score = sum(r * c for r, c in counts.items())
            avg = round(total_score / total_games, 2)
        else:
            avg = 0
            
        stats = {"名前": player, "平均": avg, "試合数": total_games, "1着": counts[1], "2着": counts[2], "3着": counts[3]}
        player_stats.append(stats)
    
    df_player = pd.DataFrame(player_stats)
    if not df_player.empty:
        df_player = df_player[["名前", "1着", "2着", "3着", "平均", "試合数"]].set_index("名前")

    target_types = ["A客", "B客", "AS", "BS"]
    type_stats = {t: 0 for t in target_types}
    FEE_MAP = {"A客": 3, "B客": 5, "AS": 1, "BS": 1}
    total_fee = 0
    
    for _, row in subset_df.iterrows():
        w_type = None
        for p_col, r_col, t_col in zip(player_cols, rank_cols, ["Aタイプ", "Bタイプ", "Cタイプ"]):
            try:
                if int(float(row[r_col])) == 1:
                    w_type = row[t_col]
                    break
            except: pass
        
        if w_type in target_types:
            type_stats[w_type] += 1
            if w_type in FEE_MAP: total_fee += FEE_MAP[w_type]
        
        note = str(row["備考"])
        if note == "東１終了": total_fee -= 1
        elif note == "２人飛ばし": total_fee -= 2
        elif note == "５連勝〜": total_fee -= 5

    df_type = pd.DataFrame(list(type_stats.items()), columns=["タイプ", "1着回数"]).set_index("タイプ").T
    return df_player, df_type, total_fee

def render_history_table(df, highlight_game_id=None):
    if df.empty:
        st.info("この日のデータはありません")
        return

    df_sorted = df.sort_values(["TableNo", "SetNo", "GameNo"])
    unique_tables = sorted(df_sorted["TableNo"].unique())

    for table_no in unique_tables:
        table_df = df_sorted[df_sorted["TableNo"] == table_no]
        if table_df.empty: continue
        
        unique_sets = sorted(table_df["SetNo"].unique(), reverse=True)
        
        for set_no in unique_sets:
            subset = table_df[table_df["SetNo"] == set_no]
            if subset.empty: continue
                
            start_game = subset["GameNo"].min()
            end_game = subset["GameNo"].max()
            df_player, df_type, total_fee = calculate_summary(subset)
            
            label = f"📄 第 {int(set_no)} セット (Game {start_game} ～ {end_game})　　💰 合計: {total_fee} 枚"
            is_expanded = (set_no == max(unique_sets)) or (highlight_game_id is not None and highlight_game_id in subset["GameNo"].values)
            
            with st.expander(label, expanded=is_expanded):
                c1, c2 = st.columns([2, 1])
                with c1:
                    if not df_player.empty:
                        st.caption("👤 個人成績")
                        st.dataframe(df_player, use_container_width=True)
                with c2:
                    st.caption("🏆 タイプ別トップ")
                    st.table(df_type)
                st.divider()
                
                display_cols = ["GameNo", "日時", "Aさん", "Aタイプ", "A着順", "Bさん", "Bタイプ", "B着順", "Cさん", "Cタイプ", "C着順", "備考"]
                display_df = subset[display_cols].copy()
                
                SPECIAL_NOTES = ["東１終了", "２人飛ばし", "５連勝〜"]
                special_mask = display_df["備考"].isin(SPECIAL_NOTES)
                for col in ["A着順", "B着順", "C着順"]:
                    display_df[col] = display_df[col].astype(str).replace({"1": "①", "2": "②", "3": "③", "1.0": "①", "2.0": "②", "3.0": "③"})
                    display_df.loc[special_mask & (display_df[col] == "①"), col] = "❶"

                target_cols = ["Aさん", "Aタイプ", "Bさん", "Bタイプ", "Cさん", "Cタイプ"]
                display_df[target_cols] = display_df[target_cols].mask(display_df[target_cols] == display_df[target_cols].shift(), "")
                
                def highlight(val):
                    return 'background-color: #ffcccc; color: #cc0000; font-weight: bold;' if val in ["①", "❶"] else ''
                
                styler = display_df.style.map(highlight)
                if highlight_game_id:
                    styler.apply(lambda r: ['background-color: #ffffcc']*len(r) if r.name in df[df["GameNo"]==highlight_game_id].index else ['']*len(r), axis=1)

                st.dataframe(styler, use_container_width=True, hide_index=True)

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
    
    # --- 初期値設定（フォームの外で日付を決定）---
    current_dt = datetime.now()
    default_date_obj = (current_dt - timedelta(hours=9)).date()
    
    # ユーザーが操作する部分（フォームの外）
    c_top1, c_top2 = st.columns(2)
    with c_top1:
        current_table = st.selectbox("入力する卓を選択してください", [1, 2, 3], index=0)
    with c_top2:
        input_date = st.date_input("日付 (朝9時切替)", value=default_date_obj)

    # --- バグ修正：選択された「卓」と「日付」に基づいてセット番号を計算 ---
    df_table = df[df["TableNo"] == current_table]
    
    # 日付フィルタリング (論理日付)
    if not df_table.empty:
        df_table["日時Obj"] = pd.to_datetime(df_table["日時"])
        df_table["論理日付"] = (df_table["日時Obj"] - timedelta(hours=9)).dt.date
        df_today = df_table[df_table["論理日付"] == input_date]
    else:
        df_today = pd.DataFrame()

    # その日のその卓のデータがあれば続きのセット、なければ1から
    if not df_today.empty:
        current_set_no = int(df_today["SetNo"].max())
    else:
        current_set_no = 1
    # -------------------------------------------------------------

    is_edit_mode = st.checkbox("🔧 過去の記録を修正・削除する")
    
    def safe_default(name):
        return name if name in member_list else None # 名前がない場合はNone

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
            # 編集モード時は日付もデータから復元
            try: 
                # 日付変更に対応するためinput_dateは上書きしないが、表示用として認識
                pass 
            except: pass
            
            if current_table != defaults["table_no"]:
                st.info(f"※ 選択中のゲームは「{defaults['table_no']}卓」のデータです")
        else:
            st.warning("データがありません")
            return

    with st.form("input_form"):
        st.write(f"**Game No: {defaults['game_no']}**")
        if not is_edit_mode:
            st.caption(f"【{defaults['table_no']}卓】 第 {defaults['set_no']} セット")
        
        if not is_edit_mode:
            start_new_set = st.checkbox(f"🆕 ここから新しいセットにする ({defaults['table_no']}卓の第{defaults['set_no']+1}セットへ)")

        st.divider()

        TYPE_OPTS = ["A客", "B客", "AS", "BS"]
        def idx(opts, val): return opts.index(val) if val in opts else 0
        def get_idx_in_list(lst, val): return lst.index(val) if val in lst else None
        
        # UI変更: index=None, placeholder指定
        def player_input_row(label, placeholder_text, def_n, def_t, def_r):
            st.markdown(f"**▼ {label}**")
            c1, c2 = st.columns([1, 2])
            with c1:
                # デフォルト値がNoneならプレースホルダーが表示される
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
            delete = False
        else:
            c_btn1, c_btn2 = st.columns(2)
            with c_btn1: submitted = st.form_submit_button("🔄 更新する", type="primary", use_container_width=True)
            with c_btn2: delete = st.form_submit_button("🗑 削除する", type="secondary", use_container_width=True)

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
        
        if delete and selected_game_id:
            df = df[df["GameNo"] != selected_game_id]
            save_score_data(df)
            st.session_state["success_msg"] = "🗑 削除しました"
            st.rerun()

    # --- 履歴表示（当日・対象卓のみ） ---
    st.markdown(f"### 📋 {input_date.strftime('%Y/%m/%d')} の対局結果 ({current_table}卓)")
    
    if not df.empty:
        # 日付・卓で絞り込み
        df["日時Obj"] = pd.to_datetime(df["日時"])
        df["論理日付"] = (df["日時Obj"] - timedelta(hours=9)).dt.date
        
        history_subset = df[
            (df["TableNo"] == current_table) & 
            (df["論理日付"] == input_date)
        ]
        
        render_history_table(history_subset, selected_game_id if is_edit_mode else None)
    else:
        render_history_table(df)

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
    all_players = get_all_member_names()
    unique_tables = sorted(df["TableNo"].unique())

    st.markdown("### 🔍 データの絞り込み")
    c1, c2, c3 = st.columns(3)
    with c1: sel_date = st.selectbox("📅 日付を選択", ["(指定なし)"] + list(unique_dates))
    with c2: sel_table = st.selectbox("🀄 卓を選択", ["(指定なし)"] + list(unique_tables))
    with c3: sel_player = st.selectbox("👤 プレイヤーを選択", ["(指定なし)"] + list(all_players))

    is_filtered = False
    
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

    if is_filtered:
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
            st.write("")
        
        if not df.empty:
            render_history_table(df)
        else:
            st.warning("条件に一致するデータが見つかりませんでした")
    else:
        st.info("☝️ 上のボックスから絞り込み条件を選択してください")

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
