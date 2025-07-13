# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

st.set_page_config(page_title="グランベルム GSheets予測ツール", layout="centered")
st.title("🔍 グランベルム GSheets版 2ndナビ予測ツール（類似履歴ロジック統合）")

# --- Google Sheets認証 ---
def auth_sheets():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive.file",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name("granbelm-predictor-9553b584d5e5.json", scope)
    client = gspread.authorize(creds)
    return client

def get_sheet():
    client = auth_sheets()
    return client.open("Granbelm_History").sheet1

# --- データ読み書き ---
def load_history():
    try:
        sheet = get_sheet()
        records = sheet.get_all_records()
        return pd.DataFrame(records)
    except Exception as e:
        st.error(f"Google Sheets 読み込みエラー: {e}")
        return pd.DataFrame(columns=["nav", "role"])

def append_history(nav, role):
    try:
        sheet = get_sheet()
        sheet.append_row([nav, role])
    except Exception as e:
        st.error(f"Google Sheets 書き込みエラー: {e}")

# --- 類似履歴予測ロジック ---
def hamming_distance(s1, s2):
    if len(s1) != len(s2):
        return float("inf")
    return sum(c1 != c2 for c1, c2 in zip(s1, s2))

def partial_match_score(nav1, nav2):
    return sum([nav1[i] == nav2[i] for i in range(3)])

def suggest_second_based_on_similarity(df, recent_df, selected_1st):
    pattern_counts = recent_df["nav"].dropna().astype(str).value_counts()
    if pattern_counts.empty:
        return None, 0.0
    common_patterns = pattern_counts.head(10).index.tolist()

    scored_rows = []
    for _, row in df.iterrows():
        nav_str = str(row["nav"])
        if len(nav_str) != 3:
            continue
        if nav_str[0] != str(selected_1st):
            continue
        max_score = 0
        for recent_nav in common_patterns:
            if not isinstance(recent_nav, str):
                continue
            if len(nav_str) == len(recent_nav):
                h_score = max(0, 3 - hamming_distance(nav_str, recent_nav))
                p_score = partial_match_score(nav_str, recent_nav)
                total = h_score + p_score
                max_score = max(max_score, total)
        scored_rows.append((nav_str, row["role"], max_score))

    if not scored_rows:
        return None, 0.0

    sim_df = pd.DataFrame(scored_rows, columns=["nav", "role", "sim_score"])
    sim_df = sim_df.sort_values(by="sim_score", ascending=False).head(20)
    sim_df["2nd"] = sim_df["nav"].astype(str).str[1].astype(int)
    success_rates = sim_df.groupby("2nd")["role"].apply(lambda x: (x == "魔力目").mean())
    if success_rates.empty:
        return None, 0.0
    best_2nd = success_rates.idxmax()
    confidence = round(success_rates.max() * 100, 1)
    return best_2nd, confidence

# --- Streamlit UI ---
df = load_history()

st.subheader("➕ 押し順履歴を追加（Google Sheetsに保存）")
col1, col2 = st.columns(2)
with col1:
    role = st.selectbox("成立役", ["魔力目", "ベル", "リプレイ"])
押し順一覧 = ["123", "132", "213", "231", "312", "321"]
for i in range(0, len(押し順一覧), 3):
    cols = st.columns(3)
    for j in range(3):
        if i + j < len(押し順一覧):
            with cols[j]:
                nav = 押し順一覧[i + j]
                if st.button(nav):
                    append_history(nav, role)
                    df = load_history()
                    st.success(f"{nav} を追加し保存しました")

st.subheader("🔮 類似履歴による予測モード")
recent_df = df.tail(10)
selected_1st = st.selectbox("現在の1stナビを選択", [1, 2, 3])
if st.button("🧠 類似履歴から2ndナビを予測"):
    if len(recent_df) < 1:
        st.warning("履歴が不足しています")
    else:
        suggestion, confidence = suggest_second_based_on_similarity(df, recent_df, selected_1st)
        if suggestion:
            st.success(f"✅ 推奨2ndナビ：{suggestion}（魔力目率：{confidence}%）")
        else:
            st.warning("十分な類似履歴が見つかりませんでした")

st.subheader("📑 現在の履歴（Google Sheets）")
st.dataframe(df, use_container_width=True)
