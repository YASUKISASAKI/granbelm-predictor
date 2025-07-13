
# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="グランベルム 類似履歴予測ツール", layout="centered")
st.title("🔍 グランベルム 類似履歴型 2ndナビ予測ツール v5.2.2（比較対象10件に固定）")

@st.cache_data
def load_history():
    try:
        return pd.read_csv("Granbelm history.csv")
    except FileNotFoundError:
        return pd.DataFrame(columns=["nav", "role"])

def save_history(df):
    df.to_csv("Granbelm history.csv", index=False)

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
    for idx, row in df.iterrows():
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

df = load_history()
st.subheader("➕ 実践履歴の追加（ボタン式）")
col1, col2 = st.columns(2)
with col1:
    role_input = st.selectbox("成立役", ["魔力目", "ベル"], key="role_select")
with col2:
    if st.button("履歴をリセット"):
        df = pd.DataFrame(columns=["nav", "role"])
        save_history(df)
        st.success("履歴をリセットしました")

navs = ["123", "132", "213", "231", "312", "321"]
nav_cols = st.columns(3)
for i, nav in enumerate(navs):
    if nav_cols[i % 3].button(nav):
        new_row = pd.DataFrame([[nav, role_input]], columns=["nav", "role"])
        df = pd.concat([df, new_row], ignore_index=True)
        save_history(df)
        st.success(f"{nav} を追加しました")

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

st.subheader("📜 履歴一覧（Granbelm history.csv）")
st.dataframe(df.tail(30), use_container_width=True)
