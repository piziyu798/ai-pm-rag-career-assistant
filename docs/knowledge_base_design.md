# AI 产品经理求职 RAG 助手：知识库设计文档

> 版本：v1.0  
> 日期：2026-05-07  
> 知识库类型：JD 库、AI 技术知识库、能力模型库

---

## 1. 设计目标

本项目的知识库不是通用百科，而是围绕 AI 产品经理求职场景设计的垂直知识库。它需要同时支持：

1. JD 解析；
2. AI 技术知识问答；
3. 能力诊断；
4. 项目包装；
5. 面试准备。

因此，知识库需要覆盖三类内容：

```text
岗位需要什么 → JD 库
技术概念是什么 → AI 技术知识库
用户差在哪里 → 能力模型库
```

---

## 2. 知识库总体结构

| 知识库 | 数量 | 作用 |
|---|---:|---|
| JD 库 | 32 条 | 提供岗位要求、职责、任职要求、加分项等证据 |
| AI 技术知识库 | 71 条 | 解释 RAG、Agent、Prompt、评估、AIGC、API 等技术概念 |
| 能力模型库 | 12 条 | 支撑 L1-L5 能力诊断和补强建议 |

合计：

```text
32 + 71 + 12 = 115 chunks
```

---

## 3. JD 库设计

### 3.1 字段结构

| 字段 | 含义 |
|---|---|
| source_id | JD 唯一编号 |
| title | JD 标题 |
| company_name | 公司名称 |
| company_type | 公司类型 |
| job_title | 岗位名称 |
| role_type | 岗位类型 |
| seniority | 岗位级别 |
| responsibilities | 岗位职责 |
| requirements | 任职要求 |
| bonus_points | 加分项 |
| skill_keywords | 技术关键词 |
| product_keywords | 产品关键词 |
| source_name | 来源名称 |
| source_url | 来源链接 |
| reliability | 可信度 |
| notes | 备注 |

### 3.2 设计价值

JD 库用于回答：

1. AI 产品经理岗位主要有哪些方向？
2. 实习岗通常需要什么能力？
3. Agent / RAG / Prompt 在 JD 中如何出现？
4. 用户项目与目标岗位是否匹配？
5. 哪些能力是必备项，哪些是加分项？

---

## 4. AI 技术知识库设计

### 4.1 字段结构

| 字段 | 含义 |
|---|---|
| source_id | 知识点编号 |
| title | 知识点标题 |
| concept_name | 概念名称 |
| content | 核心解释 |
| pm_relevance | AI 产品经理为什么需要懂 |
| use_cases | 应用场景 |
| risks_or_misunderstandings | 风险、误区或边界 |
| ai_topic | AI 技术主题 |
| product_topic | 产品主题 |
| difficulty | 难度 |
| source_name | 来源名称 |
| source_url | 来源链接 |
| reliability | 可信度 |
| notes | 备注 |

### 4.2 分类

| 分类 | 示例知识点 |
|---|---|
| 大模型基础 | LLM、Token、上下文窗口、模型能力边界 |
| Prompt Engineering | 结构化输出、Few-shot、Prompt 模板化 |
| RAG | Chunk、Embedding、Vector DB、Rerank、引用溯源 |
| Agent | Planning、Tool Use、Function Calling、Memory、Multi-Agent |
| Workflow / 工具 | Dify、Coze、n8n、LangChain、LlamaIndex |
| AI 产品评估 | Answer Relevancy、Faithfulness、Context Precision、任务完成率 |
| 风控与可信机制 | 幻觉、Guardrails、数据隐私、权限控制 |
| AIGC / 多模态 | 文生图、文生视频、数字人、多模态大模型 |
| AI 产品工程理解 | LLM API、前后端协作、日志监控、灰度发布 |

### 4.3 设计原则

1. 不把知识库写成算法教程；
2. 每条知识都强调产品经理相关性；
3. 避免过度结构化导致字段重复；
4. 将面试表达交给 Prompt 动态生成；
5. 保留来源字段，支持后续引用溯源。

---

## 5. 能力模型库设计

### 5.1 字段结构

| 字段 | 含义 |
|---|---|
| source_id | 能力项编号 |
| title | 能力标题 |
| capability_name | 能力名称 |
| level_l1 - level_l5 | 能力等级描述 |
| diagnosis_rules | 诊断规则 |
| improvement_suggestions | 提升建议 |
| role_type | 适用岗位 |
| ai_topic | 关联 AI 技术主题 |
| career_topic | 关联求职场景 |
| reliability | 可信度 |
| difficulty | 难度 |
| notes | 备注 |

### 5.2 12 个核心能力项

| 编号 | 能力项 |
|---|---|
| cap_001 | RAG 产品理解能力 |
| cap_002 | Agent 产品理解能力 |
| cap_003 | Prompt 设计能力 |
| cap_004 | AI 产品评估能力 |
| cap_005 | AI 工具与工作流搭建能力 |
| cap_006 | 产品需求分析能力 |
| cap_007 | PRD / 原型 / 交互表达能力 |
| cap_008 | 数据分析能力 |
| cap_009 | 技术协作与 API 理解能力 |
| cap_010 | 项目推进与落地能力 |
| cap_011 | AI 项目简历包装能力 |
| cap_012 | AI 产品面试表达能力 |

### 5.3 L1-L5 等级体系

| 等级 | 含义 |
|---|---|
| L1 | 概念认知：知道名词和基本作用 |
| L2 | 流程理解：能解释基础流程 |
| L3 | 项目应用：能结合自己的项目说明如何应用 |
| L4 | 评估迭代：能设计指标、风险控制和优化路径 |
| L5 | 独立方案设计：能根据业务场景做系统方案设计 |

---

## 6. Chunk 构建策略

当前 MVP 采用“一行一 chunk”的策略：

| 来源 | Chunk 策略 |
|---|---|
| JD 库 | 每条 JD 生成一个 chunk |
| AI 技术知识库 | 每个知识点生成一个 chunk |
| 能力模型库 | 每个能力项生成一个 chunk |

这样做的原因：

1. 当前知识条目较短，不需要复杂切分；
2. 每条记录天然具有完整语义；
3. 方便追踪来源；
4. 方便后续测试和调试。

---

## 7. 元数据设计

每个 chunk 包含以下元数据：

| 字段 | 作用 |
|---|---|
| chunk_id | 唯一标识 |
| source_id | 来源编号 |
| title | 展示标题 |
| source_type | JD / AI知识 / 能力模型 |
| scenario | 适用场景 |
| role_type | 适用岗位 |
| ai_topic | AI 技术主题 |
| career_topic | 求职主题 |
| product_topic | 产品主题 |
| difficulty | 难度 |
| reliability | 可信度 |
| source_name | 来源名称 |
| source_url | 来源链接 |
| notes | 备注 |

这些元数据用于：

1. 场景过滤；
2. 来源展示；
3. 检索调试；
4. 前端来源卡片展示；
5. 后续扩展排序策略。

---

## 8. 检索策略

当前 MVP 使用：

```text
Embedding 模型：BAAI/bge-small-zh-v1.5
向量数据库：Qdrant 本地模式
检索方式：语义向量检索
Top-K：默认 8-10
```

不同场景的推荐 Top-K：

| 场景 | 推荐 Top-K |
|---|---:|
| 知识问答 | 5-8 |
| JD 解析 | 8-10 |
| 能力诊断 | 10 |
| 项目包装 | 10 |
| 面试准备 | 8-10 |

---

## 9. 后续知识库迭代

| 方向 | 说明 | 优先级 |
|---|---|---|
| Compare 类知识点 | 补充 Agent/RAG/Workflow 等对比型问题 | P1 |
| 面试题库 | 增加 AI PM 技术面和项目面试问题 | P1 |
| 简历模板库 | 增加项目 bullet 模板 | P1 |
| 项目案例库 | 增加 RAG、Agent、Copilot 项目案例 | P1 |
| 用户画像库 | 支持更稳定的个性化诊断 | P2 |

---

## 10. 设计结论

本项目的知识库设计采用“岗位证据 + 技术理解 + 能力诊断”的三层结构，使系统能够从不同角度支持 AI 产品经理求职任务。

这种设计相比单一技术知识库更适合求职场景，因为它不仅回答“技术是什么”，还回答：

1. 岗位为什么需要它；
2. 用户是否具备它；
3. 用户应该如何补齐；
4. 如何把它写进简历和面试回答。
