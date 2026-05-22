# AI 产品经理求职 RAG 助手

> 面向 AI 产品经理实习求职者的 RAG 求职辅助产品，支持 AI 技术知识问答、JD 解析、能力诊断、项目包装和面试准备。

---

## 1. 项目简介

本项目面向 AI 产品经理实习求职场景，设计并搭建一款基于 RAG 的求职辅助产品。系统整合 AI 产品经理 JD、AI 技术知识点和能力模型，帮助用户理解岗位要求、补齐能力短板、包装 AI 项目并准备面试。

---

## 2. 核心功能

| 功能 | 说明 |
|---|---|
| 知识问答 | 解释 RAG、Agent、Prompt、Function Calling 等 AI 技术概念 |
| JD 解析 | 分析 AI 产品经理岗位职责、能力要求和加分项 |
| 能力诊断 | 根据用户背景输出 L1-L5 能力差距和补强计划 |
| 项目包装 | 将用户 AI 项目转化为简历 bullet 和面试表达 |
| 面试准备 | 生成回答框架、示例回答和追问预测 |

---

## 3. 知识库设计

当前知识库包含：

| 知识库 | 数量 | 作用 |
|---|---:|---|
| JD 库 | 32 条 | 提供岗位要求证据 |
| AI 技术知识库 | 71 条 | 解释 AI 技术概念 |
| 能力模型库 | 12 条 | 支撑能力诊断 |

---

## 4. 技术栈

| 模块 | 技术 |
|---|---|
| 前端 | Streamlit |
| 后端 | FastAPI |
| 向量数据库 | Qdrant 本地模式 |
| Embedding | BAAI/bge-small-zh-v1.5 |
| LLM 调用 | OpenAI-compatible API，如硅基流动 |
| 数据格式 | CSV / JSONL |

---

## 5. 项目结构

```text
ai_pm_knowledge_framework/
├── backend/
│   ├── app_rag.py
│   ├── rag_answer.py
│   ├── ingest_qdrant.py
│   ├── retrieve_qdrant.py
│   ├── build_chunks.py
│   └── validate_sources.py
├── frontend/
│   └── streamlit_app.py
├── data/
│   ├── templates/
│   └── processed/
├── docs/
├── tests/
├── qdrant_storage_local/
├── requirements.txt
└── README.md
```

---

## 6. 运行方式

### 6.1 激活环境

```bash
cd "/Users/yuer-xiao/Desktop/AI项目/AI产品经理求职RAG助手/ai_pm_knowledge_framework"
source .venv/bin/activate
```

### 6.2 构建 chunks

```bash
python backend/validate_sources.py
python backend/build_chunks.py
```

### 6.3 导入 Qdrant

```bash
python backend/ingest_qdrant.py --file data/processed/chunks.jsonl --recreate
```

### 6.4 启动后端

```bash
export LLM_API_KEY="你的API Key"
export LLM_BASE_URL="https://api.siliconflow.cn/v1"
export LLM_MODEL="Qwen/Qwen2.5-72B-Instruct"

uvicorn backend.app_rag:app --reload --port 8000
```

### 6.5 启动前端

```bash
streamlit run frontend/streamlit_app.py
```

---

## 7. MVP 测试结果

本项目设计了 15 条测试样例，覆盖 5 个核心场景。评估维度包括：

1. 检索准确性；
2. 回答有用性；
3. 产品视角；
4. 来源引用。

当前 15 条测试样例全部通过，项目已达到可演示 MVP 标准。

---

## 8. 项目亮点

1. 围绕 AI 产品经理求职场景，而不是做泛问答；
2. 构建 JD 库、AI 技术知识库、能力模型库三层知识结构；
3. 使用 L1-L5 能力模型支持个性化能力诊断；
4. 支持结构化回答与参考来源展示；
5. 完成从需求分析、知识库设计、RAG 实现到前端 Demo 和测试评估的完整闭环。

---

## 9. 后续规划

1. 增加 Markdown 导出和复制回答按钮；
2. 增加用户画像表单；
3. 增加简历模板库、面试题库和项目案例库；
4. 支持上传目标 JD 和个人简历；
5. 引入用户反馈闭环，持续优化回答质量。
