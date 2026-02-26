import os
import time
import requests
import zipfile
from src.pdf_mineru import build_markdown_with_pages


# 建议：api_key 改成从环境变量读

api_key = 'eyJ0eXBlIjoiSldUIiwiYWxnIjoiSFM1MTIifQ.eyJqdGkiOiI1NjEwMDg0NyIsInJvbCI6IlJPTEVfUkVHSVNURVIiLCJpc3MiOiJPcGVuWExhYiIsImlhdCI6MTc2NzEwNTQ4OCwiY2xpZW50SWQiOiJsa3pkeDU3bnZ5MjJqa3BxOXgydyIsInBob25lIjoiIiwib3BlbklkIjpudWxsLCJ1dWlkIjoiZTUyZTAzMzUtOGVmZi00Mzg5LWIyZDItYmUwOTVhNGIzOTM2IiwiZW1haWwiOiIiLCJleHAiOjE3NjgzMTUwODh9.GubJ6kD23O7kpVTrcCguu44S7jxEJO7ldh4WJ1AQdGb0RX3NgToJiPGQC5qhgTFLtjILG_M-HDt8Py3mOhT0Yw'
PDF_BASE_URL = "https://ding-mineru-pdf-2026.oss-cn-beijing.aliyuncs.com/"

def get_task_id(file_name: str) -> str:
    url = "https://mineru.net/api/v4/extract/task"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    pdf_url = PDF_BASE_URL + file_name
    data = {
        "url": pdf_url,
        "is_ocr": True,
        "enable_formula": False,
    }
    res = requests.post(url, headers=headers, json=data, timeout=60)
    res.raise_for_status()
    return res.json()["data"]["task_id"]

def unzip_file(zip_path, extract_dir=None):
    if extract_dir is None:
        extract_dir = zip_path[:-4] if zip_path.endswith(".zip") else zip_path
    os.makedirs(extract_dir, exist_ok=True)
    with zipfile.ZipFile(zip_path, "r") as z:
        z.extractall(extract_dir)
    return extract_dir

def wait_and_download(task_id: str, out_dir: str, poll_sec: int = 5, timeout_sec: int = 1800):
    """
    等待任务完成 -> 下载 full_zip -> 解压
    返回解压目录路径
    """
    url = f"https://mineru.net/api/v4/extract/task/{task_id}"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    start = time.time()
    while True:
        if time.time() - start > timeout_sec:
            raise TimeoutError(f"task {task_id} 超时未完成（>{timeout_sec}s）")

        res = requests.get(url, headers=headers, timeout=60)
        res.raise_for_status()
        data = res.json()["data"]

        state = data.get("state")
        err_msg = data.get("err_msg", "")

        if state in ("pending", "running"):
            time.sleep(poll_sec)
            continue

        if err_msg:
            raise RuntimeError(f"task {task_id} 出错: {err_msg}")

        if state == "done":
            full_zip_url = data.get("full_zip_url")
            if not full_zip_url:
                raise RuntimeError(f"task {task_id} done 但没有 full_zip_url")

            os.makedirs(out_dir, exist_ok=True)
            zip_path = os.path.join(out_dir, f"{task_id}.zip")

            r = requests.get(full_zip_url, stream=True, timeout=120)
            r.raise_for_status()
            with open(zip_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        f.write(chunk)

            extract_dir = os.path.join(out_dir, task_id)
            unzip_file(zip_path, extract_dir)
            return extract_dir

        raise RuntimeError(f"task {task_id} 未知状态: {state}")

# 你原来的 build_markdown_with_pages / _format_* 函数保持不动，继续用即可
# from pdf_mineru import build_markdown_with_pages  (如果你拆文件的话)

def run_batch(file_names, zip_out_dir, md_out_dir):
    ok, fail = [], []
    for fn in file_names:
        try:
            print(f"\n=== 处理: {fn}")
            task_id = get_task_id(fn)
            print("task_id:", task_id)

            extract_dir = wait_and_download(task_id, out_dir=zip_out_dir)

            # 输出 md 文件名：用原文件名（去掉 .pdf）+ .md
            base = os.path.splitext(fn)[0]
            out_md_path = os.path.join(md_out_dir, base + ".md")

            # 这里调用你现成的 build_markdown_with_pages
            success = build_markdown_with_pages(extract_dir, out_md_path)
            if not success:
                raise RuntimeError("未找到 *_content_list.json，无法生成 markdown")

            ok.append(fn)
            print("✅ 完成:", out_md_path)
        except Exception as e:
            fail.append((fn, str(e)))
            print("❌ 失败:", fn, "->", e)

    print("\n===== 总结 =====")
    print("成功:", len(ok))
    print("失败:", len(fail))
    for fn, err in fail:
        print(" -", fn, err)

if __name__ == "__main__":
    # 1) 把你 OSS 里的文件名填到这里（注意：包含 .pdf，保持和 OSS 对象名一致）
    file_names = [
        "【中原证券】产能利用率显著提升，持续推进工艺迭代升级——中芯国际(688981)季报点评.pdf",
        "【东方证券】产能利用率提升，持续推进工艺迭代和产品性能升级.pdf",
        "【光大证券】中芯国际2025年一季度业绩点评：1Q突发生产问题，2Q业绩有望筑底，自主可控趋势不改.pdf",
        "【国信证券】工业与汽车触底反弹，良率影响短期营收.pdf",
        "【华泰证券】中芯国际（688981）：上调港股目标价到63港币，看好DeepSeek推动代工需求强劲增长.pdf",
        "【兴证国际】季度盈利低于预期，看好国产芯片长期空间.pdf",
        "中芯国际机构调研纪要.pdf",

        # "xxx.pdf",
        # "yyy.pdf",
    ]

    # 2) zip & 解压输出目录（建议放到 data/stock_data/debug_data 下面，便于你 pipeline 接）
    zip_out_dir = "data/stock_data/debug_data/01_mineru_zip"
    md_out_dir  = "data/stock_data/debug_data/03_reports_markdown"

    run_batch(file_names, zip_out_dir, md_out_dir)
