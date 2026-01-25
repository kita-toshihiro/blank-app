import streamlit as st

# ページ設定
st.set_page_config(page_title="動画学習クイズアプリ", layout="wide")

# --- サイドバー (チェックリスト A-F) ---
with st.sidebar:
    st.header("📋 完了チェックリスト")
    st.write("各項目を確認してください：")
    
    # チェックボックスの作成
    item_a = st.checkbox("項目 A: 導入部分の理解")
    item_b = st.checkbox("項目 B: 基本用語の把握")
    item_c = st.checkbox("項目 C: デモの確認")
    item_d = st.checkbox("項目 D: 応用例の検討")
    item_e = st.checkbox("項目 E: 数式の理解")
    item_f = st.checkbox("項目 F: まとめ")

    # 進捗率の表示（おまけ）
    checks = [item_a, item_b, item_c, item_d, item_e, item_f]
    progress = sum(checks) / len(checks)
    st.progress(progress)
    st.write(f"進捗率: {int(progress * 100)}%")

# --- メインエリア (動画とクイズ) ---
st.title("🎥 動画でクイズ学習")

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("動画を視聴")
    # YouTube動画の埋め込み (サンプルURL)
    video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ" 
    st.video(video_url)

with col2:
    st.subheader("✍️ クイズ")
    q1 = st.radio(
        "動画の内容に関する質問：〇〇の正解は？",
        ["選択肢 1", "選択肢 2", "選択肢 3"]
    )
    
    if st.button("回答する"):
        if q1 == "選択肢 1":
            st.success("正解です！")
        else:
            st.error("残念！もう一度動画を見てみましょう。")
