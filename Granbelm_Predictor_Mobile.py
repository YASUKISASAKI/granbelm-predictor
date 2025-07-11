# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder

st.set_page_config(page_title="グランベルム 2択予想ツール", layout="centered")

st.title("🧠 グランベルム 2択予想ツール（モバイル版）")

@st.cache_data
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
    df["is_magic"] = (df["role"] == "魔力目").astype(int)
    df["prev_1st"] = df["1st"].shift(1).fillna(1).astype(int)
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

def predict_second_candidate(f1, df):
    model = train_model(df)
    if model is None:
        return "学習データが不足しています"

    # 前回1stを履歴から自動取得
    try:
        prev_nav = df["nav"].iloc[-1]
        prev_1st = int(str(prev_nav)[0])
    except:
        prev_1st = 1

    best_prob = -1
    best_2nd = None
    for f2 in [1, 2, 3]:
        if f2 == f1:
            continue
        for f3 in [1, 2, 3]:
            if f3 in (f1, f2):
                continue
            X_test = np.array([[f1, f2, f3, prev_1st]])
            prob = model.predict_proba(X_test)[0][1]
            if prob > best_prob:
                best_prob = prob
                best_2nd = f2
    return best_2nd

# --- メイン処理 ---
df = load_history()

st.subheader("✍️ 押し順履歴をボタンで追加")
role = st.selectbox("成立役", ["魔力目", "ベル", "リプレイ"], key="role_input")

cols = st.columns(3)
orders = ["123", "132", "213", "231", "312", "321"]
for i, o in enumerate(orders):
    if cols[i % 3].button(o):
        df = pd.concat([df, pd.DataFrame([[o, role]], columns=["nav", "role"])], ignore_index=True)
        save_history(df)
        st.success(f"{o} を追加しました")

st.subheader("🔮 魔力目 成立予測モード")
f1 = st.selectbox("1stナビを選択", [1, 2, 3], key="f1")

if st.button("🧠 AIで2ndナビ候補を予測"):
    if f1 is None:
        st.warning("1stナビを選択してください。")
    else:
        try:
            suggestion = predict_second_candidate(f1, df)
            st.success(f"AI推奨の2ndナビ候補は：{suggestion}")
        except Exception as e:
            st.error(f"エラーが発生しました: {e}")

st.subheader("📜 履歴一覧")
st.dataframe(df, use_container_width=True)
