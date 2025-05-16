import os
import re
import requests
import json
import time

# 配置区
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
import streamlit as st
DEEPSEEK_API_KEY = st.secrets["DEEPSEEK_API_KEY"]
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--input", required=True, help="预填txt文件夹")
parser.add_argument("--output", required=True, help="生成答案输出文件夹")
args = parser.parse_args()

INPUT_TXT_FOLDER = args.input
OUTPUT_FOLDER = args.output


# 系统提示
BASE_PROMPT =  """
# Role
You are an experienced IELTS Speaking teacher who understands the test criteria and the real performance levels of Chinese students aged under 16.

# Objective
You must give complete answers to the IELTS Part 1/2/3 questions based on the given texts.
Only answers are needed, not outlines, summaries, or tips.

# Requirements for Each Part
## Part 1
- First, list all the questions in the reply first.
- Second, answer each individual question separately.
- Each answer must contain no fewer than 3 sentences and no more than 5 sentences.
- Answers should be natural and detailed, from the perspective of a typical Chinese secondary school student.
- Part 1 is independent of Part 2 and Part 3, so do not refer to them or hallucinate Part 2 or Part 3 content based on Part 1.
- Avoid using overly complex language or cultural references that may not resonate with Chinese students.

## Part 2
- First, list all the questions in the reply first.
- Second, write a natural 2-minute speech, i.e. 18-22 sentences approximately.
- The speech should be a coherent narrative, not just a list of points.
- Question points can be re-ordered if needed to make the narrative flow smoothly.
- Include juicy, vivid personal details that match a Chinese student's real-life experience.

## Part 3
- First, list all the questions in the reply first.
- Second, answer each individual question separately.
- Each answer must contain no fewer than 4 sentences and no more than 6 sentences.
- Answers must be analytical and slightly more mature than Part 1, but still from the perspective of a high school student.

# Pitfalls to Avoid
- Talking too simply or going off-topic.
- Writing language that is either too difficult or too elementary.
- Using cultural assumptions that do not fit Chinese students.

# Language Requirements
- Use colloquial, natural English.
- Include idiomatic expressions and phrases when appropriate.
- Responses should match approximately Band 6.5 in IELTS Speaking.
- Always include specific examples and juicy details.

# Output Format
- Use “Part 1 / Part 2 / Part 3” headings clearly.
- For Part 1 and Part 3, list the question first, then give the full answer immediately underneath.
- For Part 2, present the entire speech after the prompt description.
- Add a line `---` between each Part for clarity.
"""

os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# 调用Deepseek的函数（带重试）
def call_deepseek(prompt_content: str, retries=3, delay=5):
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": BASE_PROMPT},
            {"role": "user", "content": prompt_content}
        ],
        "temperature": 0.7,
        "max_tokens": 3000,
        "top_p": 1,
        "frequency_penalty": 0,
        "presence_penalty": 0
    }

    for attempt in range(retries):
        response = requests.post(DEEPSEEK_API_URL, headers=headers, json=payload)
        if response.status_code == 200:
            result = response.json()
            return result["choices"][0]["message"]["content"].strip()
        else:
            print(f"请求失败（第{attempt + 1}次），状态码: {response.status_code}")
            time.sleep(delay)

    print("所有重试失败，跳过该段落。")
    return None

def split_parts(file_content: str):
    parts = {}
    pattern = r"(Part\s*\d+(?:-\d+)?)[\s\S]*?(?=Part\s*\d+(?:-\d+)?|$)"
    matches = re.finditer(pattern, file_content, re.IGNORECASE)

    count_tracker = {}  # 用来记录 Part 1/2/3 出现了几次

    for match in matches:
        full_text = match.group(0).strip()

        # 提取 Part 编号：只取 Part 后的数字（例如 Part 1-2 -> 1）
        part_number_match = re.match(r"Part\s*(\d+)", full_text, re.IGNORECASE)
        if not part_number_match:
            continue
        part_number = int(part_number_match.group(1))

        # 维护每种 Part 的出现次数
        count_tracker[part_number] = count_tracker.get(part_number, 0) + 1
        suffix = count_tracker[part_number]

        # 构造统一格式：Part x-y
        part_title = f"Part {part_number}-{suffix}"

        # 存入 dict
        parts[part_title] = [full_text]

    return parts

# 主处理流程
def process_all_txts():
    txt_files = [f for f in os.listdir(INPUT_TXT_FOLDER) if f.endswith("_口语话题_预填.txt")]

    if not txt_files:
        print("没找到符合要求的预填文件。")
        return

    for txt_filename in txt_files:
        txt_path = os.path.join(INPUT_TXT_FOLDER, txt_filename)
        base_name = os.path.splitext(txt_filename)[0]

        print(f"正在读取: {txt_filename}")
        with open(txt_path, "r", encoding="utf-8") as file:
            file_content = file.read()

        parts = split_parts(file_content)

        if not parts:
            print(f"没拆分出任何Part，跳过 {txt_filename}")
            continue

        # 处理每个Part
        for part_title, part_text_list in parts.items():
            # part_text_list 是一个列表，包含了多个相同的Part内容
            for part_index, part_text in enumerate(part_text_list, start=1):
                prompt_text = part_text.strip()
                if not prompt_text:
                    continue

                print(f"正在处理 {base_name}-{part_title} ...")
                generated_answer = call_deepseek(prompt_text)

                if generated_answer:
                    # 为避免文件名冲突，添加序号
                    output_filename = f"{base_name}-{part_title}-已生成-{part_index}.txt"
                    output_path = os.path.join(OUTPUT_FOLDER, output_filename)
                    with open(output_path, "w", encoding="utf-8") as out_f:
                        out_f.write(generated_answer)
                    print(f"成功生成: {output_filename}")
                else:
                    print(f"Deepseek失败: {base_name}-{part_title}-{part_index}")

    print("\n全部txt处理完成！")
# 执行主程序
if __name__ == "__main__":
    process_all_txts()