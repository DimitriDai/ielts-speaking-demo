import os
import re
import time
import requests
from PIL import Image
import pytesseract

# === 配置区 ===
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--input", required=True, help="图片输入路径")
parser.add_argument("--output", required=True, help="预填文本输出路径")
args = parser.parse_args()

IMAGE_FOLDER = args.input
OUTPUT_FOLDER = args.output

DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
import streamlit as st
DEEPSEEK_API_KEY = st.secrets["DEEPSEEK_API_KEY"]
TESSERACT_CMD = r"D:\Outlet\tesseract\tesseract.exe"
pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD
os.environ["TESSDATA_PREFIX"] = r"D:\Outlet\tesseract\tessdata"

# === LLM 提示词 ===
STRUCT_PROMPT = """
你是一位专业的 IELTS Speaking 教师助手。
以下是一段 OCR 提取的英文文本，可能包含 IELTS Speaking 的 Part 1 / Part 2 / Part 3 的题目。

你的任务是：

1. **仅输出 OCR 文本中真实出现的 话题词 和 Part 部分**（例如：如果 OCR 只包含 Part 2 和 3，就只输出它们）；
2. **不要编造不存在的 Part 部分**；
3. **不要添加中文或解释说明语句**；
4. **结构要求如下**：

---
 如果识别到 Part 1，请为每一组问题输出以下结构，其中关键词一般是英文：
```

[关键词]
Part 1
1. [问题]
2. [问题]
3. [问题]
   ...

```

- 每一套 Part 1（通常包含 3~6 个问题）可独立作为一个 Topic 输出；
---
 如果识别到 Part 2 和 Part 3，请作为一个话题块输出，格式如下，关键词一般是中文：
```

[关键词]
Part 2
Describe a [话题内容].
You should say:
* what ...
* where ...
* who ...
* and explain why ...
Part 3
1. [相关分析问题]
2. [相关分析问题]
   ...

- Part 2 和 Part 3 属于同一个话题，**必须合在同一个 关键词 区块内**；
- 话题关键词应从 Part 2的文本中得到。

## 输出示例 1：**只有 Part 1（两套问题）**

```
Daily routines
Part 1
1. What is your morning routine like?
2. Do you prefer planning your day or being spontaneous?
3. Do you think routines are important?

Technology
Part 1
1. How often do you use your phone?
2. What apps do you use most frequently?
3. Do you think technology helps or harms communication?
```

---

## 输出示例 2：**只有 Part 2 和 Part 3**

```
热心的人
Part 2
Describe a person who helped you in a difficult situation.
You should say:
- who this person is
- what the situation was
- how he/she helped you
- and explain how you felt about it
Part 3
1. What qualities make someone helpful?
2. Do people help others more now than in the past?
3. How do communities support people in need?
```

---

## 输出示例 3：**完整包含 Part 1 + Part 2 + Part 3**

```
Free time
Part 1
1. What do you like to do in your free time?
2. How often do you have free time during the week?
3. Do you prefer relaxing alone or with others?

放松的活动
Part 2
Describe a relaxing activity you enjoy doing.
You should say:
- what it is
- where you do it
- how often you do it
- and explain why it relaxes you
Part 3
1. Why do people need time to relax?
2. Do you think people relax in the same way now as in the past?
3. Should schools teach students how to manage stress?
"""

def extract_clean_parts(text: str) -> str:
    # 去 markdown 粗体（保留内容）
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)

    # 去掉中英文注释括号内的内容，但保留英文说明（更安全）
    # 仅去除 “括号内全是中文或标点”的情况
    text = re.sub(r"[（(][\u4e00-\u9fa5，。、《》！？：；、—…·【】]*[）)]", "", text)

    # 去分割线（---）
    text = re.sub(r"-{2,}", "", text)

    # 去除多余空行
    text = re.sub(r"\n{2,}", "\n\n", text)

    return text.strip()

    # 提取 Part 1/2/3
    part_pattern = r"(Part\s+[123][\s\S]*?)(?=Part\s+[123]|$)"
    parts = re.findall(part_pattern, text, flags=re.IGNORECASE)

    cleaned_parts = []
    for p in parts:
        p = re.sub(r"\n{2,}", "\n", p.strip())     # 多空行压缩
        p = re.sub(r" {2,}", " ", p)               # 多空格压缩
        cleaned_parts.append(p.strip())

    return "\n\n".join(cleaned_parts).strip()

# === 调用 Deepseek ===
def call_deepseek(prompt_text):
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt_text}],
        "temperature": 0.3
    }
    try:
        res = requests.post(DEEPSEEK_API_URL, headers=headers, json=data, timeout=30)
        if res.status_code == 200:
            return res.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"Deepseek 请求失败: {e}")
    return ""

# === 主处理流程 ===
def process_all_images():
    image_files = [
    f for f in os.listdir(IMAGE_FOLDER)
    if f.lower().endswith(('.png', '.jpg', '.jpeg')) and f.startswith("雅思哥截图")
    ]
    if not image_files:
        print("没有找到任何图片。")
        return

    for idx, filename in enumerate(sorted(image_files), start=1):
        image_path = os.path.join(IMAGE_FOLDER, filename)
        print(f"正在处理第 {idx} 张图：{filename}")

        try:
            image = Image.open(image_path)
            ocr_text = pytesseract.image_to_string(image, lang="eng")

            prompt = STRUCT_PROMPT + ocr_text
            print("正在调用 Deepseek...")
            result = call_deepseek(prompt)

            if result:
                cleaned = extract_clean_parts(result)
                output_name = os.path.splitext(filename)[0] + "-已识别.txt"
                output_path = os.path.join(IMAGE_FOLDER, output_name)
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(cleaned)
                print(f"已保存：{output_name}")
            else:
                print(f"Deepseek 无返回，跳过该图。")

        except Exception as e:
            print(f"处理失败：{filename} → {e}")

    print("\n所有图片处理完毕！")

#对txt文件进行合并与重命名#
import random

def merge_output_files():
    input_dir = IMAGE_FOLDER
    output_dir = OUTPUT_FOLDER  # ✅ 使用传入参数，而不是写死路径
    os.makedirs(output_dir, exist_ok=True)

    merged_text = ""
    file_list = sorted(f for f in os.listdir(input_dir) if f.endswith("-已识别.txt"))

    for f in file_list:
        file_path = os.path.join(input_dir, f)
        with open(file_path, "r", encoding="utf-8") as infile:
            content = infile.read().strip()
            if content:
                merged_text += content + "\n\n"  # 每份之间留空行分隔

    if not merged_text.strip():
        print("没有可合并的内容。")
        return

    random_number = f"{random.randint(1000, 9999)}"
    merged_filename = f"{random_number}_口语话题_预填.txt"
    merged_path = os.path.join(output_dir, merged_filename)

    with open(merged_path, "w", encoding="utf-8") as outfile:
        outfile.write(merged_text.strip())

    print(f"\n所有已识别文本已合并为：{merged_filename}")

# === 入口 ===
if __name__ == "__main__":
    process_all_images()
    merge_output_files()