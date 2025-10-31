import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import uuid
import plotly.express as px

# --- Google Sheets 認証（Secretsから取得） ---
SHEET_ID = st.secrets["spreadsheet_id"]
creds = Credentials.from_service_account_info(
    st.secrets["google_service_account"],
    scopes=[
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
)
client = gspread.authorize(creds)
sheet = client.open_by_key(SHEET_ID).sheet1

# --- ページ設定（中央表示） ---
st.set_page_config(page_title="投票アプリ", page_icon="🗳️")

# --- URLパラメータ取得 ---
query_params = st.experimental_get_query_params()
poll_id = query_params.get("poll_id", [None])[0]

# --- 投票ページ ---
if poll_id:
    st.title("📸 投票ページ")

    # シートから投票データ取得
    rows = sheet.get_all_values()
    header, *data = rows
    poll = next((row for row in data if row[0] == poll_id), None)

    if not poll:
        st.error("指定された投票は存在しません。")
    else:
        # タイトルとURLを取得
        titles = poll[1:8:2]   # 1,3,5,7列
        urls = poll[2:9:2]     # 2,4,6,8列
        votes = list(map(int, poll[9:13]))  # 票数列

        st.write("好きな候補を1つ選んで投票してください👇")
        cols = st.columns(4)
        for i, title in enumerate(titles):
            with cols[i]:
                st.subheader(title)
                url = urls[i]
                if url.strip():  # URLが空でなければ表示
                    try:
                        st.image(url, use_column_width=True)
                    except Exception:
                        st.write("画像を表示できません")
                if st.button(f"投票する {i+1}", key=f"vote_{i}"):
                    votes[i] += 1
                    sheet.update_cell(data.index(poll)+2, 10+i, votes[i])
                    st.success("投票ありがとうございました！")

        st.write("---")
        st.subheader("📊 投票結果")
        df = pd.DataFrame({"候補": titles, "投票数": votes})
        fig = px.bar(
            df,
            x="候補",
            y="投票数",
            text="投票数",
            color="候補",
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        fig.update_traces(textposition='outside')
        fig.update_layout(
            yaxis=dict(title="票数"),
            xaxis=dict(title="候補"),
            showlegend=False,
            margin=dict(l=20, r=20, t=20, b=20)
        )
        st.plotly_chart(fig, use_container_width=True)

# --- 新規作成ページ ---
else:
    st.title("🗳️ 新しい投票を作成")

    titles = []
    urls = []
    for i in range(4):
        st.subheader(f"候補 {i+1}")
        title = st.text_input(f"タイトル {i+1}", key=f"title_{i}")
        url = st.text_input(f"画像URL {i+1}（任意）", key=f"url_{i}")
        titles.append(title)
        urls.append(url)

    if st.button("投票ページを作成"):
        if all(titles):
            poll_id = str(uuid.uuid4())[:8]
            # URLが空でもOK
            sheet.append_row([poll_id] + [val for pair in zip(titles, urls)
                             for val in pair] + [0, 0, 0, 0])

            base_url = "https://blue-archive-vote-app.streamlit.app"
            full_url = f"{base_url}?poll_id={poll_id}"

            st.success("投票ページが作成されました！")
            st.write("下のURLをコピーして友達に共有してください👇")
            st.text_input("投票URL", full_url, key="copy_url")
        else:
            st.warning("すべてのタイトルを入力してください。")
