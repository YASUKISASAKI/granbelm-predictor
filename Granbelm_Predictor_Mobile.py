# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

st.set_page_config(page_title="グランベルム GSheets版", layout="centered")
st.title("📊 グランベルム 2択予想ツール（Google Sheets連携版）")

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

# --- データ読み書き関数 ---
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

# --- UI部分 ---
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

st.subheader("📑 現在の履歴（Google Sheets）")
st.dataframe(df, use_container_width=True)
