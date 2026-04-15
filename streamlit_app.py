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
    
    # --- 内部構造のチェック ---
    try:
        doc = ezodf.opendoc(io.BytesIO(file_bytes))
        sheets = {s.name: s for s in doc.sheets}
        is_parsed = True
    except Exception:
        is_parsed = False

    def get_cell_info(s_name, r, c):
        if not is_parsed or s_name not in sheets: 
            return "", None
        sheet = sheets[s_name]
        # ezodfのnrows/ncolsはデータがある範囲を返すため、指定セルが範囲外でもエラーにならないよう制御
        try:
            cell = sheet[r-1, c-1]
            # 数式は先頭に [=] がつく場合があるため、正規化
            f = (cell.formula or "").replace(" ", "").upper()
            v = cell.value
            return f, v
        except: 
            return "", None

    def has_chart(s_name):
        if not is_parsed or s_name not in sheets: return False
        # draw:frame 要素を探す（グラフや画像が含まれる場合に反応）
        return len(sheets[s_name].xmlnode.findall(f".//{{{NS['draw']}}}frame")) > 0

    # 必要なセル情報の取得
    f_d34, v_d34 = get_cell_info("試験と成績", 34, 4)   # D34
    f_k46, v_k46 = get_cell_info("試験と成績", 46, 11)  # K46
    f_r46, v_r46 = get_cell_info("試験と成績", 46, 18)  # R46
    f_s46, v_s46 = get_cell_info("試験と成績", 46, 19)  # S46
    f_t46, v_t46 = get_cell_info("試験と成績", 46, 20)  # T46
    f_u46, v_u46 = get_cell_info("試験と成績", 46, 21)  # U46

    # --- 12項目の判定ロジック ---
    
    # 2. シート名チェック
    required_fixed = ["sample", "data", "試験と成績", "結果"]
    has_fixed = all(s in sheets for s in required_fixed)
    has_sheet1 = "シート 1" in sheets or "Sheet1" in sheets
    check2 = is_parsed and has_fixed and has_sheet1

    # リスト定義 (項目名, 判定式, 詳細情報)
    checks = [
        ("1. ODS形式である", is_parsed and file_name.lower().endswith('.ods'), file_name),
        ("2. 指定の5つのシートを含んでいる", check2, "シート構成を確認してください"),
        ("3. 「結果」にグラフがある", has_chart("結果"), "draw:frameの有無"),
        ("4. 「試験と成績」D34に数式がある", f_d34 != "", f_d34),
        ("5. 「試験と成績」K46に判定式がある", "IF" in f_d34 or "IF" in f_k46, f_k46), # D34かK46か文脈によりますが指示はK46
        ("6. 「試験と成績」R46にCOUNT関数がある", "COUNT" in f_r46, f_r46),
        ("7. 「試験と成績」R46の結果が7である", v_r46 == 7 or v_r46 == 7.0, f"現在の値: {v_r46}"),
        ("8. 「試験と成績」S46にCOUNT関数がある", "COUNT" in f_s46, f_s46),
        ("9. 「試験と成績」T46にROUNDとAVERAGE関数がある", "ROUND" in f_t46 and "AVERAGE" in f_t46, f_t46),
        ("10. 「試験と成績」U46に判定式がある", "IF" in f_u46, f_u46),
        ("11. 「試験と成績」U46に数式がある", f_u46 != "", f_u46),
        ("12. 「試験と成績」にグラフがある", has_chart("試験と成績"), "draw:frameの有無")
    ]
    
    # 関数の最後にある return 部分を以下のように修正します

    return [
        {
            "No": i + 1,
            "チェック項目": c[0],
            "判定": "✔" if c[1] else "NG",
            # バッククォートで囲むことで、$記号が数式として解釈されるのを防ぎます
            "内容/数式": f"`{str(c[2])}`" if c[2] else ""
        }
        for i, c in enumerate(checks)
    ]
# --- Streamlit UI ---
st.set_page_config(page_title="ODS Checker", layout="wide")

st.title("📊 課題3 ファイル提出前の最低限のチェック")
st.info("このサイトは、課題3の提出ファイルが最低限の条件を満たしているか確認するためのツールです。ここで課題3の**提出はできません。**")

uploaded_file = st.file_uploader("ODSファイルをアップロードしてください", type=["ods"])

if uploaded_file:
    # バイナリを読み込み
    file_bytes = uploaded_file.read()
    res = get_check_results(file_bytes, uploaded_file.name)
    
    if res:
        score = sum(1 for r in res if r["判定"] == "✔")
        
        # スコア表示
        if score == 12:
            st.success(f"🎉 最低限のチェック完了。クリア項目数: {score} / 12")
            st.balloons()
        elif score >= 8:
            st.warning(f"💡 あと少しです。 テキストを良く読んでください。クリア項目数: {score} / 12")
        else:
            st.error(f"⚠️ 修正が必要です。 テキストを良く読んでください。クリア項目数: {score} / 12")
        
        # 結果のテーブル表示
        st.dataframe(res, use_container_width=True, height=460)
        #st.table(res)
        
        st.write("---")
        st.caption("※判定は数式内の文字列（IF, COUNT等）を検索して行っています。")
        st.write("📸 **提出用メモ**: この画面のスクリーンショットを撮って、提出時に添付してください。")
