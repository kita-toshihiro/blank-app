import streamlit as st
import random
import csv
import os
from datetime import datetime
from words import WORDS

st.set_page_config(page_title="TOEIC600 単語クイズ", layout="centered")

ANSWER_FILE = "answers.csv"

# -----------------------
# CSV 初期化
# -----------------------
if not os.path.exists(ANSWER_FILE):
    with open(ANSWER_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp", "word", "selected", "correct", "is_correct"])

# -----------------------
# セッション初期化
# -----------------------
if "question" not in st.session_state:
    st.session_state.question = random.choice(WORDS)

# -----------------------
# タイトル
# -----------------------
st.title("📘 TOEIC600 英単語クイズ")
st.write("1問ずつ解いて、苦手単語を克服しよう！")

q = st.session_state.question

# -----------------------
# クイズ表示
# -----------------------
st.subheader(f"英単語： **{q['word']}**")

choice = st.radio("意味を選んでください", q["choices"])

if st.button("解答する"):
    is_correct = choice == q["answer"]

    # 結果表示
    if is_correct:
        st.success("正解！ 🎉")
    else:
        st.error(f"不正解 😢 正解：{q['answer']}")

    # CSVに保存
    with open(ANSWER_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            datetime.now().isoformat(),
            q["word"],
            choice,
            q["answer"],
            is_correct
        ])

    # 次の問題へ
    st.session_state.question = random.choice(WORDS)
    st.rerun()

# -----------------------
# 間違えた単語一覧
# -----------------------
st.divider()
st.subheader("❌ 間違えた単語一覧")

wrong_words = {}

with open(ANSWER_FILE, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row["is_correct"] == "False":
            wrong_words[row["word"]] = row["correct"]

if wrong_words:
    for w, meaning in wrong_words.items():
        st.write(f"- **{w}** ： {meaning}")
else:
    st.write("まだ間違いはありません 👍")
