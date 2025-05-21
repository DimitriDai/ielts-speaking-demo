import streamlit as st
import subprocess
import os
import json

CONFIG_PATH = "Spk_Config.json"

SCRIPT_MAP = {
    "Step 1": "Spk_S1_Screenshot_Rename.py",
    "Step 2": "Spk_S2_Screenshot_to_text.py",
    "Step 3": "Spk_S3_Dpsk_Answer_Draft.py",
    "Step 4": "Spk_S4_Txt_to_Docx.py",
    "Step 5": "Spk_S5_Q&A_Together.py"
}

def load_or_create_config():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        return {
            "IMG_DIR": "",
            "TXT_PREFILL_DIR": "",
            "ANSWER_DIR": ""
        }

def save_config(config):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

# === Streamlit 页面开始 ===
st.set_page_config(page_title="雅思口语全流程工具", layout="wide")
st.title("📘 雅思口语批处理工具 Demo")

config = load_or_create_config()

# === 选择路径 ===
st.subheader("🗂️ 路径设置")
config["IMG_DIR"] = st.text_input("📁 截图文件夹 IMG_DIR", config["IMG_DIR"])
config["TXT_PREFILL_DIR"] = st.text_input("📄 预填文本 TXT_PREFILL_DIR", config["TXT_PREFILL_DIR"])
config["ANSWER_DIR"] = st.text_input("📂 已生成答案 ANSWER_DIR", config["ANSWER_DIR"])
DOCX_PATH = os.path.join(config["ANSWER_DIR"], "汇总口语答案.docx")

if st.button("💾 保存路径配置"):
    save_config(config)
    st.success("✅ 已保存配置！")

st.divider()

# === 每个功能模块按钮 ===
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

col1, col2 = st.columns(2)

with col1:
    if st.button("Step 1: 重命名截图"):
        run_step("Step 1", SCRIPT_MAP["Step 1"], ["--input", config["IMG_DIR"], "--prefix", "雅思哥截图"])

    if st.button("Step 3: 生成答案"):
        run_step("Step 3", SCRIPT_MAP["Step 3"], ["--input", config["TXT_PREFILL_DIR"], "--output", config["ANSWER_DIR"]])

    if st.button("Step 5: 合并Q&A"):
        run_step("Step 5", SCRIPT_MAP["Step 5"], ["--input", config["TXT_PREFILL_DIR"], "--output", config["ANSWER_DIR"]])

with col2:
    if st.button("Step 2: 截图转文本"):
        run_step("Step 2", SCRIPT_MAP["Step 2"], ["--input", config["IMG_DIR"], "--output", config["TXT_PREFILL_DIR"]])

    if st.button("Step 4: TXT转Word"):
        run_step("Step 4", SCRIPT_MAP["Step 4"], ["--input", config["ANSWER_DIR"], "--output", DOCX_PATH])

st.divider()
st.caption("© DimitriDai 口语工作流原型 | Powered by Streamlit + Python")
# 输入 cd "D:\Python\Code\EduTech"      
#      streamlit run Spk_topic_org_app.py
