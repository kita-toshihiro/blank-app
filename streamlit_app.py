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
        def get_cell(row_idx, col_idx): # 1-based index
            try:
                # ezodfのrowsは0-indexed
                return sheet_exam.rows()[row_idx-1][col_idx-1]
            except:
                return None

        # --- 判定項目 ---
        
        # 3. D34:J34 の値 (80以上100以下)
        d34_j34_ok = True
        for col in range(4, 11): # D(4) to J(10)
            c = get_cell(34, col)
            if c is None or c.value is None or not (80 <= float(c.value) <= 100):
                d34_j34_ok = False
                break
        results.append({"check": "D34:J34 のオートフィル後の値が 80以上100以下である", "status": "Done" if d34_j34_ok else "NG"})

        # 4. K46:Q75 (OK または ー)
        k46_q75_ok = True
        for row in range(46, 76):
            for col in range(11, 18): # K(11) to Q(17)
                c = get_cell(row, col)
                if c is None or c.value not in ["OK", "ー", "-", "—"]: # 表記ゆれ考慮
                    k46_q75_ok = False
                    break
            if not k46_q75_ok: break
        results.append({"check": "K46:Q75 のオートフィル後の値が「OK」か「ー」である", "status": "Done" if k46_q75_ok else "NG"})

        # 6. R列 実施回数 (数値7 かつ count関数)
        r_col_ok = True
        for row in range(46, 76):
            c = get_cell(row, 18) # R
            if c is None or c.value != 7 or "count" not in (c.formula or "").lower():
                r_col_ok = False
                break
        results.append({"check": "R46:R75 が数値 7 で、count 関数を用いた式である", "status": "Done" if r_col_ok else "NG"})

        # 7. S列 合格回数 (0-7整数 かつ countif関数)
        s_col_ok = True
        for row in range(46, 76):
            c = get_cell(row, 19) # S
            if c is None or not (0 <= (c.value or -1) <= 7) or "countif" not in (c.formula or "").lower():
                s_col_ok = False
                break
        results.append({"check": "S46:S75 が 0〜7 の整数で、countif 関数を用いた式である", "status": "Done" if s_col_ok else "NG"})

        # 8. T列 平均点 (80-100整数 かつ round, average関数)
        t_col_ok = True
        for row in range(46, 76):
            c = get_cell(row, 20) # T
            formula = (c.formula or "").lower()
            if c is None or not (80 <= (c.value or 0) <= 100) or "round" not in formula or "average" not in formula:
                t_col_ok = False
                break
        results.append({"check": "T46:T75 が 80〜100 の整数で、round と average 関数を用いた式である", "status": "Done" if t_col_ok else "NG"})

        # 9. U列 評価 (「不可」か「平均点」と同じ)
        u_col_ok = True
        for row in range(46, 76):
            c_u = get_cell(row, 21) # U (評価)
            c_t = get_cell(row, 20) # T (平均点)
            if c_u is None or c_t is None or (c_u.value != "不可" and c_u.value != c_t.value):
                u_col_ok = False
                break
        results.append({"check": "U46:U75 の評価欄が「不可」または「平均点」と同じである", "status": "Done" if u_col_ok else "NG"})

    # 「結果」シートのグラフチェック
    sheet_result = sheets.get("結果")
    if sheet_result:
        # グラフがある場合、XMLのなかに 'draw:control' や 'draw:frame' などが含まれる
        # ezodfの簡易的な判定として、xmlツリー内に 'chart' という文字列が含まれるかを確認
        xml_content = sheet_result.xmlnode.decode() if hasattr(sheet_result.xmlnode, 'decode') else str(sheet_result.xmlnode)
        has_chart = "chart" in xml_content.lower() or "draw:frame" in xml_content.lower()
        results.append({"check": "「結果」シートにグラフが貼り付けられている", "status": "Done" if has_chart else "NG"})
    else:
        results.append({"check": "「結果」シートが存在しない", "status": "NG"})

    return results

# --- Streamlit UI ---
st.title("📊 ODS 課題自動判定システム")

uploaded_file = st.file_uploader("ODSファイルをアップロード", type=["ods"])

if uploaded_file:
    try:
        res = check_ods_task(uploaded_file.read())
        for item in res:
            col1, col2 = st.columns([4, 1])
            col1.write(item["check"])
            if item["status"] == "Done":
                col2.success("Done")
            else:
                col2.error("NG")
    except Exception as e:
        st.error(f"解析中にエラーが発生しました: {e}")
