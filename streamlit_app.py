import streamlit as st
import ezodf
import io

# グラフ判定用のネームスペース
NS = {'draw': 'urn:oasis:names:tc:opendocument:xmlns:drawing:1.0'}

def get_check_results(file_bytes, file_name):
    # 判定用の変数初期化
    is_parsed = False
    doc = None
    sheets = {}
    
    # --- 内部構造のチェック (中身が本当に ODS か) ---
    try:
        doc = ezodf.opendoc(io.BytesIO(file_bytes))
        sheets = {s.name: s for s in doc.sheets}
        is_parsed = True
    except Exception:
        is_parsed = False

    def get_cell_safe(s_name, r, c):
        if s_name not in sheets: return "シートなし", None
        sheet = sheets[s_name]
        if r > sheet.nrows() or c > sheet.ncols(): return "範囲外", None
        try:
            cell = sheet[r-1, c-1]
            f = (cell.formula or "").replace(" ", "").upper()
            v = cell.value
            return f, v
        except: return "エラー", None

    def has_chart(s_name):
        if not is_parsed or s_name not in sheets: return False
        return len(sheets[s_name].xmlnode.findall(f".//{{{NS['draw']}}}frame")) > 0

    # 中身が解析できていれば各セルの情報を取得
    f_d34, v_d34 = get_cell_safe("試験と成績", 34, 4)
    f_k46, v_k46 = get_cell_safe("試験と成績", 46, 11)
    f_r46, v_r46 = get_cell_safe("試験と成績", 46, 18)
    f_s46, v_s46 = get_cell_safe("試験と成績", 46, 19)
    f_t46, v_t46 = get_cell_safe("試験と成績", 46, 20)
    f_u46, v_u46 = get_cell_safe("試験と成績", 46, 21)

    # 12項目の判定リスト
    checks = [
        ("1. ODS形式 (ファイル構造の検証)", is_parsed and file_name.lower().endswith('.ods'), 
         "解析成功" if is_parsed else "解析失敗 (ODS形式ではありません)"),
        ("2. 5つのシート構成", is_parsed and all(s in sheets for s in ["sample", "data", "試験と成績", "結果"]), 
         f"確認: {', '.join(list(sheets.keys())[:5])}..." if is_parsed else "不可"),
        ("3. 「結果」のグラフ", has_chart("結果"), "あり" if has_chart("結果") else "なし"),
        ("4. D34: 関数", "AVERAGE" in f_d34, f_d34 if f_d34 else v_d34),
        ("5. K46: 判定式", "IF" in f_k46 and "D46" in f_k46 and "$D$12" in f_k46, f_k46),
        ("6. R46: COUNT関数", "COUNT" in f_r46 and "D46" in f_r46, f_r46),
        ("7. R46: 結果が7", v_r46 == 7 or v_r46 == 7.0, f"値: {v_r46}"),
        ("8. S46: COUNTIF関数", "COUNTIF" in f_s46 and "$H$9" in f_s46, f_s46),
        ("9. T46: ROUND,AVERAGE", "ROUND" in f_t46 and "AVERAGE" in f_t46, f_t46),
        ("10. U46: 合格判定", "IF" in f_u46 and "S46" in f_u46 and "R46" in f_u46, f_u46),
        ("11. U46: 参照", "S46" in f_u46, f_u46),
        ("12. 「試験と成績」のグラフ", has_chart("試験と成績"), "あり" if has_chart("試験と成績") else "なし"),
    ]
    
    return [{"項目": c[0], "判定": "✔" if c[1] else "NG", "実際の内容/数式": str(c[2])} for c in checks]

# --- UI ---
st.set_page_config(page_title="ODS Checker", layout="wide")
st.title("📊 課題3のファイル提出前の最低限のチェック")
st.write("### このサイトで課題3の提出はできません。\n \n 最低限の条件をクリアするかどうか、課題３のファイルをチェックするためのサイトです。")
st.write("このサイトでの判定結果のスクリーンショット画像を撮って、課題3のファイルをMoodle上で提出するときにその画像も添付してください。")
st.write("（12個全部をクリアしなくても、課題3の提出は可能です。ただしNG評価を受ける可能性が高いです）")

uploaded_file = st.file_uploader("ODSファイルをアップロード", type=["ods"], label_visibility="collapsed")

if uploaded_file:
    # 判定実行
    res = get_check_results(uploaded_file.read(), uploaded_file.name)
    
    if res:
        score = sum(1 for r in res if r["判定"] == "✔")
        st.subheader(f"クリア項目数: {score} / 12")
        
        # 結果テーブル
        st.table(res)
        
        if score == 12:
            st.balloons()
            st.success("全ての最低限のチェックをクリアしました！")
    else:
        st.error("判定処理中に致命的なエラーが発生しました。")
