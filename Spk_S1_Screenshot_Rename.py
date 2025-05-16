import os
import argparse

def rename_screenshots(folder_path, new_name):
    files = os.listdir(folder_path)
    
    for index, file in enumerate(files):
        if file.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
            file_extension = os.path.splitext(file)[1]
            new_file_name = f"{new_name}_{index + 1}{file_extension}"

            old_file_path = os.path.join(folder_path, file)
            new_file_path = os.path.join(folder_path, new_file_name)

            if os.path.exists(new_file_path):
                print(f"已存在目标文件，跳过：{new_file_name}")
                continue

            os.rename(old_file_path, new_file_path)
            print(f"Renamed: {file} -> {new_file_name}")

# ⬇️ 下面是入口，负责接收命令行参数
parser = argparse.ArgumentParser()
parser.add_argument("--input", required=True, help="截图文件夹路径")
parser.add_argument("--prefix", default="雅思哥截图", help="文件名前缀")
args = parser.parse_args()

rename_screenshots(args.input, args.prefix)