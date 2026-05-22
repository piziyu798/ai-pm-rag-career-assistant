# Metadata 标注规则

每条 chunk 都要包含以下核心字段：

| 字段 | 是否必填 | 示例 |
|---|---|---|
| chunk_id | 是 | jd_001_req |
| title | 是 | AI 产品经理实习 JD |
| text | 是 | chunk 正文 |
| source_type | 是 | JD / AI知识 / 能力模型 / 项目案例 / 简历模板 / 面试题 |
| scenario | 是 | JD解析 / 能力诊断 / 项目包装 / 面试准备 / 知识问答 |
| role_type | 是 | AI产品经理 / RAG产品经理 / Agent产品经理 |
| ai_topic | 否 | RAG / Agent / Prompt |
| career_topic | 否 | JD / 简历 / 面试 / 项目包装 |
| product_topic | 否 | MVP / 需求分析 / 指标设计 |
| difficulty | 否 | 入门 / 中级 / 高级 |
| reliability | 是 | high / medium / low |

## 场景标签建议

### JD 解析
适合内容：
- JD 原文
- 岗位职责
- 任职要求
- 能力模型
- 岗位关键词解释

### 能力诊断
适合内容：
- 能力模型
- 岗位要求
- 能力等级
- 补强建议

### 项目包装
适合内容：
- 项目案例
- 简历 bullet 模板
- 产品经理表达模板
- 项目亮点提炼方法

### 面试准备
适合内容：
- 面试题
- 回答框架
- 项目深挖题
- 追问预测
- AI 产品知识

### 知识问答
适合内容：
- AI 概念解释
- 产品方法论
- RAG/Agent/Prompt 知识
- 评估指标
