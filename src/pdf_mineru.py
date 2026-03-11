import json
import os
import requests
import time
import zipfile

api_key = 'api_key'
PDF_BASE_URL = 'https://ding-mineru-pdf-2026.oss-cn-beijing.aliyuncs.com/'

def get_task_id(file_name):
    url='https://mineru.net/api/v4/extract/task'
    header = {
        'Content-Type':'application/json',
        "Authorization":f"Bearer {api_key}".format(api_key)
    }
    pdf_url = PDF_BASE_URL + file_name
    data = {
        'url':pdf_url,
        'is_ocr':True,
        'enable_formula': False,
    }

    res = requests.post(url,headers=header,json=data)
    print(res.status_code)
    print(res.json())
    print(res.json()["data"])
    task_id = res.json()["data"]['task_id']
    return task_id

def get_result(task_id):
    url = f'https://mineru.net/api/v4/extract/task/{task_id}'
    header = {
        'Content-Type':'application/json',
        "Authorization":f"Bearer {api_key}".format(api_key)
    }

    while True:
        res = requests.get(url, headers=header)
        result = res.json()["data"]
        print(result)
        state = result.get('state')
        err_msg = result.get('err_msg', '')
        # 如果任务还在进行中，等待后重试
        if state in ['pending', 'running']:
            print("任务未完成，等待5秒后重试...")
            time.sleep(5)
            continue
        # 如果有错误，输出错误信息
        if err_msg:
            print(f"任务出错: {err_msg}")
            return
        # 如果任务完成，下载文件
        if state == 'done':
            full_zip_url = result.get('full_zip_url')
            if full_zip_url:
                local_filename = f"{task_id}.zip"
                print(f"开始下载: {full_zip_url}")
                r = requests.get(full_zip_url, stream=True)
                with open(local_filename, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                print(f"下载完成，已保存到: {local_filename}")
                # 下载完成后自动解压
                unzip_file(local_filename)
            else:
                print("未找到 full_zip_url，无法下载。")
            return
        # 其他未知状态
        print(f"未知状态: {state}")
        return

# 解压zip文件的函数
def unzip_file(zip_path, extract_dir=None):
    """
    解压指定的zip文件到目标文件夹。
    :param zip_path: zip文件路径
    :param extract_dir: 解压目标文件夹，默认为zip同名目录
    """
    if extract_dir is None:
        extract_dir = zip_path.rstrip('.zip')
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_dir)
    print(f"已解压到: {extract_dir}")

def _format_text_block(item):
    text = (item.get("text") or "").strip()
    if not text:
        return ""

    text_level = item.get("text_level")
    if text_level == 1:
        return f"# {text}"
    if text_level == 2:
        return f"## {text}"
    if text_level == 3:
        return f"### {text}"
    return text

def _format_table_block(item):
    parts = []
    caption = item.get("table_caption") or []
    if caption:
        parts.append("\n".join(caption))

    table_body = item.get("table_body") or ""
    if table_body:
        parts.append(table_body)

    footnote = item.get("table_footnote") or []
    if footnote:
        parts.append("\n".join(footnote))

    return "\n\n".join([p for p in parts if p])

def build_markdown_with_pages(extract_dir, output_path):
    content_list_files = [
        name for name in os.listdir(extract_dir)
        if name.endswith("_content_list.json")
    ]
    if not content_list_files:
        return False

    content_list_path = os.path.join(extract_dir, content_list_files[0])
    with open(content_list_path, "r", encoding="utf-8") as f:
        content_list = json.load(f)

    blocks_by_page = {}
    for item in content_list:
        page_idx = item.get("page_idx")
        if page_idx is None:
            continue
        blocks_by_page.setdefault(page_idx, []).append(item)

    lines = []
    for page_idx in sorted(blocks_by_page.keys()):
        page_number = page_idx + 1
        lines.append(f"# Page {page_number}")
        lines.append("")
        for item in blocks_by_page[page_idx]:
            block_type = item.get("type")
            if block_type == "discarded":
                continue
            if block_type == "text":
                block_text = _format_text_block(item)
            elif block_type == "table":
                block_text = _format_table_block(item)
            elif block_type == "image":
                img_path = item.get("img_path") or ""
                block_text = f"![]({img_path})" if img_path else ""
            else:
                block_text = ""

            if block_text:
                lines.append(block_text)
                lines.append("")

        lines.append("---")
        lines.append("")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines).rstrip() + "\n")

    return True

if __name__ == "__main__":
    file_name = '【财报】中芯国际：中芯国际2024年年度报告.pdf'
    task_id = get_task_id(file_name)
    print('task_id:',task_id)
    get_result(task_id)

