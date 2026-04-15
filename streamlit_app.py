import streamlit as st
import ezodf
import io

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
        "check": "5つのシート（sample, data, シート1, 試験と成績, 結果）が含まれている",
        "status": "Done" if all_required_exists else "NG"
    })

    # 「試験と成績」シートの解析
    sheet_exam = sheets.get("試験と成績")
    
    if sheet_exam:
        def get_cell_safe(row_idx, col_idx):
            """セルのオブジェクト、値、数式を安全に取得する"""
            try:
                # 行が存在するか確認
                rows = sheet_exam.rows()
                if row_idx-1 < len(rows):
                    row = rows[row_idx-1]
                    if col_idx-1 < len(row):
                        cell = row[col_idx-1]
                        # ezodfのセルオブジェクトから安全に値と数式を取得
                        val = cell.value if cell is not None else None
                        form = getattr(cell, 'formula', "") or ""
                        return val, form
                return None, ""
            except:
                return None, ""

        # --- 判定項目 ---
        
        # 3. D34:J34 の値 (80以上100以下)
        d34_j34_ok = True
        for col in range(4, 11): 
            val, _ = get_cell_safe(34, col)
            if val is None or not (80 <= float(val) <= 100):
                d34_j34_ok = False
                break
        results.append({"check": "D34:J34 のオートフィル後の値が 80以上100以下である", "status": "Done" if d34_j34_ok else "NG"})

        # 4. K46:Q75 (OK または ー)
        k46_q75_ok = True
        for row in range(46, 76):
            for col in range(11, 18): 
                val, _ = get_cell_safe(row, col)
                if val not in ["OK", "ー", "-", "—"]:
                    k46_q75_ok = False
                    break
            if not k46_q75_ok: break
        results.append({"check": "K46:Q75 のオートフィル後の値が「OK」か「ー」である", "status": "Done" if k46_q75_ok else "NG"})

        # 6. R列 実施回数 (数値7 かつ count関数)
        r_col_ok = True
        for row in range(46, 76):
            val, form = get_cell_safe(row, 18)
            if val != 7 or "count" not in form.lower():
                r_col_ok = False
                break
        results.append({"check": "R46:R75 が数値 7 で、count 関数を用いた式である", "status": "Done" if r_col_ok else "NG"})

        # 7. S列 合格回数 (0-7整数 かつ countif関数)
        s_col_ok = True
        for row in range(46, 76):
            val, form = get_cell_safe(row, 19)
            if val is None or not (0 <= float(val) <= 7) or "countif" not in form.lower():
                s_col_ok = False
                break
        results.append({"check": "S46:S75 が 0〜7 の整数で、countif 関数を用いた式である", "status": "Done" if s_col_ok else "NG"})

        # 8. T列 平均点 (80-100整数 かつ round, average関数)
        t_col_ok = True
        for row in range(46, 76):
            val, form = get_cell_safe(row, 20)
            if val is None or not (80 <= float(val) <= 100) or "round" not in form.lower() or "average" not in form.lower():
                t_col_ok = False
                break
        results.append({"check": "T46:T75 が 80〜100 の整数で、round と average 関数を用いた式である", "status": "Done" if t_col_ok else "NG"})

        # 9. U列 評価 (「不可」か「平均点」と同じ)
        u_col_ok = True
        for row in range(46, 76):
            val_u, _ = get_cell_safe(row, 21)
            val_t, _ = get_cell_safe(row, 20)
            if val_u is None or (val_u != "不可" and str(val_u) != str(val_t)):
                u_col_ok = False
                break
        results.append({"check": "U46:U75 の評価欄が「不可」または「平均点」と同じである", "status": "Done" if u_col_ok else "NG"})

    # グラフチェック
    sheet_result = sheets.get("結果")
    if sheet_result:
        xml_content = str(sheet_result.xmlnode)
        has_chart = "chart" in xml_content.lower() or "draw:frame" in xml_content.lower()
        results.append({"check": "「結果」シートにグラフが貼り付けられている", "status": "Done" if has_chart else "NG"})
    else:
        results.append({"check": "「結果」シートが存在しない", "status": "NG"})

    return results

# --- Streamlit UI ---
st.set_page_config(page_title="ODS Checker", layout="wide")
st.title("📑 ODS 課題自動判定システム")

uploaded_file = st.file_uploader("ODSファイルをアップロード", type=["ods"])

if uploaded_file:
    try:
        # アップロードされたファイルをメモリ内で読み込み
        data = uploaded_file.read()
        res = check_ods_task(data)
        
        for item in res:
            col1, col2 = st.columns([4, 1])
            col1.write(item["check"])
            if item["status"] == "Done":
                col2.success("Done")
            else:
                col2.error("NG")
                
    except Exception as e:
        st.error(f"解析中にエラーが発生しました: {e}")
        st.info("ヒント: セルが結合されていたり、想定外のデータ型が入っている可能性があります。")
