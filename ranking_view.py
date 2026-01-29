import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime, date, timedelta # datetimeを追加
from streamlit_gsheets import GSheetsConnection

# ==========================================
# 1. ページ設定 (閲覧専用)
# ==========================================
st.set_page_config(page_title="ランキング表", layout="wide")

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
SHEET_MEMBER = "members" # メンバーシート定義を追加

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

# --- ★追加箇所: メンバーデータを読み込む関数 ---
def load_member_data():
    conn = get_conn()
    try:
        df = fetch_data_cached(conn, SHEET_MEMBER).fillna("")
        
        # 必要な列がなければ空で作る（エラー回避）
        if "名前" not in df.columns: df["名前"] = []
        if "最大飜数" not in df.columns: df["最大飜数"] = 0
        if "役満回数" not in df.columns: df["役満回数"] = 0
            
        # 数値型に変換
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
        df_mem = load_member_data() # ★ここでメンバーデータも読み込む

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
                    records.append({"name": name, "rank": r})
    
    if not records:
        st.warning("集計できるデータがありません")
        return

    df_raw = pd.DataFrame(records)
    
    stats = df_raw.groupby("name")["rank"].agg(
        games="count",
        avg_rank="mean",
        first_count=lambda x: (x==1).sum(),
        third_count=lambda x: (x==3).sum()
    ).reset_index()

    stats["top_rate"] = (stats["first_count"] / stats["games"]) * 100
    stats["last_avoid_rate"] = ((stats["games"] - stats["third_count"]) / stats["games"]) * 100
    
    min_games = st.slider("規定打数 (これ以下の人はランキングに表示しません)", 1, 50, 5)
    
    filtered_stats = stats[stats["games"] >= min_games].copy()
    
    if filtered_stats.empty:
        st.warning(f"打数が {min_games} 回以上のプレイヤーがいません。")
        return

    st.write("---")
    
    # --- タブを6つに拡張 ---
    t1, t2, t3, t4, t5, t6 = st.tabs(["📊 打数", "🥇 平均着順", "👑 トップ率", "🛡 ラス回避率", "💥 最大飜数", "🀅 役満回数"])
    
    with t1:
        st.subheader("📊 打数ランキング (Top 5)")
        res = filtered_stats.sort_values("games", ascending=False).reset_index(drop=True).head(5)
        res["順位"] = res.index + 1
        st.dataframe(
            res[["順位", "name", "games"]].rename(columns={"name":"名前", "games":"打数"}),
            hide_index=True, use_container_width=True
        )

    with t2:
        st.subheader("🥇 平均着順ランキング (Top 5)")
        res = filtered_stats.sort_values("avg_rank", ascending=True).reset_index(drop=True).head(5)
        res["順位"] = res.index + 1
        res["avg_rank"] = res["avg_rank"].map('{:.2f}'.format)
        st.dataframe(
            res[["順位", "name", "avg_rank", "games"]].rename(columns={"name":"名前", "avg_rank":"平均着順", "games":"打数"}),
            hide_index=True, use_container_width=True
        )

    with t3:
        st.subheader("👑 トップ率ランキング (Top 5)")
        res = filtered_stats.sort_values("top_rate", ascending=False).reset_index(drop=True).head(5)
        res["順位"] = res.index + 1
        res["top_rate"] = res["top_rate"].map('{:.1f}%'.format)
        st.dataframe(
            res[["順位", "name", "top_rate", "first_count", "games"]].rename(columns={"name":"名前", "top_rate":"トップ率", "first_count":"トップ回数", "games":"打数"}),
            hide_index=True, use_container_width=True
        )

    with t4:
        st.subheader("🛡 ラス回避率ランキング (Top 5)")
        res = filtered_stats.sort_values("last_avoid_rate", ascending=False).reset_index(drop=True).head(5)
        res["順位"] = res.index + 1
        res["last_avoid_rate"] = res["last_avoid_rate"].map('{:.1f}%'.format)
        st.dataframe(
            res[["順位", "name", "last_avoid_rate", "games"]].rename(columns={"name":"名前", "last_avoid_rate":"ラス回避率", "games":"打数"}),
            hide_index=True, use_container_width=True
        )

    # --- 新ランキング（メンバーシートから） ---
    with t5:
        st.subheader("💥 最大飜数ランキング (Top 5)")
        if not df_mem.empty:
            res_max = df_mem.sort_values("最大飜数", ascending=False).reset_index(drop=True).head(5)
            res_max = res_max[res_max["最大飜数"] > 0]
            if not res_max.empty:
                res_max["順位"] = res_max.index + 1
                st.dataframe(
                    res_max[["順位", "名前", "最大飜数"]],
                    hide_index=True, use_container_width=True
                )
            else:
                st.info("データがありません")
        else:
            st.info("データがありません")

    with t6:
        st.subheader("🀅 役満回数ランキング (Top 5)")
        if not df_mem.empty:
            res_yaku = df_mem.sort_values("役満回数", ascending=False).reset_index(drop=True).head(5)
            res_yaku = res_yaku[res_yaku["役満回数"] > 0]
            if not res_yaku.empty:
                res_yaku["順位"] = res_yaku.index + 1
                st.dataframe(
                    res_yaku[["順位", "名前", "役満回数"]],
                    hide_index=True, use_container_width=True
                )
            else:
                st.info("データがありません")
        else:
            st.info("データがありません")

if __name__ == '__main__':
    main()
