import streamlit as st
import pandas as pd
import os
from datetime import datetime, date, timedelta

# ==========================================
# 【設定】テーマ強制 (ライトモード)
# ==========================================
if not os.path.exists(".streamlit"):
    os.makedirs(".streamlit")

with open(".streamlit/config.toml", "w") as f:
    f.write('''
[theme]
base="light"
primaryColor="#FF4B4B"
backgroundColor="#FFFFFF"
secondaryBackgroundColor="#F0F2F6"
textColor="#31333F"
font="sans serif"
''')

# ページ設定
st.set_page_config(page_title="麻雀スコア管理", layout="wide")

# ==========================================
# 共通関数
# ==========================================
def load_data(filename, mode="sanma"):
    if os.path.exists(filename):
        df = pd.read_csv(filename).fillna("")
        # --- データ移行処理: SetNo列がない場合、旧ルール(10回区切り)で作成 ---
        if "SetNo" not in df.columns and not df.empty:
            # GameNoに基づいてセット番号を計算 (1~10=>1, 11~20=>2...)
            df["SetNo"] = (df["GameNo"] - 1) // 10 + 1
        elif "SetNo" not in df.columns:
            # データが空の場合
            df["SetNo"] = []
        return df
    else:
        # 新規作成時はSetNo列を含める
        base_cols = ["GameNo", "SetNo", "日時", "備考", "Aさん", "Aタイプ", "A着順", "Bさん", "Bタイプ", "B着順", "Cさん", "Cタイプ", "C着順"]
        if mode == "yonma":
            base_cols += ["Dさん", "Dタイプ", "D着順"]
        return pd.DataFrame(columns=base_cols)

def save_data(df, filename):
    df.to_csv(filename, index=False)

# 日付ロジック（朝9時切り替え）
def get_logical_date(dt_str):
    """
    文字列の日時を受け取り、9時間引いた『麻雀上の日付』を返す
    例: 1月10日 02:00 -> 1月9日
    """
    try:
        dt = pd.to_datetime(dt_str)
        return (dt - timedelta(hours=9)).date()
    except:
        return date.today()

# 全体集計ロジック
def calculate_summary(subset_df, mode="sanma"):
    player_cols = ["Aさん", "Bさん", "Cさん"]
    rank_cols = ["A着順", "B着順", "C着順"]
    if mode == "yonma":
        player_cols.append("Dさん")
        rank_cols.append("D着順")

    all_players = pd.concat([subset_df[col] for col in player_cols]).unique()
    all_players = [p for p in all_players if p != ""]
    
    player_stats = []
    for player in all_players:
        counts = {r: 0 for r in range(1, 5)}
        for p_col, r_col in zip(player_cols, rank_cols):
            for idx, row in subset_df.iterrows():
                if row[p_col] == player:
                    try:
                        r = int(float(row[r_col]))
                        if 1 <= r <= 4: counts[r] += 1
                    except: pass
        
        total_games = sum(counts.values())
        if total_games > 0:
            total_score = sum(rank * count for rank, count in counts.items())
            avg = round(total_score / total_games, 2)
        else:
            avg = 0
            
        stats = {"名前": player, "平均": avg, "試合数": total_games}
        for r in range(1, 5):
            if mode == "sanma" and r == 4: continue
            stats[f"{r}着"] = counts[r]
        player_stats.append(stats)
    
    df_player = pd.DataFrame(player_stats)
    if not df_player.empty:
        cols_order = ["名前", "1着", "2着", "3着"]
        if mode == "yonma": cols_order.append("4着")
        cols_order += ["平均", "試合数"]
        df_player = df_player[cols_order].set_index("名前")

    target_types = ["A客", "B客", "AS", "BS"]
    type_stats = {t: 0 for t in target_types}
    FEE_MAP = {"A客": 3, "B客": 5, "AS": 1, "BS": 1}
    total_fee = 0
    
    for i, row in subset_df.iterrows():
        w_type = None
        type_cols = ["Aタイプ", "Bタイプ", "Cタイプ", "Dタイプ"]
        for p_col, r_col, t_col in zip(player_cols, rank_cols, type_cols):
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
# 個人成績分析ビュー
# ==========================================
def render_player_analysis(df, mode="sanma"):
    st.markdown("### 🔍 個人成績分析")
    st.caption("現在表示されているデータ範囲（日付絞り込み含む）での成績が集計されます")
    
    if df.empty:
        st.info("データがありません")
        return

    player_cols = ["Aさん", "Bさん", "Cさん"]
    rank_cols = ["A着順", "B着順", "C着順"]
    if mode == "yonma":
        player_cols.append("Dさん")
        rank_cols.append("D着順")
    
    all_players = pd.concat([df[c] for c in player_cols]).unique()
    all_players = [p for p in all_players if p != ""]
    all_players.sort()
    
    selected_player = st.selectbox("分析するプレイヤーを選択", ["(選択してください)"] + list(all_players), key=f"analysis_{mode}")
    
    if selected_player != "(選択してください)":
        ranks = []
        for _, row in df.iterrows():
            for p_col, r_col in zip(player_cols, rank_cols):
                if row[p_col] == selected_player:
                    try:
                        r = int(float(row[r_col]))
                        ranks.append(r)
                    except: pass
                    break
        
        if ranks:
            total_games = len(ranks)
            avg_rank = sum(ranks) / total_games
            counts = {r: ranks.count(r) for r in range(1, 5)}
            if mode == "sanma": counts.pop(4, None)
            
            st.markdown(f"#### 👤 {selected_player} さんの成績")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("打半荘回数", f"{total_games} 回")
            c1.metric("平均着順", f"{avg_rank:.2f}")
            c2.metric("1着回数", f"{counts[1]} 回")
            
            chart_df = pd.DataFrame.from_dict(counts, orient='index', columns=['回数'])
            chart_df.index.name = '着順'
            c3.bar_chart(chart_df)
            
            dist_table = pd.DataFrame([counts])
            dist_table.index = ["回数"]
            st.table(dist_table)

# ==========================================
# 履歴テーブル表示（セット区切り）
# ==========================================
def render_history_table(df, mode="sanma", highlight_game_id=None):
    if df.empty:
        st.info("データがありません")
        return

    # SetNo順、GameNo順にソート
    df_sorted = df.sort_values(["SetNo", "GameNo"])
    
    # 存在するセット番号を取得（降順＝新しい順）
    unique_sets = sorted(df_sorted["SetNo"].unique(), reverse=True)
    
    for set_no in unique_sets:
        # そのセットのデータを抽出
        subset = df_sorted[df_sorted["SetNo"] == set_no]
        
        if not subset.empty:
            start_game = subset["GameNo"].min()
            end_game = subset["GameNo"].max()
            
            # 集計計算
            df_player, df_type, total_fee = calculate_summary(subset, mode)
            
            label = f"📄 第 {int(set_no)} セット (Game {start_game} ～ {end_game})　　💰 ゲーム代合計: {total_fee} 枚"
            
            # 最新セットまたは編集中なら開く
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
                st.caption("📝 対局履歴詳細")
                
                if mode == "sanma":
                    display_cols = ["GameNo", "日時", "Aさん", "Aタイプ", "A着順", "Bさん", "Bタイプ", "B着順", "Cさん", "Cタイプ", "C着順", "備考"]
                    target_cols = ["Aさん", "Aタイプ", "Bさん", "Bタイプ", "Cさん", "Cタイプ"]
                    rank_cols = ["A着順", "B着順", "C着順"]
                else:
                    display_cols = ["GameNo", "日時", "Aさん", "Aタイプ", "A着順", "Bさん", "Bタイプ", "B着順", "Cさん", "Cタイプ", "C着順", "Dさん", "Dタイプ", "D着順", "備考"]
                    target_cols = ["Aさん", "Aタイプ", "Bさん", "Bタイプ", "Cさん", "Cタイプ", "Dさん", "Dタイプ"]
                    rank_cols = ["A着順", "B着順", "C着順", "D着順"]

                display_df = subset[display_cols].copy()
                
                SPECIAL_NOTES = ["東１終了", "２人飛ばし", "５連勝〜"]
                special_mask = display_df["備考"].isin(SPECIAL_NOTES)
                
                for col in rank_cols:
                    display_df[col] = display_df[col].astype(str)
                    display_df[col] = display_df[col].replace({"1": "①", "2": "②", "3": "③", "4": "④", "1.0": "①", "2.0": "②", "3.0": "③", "4.0": "④"})
                    target_mask = special_mask & (display_df[col] == "①")
                    display_df.loc[target_mask, col] = "❶"

                mask = display_df[target_cols] == display_df[target_cols].shift()
                display_df[target_cols] = display_df[target_cols].mask(mask, "")
                
                styler = display_df.style
                def highlight_top(val):
                    if val in ["①", "❶"]:
                        return 'background-color: #ffcccc; color: #cc0000; font-weight: bold;'
                    return ''
                styler = styler.map(highlight_top)
                
                if highlight_game_id and highlight_game_id in subset["GameNo"].values:
                    def highlight_edit_row(row):
                        return ['background-color: #ffffcc']*len(row) if row.name in df[df["GameNo"]==highlight_game_id].index else ['']*len(row)
                    styler = styler.apply(highlight_edit_row, axis=1)

                st.dataframe(styler, use_container_width=True, hide_index=True)

# ==========================================
# ページ遷移と機能
# ==========================================
def page_home():
    st.title("🀄 麻雀スコア管理ホーム")
    st.write("モードを選択してください")
    
    c1, c2, c3 = st.columns(3)
    with c1:
        st.info("### 3人麻雀")
        if st.button("3人麻雀を始める", use_container_width=True):
            st.session_state["page"] = "sanma"
            st.rerun()
    with c2:
        st.success("### 4人麻雀")
        if st.button("4人麻雀を始める", use_container_width=True):
            st.session_state["page"] = "yonma"
            st.rerun()
    with c3:
        st.warning("### 過去データ")
        if st.button("過去データを見る", use_container_width=True):
            st.session_state["page"] = "history"
            st.rerun()

def page_game_input(mode="sanma"):
    filename = "sanma_score.csv" if mode == "sanma" else "yonma_score.csv"
    title = "🀄 3人麻雀" if mode == "sanma" else "🀄 4人麻雀"
    rank_options = [1, 2, 3] if mode == "sanma" else [1, 2, 3, 4]
    
    st.title(f"{title} 成績入力")
    if st.button("🏠 ホームに戻る"):
        st.session_state["page"] = "home"
        st.rerun()
        
    df = load_data(filename, mode)
    
    st.sidebar.header(f"{title} メニュー")
    op_mode = st.sidebar.radio("操作", ["📝 新規登録", "🔧 修正・削除"], horizontal=True, key=f"{mode}_op")
    
    # --- 日付の初期値 (9時区切りロジック適用) ---
    current_dt = datetime.now()
    default_date_obj = (current_dt - timedelta(hours=9)).date()
    
    # --- 現在のセット番号を取得 ---
    current_set_no = 1
    if not df.empty:
        current_set_no = int(df["SetNo"].max())
    
    defaults = {
        "n1": "内山", "t1": "A客", "r1": 2,
        "n2": "野田", "t2": "B客", "r2": 1,
        "n3": "豊村", "t3": "AS", "r3": 3,
        "n4": "ゲスト", "t4": "BS", "r4": 4,
        "note": "なし",
        "game_no": df["GameNo"].max() + 1 if not df.empty else 1,
        "date_obj": default_date_obj,
        "set_no": current_set_no
    }
    
    selected_game_id = None
    if op_mode == "🔧 修正・削除":
        if not df.empty:
            ids = df["GameNo"].sort_values(ascending=False).tolist()
            selected_game_id = st.sidebar.selectbox("修正No", ids, key=f"{mode}_sel")
            row = df[df["GameNo"] == selected_game_id].iloc[0]
            
            # 日付解析 (エラー回避)
            try:
                d_str = str(row["日時"]).split(" ")[0]
                d_obj = datetime.strptime(d_str, "%Y-%m-%d").date()
            except:
                d_obj = default_date_obj

            defaults.update({
                "n1": row["Aさん"], "t1": row["Aタイプ"], "r1": int(float(row["A着順"])),
                "n2": row["Bさん"], "t2": row["Bタイプ"], "r2": int(float(row["B着順"])),
                "n3": row["Cさん"], "t3": row["Cタイプ"], "r3": int(float(row["C着順"])),
                "note": row["備考"] if row["備考"] else "なし",
                "date_obj": d_obj, 
                "game_no": selected_game_id,
                "set_no": int(row["SetNo"])
            })
            if mode == "yonma":
                defaults.update({"n4": row["Dさん"], "t4": row["Dタイプ"], "r4": int(float(row["D着順"]))})
        else:
            st.sidebar.warning("データなし")

    with st.sidebar.form(f"{mode}_form"):
        # --- セット区切り機能 ---
        if op_mode == "📝 新規登録":
            st.write(f"**Game No: {defaults['game_no']}**")
            st.info(f"現在のセット: 第 {defaults['set_no']} セット")
            # 新しいセットを開始するチェックボックス
            start_new_set = st.checkbox("🆕 ここから新しいセットにする (清算して次へ)", key=f"{mode}_newset")
        else:
            st.write(f"**Game No: {defaults['game_no']}** (第 {defaults['set_no']} セット)")
            start_new_set = False # 編集モードではセット番号変更は複雑になるため非表示（要望があれば追加可）
            
        input_date = st.date_input("日付 (朝9時切替)", value=defaults['date_obj'], key=f"{mode}_date")
        
        # ---------------------
        
        TYPE_OPTS = ["A客", "B客", "AS", "BS"]
        NOTE_OPTS = ["なし", "東１終了", "２人飛ばし", "５連勝〜"]
        def idx(opts, val): return opts.index(val) if val in opts else 0
        
        def player_input(label, suffix, def_n, def_t, def_r):
            st.markdown(f"**▼ {label}**")
            c1, c2 = st.columns([1, 2])
            with c1: name = st.text_input("名前", value=def_n, key=f"{mode}_n{suffix}")
            with c2:
                rank = st.radio("着順", rank_options, index=idx(rank_options, def_r), horizontal=True, key=f"{mode}_r{suffix}")
                type_ = st.radio("タイプ", TYPE_OPTS, index=idx(TYPE_OPTS, def_t), horizontal=True, key=f"{mode}_t{suffix}")
            st.markdown("---")
            return name, type_, rank

        p1_n, p1_t, p1_r = player_input("A席", "1", defaults["n1"], defaults["t1"], defaults["r1"])
        p2_n, p2_t, p2_r = player_input("B席", "2", defaults["n2"], defaults["t2"], defaults["r2"])
        p3_n, p3_t, p3_r = player_input("C席", "3", defaults["n3"], defaults["t3"], defaults["r3"])
        
        p4_n, p4_t, p4_r = "", "", 0
        if mode == "yonma":
            p4_n, p4_t, p4_r = player_input("D席", "4", defaults["n4"], defaults["t4"], defaults["r4"])

        st.markdown("**▼ 備考**")
        cur_note = defaults["note"]
        opts = NOTE_OPTS if cur_note in NOTE_OPTS else NOTE_OPTS + [cur_note]
        note = st.radio("備考", opts, index=idx(opts, cur_note), horizontal=True, key=f"{mode}_note")
        
        st.markdown("---")
        
        if op_mode == "📝 新規登録":
            submitted = st.form_submit_button("📝 記録", type="primary")
            delete = False
        else:
            c1, c2 = st.columns(2)
            with c1: submitted = st.form_submit_button("🔄 更新", type="primary")
            with c2: delete = st.form_submit_button("🗑 削除", type="secondary")

        if submitted:
            ranks = [p1_r, p2_r, p3_r]
            if mode == "yonma": ranks.append(p4_r)
            if sorted(ranks) != rank_options:
                st.error(f"⚠️ 着順重複: {ranks}")
            else:
                save_note = "" if note == "なし" else note
                save_date_str = input_date.strftime("%Y-%m-%d") + " " + datetime.now().strftime("%H:%M")

                # セット番号の決定
                if op_mode == "📝 新規登録":
                    final_set_no = defaults['set_no'] + 1 if start_new_set else defaults['set_no']
                else:
                    final_set_no = defaults['set_no'] # 編集時は変更しない

                new_row = {
                    "GameNo": defaults["game_no"], "SetNo": final_set_no,
                    "日時": save_date_str, "備考": save_note,
                    "Aさん": p1_n, "Aタイプ": p1_t, "A着順": p1_r,
                    "Bさん": p2_n, "Bタイプ": p2_t, "B着順": p2_r,
                    "Cさん": p3_n, "Cタイプ": p3_t, "C着順": p3_r
                }
                if mode == "yonma":
                    new_row.update({"Dさん": p4_n, "Dタイプ": p4_t, "D着順": p4_r})
                
                if op_mode == "📝 新規登録":
                    df = pd.concat([pd.DataFrame([new_row]), df], ignore_index=True)
                    st.success(f"記録完了 (第 {final_set_no} セット)")
                else:
                    idx_list = df[df["GameNo"] == selected_game_id].index
                    if len(idx_list) > 0: df.loc[idx_list[0]] = new_row
                    st.success("更新完了")
                save_data(df, filename)
                st.rerun()
        
        if delete and selected_game_id:
            df = df[df["GameNo"] != selected_game_id]
            save_data(df, filename)
            st.warning("削除完了")
            st.rerun()

    render_history_table(df, mode, selected_game_id if op_mode == "🔧 修正・削除" else None)

def page_history():
    st.title("📊 過去データ参照")
    if st.button("🏠 ホームに戻る"):
        st.session_state["page"] = "home"
        st.rerun()
        
    tab1, tab2 = st.tabs(["3人麻雀データ", "4人麻雀データ"])
    
    # 共通フィルタリング処理 (9時区切り対応)
    def filter_by_date(df, key_suffix):
        if df.empty: return df
        
        # 9時間引いた「論理日付」列を作る
        df["日時Obj"] = pd.to_datetime(df["日時"])
        df["論理日付"] = (df["日時Obj"] - timedelta(hours=9)).dt.date
        
        unique_dates = sorted(df["論理日付"].unique(), reverse=True)
        
        col1, col2 = st.columns([1, 3])
        with col1:
            selected_date = st.selectbox("📅 日付で絞り込み (朝9時切替)", ["(すべて)"] + list(unique_dates), key=f"date_filter_{key_suffix}")
        
        if selected_date != "(すべて)":
            return df[df["論理日付"] == selected_date]
        return df

    with tab1:
        df_sanma = load_data("sanma_score.csv", "sanma")
        filtered_sanma = filter_by_date(df_sanma, "sanma")
        render_player_analysis(filtered_sanma, "sanma")
        st.divider()
        render_history_table(filtered_sanma, "sanma")
        
    with tab2:
        df_yonma = load_data("yonma_score.csv", "yonma")
        filtered_yonma = filter_by_date(df_yonma, "yonma")
        render_player_analysis(filtered_yonma, "yonma")
        st.divider()
        render_history_table(filtered_yonma, "yonma")

if "page" not in st.session_state:
    st.session_state["page"] = "home"

if st.session_state["page"] == "home":
    page_home()
elif st.session_state["page"] == "sanma":
    page_game_input("sanma")
elif st.session_state["page"] == "yonma":
    page_game_input("yonma")
elif st.session_state["page"] == "history":
    page_history()