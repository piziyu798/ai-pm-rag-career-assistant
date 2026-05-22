# AI 产品经理求职 RAG 助手：知识库框架

这个包只负责“知识库框架”，不内置正式知识内容。你负责收集内容，我负责把内容组织成可导入、可检索、可引用的 RAG 知识库结构。

## 核心目标

知识库服务 5 个 MVP 场景：

1. AI 产品经理 JD 解析
2. 个人能力诊断
3. AI 项目简历包装
4. AI 产品面试准备
5. AI 产品知识问答

## 推荐知识库分类

| 分类 | 文件模板 | 用途 |
|---|---|---|
| JD 库 | `data/templates/jd_template.csv` | 支撑 JD 解析、岗位能力提取 |
| AI 产品知识库 | `data/templates/ai_knowledge_template.csv` | 支撑 RAG、Agent、Prompt 等知识问答 |
| 能力模型库 | `data/templates/capability_model_template.csv` | 支撑能力诊断 |
| 项目案例库 | `data/templates/project_case_template.csv` | 支撑项目包装、面试深挖 |
| 简历模板库 | `data/templates/resume_template_template.csv` | 支撑简历 bullet 生成 |
| 面试题库 | `data/templates/interview_question_template.csv` | 支撑面试准备 |

## 你要怎么用

### 1. 先填模板

把你找到的资料整理到 `data/templates/*.csv` 对应模板中。

例如：
- 找到一个 AI 产品经理 JD，就填到 `jd_template.csv`
- 找到一个 RAG 概念解释，就填到 `ai_knowledge_template.csv`
- 找到一个面试题，就填到 `interview_question_template.csv`

### 2. 校验 CSV

```bash
python backend/validate_sources.py
```

### 3. 生成 chunks

```bash
python backend/build_chunks.py
```

生成结果：

```text
data/processed/chunks.jsonl
```

### 4. 启动 Qdrant

```bash
docker run -p 6333:6333 -p 6334:6334 \
  -v "$(pwd)/qdrant_storage:/qdrant/storage" \
  qdrant/qdrant
```

Windows PowerShell：

```powershell
docker run -p 6333:6333 -p 6334:6334 -v "${PWD}/qdrant_storage:/qdrant/storage" qdrant/qdrant
```

### 5. 安装依赖

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Windows PowerShell：

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 6. 导入 Qdrant

```bash
python backend/ingest_qdrant.py --file data/processed/chunks.jsonl --recreate
```

### 7. 测试检索

```bash
python backend/retrieve_qdrant.py \
  --query "我的RAG项目怎么写进简历" \
  --scenario "项目包装" \
  --top-k 5
```

## 第一版建议内容规模

| 知识库 | 第一版目标 |
|---|---:|
| JD 库 | 20-30 条 |
| AI 产品知识库 | 50-80 条 |
| 能力模型库 | 20-30 条 |
| 项目案例库 | 15-25 条 |
| 简历模板库 | 20-30 条 |
| 面试题库 | 80-120 条 |

第一版不要追求数量，优先保证结构清晰、标签准确、来源可靠。
