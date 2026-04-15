import streamlit as st
import ezodf
import io

def check_ods_task(file_bytes):
    doc = ezodf.opendoc(io.BytesIO(file_bytes))
    sheets = {s.name: s for s in doc.sheets}
    found_sheets = list(sheets.keys())
    results = []

    # --- 1. シート構成チェック ---
    required = ["sample", "data", "試験と成績", "結果"]
    # 「シート 1」または「Sheet1」系の表記ゆれを許容
    sheet1_variations = ["シート 1", "シート1", "Sheet1", "Sheet 1"]
    has_sheet1 = any(s in found_sheets for s in sheet1_variations)
    has_others = all(s in found_sheets for s in required)
    
    status_sheets = "Done" if (has_sheet1 and has_others) else "NG"
    results.append({
        "check": "5つのシート（sample, data, シート1, 試験と成績, 結果）が含まれている",
        "status": status_sheets,
        "detail": f"見つかったシート: {', '.join(found_sheets)}"
    })

    # --- 2. 「試験と成績」シートの COUNT 関数判定 ---
    sheet_exam = sheets.get("試験と成績")
    status_count = "NG"
    count_detail = "シートが見つかりません"

    if sheet_exam:
        try:
            # 探索範囲（例として46行目から75行目、R列を確認）
            # ezodfのrows[row_idx][col_idx]は 0-indexed
            target_row = 45 # 46行目
            target_col = 17 # R列
            
            cell = sheet_exam.rows()[target_row][target_col]
            val = cell.value
            # ezodfのformulaは "oooc:=COUNT(...)" のような形式で取得される
            formula = str(cell.formula or "").lower()

            # 判定条件：数式に count が含まれる、かつ 計算結果が 7
            has_count_func = "count" in formula
            is_value_7 = (val == 7 or val == 7.0)

            if has_count_func and is_value_7:
                status_count = "Done"
                count_detail = f"数式: {cell.formula} / 結果: {val}"
            else:
                reasons = []
                if not has_count_func: reasons.append("COUNT関数が使われていません（直接入力の可能性があります）")
                if not is_value_7: reasons.append(f"結果が 7 ではありません（現在の値: {val}）")
                count_detail = "、".join(reasons)
                
        except Exception as e:
            count_detail = f"解析エラー（指定のセルにデータがない可能性があります）: {e}"

    results.append({
        "check": "「試験と成績」シート：実施回数欄に COUNT 関数が使われ、結果が 7 である",
        "status": status_count,
        "detail": count_detail
    })

    return results

# --- Streamlit UI ---
st.set_page_config(page_title="ODS課題チェッカー", page_icon="📝")
st.title("📝 ODS 課題自動判定 (Local Mode)")
st.caption("Gemini API を使用せず、ファイル内の数式を直接解析します。")

uploaded_file = st.file_uploader("ODSファイルをアップロード", type=["ods"])

if uploaded_file:
    res_list = check_ods_task(uploaded_file.read())
    
    st.divider()
    
    for item in res_list:
        col1, col2 = st.columns([0.8, 0.2])
        
        with col1:
            st.markdown(f"**{item['check']}**")
            if item['status'] == "NG":
                st.caption(f"❌ 理由: {item['detail']}")
            else:
                st.caption(f"✅ 内容確認: {item['detail']}")
                
        with col2:
            if item["status"] == "Done":
                st.success("Done")
            else:
                st.error("NG")
