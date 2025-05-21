import streamlit as st
import subprocess
import os
import shutil

# === 脚本路径映射 ===
SCRIPT_MAP = {
    "Step 1": "Spk_S1_Screenshot_Rename.py",
    "Step 2": "Spk_S2_Screenshot_to_text.py",
    "Step 3": "Spk_S3_Dpsk_Answer_Draft.py",
    "Step 4": "Spk_S4_Txt_to_Docx.py",
    "Step 5": "Spk_S5_Q&A_Together.py"
}

# === 页面初始化 ===
st.set_page_config(page_title="雅思口语全流程工具", layout="wide")
st.title("📘 雅思口语批处理工具 Demo")

# === 上传图片 ===
st.subheader("🖼️ Step 1：上传截图图片")
uploaded_files = st.file_uploader("上传截图（可多选）", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

TEMP_IMG_DIR = "uploaded_imgs"
TXT_PREFILL_DIR = "txt_prefill"
ANSWER_DIR = "answer_output"
DOCX_PATH = os.path.join(ANSWER_DIR, "汇总口语答案.docx")

os.makedirs(TEMP_IMG_DIR, exist_ok=True)
os.makedirs(TXT_PREFILL_DIR, exist_ok=True)
os.makedirs(ANSWER_DIR, exist_ok=True)

if uploaded_files:
    for i, file in enumerate(uploaded_files):
        ext = os.path.splitext(file.name)[-1]
        save_path = os.path.join(TEMP_IMG_DIR, f"input_{i+1}{ext}")
        with open(save_path, "wb") as f:
            f.write(file.read())
    st.success(f"✅ 已保存 {len(uploaded_files)} 张图片到 {TEMP_IMG_DIR} 文件夹")

# === 执行函数 ===
def run_step(label, script_path, args_list):
    with st.status(f"{label} 执行中...", expanded=True) as status:
        try:
            result = subprocess.run(["python", script_path] + args_list, capture_output=True, text=True)
            st.code(result.stdout)
            if result.stderr:
                st.error(result.stderr)
            else:
                status.update(label=f"{label} ✅ 成功", state="complete")
        except Exception as e:
            st.error(f"❌ 执行失败: {e}")

# === 操作按钮 ===
col1, col2 = st.columns(2)

with col1:
    if st.button("Step 1: 重命名截图"):
        run_step("Step 1", SCRIPT_MAP["Step 1"], ["--input", TEMP_IMG_DIR, "--prefix", "input"])

    if st.button("Step 3: 生成答案"):
        run_step("Step 3", SCRIPT_MAP["Step 3"], ["--input", TXT_PREFILL_DIR, "--output", ANSWER_DIR])

    if st.button("Step 5: 合并Q&A"):
        run_step("Step 5", SCRIPT_MAP["Step 5"], ["--input", TXT_PREFILL_DIR, "--output", ANSWER_DIR])

with col2:
    if st.button("Step 2: 截图转文本"):
        run_step("Step 2", SCRIPT_MAP["Step 2"], ["--input", TEMP_IMG_DIR, "--output", TXT_PREFILL_DIR])

    if st.button("Step 4: TXT转Word"):
        run_step("Step 4", SCRIPT_MAP["Step 4"], ["--input", ANSWER_DIR, "--output", DOCX_PATH])

st.divider()
st.caption("© DimitriDai 口语工作流原型 | Powered by Streamlit + Python")
