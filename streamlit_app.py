import streamlit as st
import pandas as pd

st.set_page_config(page_title="クイズ作成ツール", layout="wide")

# --- サイドバー (チェックリスト A-F) ---
with st.sidebar:
    st.header("📋 確認項目")
    # シンプルなチェックボックス（進捗率は削除）
    for label in ["A", "B", "C", "D", "E", "F"]:
        st.checkbox(f"項目 {label}")

# --- メインエリア ---
st.title("🎥 動画クイズ・エディター")

# 動画表示エリア
st.video("https://www.youtube.com/watch?v=dQw4w9WgXcQ") # サンプルURL

st.divider()

# --- クイズ作成フォーム ---
st.subheader("📝 クイズ案の作成")

with st.form("quiz_form"):
    question = st.text_input("問題文を入力してください", placeholder="例：動画内で紹介された手法の名前は？")
    
    col1, col2 = st.columns(2)
    with col1:
        choice_a = st.text_input("選択肢 A")
        choice_b = st.text_input("選択肢 B")
    with col2:
        choice_c = st.text_input("選択肢 C")
        correct_ans = st.selectbox("正解を選択", ["A", "B", "C"])

    # フォーム内の送信ボタン
    submitted = st.form_submit_button("作成したクイズを確定する")

# --- 保存処理 ---
if submitted:
    # データをデータフレームにまとめる
    quiz_data = {
        "問題": [question],
        "選択肢A": [choice_a],
        "選択肢B": [choice_b],
        "選択肢C": [choice_c],
        "正解": [correct_ans]
    }
    df = pd.DataFrame(quiz_data)
    
    st.success("クイズ案を確定しました！下のボタンからダウンロードできます。")
    st.table(df) # プレビュー表示

    # CSVとしてダウンロードするボタン
    csv = df.to_csv(index=False).encode('utf-8-sig') # Shift-JIS環境(Excel)でも化けないようにsig付与
    st.download_button(
        label="📥 CSVとして保存（ダウンロード）",
        data=csv,
        file_name="my_quiz_draft.csv",
        mime="text/csv",
    )
