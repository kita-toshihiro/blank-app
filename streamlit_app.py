import streamlit as st
import ezodf
import io

# ODFのネームスペース定義（グラフ/図形の抽出用）
NS = {
    'table': 'urn:oasis:names:tc:opendocument:xmlns:table:1.0',
    'draw': 'urn:oasis:names:tc:opendocument:xmlns:drawing:1.0',
    'office': 'urn:oasis:names:tc:opendocument:xmlns:office:1.0',
    'text': 'urn:oasis:names:tc:opendocument:xmlns:text:1.0',
}

def check_ods_task(file_bytes, file_name):
    try:
        doc = ezodf.opendoc(io.BytesIO(file_bytes))
    except Exception as e:
        return [{"check": "1. ODS形式の読み込み", "status": "NG"}]

    sheets = {s.name: s for s in doc.sheets}
    found_sheets = list(sheets.keys())
    results = []

    # --- 1. 形式チェック ---
    is_ods = file_name.lower().endswith('.ods')
    results.append({"check": "1. ODS形式のファイルである", "status": "Done" if is_ods else "NG"})

    # --- 2. シート構成チェック ---
    core_required = ["sample", "data", "試験と成績", "結果"]
    sheet1_exists = "シート 1" in found_sheets or "Sheet1" in found_sheets
    all_core_exists = all(s in found_sheets for s in core_required)
    results.append({"check": "2. 指定の5つのシートを含んでいる", "status": "Done" if (all_core_exists and sheet1_exists) else "NG"})

    # ヘルパー: 指定セルの数式と値を取得 (1-indexed)
    def get_cell_info(sheet_name, row, col):
        if sheet_name not in sheets: return None, None
        try:
            cell = sheets[sheet_name].cells[(row-1, col-1)]
            return (cell.formula or "").replace(" ", "").upper(), cell.value
        except: return None, None

    # ヘルパー: シート内にグラフ（draw:frame）があるかチェック
    def has_chart(sheet_name):
        if sheet_name not in sheets: return False
        # xmlnode内から draw:frame を探す
        frames = sheets[sheet_name].xmlnode.findall(f".//{{{NS['draw']}}}frame")
        return len(frames) > 0

    # --- 3. グラフ（結果シート） ---
    results.append({"check": "3. シート「結果」にグラフがある", "status": "Done" if has_chart("結果") else "NG"})

    # --- 4. 試験と成績 D34: AVERAGE ---
    f, v = get_cell_info("試験と成績", 34, 4)
    results.append({"check": "4. D34にAVERAGE関数がある", "status": "Done" if f and "AVERAGE" in f else "NG"})

    # --- 5. 試験と成績 K46: IF(D46>=$D$12, $H$9, $H$10) ---
    f, v = get_cell_info("試験と成績", 46, 11)
    cond5 = f and "IF" in f and "D46" in f and "$D$12" in f
    results.append({"check": "5. K46にIF関数の判定式がある", "status": "Done" if cond5 else "NG"})

    # --- 6. 試験と成績 R46: COUNT(D46:J46) ---
    f, v = get_cell_info("試験と成績", 46, 18)
    cond6 = f and "COUNT" in f and "D46" in f and "J46" in f
    results.append({"check": "6. R46にCOUNT関数の数式がある", "status": "Done" if cond6 else "NG"})

    # --- 7. R46の結果が7 ---
    results.append({"check": "7. R46の計算結果が7である", "status": "Done" if v == 7 else "NG"})

    # --- 8. S46: COUNTIF(K46:Q46, $H$9) ---
    f, v = get_cell_info("試験と成績", 46, 19)
    cond8 = f and "COUNTIF" in f and "K46" in f and "$H$9" in f
    results.append({"check": "8. S46にCOUNTIF関数の数式がある", "status": "Done" if cond8 else "NG"})

    # --- 9. T46: ROUND(AVERAGE(D46:J46),0) ---
    f, v = get_cell_info("試験と成績", 46, 20)
    cond9 = f and "ROUND" in f and "AVERAGE" in f
    results.append({"check": "9. T46にROUND(AVERAGE)の数式がある", "status": "Done" if cond9 else "NG"})

    # --- 10. U46: IF(S46>=R46*$F$21,T46,$G$22) ---
    f, v = get_cell_info("試験と成績", 46, 21)
    cond10 = f and "IF" in f and "S46" in f and "R46" in f
    results.append({"check": "10. U46に合格判定のIF数式がある", "status": "Done" if cond10 else "NG"})

    # --- 11. U46がS46を参照 ---
    results.append({"check": "11. U46の数式がS46を参照している", "status": "Done" if f and "S46" in f else "NG"})

    # --- 12. 試験と成績シートにグラフがある ---
    results.append({"check": "12. 「試験と成績」の表付近にグラフがある", "status": "Done" if has_chart("試験と成績") else "NG"})

    return results

# --- Streamlit 表示部分 ---
st.set_page_config(page_title="ODS 課題チェック", layout="wide")

st.title("📊 ODS 課題自動判定")
uploaded_file = st.file_uploader("ODSファイルをアップロード", type=["ods"])

if uploaded_file:
    check_results = check_ods_task(uploaded_file.read(), uploaded_file.name)
    
    # スコア計算
    done_count = sum(1 for item in check_results if item["status"] == "Done")
    st.subheader(f"判定スコア: {done_count} / 12")
    
    # テーブル形式で結果表示
    cols = st.columns(2)
    for i, item in enumerate(check_results):
        target_col = cols[i % 2]
        with target_col.container():
            c1, c2 = st.columns([4, 1])
            c1.info(item["check"]) if item["status"] == "Done" else c1.warning(item["check"])
            if item["status"] == "Done":
                c2.success("Done")
            else:
                c2.error("NG")

    if done_count == 12:
        st.balloons()
