import streamlit as st
import ezodf
import io
import re

def check_ods_task(file_bytes):
    doc = ezodf.opendoc(io.BytesIO(file_bytes))
    sheets = {s.name: s for s in doc.sheets}
    results = []

    # 1. シート構成チェック
    required_sheets = ["sample", "data", "試験と成績", "結果"]
    found_sheets = list(sheets.keys())
    sheet1_exists = "シート 1" in found_sheets or "Sheet1" in found_sheets
    all_required_exists = all(s in found_sheets for s in required_sheets) and sheet1_exists
    results.append({
        "check": "5つのシート（sample, data, シート1, 試験と成績, 結果）が存在するか",
        "status": "Done" if all_required_exists else "NG"
    })

    # 「試験と成績」シートの解析
    sheet_exam = sheets.get("試験と成績")
    
    if sheet_exam:
        # ヘルパー：セルの値と数式を取得 (1-based index)
        def get_cell_info(row, col):
            try:
                cell = sheet_exam.rows()[row-1][col-1]
                return {"value": cell.value, "formula": cell.formula if cell.formula else ""}
            except:
                return {"value": None, "formula": ""}

        # 3. セル D34 のチェック (オートフィル想定範囲 D34:J34)
        d34_j34_ok = True
        for col in range(4, 11):  # D(4)からJ(10)
            c = get_cell_info(34, col)
            val = c["value"]
            if val is None or not (80 <= float(val) <= 100):
                d34_j34_ok = False
        results.append({"check": "D34:J34 の値が 80以上100以下か", "status": "Done" if d34_j34_ok else "NG"})

        # 6. 試験の実施回数 (R46:R75想定) count関数
        count_ok = True
        for row in range(46, 76):
            c = get_cell_info(row, 18) # R列
            if c["value"] != 7 or "count" not in c["formula"].lower():
                count_ok = False
        results.append({"check": "実施回数が7であり、count関数を使用しているか", "status": "Done" if count_ok else "NG"})

        # 7. 合格回数 (S46:S75想定) countif関数
        countif_ok = True
        for row in range(46, 76):
            c = get_cell_info(row, 19) # S列
            val = c["value"]
            if val is None or not (0 <= int(val) <= 7) or "countif" not in c["formula"].lower():
                countif_ok = False
        results.append({"check": "合格回数が0-7で、countif関数を使用しているか", "status": "Done" if countif_ok else "NG"})

        # 8. 平均点 (T46:T75想定) round, average
        avg_ok = True
        for row in range(46, 76):
            c = get_cell_info(row, 20) # T列
            val = c["value"]
            if val is None or not (80 <= float(val) <= 100) or "round" not in c["formula"].lower() or "average" not in c["formula"].lower():
                avg_ok = False
        results.append({"check": "平均点が80-100の整数で、round/averageを使用しているか", "status": "Done" if avg_ok else "NG"})

    # 「結果」シートの解析（簡易判定）
    sheet_result = sheets.get("結果")
    if sheet_result:
        # グラフの存在確認は ezodf では限定的ですが、オブジェクトがあるかチェック
        has_chart = len(sheet_result.objects) > 0
        results.append({"check": "「結果」シートにグラフ等が存在するか", "status": "Done" if has_chart else "NG"})
    else:
        results.append({"check": "「結果」シートの解析", "status": "NG"})

    return results

# --- Streamlit アプリ構成 ---
st.set_page_config(page_title="ODS課題自動判定", layout="centered")
st.title("📑 ODS課題・提出前自動セルフチェック")

uploaded_file = st.file_uploader("ODSファイルをアップロードしてください", type=["ods"])

if uploaded_file:
    file_bytes = uploaded_file.read()
    check_results = check_ods_task(file_bytes)
    
    st.subheader("判定結果")
    for res in check_results:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write(res["check"])
        with col2:
            if res["status"] == "Done":
                st.success("Done")
            else:
                st.error("NG")

    st.info("※オートフィルのシミュレーションはアップロード時点のセルの状態に基づき判定しています。")
