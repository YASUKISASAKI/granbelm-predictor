# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder

st.set_page_config(page_title="グランベルム 2択予想ツール", layout="centered")
st.title("グランベルム 2択予想ツール（モバイル対応版）")

def load_history():
    try:
        return pd.read_csv("Granbelm history.csv")
    except FileNotFoundError:
        return pd.DataFrame(columns=["nav", "role"])

def save_history(df):
    df.to_csv("Granbelm history.csv", index=False)

def create_features(df):
    df = df.copy()
    df["1st"] = df["nav"].astype(str).str[0].astype(int)
    df["2nd"] = df["nav"].astype(str).str[1].astype(int)
    df["3rd"] = df["nav"].astype(str).str[2].astype(int)
    df["role_encoded"] = LabelEncoder().fit_transform(df["role"])
    df["prev_1st"] = df["nav"].shift(1).fillna("000").astype(str).str[0].astype(int)
    df["is_magic"] = (df["role"] == "魔力目").astype(int)
    return df

def train_model(df):
    if df.empty:
        return None
    df = create_features(df)
    X = df[["1st", "2nd", "3rd", "prev_1st"]]
    y = df["is_magic"]
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X, y)
    return model

def predict_magic(df, first, second, third, model):
    prev_lst = int(df["nav"].iloc[-1][0]) if not df.empty else 1
    X_test = np.array([[int(first), int(second), int(third), prev_lst]])
    prob = model.predict_proba(X_test)[0][1]
    return round(prob * 100, 1)

df = load_history()
model = train_model(df)

st.subheader("📥 OCR履歴のインポート")
uploaded_file = st.file_uploader("CSVファイルをアップロード", type=["csv"])
if uploaded_file is not None:
    try:
        ocr_df = pd.read_csv(uploaded_file)
        if set(["nav", "role"]).issubset(ocr_df.columns):
            df = pd.concat([df, ocr_df], ignore_index=True)
            save_history(df)
            st.success("OCRデータをインポートしました")
        else:
            st.error("CSVに 'nav' と 'role' の列が必要です")
    except Exception as e:
        st.error(f"読み込みエラー: {e}")

st.subheader("➕ 押し順履歴をボタンで追加")
col1, col2 = st.columns(2)
with col1:
    role = st.selectbox("成立役", ["魔力目", "ベル", "リプレイ"])

押し順一覧 = ["123", "132", "213", "231", "312", "321"]
for i in range(0, len(押し順一覧), 3):
    cols = st.columns(3)
    for j in range(3):
        if i + j < len(押し順一覧):
            with cols[j]:
                if st.button(押し順一覧[i + j]):
                    new_row = pd.DataFrame([[押し順一覧[i + j], role]], columns=["nav", "role"])
                    df = pd.concat([df, new_row], ignore_index=True)
                    save_history(df)
                    st.success(f"押し順 {押し順一覧[i + j]} を追加しました")

st.subheader("🔮 魔力目 成立予測モード")
f1 = st.selectbox("1stナビを選択", [1, 2, 3])
if st.button("🧠 AIで2ndナビ候補を予測"):
    second_probs = {}
    for f2 in [1, 2, 3]:
        if f2 != f1 and f2 != f3:
            prob = predict_magic(df, f1, f2, model)
            second_probs[f2] = prob
    if second_probs:
        best = max(second_probs, key=second_probs.get)
        st.success(f"おすすめの2ndナビは **{best}**（魔力目成立確率：{second_probs[best]}%）")
    else:
        st.warning("2ndナビ候補が見つかりません")

st.subheader("📑 履歴一覧")
st.dataframe(df, use_container_width=True)
