import streamlit as st
import ezodf
import io

def check_ods_task(file_bytes):
    doc = ezodf.opendoc(io.BytesIO(file_bytes))
    sheets = {s.name: s for s in doc.sheets}
    found_sheets = list(sheets.keys())
    results = []

    # --- 1. シート構成チェック ---
    core_required = ["sample", "data", "試験と成績", "結果"]
    sheet1_exists = "シート 1" in found_sheets or "Sheet1" in found_sheets
    all_core_exists = all(s in found_sheets for s in core_required)
    
    is_sheet_structure_ok = all_core_exists and sheet1_exists

    results.append({
        "check": "5つのシート（sample, data, シート 1, 試験と成績, 結果）が含まれている",
        "status": "Done" if is_sheet_structure_ok else "NG"
    })

    # --- 2. 「試験と成績」シートの数式チェック ---
    sheet_exam = sheets.get("試験と成績")
    
    if sheet_exam:
        r_col_ok = True
        try:
            # 【修正ポイント】 rows() をリストに変換してからアクセスする
            rows = list(sheet_exam.rows()) 
            
            # 46行目から75行目までループ (0-indexed なので 45から75)
            for row_idx in range(45, 75):
                # 行が存在するかチェック
                if row_idx >= len(rows):
                    r_col_ok = False
                    break
                
                row = rows[row_idx]
                # R列(18番目)が存在するかチェック
                if len(row) < 18:
                    r_col_ok = False
                    break
                    
                cell = row[17] # R列
                
                formula = (cell.formula or "").lower()
                value = cell.value
                
                # count関数が含まれているか、かつ結果が7か
                # (ezodfの仕様により数値は float で比較するのが安全です)
                if "count" not in formula or value != 7:
                    r_col_ok = False
                    break
        except Exception as e:
            # デバッグ用にエラーを print しても良いです
            r_col_ok = False

        results.append({
            "check": "「試験の実施回数」欄（R46:R75）にcount関数が使われ、結果が7である",
            "status": "Done" if r_col_ok else "NG"
        })
    else:
        results.append({
            "check": "「試験と成績」シートが見つからないため判定不可",
            "status": "NG"
        })

    return results

# --- Streamlit UI ---
st.set_page_config(page_title="ODS 課題チェック", layout="centered")

st.title("📊 ODS 課題自動判定アプリ")
st.write("アップロードされた .ods ファイルが課題の要件を満たしているか判定します。")

uploaded_file = st.file_uploader("ODSファイルをアップロードしてください", type=["ods"])

if uploaded_file:
    try:
        # ファイルの読み込みと判定
        check_results = check_ods_task(uploaded_file.read())
        
        st.subheader("判定結果")
        
        for item in check_results:
            with st.container():
                col1, col2 = st.columns([4, 1])
                col1.markdown(f"**{item['check']}**")
                
                if item["status"] == "Done":
                    col2.success("Done")
                else:
                    col2.error("NG")
                    
    except Exception as e:
        st.error(f"解析中にエラーが発生しました。ファイル形式を確認してください。\nエラー内容: {e}")

else:
    st.info("ファイルをアップロードすると、自動的に判定が開始されます。")
