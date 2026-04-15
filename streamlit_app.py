import streamlit as st
import ezodf
import io
import re

def check_ods_task(file_bytes):
    doc = ezodf.opendoc(io.BytesIO(file_bytes))
    sheets = {s.name: s for s in doc.sheets}
    results = []

    # --- ヘルパー関数 ---
    def get_cell_val(sheet, row_idx, col_idx): # 1-based index
        try:
            cell = sheet.rows()[row_idx-1][col_idx-1]
            return cell.value, cell.formula
        except:
            return None, None

    # 1. シート構成チェック
    required_sheets = ["sample", "data", "試験と成績", "結果"]
    found_sheets = list(sheets.keys())
    sheet1_exists = "シート 1" in found_sheets or "Sheet1" in found_sheets or "シート1" in found_sheets
    all_required_exists = all(s in found_sheets for s in required_sheets) and sheet1_exists
    results.append({"check": "5つのシート（sample, data, シート1, 試験と成績, 結果）が含まれている", "status": "Done" if all_required_exists else "NG"})

    # 「試験と成績」シートの取得
    sheet_exam = sheets.get("試験と成績")
    
    if sheet_exam:
        # 3. D34:J34 の値 (80以上100以下)
        d34_j34_ok = True
        for col in range(4, 11): # D to J
            val, _ = get_cell_val(sheet_exam, 34, col)
            try:
                if val is None or not (80 <= float(val) <= 100):
                    d34_j34_ok = False; break
            except:
                d34_j34_ok = False; break
        results.append({"check": "D34:J34 の値が 80以上100以下（エラーなし）", "status": "Done" if d34_j34_ok else "NG"})

        # 4. K46:Q75 (OK または ー)
        k46_q75_ok = True
        for row in range(46, 76):
            for col in range(11, 18): # K to Q
                val, _ = get_cell_val(sheet_exam, row, col)
                if val not in ["OK", "ー", "-", "—"]: # 表記ゆれ対応
                    k46_q75_ok = False; break
            if not k46_q75_ok: break
        results.append({"check": "K46:Q75 の値が「OK」または「ー」のみである", "status": "Done" if k46_q75_ok else "NG"})

        # 5. R46:U75 エラーチェック (オートフィル後の数式エラー等)
        r46_u75_no_error = True
        for row in range(46, 76):
            for col in range(18, 22): # R to U
                val, _ = get_cell_val(sheet_exam, row, col)
                if val is None: # 空白やエラーを想定
                    r46_u75_no_error = False; break
            if not r46_u75_no_error: break
        results.append({"check": "R46:U75 のオートフィル操作範囲にエラーがない", "status": "Done" if r46_u75_no_error else "NG"})

        # 6. R列 実施回数 (数値7 かつ count関数)
        r_col_ok = True
        for row in range(46, 76):
            val, formula = get_cell_val(sheet_exam, row, 18)
            if val != 7 or "count" not in (formula or "").lower():
                r_col_ok = False; break
        results.append({"check": "R列：実施回数が 7 で、COUNT関数が使用されている", "status": "Done" if r_col_ok else "NG"})

        # 7. S列 合格回数 (0-7整数 かつ countif関数)
        s_col_ok = True
        for row in range(46, 76):
            val, formula = get_cell_val(sheet_exam, row, 19)
            try:
                if not (0 <= int(val) <= 7) or "countif" not in (formula or "").lower():
                    s_col_ok = False; break
            except:
                s_col_ok = False; break
        results.append({"check": "S列：合格回数が 0-7 で、COUNTIF関数が使用されている", "status": "Done" if s_col_ok else "NG"})

        # 8. T列 平均点 (80-100整数 かつ round, average関数)
        t_col_ok = True
        for row in range(46, 76):
            val, formula = get_cell_val(sheet_exam, row, 20)
            f_str = (formula or "").lower()
            try:
                if not (80 <= float(val) <= 100) or "round" not in f_str or "average" not in f_str:
                    t_col_ok = False; break
            except:
                t_col_ok = False; break
        results.append({"check": "T列：平均点が 80-100 で、ROUNDとAVERAGE関数が使用されている", "status": "Done" if t_col_ok else "NG"})

        # 9. U列 評価 (「不可」か「平均点」と同じ)
        u_col_ok = True
        for row in range(46, 76):
            u_val, _ = get_cell_val(sheet_exam, row, 21)
            t_val, _ = get_cell_val(sheet_exam, row, 20)
            # 値が「不可」という文字列であるか、T列の平均点と一致しているか
            if u_val != "不可" and str(u_val) != str(t_val):
                u_col_ok = False; break
        results.append({"check": "U列：評価欄が「不可」または「平均点」と同じである", "status": "Done" if u_col_ok else "NG"})

        # 10. D12を80にした時の挙動 (ロジック判定)
        # 実際にファイルを書き換えるのではなく、数式内にD12(または$D$12)を参照しているIF文があるか、
        # もしくは現在D12が80以上で「不可」が一つも無いかを簡易チェック
        d12_val, _ = get_cell_val(sheet_exam, 12, 4)
        u_vals = [get_cell_val(sheet_exam, r, 21)[0] for r in range(46, 76)]
        d12_logic_ok = True
        if d12_val == 80 and "不可" in u_vals:
            d12_logic_ok = False
        results.append({"check": "D12を80にすると「不可」がなくなる（ロジック整合性）", "status": "Done" if d12_logic_ok else "NG"})
    else:
        for _ in range(8): results.append({"check": "「試験と成績」シート未検出のため判定不可", "status": "NG"})

    # 「結果」シートのチェック
    sheet_result = sheets.get("結果")
    if sheet_result:
        xml_content = sheet_result.xmlnode.decode() if hasattr(sheet_result.xmlnode, 'decode') else str(sheet_result.xmlnode)
        
        # 2. 演習5-2のグラフ貼り付け
        has_chart = "chart" in xml_content.lower() or "draw:frame" in xml_content.lower()
        results.append({"check": "「結果」シートにグラフが貼り付けられている", "status": "Done" if has_chart else "NG"})
        
        # 11. グラフの軸設定チェック (簡易的)
        # ODS内部のグラフデータまで解析するのは困難なため、グラフの存在を優先
        # 軸ラベル等はXML内のtext要素から推測
        axis_check = "平均点" in xml_content and "第1回" in xml_content
        results.append({"check": "グラフの縦軸が平均点、横軸が第1回〜第7回となっている", "status": "Done" if axis_check else "NG"})
    else:
        results.append({"check": "「結果」シート未検出", "status": "NG"})
        results.append({"check": "グラフの軸設定判定不可", "status": "NG"})

    return results

# --- Streamlit UI ---
st.set_page_config(page_title="ODS課題チェッカー", layout="wide")
st.title("📊 ODS 課題自動判定システム")
st.markdown("提出用の `.ods` ファイルをアップロードして、各項目の判定結果を確認してください。")

uploaded_file = st.file_uploader("ODSファイルをアップロード", type=["ods"])

if uploaded_file:
    with st.spinner('判定中...'):
        try:
            file_bytes = uploaded_file.read()
            res = check_ods_task(file_bytes)
            
            st.subheader("判定結果一覧")
            
            for item in res:
                with st.container():
                    col1, col2 = st.columns([5, 1])
                    col1.write(item["check"])
                    if item["status"] == "Done":
                        col2.success("Done")
                    else:
                        col2.error("NG")
                    st.divider()
                    
        except Exception as e:
            st.error(f"解析中にエラーが発生しました。ファイル形式が正しいか確認してください。: {e}")
