import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.title("🏥 接続診断モード")

# 1. Secretsの情報を表示（パスワードは見せずに）
st.write("### 1. 設定ファイルの確認")
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    url = st.secrets["connections"]["gsheets"]["spreadsheet"]
    email = st.secrets["connections"]["gsheets"]["client_email"]
    st.success("✅ Secretsは読み込めました")
    st.info(f"📋 **書き込み先のURL:** {url}")
    st.info(f"📧 **このロボットのメール:** {email}")
    st.warning("👆 このメールアドレスが、スプレッドシートの「共有」に「編集者」として入っていますか？")
except Exception as e:
    st.error(f"❌ Secretsの読み込み失敗: {e}")
    st.stop()

# 2. 読み込みテスト
st.write("### 2. 読み込みテスト")
try:
    df = conn.read(worksheet="members", ttl=0)
    st.success("✅ 'members' シートの読み込みに成功しました！")
    st.dataframe(df)
except Exception as e:
    st.error(f"❌ 読み込み失敗: {e}")
    st.write("原因の可能性: URLが違う、シート名が 'members' ではない、共有されていない")
    st.stop()

# 3. 書き込みテスト
st.write("### 3. 書き込みテスト")
if st.button("書き込みテストを実行"):
    try:
        # テストデータを書き込む
        test_df = pd.DataFrame({"名前": ["テスト太郎"], "登録日": ["2026-01-01"]})
        conn.update(worksheet="members", data=test_df)
        st.success("🎉 **書き込み成功！エラーは解消されました！**")
        st.balloons()
    except Exception as e:
        st.error(f"❌ 書き込み失敗: {e}")
        st.error("原因: このロボット（メールアドレス）に『編集者』権限がないか、Google Drive APIが無効です。")
