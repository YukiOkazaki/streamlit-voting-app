import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import uuid

# --- Google Sheets 認証 ---
SHEET_ID = "15q6gB5RbBLVxubLiwpG_-IKVHRNdHcO8XLluGoDwctw"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets",
          "https://www.googleapis.com/auth/drive"]

# 🔒 Streamlit Secrets から認証情報を取得
credentials = Credentials.from_service_account_info(
    st.secrets["google_service_account"],  # ← Secretsのキー名と一致させる
    scopes=SCOPES
)

client = gspread.authorize(credentials)
sheet = client.open_by_key(SHEET_ID).sheet1

# --- Streamlit ページ設定 ---
st.set_page_config(page_title="投票アプリ", page_icon="🗳️", layout="wide")
st.sidebar.title("メニュー")
page = st.sidebar.selectbox("ページを選択", ["新規設定", "投票ページ"])

# --- ① 新規設定ページ ---
if page == "新規設定":
    st.title("🗳️ 新しい投票を作成")

    urls = [st.text_input(f"画像 {i+1} のURL") for i in range(4)]

    if st.button("投票ページを作成"):
        if all(urls):
            poll_id = str(uuid.uuid4())[:8]

            # Google Sheetsに新規行を追加
            sheet.append_row([poll_id] + urls + [0, 0, 0, 0])

            base_url = st.get_option("server.baseUrlPath") or ""
            st.success("投票ページが作成されました！")
            st.write("共有用URL👇")
            st.code(f"{base_url}/?poll_id={poll_id}")
        else:
            st.warning("4つすべての画像URLを入力してください。")

# --- ② 投票ページ ---
elif page == "投票ページ":
    st.title("📸 投票ページ")

    query_params = st.experimental_get_query_params()
    poll_id = query_params.get("poll_id", [None])[0]

    if not poll_id:
        st.warning("URLに poll_id が含まれていません。新規設定画面から作成してください。")
    else:
        # 該当投票を探す
        rows = sheet.get_all_values()
        header, *data = rows

        poll = None
        for row in data:
            if row[0] == poll_id:
                poll = row
                break

        if not poll:
            st.error("指定された投票は存在しません。")
        else:
            urls = poll[1:5]
            votes = list(map(int, poll[5:9]))

            st.write("好きな画像を1つ選んで投票してください👇")
            cols = st.columns(4)

            for i, url in enumerate(urls):
                with cols[i]:
                    if st.button(f"投票する {i+1}", key=f"vote_{i}"):
                        votes[i] += 1
                        sheet.update_cell(data.index(poll)+2,
                                          6+i, votes[i])  # シート更新
                        st.success("投票ありがとうございました！")

                    st.image(url, use_column_width=True)

            st.write("---")
            st.subheader("📊 投票結果")
            df = pd.DataFrame({
                "画像": [f"候補 {i+1}" for i in range(4)],
                "投票数": votes
            })
            st.bar_chart(df.set_index("画像"))
