import streamlit as st
import pandas as pd
import os
from datetime import datetime, date, timedelta

# ==========================================
# 1. ページ設定 & デザイン調整
# ==========================================
st.set_page_config(page_title="3人麻雀スコア管理", layout="wide")

# 余計な表示を消すCSS
hide_style = """
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
"""
st.markdown(hide_style, unsafe_allow_html=True)

# ==========================================
# 2. パスワード認証
# ==========================================
def check_password():
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False
    if st.session_state["password_correct"]:
        return True
    
    st.title("🔒 ログイン")
    password = st.text_input("パスワード", type="password")
    if st.button("ログイン"):
        if password == "mahjong2026":  # パスワードはここで変更可能
            st.session_state["password_correct"] = True
            st.rerun()
        else:
            st.error("パスワードが違います")
    return False

if not check_password():
    st.stop()

# ==========================================
# 3. データ管理関数 (サンマ専用)
# ==========================================
DATA_FILE = "sanma_score.csv"

def load_data():
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE).fillna("")
        if "SetNo" not in df.columns and not df.empty:
            df["SetNo"] = (df["GameNo"] - 1) // 10 + 1
        elif "SetNo" not in df.columns:
            df["SetNo"] = []
        return df
    else:
        # 3人麻雀専用のカラム定義
        cols = ["GameNo", "SetNo", "日時", "備考", "Aさん", "Aタイプ", "A着順", "Bさん", "Bタイプ", "B着順", "Cさん", "Cタイプ", "C着順"]
        return pd.DataFrame(columns=cols)

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

# 集計ロジック
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

# ==========================================
# 4. 表示コンポーネント
# ==========================================
def render_history_table(df, highlight_game_id=None):
    if df.empty:
        st.info("データがありません")
        return

    df_sorted = df.sort_values(["SetNo", "GameNo"])
    unique_sets = sorted(df_sorted["SetNo"].unique(), reverse=True)
    
    for set_no in unique_sets:
        subset = df_sorted[df_sorted["SetNo"] == set_no]
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
            
            # 見やすく加工
            SPECIAL_NOTES = ["東１終了", "２人飛ばし", "５連勝〜"]
            special_mask = display_df["備考"].isin(SPECIAL_NOTES)
            for col in ["A着順", "B着順", "C着順"]:
                display_df[col] = display_df[col].astype(str).replace({"1": "①", "2": "②", "3": "③", "1.0": "①", "2.0": "②", "3.0": "③"})
                display_df.loc[special_mask & (display_df[col] == "①"), col] = "❶"

            target_cols = ["Aさん", "Aタイプ", "Bさん", "Bタイプ", "Cさん", "Cタイプ"]
            display_df[target_cols] = display_df[target_cols].mask(display_df[target_cols] == display_df[target_cols].shift(), "")
            
            # スタイリング
            def highlight(val):
                return 'background-color: #ffcccc; color: #cc0000; font-weight: bold;' if val in ["①", "❶"] else ''
            
            styler = display_df.style.map(highlight)
            if highlight_game_id:
                styler.apply(lambda r: ['background-color: #ffffcc']*len(r) if r.name in df[df["GameNo"]==highlight_game_id].index else ['']*len(r), axis=1)

            st.dataframe(styler, use_container_width=True, hide_index=True)

# ==========================================
# 5. ページ定義
# ==========================================
def page_game_input():
    st.title("🀄 3人麻雀スコア入力")
    
    # モード選択をサイドバーではなくメイン画面の上部に配置
    op_mode = st.radio("操作選択", ["📝 新規登録", "🔧 修正・削除", "📊 過去データを見る"], horizontal=True)
    
    if op_mode == "📊 過去データを見る":
        page_history()
        return

    df = load_data()
    
    # --- 初期値設定 ---
    current_dt = datetime.now()
    default_date_obj = (current_dt - timedelta(hours=9)).date()
    current_set_no = int(df["SetNo"].max()) if not df.empty else 1
    
    defaults = {
        "n1": "A", "t1": "A客", "r1": 2,
        "n2": "B", "t2": "B客", "r2": 1,
        "n3": "C", "t3": "AS", "r3": 3,
        "note": "なし",
        "game_no": df["GameNo"].max() + 1 if not df.empty else 1,
        "date_obj": default_date_obj,
        "set_no": current_set_no
    }
    
    selected_game_id = None
    if op_mode == "🔧 修正・削除":
        if not df.empty:
            ids = df["GameNo"].sort_values(ascending=False).tolist()
            selected_game_id = st.selectbox("修正するゲームを選択", ids)
            row = df[df["GameNo"] == selected_game_id].iloc[0]
            
            try:
                d_obj = datetime.strptime(str(row["日時"]).split(" ")[0], "%Y-%m-%d").date()
            except: d_obj = default_date_obj

            defaults.update({
                "n1": row["Aさん"], "t1": row["Aタイプ"], "r1": int(float(row["A着順"])),
                "n2": row["Bさん"], "t2": row["Bタイプ"], "r2": int(float(row["B着順"])),
                "n3": row["Cさん"], "t3": row["Cタイプ"], "r3": int(float(row["C着順"])),
                "note": row["備考"] if row["備考"] else "なし",
                "date_obj": d_obj, "game_no": selected_game_id, "set_no": int(row["SetNo"])
            })
        else:
            st.warning("データがありません")
            return

    # --- 入力フォーム (メイン画面に配置) ---
    with st.form("input_form"):
        c_info1, c_info2 = st.columns(2)
        with c_info1:
            st.write(f"**Game No: {defaults['game_no']}**")
        with c_info2:
            input_date = st.date_input("日付 (朝9時切替)", value=defaults['date_obj'])

        if op_mode == "📝 新規登録":
            start_new_set = st.checkbox(f"🆕 現在「第{defaults['set_no']}セット」です。ここから新しいセットにしますか？")
        
        st.markdown("---")
        
        TYPE_OPTS = ["A客", "B客", "AS", "BS"]
        def idx(opts, val): return opts.index(val) if val in opts else 0
        
        # 3人の入力欄を横並びではなく、スマホ用に縦に並べる（またはカード状にする）
        # スマホで見やすいように1人ずつ区切る
        def player_input(label, def_n, def_t, def_r):
            st.markdown(f"**▼ {label}**")
            c1, c2, c3 = st.columns([2, 1.5, 1])
            with c1: name = st.text_input("名前", value=def_n, key=f"n_{label}")
            with c2: type_ = st.selectbox("タイプ", TYPE_OPTS, index=idx(TYPE_OPTS, def_t), key=f"t_{label}")
            with c3: rank = st.selectbox("着順", [1, 2, 3], index=idx([1, 2, 3], def_r), key=f"r_{label}")
            return name, type_, rank

        p1_n, p1_t, p1_r = player_input("A席", defaults["n1"], defaults["t1"], defaults["r1"])
        p2_n, p2_t, p2_r = player_input("B席", defaults["n2"], defaults["t2"], defaults["r2"])
        p3_n, p3_t, p3_r = player_input("C席", defaults["n3"], defaults["t3"], defaults["r3"])

        st.markdown("---")
        
        NOTE_OPTS = ["なし", "東１終了", "２人飛ばし", "５連勝〜"]
        cur_note = defaults["note"]
        opts = NOTE_OPTS if cur_note in NOTE_OPTS else NOTE_OPTS + [cur_note]
        note = st.radio("備考", opts, index=idx(opts, cur_note), horizontal=True)
        
        st.markdown("---")
        
        if op_mode == "📝 新規登録":
            submitted = st.form_submit_button("📝 記録する", type="primary", use_container_width=True)
            delete = False
        else:
            c1, c2 = st.columns(2)
            with c1: submitted = st.form_submit_button("🔄 更新する", type="primary", use_container_width=True)
            with c2: delete = st.form_submit_button("🗑 削除する", type="secondary", use_container_width=True)

        if submitted:
            if sorted([p1_r, p2_r, p3_r]) != [1, 2, 3]:
                st.error("⚠️ 着順が重複しています！")
            else:
                save_date_str = input_date.strftime("%Y-%m-%d") + " " + datetime.now().strftime("%H:%M")
                final_set_no = defaults['set_no'] + 1 if (op_mode == "📝 新規登録" and start_new_set) else defaults['set_no']
                
                new_row = {
                    "GameNo": defaults["game_no"], "SetNo": final_set_no,
                    "日時": save_date_str, "備考": ("" if note == "なし" else note),
                    "Aさん": p1_n, "Aタイプ": p1_t, "A着順": p1_r,
                    "Bさん": p2_n, "Bタイプ": p2_t, "B着順": p2_r,
                    "Cさん": p3_n, "Cタイプ": p3_t, "C着順": p3_r
                }
                
                if op_mode == "📝 新規登録":
                    df = pd.concat([pd.DataFrame([new_row]), df], ignore_index=True)
                    st.success("記録しました")
                else:
                    idx_list = df[df["GameNo"] == selected_game_id].index
                    if len(idx_list) > 0: df.loc[idx_list[0]] = new_row
                    st.success("更新しました")
                save_data(df)
                st.rerun()
        
        if delete and selected_game_id:
            df = df[df["GameNo"] != selected_game_id]
            save_data(df)
            st.warning("削除しました")
            st.rerun()

    # 下部に最新履歴を表示
    st.markdown("### 直近の成績")
    render_history_table(df, selected_game_id if op_mode == "🔧 修正・削除" else None)

def page_history():
    st.markdown("### 📊 過去データ詳細")
    df = load_data()
    
    # 日付フィルタ
    if not df.empty:
        df["日時Obj"] = pd.to_datetime(df["日時"])
        df["論理日付"] = (df["日時Obj"] - timedelta(hours=9)).dt.date
        unique_dates = sorted(df["論理日付"].unique(), reverse=True)
        
        sel_date = st.selectbox("日付で絞り込み", ["(すべて)"] + list(unique_dates))
        if sel_date != "(すべて)":
            df = df[df["論理日付"] == sel_date]
    
    # 個人分析
    st.caption("プレイヤー分析")
    all_players = pd.concat([df["Aさん"], df["Bさん"], df["Cさん"]]).unique()
    all_players = [p for p in all_players if p != ""]
    all_players.sort()
    sel_player = st.selectbox("プレイヤーを選択", ["(選択してください)"] + list(all_players))
    
    if sel_player != "(選択してください)":
        ranks = []
        for _, row in df.iterrows():
            if row["Aさん"] == sel_player: ranks.append(int(float(row["A着順"])))
            elif row["Bさん"] == sel_player: ranks.append(int(float(row["B着順"])))
            elif row["Cさん"] == sel_player: ranks.append(int(float(row["C着順"])))
        
        if ranks:
            games = len(ranks)
            avg = sum(ranks)/games
            c1, c2 = st.columns(2)
            c1.metric("回数", f"{games}回")
            c2.metric("平均着順", f"{avg:.2f}")
    
    st.divider()
    render_history_table(df)

# ==========================================
# メイン実行
# ==========================================
page_game_input()
