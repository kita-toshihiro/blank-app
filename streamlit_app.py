import streamlit as st
import ezodf
import io
import re

def check_ods_task(file_bytes, file_name):
    try:
        doc = ezodf.opendoc(io.BytesIO(file_bytes))
    except Exception as e:
        return [{"check": "ファイル解析エラー", "status": "NG", "detail": str(e)}]

    sheets = {s.name: s for s in doc.sheets}
    found_sheets = list(sheets.keys())
    results = []

    # --- 1. 形式チェック ---
    is_ods = file_name.lower().endswith('.ods')
    results.append({"check": "1. OpenDocument Spreadsheet 形式(ODS 形式)である", "status": "Done" if is_ods else "NG"})

    # --- 2. シート構成チェック ---
    core_required = ["sample", "data", "試験と成績", "結果"]
    sheet1_exists = "シート 1" in found_sheets or "Sheet1" in found_sheets
    all_core_exists = all(s in found_sheets for s in core_required)
    results.append({"check": "2. 5つのシート（sample, data, シート 1, 試験と成績, 結果）を含む", "status": "Done" if (all_core_exists and sheet1_exists) else "NG"})

    # --- ヘルパー関数: 数式と値の取得 ---
    def get_cell_info(sheet_name, row, col):
        # row, col は 1-indexed (A1 = 1, 1)
        if sheet_name not in sheets:
            return None, None
        try:
            cell = sheets[sheet_name].cells[(row-1, col-1)]
            return (cell.formula or "").replace(" ", ""), cell.value
        except:
            return None, None

    # --- 3. グラフチェック（結果シート） ---
    # ezodfではsheet.objectsにグラフなどのフレームが含まれる
    res_sheet = sheets.get("結果")
    has_graph_res = len(res_sheet.objects) > 0 if res_sheet else False
    results.append({"check": "3. グラフをシート「結果」に貼り付けている", "status": "Done" if has_graph_res else "NG"})

    # --- 4-11. 試験と成績シートの詳細チェック ---
    sheet_name = "試験と成績"
    
    # 4. D34: AVERAGE関数
    f, v = get_cell_info(sheet_name, 34, 4) # D34
    results.append({"check": "4. セル D34 に AVERAGE 関数を用いた数式がある", "status": "Done" if f and "AVERAGE" in f.upper() else "NG"})

    # 5. K46: IF(D46>=$D$12, $H$9, $H$10)
    f, v = get_cell_info(sheet_name, 46, 11) # K46
    cond5 = f and "IF" in f.upper() and "D46" in f and "$D$12" in f
    results.append({"check": "5. セル K46 に IF関数の判定式がある", "status": "Done" if cond5 else "NG"})

    # 6. R46: COUNT(D46:J46)
    f, v = get_cell_info(sheet_name, 46, 18) # R46
    cond6 = f and "COUNT" in f.upper() and "D46" in f and "J46" in f
    results.append({"check": "6. セル R46 に COUNT(D46:J46) 系の数式がある", "status": "Done" if cond6 else "NG"})

    # 7. R46 の結果が 7
    results.append({"check": "7. セル R46 の計算結果が 7 になっている", "status": "Done" if v == 7 else "NG"})

    # 8. S46: COUNTIF(K46:Q46, $H$9)
    f, v = get_cell_info(sheet_name, 46, 19) # S46
    cond8 = f and "COUNTIF" in f.upper() and "K46" in f and "$H$9" in f
    results.append({"check": "8. セル S46 に COUNTIF 系の数式がある", "status": "Done" if cond8 else "NG"})

    # 9. T46: ROUND(AVERAGE(D46:J46),0)
    f, v = get_cell_info(sheet_name, 46, 20) # T46
    cond9 = f and "ROUND" in f.upper() and "AVERAGE" in f.upper()
    results.append({"check": "9. セル T46 に ROUND と AVERAGE の数式がある", "status": "Done" if cond9 else "NG"})

    # 10. U46: IF(S46>=R46*$F$21,T46,$G$22)
    f, v = get_cell_info(sheet_name, 46, 21) # U46
    cond10 = f and "IF" in f.upper() and "S46" in f and "R46" in f and "$F$21" in f
    results.append({"check": "10. セル U46 に合格判定の IF 数式がある", "status": "Done" if cond10 else "NG"})

    # 11. U46 が S46 を参照しているか
    results.append({"check": "11. セル U46 に S46 を参照する数式がある", "status": "Done" if f and "S46" in f else "NG"})

    # 12. 試験と成績シートにグラフがあるか
    exam_sheet = sheets.get("試験と成績")
    has_graph_exam = len(exam_sheet.objects) > 0 if exam_sheet else False
    results.append({"check": "12. ＜グラフを作成するための表＞付近にグラフがある", "status": "Done" if has_graph_exam else "NG"})

    return results

# --- Streamlit UI ---
st.set_page_config(page_title="ODS 課題チェック", layout="centered")

st.title("📊 ODS 課題自動判定アプリ")
st.write("アップロードされたファイルをスキャンし、12個のチェック項目を確認します。")

uploaded_file = st.file_uploader("ODSファイルをアップロードしてください", type=["ods"])

if uploaded_file:
    with st.spinner('判定中...'):
        file_bytes = uploaded_file.read()
        check_results = check_ods_task(file_bytes, uploaded_file.name)
        
        st.subheader("判定結果一覧")
        
        # サマリー表示
        done_count = sum(1 for item in check_results if item["status"] == "Done")
        st.metric("クリア項目数", f"{done_count} / 12")

        # 詳細表示
        for item in check_results:
            col1, col2 = st.columns([5, 1])
            col1.write(item["check"])
            if item["status"] == "Done":
                col2.success("Done")
            else:
                col2.error("NG")
        
        if done_count == 12:
            st.balloons()
            st.success("おめでとうございます！すべての項目をクリアしました！")
else:
    st.info("ファイルをアップロードしてください。")
