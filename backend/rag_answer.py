#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
rag_answer.py

把当前 RAG 流程从“只检索 chunks”升级为：
用户问题 -> Qdrant 检索 -> 拼接上下文 -> 调用 LLM -> 生成结构化回答 -> 输出引用来源

推荐放置位置：
  ai_pm_knowledge_framework/backend/rag_answer.py

先用 mock 模式测试：
  python backend/rag_answer.py --query "RAG产品经理需要懂什么技术" --scenario "知识问答" --top-k 5 --mock

配置 LLM：
  export LLM_API_KEY="你的API Key"
  export LLM_BASE_URL="https://api.openai.com/v1"
  export LLM_MODEL="gpt-4o-mini"
"""

import argparse
import json
import os
import sys
from typing import Any, Dict, List, Optional

import httpx
from qdrant_client import QdrantClient
from qdrant_client.models import FieldCondition, Filter, MatchAny
from sentence_transformers import SentenceTransformer


DEFAULT_COLLECTION = "ai_pm_career_chunks"
DEFAULT_QDRANT_PATH = "qdrant_storage_local"
DEFAULT_EMBEDDING_MODEL = "BAAI/bge-small-zh-v1.5"

DEFAULT_LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
DEFAULT_LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
DEFAULT_LLM_API_KEY = os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY")


SCENARIO_INSTRUCTIONS = {
    "知识问答": """
你是一个面向 AI 产品经理求职者的技术知识解释助手。
请基于检索到的知识片段回答用户问题。

输出结构：
1. 简明回答
2. AI 产品经理需要理解的重点
3. 典型应用场景
4. 常见误区或风险
5. 面试中可以怎么表达
6. 参考来源

要求：
- 不要脱离检索内容胡编。
- 如果检索内容不足，请明确说明“不足以确定”，并给出需要补充的资料类型。
- 面向产品经理表达，不要写成算法工程师教程。
""",
    "JD解析": """
你是 AI 产品经理求职顾问。
请基于检索到的 JD 和技术知识片段，分析用户问题。

输出结构：
1. 结论概览
2. JD 中体现出的岗位方向
3. 高频技术能力要求
4. 高频产品能力要求
5. 求职者应该如何准备
6. 参考来源

要求：
- 尽量结合检索到的 JD 证据。
- 不要只泛泛讲 AI 产品经理。
- 对“实习岗”和“正式岗”的能力要求差异要敏感。
""",
    "能力诊断": """
你是 AI 产品经理求职能力诊断助手。
请基于用户背景、目标岗位、检索到的 JD、AI 技术知识和能力模型，输出结构化能力诊断报告。

必须输出以下结构：

1. 用户当前能力画像
- 根据用户输入，概括用户已有优势和明显短板。
- 不要虚构用户没有说过的经历。

2. 目标岗位能力要求
- 结合检索到的 JD 和能力模型，说明 AI 产品经理实习生通常需要哪些能力。
- 区分“必须具备”和“加分项”。

3. 能力差距表
请用表格输出：
| 能力项 | 用户当前水平 | 目标岗位要求 | 差距判断 | 证据来源 |
|---|---|---|---|---|

其中“用户当前水平”必须尽量用 L1-L5 表示：
L1 = 只知道概念；
L2 = 能解释基础流程；
L3 = 能结合项目应用；
L4 = 能设计评估、风控和迭代；
L5 = 能独立设计方案并指导他人。

4. 优先补强顺序
请按优先级排序：
P0 = 立刻补；
P1 = 近期补；
P2 = 后续补。

5. 4周行动计划
请给出具体行动计划：
第1周做什么；
第2周做什么；
第3周做什么；
第4周做什么。

6. 简历包装建议
请说明用户已有经历应该如何包装成 AI 产品经理项目表达。
不要虚构数据。如果没有真实结果数据，可以写“设计评估方案”“完成核心流程验证”“搭建可运行原型”。

7. 面试表达建议
请给出用户在面试中可以如何表达自己的优势和短板补强计划。

8. 参考来源
列出用到的参考资料，格式为：
[序号] 标题 - 类型

要求：
- 必须结合用户背景做判断，不要泛泛建议。
- 必须引用能力模型中的 L1-L5 标准。
- 如果缺少用户背景，请明确提示用户补充：目标岗位、项目经历、技术基础、产品经历。
- 不要编造没有检索到的信息。
""",
    "项目包装": """
你是 AI 产品经理项目包装与简历优化助手。
请基于检索到的项目、技术知识、JD 片段，帮助用户把 AI 项目包装成产品经理求职表达。

输出结构：
1. 项目应突出什么产品价值
2. 应体现哪些 AI 产品能力
3. 简历 bullet 写法建议
4. 面试中可能被追问的问题
5. 项目还可以如何补强
6. 参考来源

要求：
- 不要只写技术栈。
- 必须突出目标用户、痛点、解决方案、AI 能力、产品机制和评估指标。
- 不要虚构不存在的数据。如果没有结果数据，用“设计了评估方案/完成核心流程验证”等表达。
""",
    "面试准备": """
你是 AI 产品经理面试教练。
请基于检索到的面试相关知识、JD 和技术知识片段，生成面试准备回答。

输出结构：
1. 这个问题考察什么
2. 回答框架
3. 示例回答
4. 面试官可能追问
5. 容易踩坑的回答
6. 参考来源

要求：
- 回答要适合口头表达。
- 尽量给出“产品经理视角”，不是纯技术解释。
- 如果用户问题涉及项目，请引导用户结合自己的项目补充回答。
""",
}


def build_filter(
    scenario: Optional[str],
    source_type: Optional[List[str]],
    role_type: Optional[str],
    ai_topic: Optional[List[str]],
) -> Optional[Filter]:
    must = []
    if scenario:
        must.append(FieldCondition(key="scenario", match=MatchAny(any=[scenario])))
    if source_type:
        must.append(FieldCondition(key="source_type", match=MatchAny(any=source_type)))
    if role_type:
        must.append(FieldCondition(key="role_type", match=MatchAny(any=[role_type])))
    if ai_topic:
        must.append(FieldCondition(key="ai_topic", match=MatchAny(any=ai_topic)))
    return Filter(must=must) if must else None


def get_qdrant_client(qdrant_mode: str, qdrant_path: str, qdrant_url: str) -> QdrantClient:
    if qdrant_mode == "local":
        return QdrantClient(path=qdrant_path)
    if qdrant_mode == "http":
        return QdrantClient(url=qdrant_url)
    raise ValueError(f"Unsupported qdrant_mode: {qdrant_mode}")


def retrieve_chunks(
    query: str,
    scenario: Optional[str],
    top_k: int,
    collection: str,
    embedding_model_name: str,
    qdrant_mode: str,
    qdrant_path: str,
    qdrant_url: str,
    source_type: Optional[List[str]] = None,
    role_type: Optional[str] = None,
    ai_topic: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    model = SentenceTransformer(embedding_model_name)
    client = get_qdrant_client(qdrant_mode, qdrant_path, qdrant_url)
    vector = model.encode([query], normalize_embeddings=True)[0].tolist()
    query_filter = build_filter(scenario, source_type, role_type, ai_topic)

    try:
        response = client.query_points(
            collection_name=collection,
            query=vector,
            query_filter=query_filter,
            limit=top_k,
            with_payload=True,
        )
        hits = response.points
    except AttributeError:
        hits = client.search(
            collection_name=collection,
            query_vector=vector,
            query_filter=query_filter,
            limit=top_k,
            with_payload=True,
        )

    chunks = []
    for rank, hit in enumerate(hits, start=1):
        payload = hit.payload or {}
        chunks.append({
            "rank": rank,
            "score": float(getattr(hit, "score", 0.0) or 0.0),
            "chunk_id": payload.get("chunk_id") or payload.get("source_id") or "",
            "title": payload.get("title", ""),
            "source_type": payload.get("source_type", ""),
            "scenario": payload.get("scenario", []),
            "role_type": payload.get("role_type", []),
            "ai_topic": payload.get("ai_topic", []),
            "career_topic": payload.get("career_topic", []),
            "product_topic": payload.get("product_topic", []),
            "source_name": payload.get("source_name", ""),
            "source_url": payload.get("source_url", ""),
            "reliability": payload.get("reliability", ""),
            "text": payload.get("text", ""),
        })
    return chunks


def format_context(chunks: List[Dict[str, Any]], max_chars_per_chunk: int = 1800) -> str:
    parts = []
    for c in chunks:
        text = (c.get("text") or "").strip()
        if len(text) > max_chars_per_chunk:
            text = text[:max_chars_per_chunk] + "..."
        source_line = f"[{c['rank']}] {c.get('title', '')} | 类型: {c.get('source_type', '')} | 可信度: {c.get('reliability', '')}"
        if c.get("source_name"):
            source_line += f" | 来源: {c.get('source_name')}"
        if c.get("source_url"):
            source_line += f" | 链接: {c.get('source_url')}"
        parts.append(f"{source_line}\n{text}")
    return "\n\n---\n\n".join(parts)


def build_prompt(query: str, scenario: str, chunks: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    instruction = SCENARIO_INSTRUCTIONS.get(scenario, SCENARIO_INSTRUCTIONS["知识问答"])
    context = format_context(chunks)

    system_prompt = """
你是“AI 产品经理求职 RAG 助手”的核心回答模块。
你的任务是：严格基于检索到的资料，为 AI 产品经理求职者生成结构化、可执行的回答。

通用规则：
- 优先依据【检索资料】回答。
- 不要编造来源、公司、岗位、数字或事实。
- 如果资料不足，直接说明不足，并告诉用户还需要补充什么。
- 回答要清晰、直接、适合用于求职准备。
- 最后一节必须列出参考来源，格式为：[序号] 标题 - 类型。
""".strip()

    user_prompt = f"""
【用户问题】
{query}

【当前场景】
{scenario}

【场景要求】
{instruction.strip()}

【检索资料】
{context}
""".strip()

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def call_llm(
    messages: List[Dict[str, str]],
    api_key: Optional[str],
    base_url: str,
    model: str,
    temperature: float = 0.2,
    timeout: int = 120,
) -> str:
    if not api_key:
        raise RuntimeError(
            "未找到 LLM API Key。请设置环境变量 LLM_API_KEY 或 OPENAI_API_KEY；"
            "或者使用 --mock 只查看检索结果和 Prompt。"
        )

    url = base_url.rstrip("/") + "/chat/completions"
    payload = {"model": model, "messages": messages, "temperature": temperature}
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    with httpx.Client(timeout=timeout) as client:
        resp = client.post(url, headers=headers, json=payload)
        if resp.status_code >= 400:
            raise RuntimeError(f"LLM API error {resp.status_code}: {resp.text}")
        data = resp.json()

    try:
        return data["choices"][0]["message"]["content"]
    except Exception as exc:
        raise RuntimeError(f"Unexpected LLM response format: {json.dumps(data, ensure_ascii=False)[:1000]}") from exc


def print_retrieved_sources(chunks: List[Dict[str, Any]]) -> None:
    print("\n" + "=" * 88)
    print("检索到的参考资料")
    print("=" * 88)
    for c in chunks:
        print(f"[{c['rank']}] score={c['score']:.4f}")
        print(f"标题：{c.get('title')}")
        print(f"类型：{c.get('source_type')}")
        print(f"AI Topic：{c.get('ai_topic')}")
        print(f"来源：{c.get('source_name') or '未填写'}")
        if c.get("source_url"):
            print(f"链接：{c.get('source_url')}")
        print("-" * 88)


def make_mock_answer(query: str, scenario: str, chunks: List[Dict[str, Any]]) -> str:
    sources = "\n".join([f"- [{c['rank']}] {c.get('title')} - {c.get('source_type')}" for c in chunks])
    top_titles = "、".join([c.get("title", "") for c in chunks[:3]])
    return f"""
【MOCK 模式：未调用 LLM】

用户问题：{query}
场景：{scenario}

已成功检索到 {len(chunks)} 条资料。Top 3 为：{top_titles}

下一步如果配置 LLM_API_KEY，本脚本会把这些资料拼进 Prompt，并生成结构化回答。

参考来源：
{sources}
""".strip()


def save_output(path: Optional[str], data: Dict[str, Any]) -> None:
    if not path:
        return
    out_path = os.path.abspath(path)
    out_dir = os.path.dirname(out_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"\n已保存 JSON 输出：{out_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="AI PM Career RAG Answer Script")
    parser.add_argument("--query", required=True, help="用户问题")
    parser.add_argument("--scenario", default="知识问答", choices=list(SCENARIO_INSTRUCTIONS.keys()), help="场景")
    parser.add_argument("--top-k", type=int, default=5, help="检索数量")
    parser.add_argument("--collection", default=DEFAULT_COLLECTION)
    parser.add_argument("--embedding-model", default=DEFAULT_EMBEDDING_MODEL)
    parser.add_argument("--qdrant-mode", choices=["local", "http"], default="local")
    parser.add_argument("--qdrant-path", default=DEFAULT_QDRANT_PATH)
    parser.add_argument("--qdrant-url", default="http://localhost:6333")
    parser.add_argument("--source-type", nargs="*", default=None, help="可选过滤，如 AI知识 JD 面试题")
    parser.add_argument("--role-type", default=None, help="可选过滤，如 AI产品经理 RAG产品经理")
    parser.add_argument("--ai-topic", nargs="*", default=None, help="可选过滤，如 RAG Agent Prompt")
    parser.add_argument("--llm-base-url", default=DEFAULT_LLM_BASE_URL)
    parser.add_argument("--llm-model", default=DEFAULT_LLM_MODEL)
    parser.add_argument("--temperature", type=float, default=0.2)
    parser.add_argument("--mock", action="store_true", help="不调用 LLM，只测试检索和 Prompt")
    parser.add_argument("--show-prompt", action="store_true", help="打印最终发送给 LLM 的 Prompt")
    parser.add_argument("--save-json", default=None, help="保存完整输出到 JSON 文件")
    args = parser.parse_args()

    print("开始检索...")
    chunks = retrieve_chunks(
        query=args.query,
        scenario=args.scenario,
        top_k=args.top_k,
        collection=args.collection,
        embedding_model_name=args.embedding_model,
        qdrant_mode=args.qdrant_mode,
        qdrant_path=args.qdrant_path,
        qdrant_url=args.qdrant_url,
        source_type=args.source_type,
        role_type=args.role_type,
        ai_topic=args.ai_topic,
    )

    if not chunks:
        print("没有检索到任何 chunk。请检查 collection、scenario 或知识库是否已导入。")
        sys.exit(1)

    messages = build_prompt(args.query, args.scenario, chunks)

    if args.show_prompt:
        print("\n" + "=" * 88)
        print("Prompt 预览")
        print("=" * 88)
        print(messages[-1]["content"])

    if args.mock:
        answer = make_mock_answer(args.query, args.scenario, chunks)
    else:
        answer = call_llm(
            messages=messages,
            api_key=DEFAULT_LLM_API_KEY,
            base_url=args.llm_base_url,
            model=args.llm_model,
            temperature=args.temperature,
        )

    print("\n" + "=" * 88)
    print("RAG 回答")
    print("=" * 88)
    print(answer)

    print_retrieved_sources(chunks)

    save_output(args.save_json, {
        "query": args.query,
        "scenario": args.scenario,
        "answer": answer,
        "retrieved_chunks": chunks,
        "messages": messages if args.show_prompt else None,
    })


if __name__ == "__main__":
    main()
