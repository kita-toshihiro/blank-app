import streamlit as st
import ezodf
import io

# グラフ判定用のネームスペース
NS = {'draw': 'urn:oasis:names:tc:opendocument:xmlns:drawing:1.0'}

def get_check_results(file_bytes, file_name):
    try:
        doc = ezodf.opendoc(io.BytesIO(file_bytes))
        sheets = {s.name: s for s in doc.sheets}
    except:
        return None

    def get_cell_safe(s_name, r, c):
        """指定したセルの数式と値を安全に取得 (r, c は 1-indexed)"""
        if s_name not in sheets: return "", None
        sheet = sheets[s_name]
        # ezodfは sheet[row, col] でアクセス。範囲外チェック。
        if r > sheet.nrows() or c > sheet.ncols():
            return "", None
        try:
            cell = sheet[r-1, c-1]
            return (cell.formula or "").replace(" ", "").upper(), cell.value
        except:
            return "", None

    def has_chart(s_name):
        if s_name not in sheets: return False
        return len(sheets[s_name].xmlnode.findall(f".//{{{NS['draw']}}}frame")) > 0

    # 各セルの情報を取得
    f_d34, _ = get_cell_safe("試験と成績", 34, 4)
    f_k46, _ = get_cell_safe("試験と成績", 46, 11)
    f_r46, v_r46 = get_cell_safe("試験と成績", 46, 18)
    f_s46, _ = get_cell_safe("試験と成績", 46, 19)
    f_t46, _ = get_cell_safe("試験と成績", 46, 20)
    f_u46, _ = get_cell_safe("試験と成績", 46, 21)

    # 12項目の判定リスト
    checks = [
        ("1. ODS形式である", file_name.lower().endswith('.ods')),
        ("2. 指定の5シートが存在する", all(s in sheets for s in ["sample", "data", "試験と成績", "結果"]) and ("シート 1" in sheets or "Sheet1" in sheets)),
        ("3. 「結果」にグラフがある", has_chart("結果")),
        ("4. D34 に AVERAGE 関数", "AVERAGE" in f_d34),
        ("5. K46 に IF 判定式", "IF" in f_k46 and "D46" in f_k46 and "$D$12" in f_k46),
        ("6. R46 に COUNT 関数", "COUNT" in f_r46 and "D46" in f_r46),
        ("7. R46 の計算結果が 7", v_r46 == 7 or v_r46 == 7.0),
        ("8. S46 に COUNTIF 関数", "COUNTIF" in f_s46 and "$H$9" in f_s46),
        ("9. T46 に ROUND と AVERAGE", "ROUND" in f_t46 and "AVERAGE" in f_t46),
        ("10. U46 に IF 合格判定式", "IF" in f_u46 and "S46" in f_u46 and "R46" in f_u46),
        ("11. U46 が S46 を参照している", "S46" in f_u46),
        ("12. 「試験と成績」にグラフがある", has_chart("試験と成績")),
    ]
    
    return [{"No": i+1, "項目": c[0], "判定": "Done" if c[1] else "NG"} for i, c in enumerate(checks)]

# --- Streamlit UI ---
st.set_page_config(page_title="ODS Checker", layout="centered")
st.title("📊 ODS 課題判定")

uploaded_file = st.file_uploader("ODSファイルをアップロード", type=["ods"], label_visibility="collapsed")

if uploaded_file:
    res = get_check_results(uploaded_file.read(), uploaded_file.name)
    if res:
        score = sum(1 for r in res if r["判定"] == "Done")
        st.subheader(f"クリア数: {score} / 12")
        st.table(res)
        if score == 12: st.balloons()
    else:
        st.error("ファイルを読み込めませんでした。")
