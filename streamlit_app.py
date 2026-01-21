import streamlit as st
import random
import csv
import os
from datetime import datetime
from words import WORDS

# =======================
# 設定
# =======================
st.set_page_config(
    page_title="TOEIC600 英単語クイズ",
    layout="centered"
)

ANSWER_FILE = "answers.csv"

# =======================
# CSV 初期化
# =======================
def init_answer_file():
    with open(ANSWER_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp", "word", "selected", "correct", "is_correct"])

if not os.path.exists(ANSWER_FILE):
    init_answer_file()

# =======================
# リセット処理
# =======================
def reset_answers():
    init_answer_file()

# =======================
# セッション初期化
# =======================
if "question" not in st.session_state:
    st.session_state.question = random.choice(WORDS)

# =======================
# UI
# =======================
st.title("📘 TOEIC600 英単語クイズ")
st.write("TOEIC600点を目指して、英単語200語をマスターしよう！")

q = st.session_state.question

# -----------------------
# クイズ表示
# -----------------------
st.subheader(f"英単語： **{q['word']}**")

choice = st.radio(
    "意味を選んでください",
    q["choices"],
    key="choice"
)

if st.button("解答する"):
    is_correct = choice == q["answer"]

    if is_correct:
        st.success("正解！ 🎉")
    else:
        st.error(f"不正解 😢 正解：{q['answer']}")

    # 解答を保存
    with open(ANSWER_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            datetime.now().isoformat(),
            q["word"],
            choice,
            q["answer"],
            is_correct
        ])

    # 次の問題
    st.session_state.question = random.choice(WORDS)
    st.rerun()

# =======================
# 間違えた単語一覧
# =======================
st.divider()
st.subheader("❌ 間違えた単語一覧")

# リセットボタン
if st.button("🗑 間違えた単語一覧をリセット"):
    reset_answers()
    st.success("間違えた単語一覧をリセットしました")
    st.rerun()

# 間違えた単語を集計
wrong_words = {}

with open(ANSWER_FILE, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row["is_correct"] == "False":
            wrong_words[row["word"]] = row["correct"]

# 表示
if wrong_words:
    for word, meaning in sorted(wrong_words.items()):
        st.write(f"- **{word}** ： {meaning}")
else:
    st.write("まだ間違いはありません 👍")
