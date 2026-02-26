import json
from pathlib import Path

import pandas as pd

import streamlit as st

from src.pipeline import Pipeline, max_config


st.set_page_config(page_title="RAG Challenge 2", layout="wide")


@st.cache_resource(show_spinner=False)
def get_pipeline() -> Pipeline:
    root_path = Path("data/stock_data")
    return Pipeline(root_path, run_config=max_config)

@st.cache_data(show_spinner=False)
def get_report_name_map() -> dict:
    subset_path = Path("data/stock_data/subset.csv")
    if not subset_path.exists():
        return {}
    try:
        df = pd.read_csv(subset_path, encoding="utf-8")
    except UnicodeDecodeError:
        df = pd.read_csv(subset_path, encoding="gbk")
    if "sha1" not in df.columns or "file_name" not in df.columns:
        return {}
    return dict(zip(df["sha1"].astype(str), df["file_name"].astype(str)))


def _safe_json_loads(payload: str) -> dict:
    try:
        return json.loads(payload)
    except Exception:
        return {}


def normalize_answer(answer):
    if isinstance(answer, str):
        answer_dict = _safe_json_loads(answer) or {"final_answer": answer}
    else:
        answer_dict = answer or {}

    content = answer_dict.get("content", answer_dict)
    if isinstance(content, str):
        content = _safe_json_loads(content) or {"final_answer": content}

    return {
        "step_by_step": content.get("step_by_step_analysis", answer_dict.get("step_by_step_analysis", "-")),
        "reasoning_summary": content.get("reasoning_summary", answer_dict.get("reasoning_summary", "-")),
        "relevant_pages": content.get("relevant_pages", answer_dict.get("relevant_pages", [])),
        "references": content.get("references", answer_dict.get("references", [])),
        "final_answer": content.get("final_answer", answer_dict.get("final_answer", answer_dict.get("value", "-"))),
    }


st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;600;700&display=swap');

:root {
  --bg: #f4f5fb;
  --panel: #ffffff;
  --panel-alt: #f7f8ff;
  --primary: #6d5efc;
  --primary-2: #6b8cff;
  --accent: #f4a261;
  --text: #1f2937;
  --muted: #6b7280;
  --success: #d7f3e3;
  --info: #e6f1ff;
  --shadow: 0 12px 30px rgba(20, 20, 40, 0.08);
  --radius: 16px;
}

html, body, [class*="css"]  {
  font-family: "Noto Sans SC", "Segoe UI", system-ui, sans-serif;
  background: var(--bg);
  color: var(--text);
}

[data-testid="stSidebar"] {
  background: #f2f3f7;
  border-right: 1px solid #edf0f6;
}

.app-header {
  background: linear-gradient(90deg, #6d5efc 0%, #7f6df2 40%, #f4a261 100%);
  border-radius: 18px;
  padding: 20px 24px;
  color: #fff;
  box-shadow: var(--shadow);
}

.app-header h2 {
  margin: 0;
  font-weight: 700;
}

.app-header p {
  margin: 6px 0 0;
  opacity: 0.9;
}

.section-title {
  font-weight: 700;
  font-size: 20px;
  margin: 22px 0 12px;
}

.card {
  background: var(--panel);
  border-radius: var(--radius);
  padding: 18px 20px;
  box-shadow: var(--shadow);
  border: 1px solid #edf0f6;
}

.card-muted {
  background: var(--panel-alt);
  border-radius: var(--radius);
  padding: 16px 18px;
  border: 1px solid #e4e8ff;
}

.pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: #fff3e6;
  color: #8f4f00;
  border: 1px solid #ffd7b3;
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;
}

.answer-box {
  background: #f7f7fb;
  padding: 18px;
  border-radius: 14px;
  border: 1px solid #e5e7ef;
  font-size: 16px;
  line-height: 1.7;
}

.small-muted {
  color: var(--muted);
  font-size: 13px;
}
</style>
""",
    unsafe_allow_html=True,
)

st.markdown(
    """
<div class="app-header">
  <h2>🚀 RAG Challenge 2 - RTX 5080 Powered</h2>
  <p>基于深度RAG系统 · 多公司年报问答 · 向量检索 + LLM推理</p>
</div>
""",
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown("### 查询设置")
    st.markdown("<span class='small-muted'>仅需输入单个问题，默认类型为 string。</span>", unsafe_allow_html=True)
    user_question = st.text_area(
        "输入问题",
        "请简要总结公司2022年主营业务的主要内容。",
        height=110,
    )
    st.selectbox("问题类型", ["string"], index=0, disabled=True)
    submit_btn = st.button("生成答案", use_container_width=True)

pipeline = get_pipeline()
report_name_map = get_report_name_map()

st.markdown("<div class='section-title'>检索结果</div>", unsafe_allow_html=True)

if submit_btn:
    if not user_question.strip():
        st.warning("请输入问题后再提交。")
    else:
        with st.spinner("正在生成答案，请稍候..."):
            try:
                raw_answer = pipeline.answer_single_question(user_question, kind="string")
                parsed = normalize_answer(raw_answer)

                st.markdown(
                    "<div class='card'>"
                    "<div class='pill'>📌 单问检索</div>"
                    "<div style='margin-top:10px;' class='small-muted'>问题</div>"
                    f"<div style='font-weight:600;margin-top:4px;'>{user_question}</div>"
                    "</div>",
                    unsafe_allow_html=True,
                )

                st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)
                st.markdown("<div class='card-muted'><strong>分步推理</strong></div>", unsafe_allow_html=True)
                st.info(parsed["step_by_step"])

                st.markdown("<div class='card-muted'><strong>推理摘要</strong></div>", unsafe_allow_html=True)
                st.success(parsed["reasoning_summary"])

                final_answer = (parsed.get("final_answer") or "").strip()
                no_info_markers = ("N/A", "-", "无法", "未包含", "不包含", "没有", "未提及", "无法确定")
                has_answer = final_answer and not any(marker in final_answer for marker in no_info_markers)

                st.markdown("<div class='card-muted'><strong>相关页面</strong></div>", unsafe_allow_html=True)
                if has_answer:
                    st.write(parsed["relevant_pages"])
                else:
                    st.write("无来源信息")

                st.markdown("<div class='card-muted'><strong>来源文档</strong></div>", unsafe_allow_html=True)
                refs = parsed.get("references") or []
                if refs and has_answer:
                    rows = []
                    for ref in refs:
                        sha1 = str(ref.get("pdf_sha1", ""))
                        rows.append(
                            {
                                "page": ref.get("page_index", "-"),
                                "source": report_name_map.get(sha1, sha1),
                            }
                        )
                    st.table(rows)
                else:
                    st.write("无来源信息")

                st.markdown("<div class='card-muted'><strong>最终答案</strong></div>", unsafe_allow_html=True)
                st.markdown(f"<div class='answer-box'>{parsed['final_answer']}</div>", unsafe_allow_html=True)
            except Exception as exc:
                st.error(f"生成答案时出错：{exc}")
else:
    st.info("在左侧输入问题并点击【生成答案】后显示结果。")
