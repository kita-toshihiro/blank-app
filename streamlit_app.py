import streamlit as st
import ezodf
import io
import datetime  # スケジュール表示用に追加
from datetime import timezone, timedelta  # タイムゾーン設定用に追加
import time      # アニメーション演出用
import hashlib

# グラフ判定用のネームスペース
NS = {'draw': 'urn:oasis:names:tc:opendocument:xmlns:drawing:1.0'}

def get_check_results(file_bytes, file_name):
    # 判定用の変数初期化
    is_parsed = False
    doc = None
    sheets = {}
    
    # --- 内部構造のチェック ---
    try:
        doc = ezodf.opendoc(io.BytesIO(file_bytes))
        sheets = {s.name: s for s in doc.sheets}
        is_parsed = True
    except Exception:
        is_parsed = False

    def get_cell_info(s_name, r, c):
        if not is_parsed or s_name not in sheets: 
            return "", None
        sheet = sheets[s_name]
        # ezodfのnrows/ncolsはデータがある範囲を返すため、指定セルが範囲外でもエラーにならないよう制御
        try:
            cell = sheet[r-1, c-1]
            # 数式は先頭に [=] がつく場合があるため、正規化
            f = (cell.formula or "").replace(" ", "").upper()
            v = cell.value
            return f, v
        except: 
            return "", None

    def has_chart(s_name):
        if not is_parsed or s_name not in sheets: return False
        # draw:frame 要素を探す（グラフや画像が含まれる場合に反応）
        return len(sheets[s_name].xmlnode.findall(f".//{{{NS['draw']}}}frame")) > 0

    # 必要なセル情報の取得
    f_d34, v_d34 = get_cell_info("試験と成績", 34, 4)   # D34
    f_k46, v_k46 = get_cell_info("試験と成績", 46, 11)  # K46
    f_r46, v_r46 = get_cell_info("試験と成績", 46, 18)  # R46
    f_s46, v_s46 = get_cell_info("試験と成績", 46, 19)  # S46
    f_t46, v_t46 = get_cell_info("試験と成績", 46, 20)  # T46
    f_u46, v_u46 = get_cell_info("試験と成績", 46, 21)  # U46

    # --- 12項目の判定ロジック ---
    
    # 2. シート名チェック
    required_fixed = ["sample", "data", "試験と成績", "結果"]
    has_fixed = all(s in sheets for s in required_fixed)
    has_sheet1 = "シート 1" in sheets or "Sheet1" in sheets or "シート１" in sheets or "シート1" in sheets
    check2 = is_parsed and has_fixed and has_sheet1
    found_sheets_names = ", ".join(sheets.keys()) if sheets else "シートなし"
    
    # リスト定義 (項目名, 判定式, 詳細情報)
    checks = [
        ("1. ODS形式である", is_parsed and file_name.lower().endswith('.ods'), file_name),
        ("2. 指定の5つのシートを含んでいる", check2, found_sheets_names),
        ("3. 「結果」にグラフがある", has_chart("結果"), "draw:frameの有無"),
        ("4. 「試験と成績」D34に数式がある", f_d34 != "", f_d34),
        ("5. 「試験と成績」K46に判定式がある", "IF" in f_d34 or "IF" in f_k46, f_k46),
        ("6. 「試験と成績」R46にCOUNT関数がある", "COUNT" in f_r46, f_r46),
        ("7. 「試験と成績」R46の結果が7である", v_r46 == 7 or v_r46 == 7.0, f"現在の値: {v_r46}"),
        ("8. 「試験と成績」S46にCOUNTIF関数がある", "COUNTIF" in f_s46, f_s46),
        ("9. 「試験と成績」T46にROUNDとAVERAGE関数がある", "ROUND" in f_t46 and "AVERAGE" in f_t46, f_t46),
        ("10. 「試験と成績」U46に判定式がある", "IF" in f_u46, f_u46),
        ("11. 「試験と成績」U46に数式がある", f_u46 != "", f_u46),
        ("12. 「試験と成績」にグラフがある", has_chart("試験と成績"), "draw:frameの有無")
    ]
    
    return [
        {
            "No": i + 1,
            "チェック項目": c[0],
            "判定": "✔" if c[1] else "NG",
            # バッククォートで囲むことで、$記号が数式として解釈されるのを防ぎます
            "内容/数式": f"`{str(c[2])}`" if c[2] else ""
        }
        for i, c in enumerate(checks)
    ]

# --- Streamlit UI ---
st.set_page_config(page_title="ODS Checker", layout="wide")

st.title("📊 ３ブロック課題ファイル提出前の最低限のチェック")
st.info("このサイトは、３ブロック課題の提出ファイルが最低限の体裁を持っているか確認するためのツールです。ここで３ブロック課題の**提出はできません。**")

uploaded_file = st.file_uploader("３ブロック課題のODSファイルをアップロードしてください", type=["ods"])

if uploaded_file:
    # バイナリを読み込み
    file_bytes = uploaded_file.read()
    res = get_check_results(file_bytes, uploaded_file.name)
    
    if res:
        score = sum(1 for r in res if r["判定"] == "✔")
        
        # スコア表示
        if score == 12:
            st.success(f"🎉 最低限のチェック完了（{score}/12)。あとは３ブロック課題チェックリストの**Doneの条件をよく読みチェックしてから**提出してください。")
            st.balloons()
        elif score >= 8:
            st.warning(f"💡 あと少しです。 テキストを良く読んでください。クリア項目数: {score} / 12")
        else:
            st.error(f"⚠️ 修正が必要です。 テキストを良く読んでください。クリア項目数: {score} / 12")
        
        # 結果のテーブル表示
        st.dataframe(res, use_container_width=True, height=460)
        #st.table(res)
        
        # st.write("---")
   
        # --- 結果表示セクション ---
        
        # 学籍番号入力を先に判定するために位置を調整
        with st.container(border=True):
            col1, col2 = st.columns([1, 1])
            with col1:
                user_id = st.text_input("あなたの学籍番号を入力してエンターキーを押してください。", placeholder="例: 262v1234")
            with col2:
                JST = timezone(timedelta(hours=+9), 'JST')
                now = datetime.datetime.now(JST)
                current_time = now.strftime("%Y-%m-%d %H:%M:%S")
                st.metric("判定実行時刻 (JST)", current_time)

        if user_id:
            # 1. 透かし情報の生成
            v_code = hashlib.md5(f"{user_id}{current_time}".encode()).hexdigest()[:6].upper()
            watermark_str = ((f"OFFICIAL CHECKER {v_code} " * 12) + "<br>") * 80 # 表をカバーするため多めに生成

            # 2. 結果リスト(res)をHTMLのテーブルに変換
            table_html = """
            <table style="width:100%; border-collapse: collapse; font-family: sans-serif; font-size: 0.9rem;">
                <thead>
                    <tr style="background-color: rgba(200, 200, 200, 0.3);">
                        <th style="border: 1px solid #ddd; padding: 8px;">No</th>
                        <th style="border: 1px solid #ddd; padding: 8px;">チェック項目</th>
                        <th style="border: 1px solid #ddd; padding: 8px;">判定</th>
                        <th style="border: 1px solid #ddd; padding: 8px;">内容/数式</th>
                    </tr>
                </thead>
                <tbody>
            """
            for r in res:
                color = "#d32f2f" if r["判定"] == "NG" else "#2e7d32"
                table_html += f"""<tr>
                        <td style="border: 1px solid #ddd; padding: 8px; text-align: center;">{r['No']}</td>
                        <td style="border: 1px solid #ddd; padding: 8px;">{r['チェック項目']}</td>
                        <td style="border: 1px solid #ddd; padding: 8px; text-align: center; font-weight: bold; color: {color};">{r['判定']}</td>
                        <td style="border: 1px solid #ddd; padding: 8px; font-family: monospace;">{r['内容/数式']}</td>
                    </tr>"""
            table_html += "</tbody></table>"

            # 3. 透かし背景付きコンテナにテーブルとシグネチャを配置
            st.markdown(f"""
            <div style="
                position: relative;
                background: #ffffff;
                padding: 20px;
                border-radius: 10px;
                border: 5px solid #ccc;
                overflow: hidden;
            ">
                <div style="
                    position: absolute;
                    top: -1600px;
                    left: -1200px;
                    width: 600%;
                    height: 200%;
                    transform: rotate(-15deg);
                    opacity: 0.07; 
                    font-size: 24px;
                    font-weight: bold;
                    line-height: 1.5;
                    pointer-events: none;
                    z-index: 0;
                ">
                    {watermark_str}
                </div>
                <div style="position: relative; z-index: 1;">
                    <div style="text-align: center; margin-bottom: 10px; border-bottom: 2px solid #eee; padding-bottom: 5px;">
                        <p style="margin: 0; font-weight: bold; color: #444;">【チェック証明書】</p>
                        <h4 style="margin: 2px 0; color: #1565c0;">学籍番号: {user_id}</h4>
                        <p style="font-size: 1.2rem; color: #666;">CHKID: {v_code} / Time: {current_time}</p>
                    </div>                    
                    {table_html}
                </div>
            </div>
            """, unsafe_allow_html=True)
            st.write("📸 **スクショの範囲**: 上の**【チェック証明書】**（透かしが入った領域）のスクリーンショット画像を撮り、３ブロック課題の提出時に添付してください。")
            
        else:
            # 学籍番号未入力時は通常のテーブルを表示
            st.info("👆 学籍番号を入力すると、透かし入りのチェック証明書が表示されます。")
            # st.dataframe(res, use_container_width=True, height=460)
