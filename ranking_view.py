import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime, date, timedelta
from streamlit_gsheets import GSheetsConnection

# ==========================================
# 1. ページ設定 (閲覧専用)
# ==========================================
st.set_page_config(page_title="ランキング表", layout="centered") # 1カラムなのでcenteredの方が見やすい場合があります

hide_style = """
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    
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
    </style>
"""
st.markdown(hide_style, unsafe_allow_html=True)

# ==========================================
# 2. データ読み込み (読み取り専用)
# ==========================================
SHEET_SCORE = "score"
SHEET_MEMBER = "members"

EXPECTED_COLS = [
    "GameNo", "TableNo", "SetNo", "日時", "備考",
    "Aさん", "Aタイプ", "A着順",
    "Bさん", "Bタイプ", "B着順",
    "Cさん", "Cタイプ", "C着順"
]

def get_conn():
    return st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=600)
def fetch_data_cached(_conn, sheet_name):
    return _conn.read(worksheet=sheet_name, ttl=0)

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
    else:
        df["論理日付"] = []
        
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
            st.error("データの読み込みに失敗しました。")
            st.stop()
            
        return processed_df
    except:
        return pd.DataFrame(columns=EXPECTED_COLS)

def load_member_data():
    conn = get_conn()
    try:
        df = fetch_data_cached(conn, SHEET_MEMBER).fillna("")
        
        if "名前" not in df.columns: df["名前"] = []
        if "最大飜数" not in df.columns: df["最大飜数"] = 0
        if "役満回数" not in df.columns: df["役満回数"] = 0
            
        df["最大飜数"] = pd.to_numeric(df["最大飜数"], errors='coerce').fillna(0).astype(int)
        df["役満回数"] = pd.to_numeric(df["役満回数"], errors='coerce').fillna(0).astype(int)
        
        return df
    except:
        return pd.DataFrame({"名前": [], "最大飜数": [], "役満回数": []})

# ==========================================
# 3. ランキング表示ロジック
# ==========================================
def main():
    st.title("🏆 成績ランキング")
    st.caption("最終更新: " + datetime.now().strftime("%H:%M"))

    with st.spinner("データを読み込んでいます..."):
        df = load_score_data()
        df_mem = load_member_data()

    if df.empty:
        st.info("データがまだありません。")
        return

    valid_dates = pd.to_datetime(df["論理日付"]).dropna()
    if not valid_dates.empty:
        min_date = valid_dates.min().date()
        max_date = valid_dates.max().date()
    else:
        min_date = date.today()
        max_date = date.today()

    c1, c2 = st.columns([1, 2])
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
    
    # 集計計算
    stats = df_raw.groupby("name").agg(
        games=("rank", "count"),
        avg_rank=("rank", "mean"),
        first_count=("rank", lambda x: (x==1).sum()),
        third_count=("rank", lambda x: (x==3).sum()),
        days=("date", "nunique") 
    ).reset_index()

    # 計算フィールド追加
    stats["games_per_day"] = stats["games"] / stats["days"]
    stats["top_rate"] = (stats["first_count"] / stats["games"]) * 100
    stats["last_avoid_rate"] = ((stats["games"] - stats["third_count"]) / stats["games"]) * 100
    
    # ゲスト判定 & 名前整形
    stats["type"] = stats["name"].apply(lambda x: "staff" if str(x).lower().endswith("s") else "guest")
    # 名前の（）を削除
    stats["name"] = stats["name"].astype(str).str.replace(r'[（\(].*?[）\)]', '', regex=True)

    # ゲストのみ抽出
    stats_guest = stats[stats["type"] == "guest"]
    
    min_games = st.slider("規定打数 (これ以下の人はランキングに表示しません)", 50, 350, 50)
    
    # 規定打数フィルタ
    stats_guest = stats_guest[stats_guest["games"] >= min_games]
    
    if stats_guest.empty:
        st.warning(f"打数が {min_games} 回以上のお客さんがいません。")
        return

    st.write("---")
    
    t1, t2, t3, t4, t5, t6 = st.tabs(["📊 打数", "🥇 平均着順", "👑 トップ率", "🛡 ラス回避率", "💥 最大飜数", "🀅 役満回数"])
    
    # 表示用関数（ゲストのみ表示）
    def show_ranking_guest(df_g, sort_col, asc=False, format_func=None, val_col=None):
        if not df_g.empty:
            res = df_g.sort_values(sort_col, ascending=asc).reset_index(drop=True).head(5)
            res["順位"] = res.index + 1
            if format_func and val_col and val_col != "games":
                res[val_col] = res[val_col].map(format_func)
            
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
        st.subheader("📊 打数ランキング (Top 5)")
        show_ranking_guest(stats_guest, "games", False, None, "games")
    with t2:
        st.subheader("🥇 平均着順ランキング (Top 5)")
        show_ranking_guest(stats_guest, "avg_rank", True, '{:.2f}'.format, "avg_rank")
    with t3:
        st.subheader("👑 トップ率ランキング (Top 5)")
        show_ranking_guest(stats_guest, "top_rate", False, '{:.1f}%'.format, "top_rate")
    with t4:
        st.subheader("🛡 ラス回避率ランキング (Top 5)")
        show_ranking_guest(stats_guest, "last_avoid_rate", False, '{:.1f}%'.format, "last_avoid_rate")

    # --- メンバーデータのランキング ---
    df_mem["type"] = df_mem["名前"].apply(lambda x: "staff" if str(x).lower().endswith("s") else "guest")
    # 名前の（）を削除
    df_mem["名前"] = df_mem["名前"].astype(str).str.replace(r'[（\(].*?[）\)]', '', regex=True)
    
    mem_g = df_mem[df_mem["type"] == "guest"]
    
    def show_mem_ranking_guest(df_g, col):
        if not df_g.empty:
            res = df_g.sort_values(col, ascending=False).reset_index(drop=True).head(10)
            res = res[res[col] > 0]
            if not res.empty:
                res["順位"] = res.index + 1
                st.dataframe(res[["順位", "名前", col]], hide_index=True, use_container_width=True)
            else: st.info("データなし")
        else: st.info("データなし")

    with t5:
        st.subheader("💥 最大飜数ランキング (Top 5)")
        show_mem_ranking_guest(mem_g, "最大飜数")
    with t6:
        st.subheader("🀅 役満回数ランキング (Top 5)")
        show_mem_ranking_guest(mem_g, "役満回数")

if __name__ == '__main__':
    main()
