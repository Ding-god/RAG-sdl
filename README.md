# RAG-SDL

企业级 RAG（检索增强生成）系统，专注于财报、研报等复杂 PDF 文档的精准问答。

## 项目简介

本项目是一个面向金融场景的企业级 RAG 问答系统，解决海量非结构化文档（PDF、研报、规则文档）的精准检索与问答问题。

### 核心能力

- **PDF 智能解析**：支持财报、研报等复杂 PDF 文档的结构化提取
- **混合检索**：结合向量检索与关键词检索，提升召回率
- **LLM 重排**：使用大模型对检索结果进行语义重排
- **结构化输出**：生成带引用来源的可验证回答
- **多模型支持**：支持通义千问、GPT 等多种大模型

## 技术架构

```
┌─────────────────────────────────────────────────────────┐
│                    RAG Pipeline                         │
├─────────────────────────────────────────────────────────┤
│  PDF Parsing → Text Splitting → Embedding → Storage   │
│         ↓                                              │
│  Query → Hybrid Search → Rerank → LLM Generate         │
│         ↓                                              │
│  Structured Output with Citations                      │
└─────────────────────────────────────────────────────────┘
```

### 核心模块

1. **PDF 解析 (pdf_parsing.py)**
   - 使用 MinerU 进行文档结构化解析
   - 保留表格、图表等重要信息

2. **文本分块 (text_splitter.py)**
   - 基于页级的重叠切块策略
   - 确保跨页上下文连续性

3. **混合检索 (retrieval.py)**
   - FAISS 向量索引 + BM25 关键词索引
   - Parent Page 回溯检索

4. **重排机制 (reranking.py)**
   - LLM 语义重排
   - 向量相似度与模型评分加权

5. **问答生成 (pipeline.py)**
   - 结构化 Prompt 设计
   - Chain-of-thought 推理

## 安装部署

### 环境要求
- Python 3.10+
- GPU（推荐，用于 PDF 解析加速）

### 安装步骤

```bash
# 1. 克隆项目
git clone https://github.com/Ding-god/RAG-sdl.git
cd RAG-sdl

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置 API Key
# 编辑相关配置文件添加你的 API Key
```

### 配置说明

根据需要配置不同的模型：

```python
# 使用通义千问
model = "qwen-max"
base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"

# 使用 OpenAI
model = "gpt-4o"
base_url = "https://api.openai.com/v1"
```

## 使用方法

### 命令行运行

```bash
# 运行完整 pipeline
python main.py

# 或使用 Streamlit 界面
streamlit run app_streamlit.py
```

### Python API

```python
from src.pipeline import RAGPipeline

# 初始化 pipeline
rag = RAGPipeline(config="max_nst_o3m")

# 提问
question = "公司2024年的营收增长是多少？"
answer = rag.ask(question)
print(answer)
```

### 可用配置

- `max_nst_o3m` - 使用 OpenAI o3-mini 模型的最佳配置
- `qwen_rerank` - 使用通义千问加检索重排
- `gemini_thinking` - 使用 Gemini 超长上下文

## 项目结构

```
RAG-sdl/
├── src/                     # 核心源码
│   ├── pdf_parsing.py      # PDF 解析
│   ├── pdf_mineru.py       # MinerU 解析器
│   ├── text_splitter.py    # 文本分块
│   ├── ingestion.py        # 向量入库
│   ├── retrieval.py        # 检索模块
│   ├── reranking.py       # 重排模块
│   ├── pipeline.py         # 完整 pipeline
│   └── prompts.py          # Prompt 模板
├── data/                    # 测试数据
├── docs/                    # 文档
├── app_streamlit.py         # Web 界面
└── main.py                  # 入口文件
```

## 技术栈

- **语言**: Python
- **LLM**: 通义千问、OpenAI GPT、Claude、Gemini
- **向量数据库**: FAISS、Elasticsearch
- **Embedding**: BGE、DashScope
- **PDF 解析**: MinerU、Docling
- **前端**: Streamlit

## 应用场景

- 财报问答系统
- 研报摘要提取
- 企业知识库问答
- 合同条款分析
- 法规文档检索

## 性能优化建议

1. **GPU 加速**：PDF 解析使用 GPU 可大幅提升速度
2. **索引优化**：根据文档规模选择合适的向量索引
3. **缓存策略**：对常见问题使用结果缓存
4. **批量处理**：批量处理文档提升吞吐量

## 注意事项

1. 需要有效的 API Key 才能运行
2. PDF 解析对 GPU 内存有要求（推荐 24GB+）
3. 部分复杂表格可能需要手动处理

## License

MIT License
