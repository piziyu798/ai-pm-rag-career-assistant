#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
app_rag.py

FastAPI 后端服务，把命令行版 rag_answer.py 产品化为 HTTP API。

推荐放置位置：
  ai_pm_knowledge_framework/backend/app_rag.py

运行方式：
  uvicorn backend.app_rag:app --reload --port 8000
"""

import os
import time
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

try:
    from backend.rag_answer import (
        DEFAULT_COLLECTION,
        DEFAULT_EMBEDDING_MODEL,
        DEFAULT_QDRANT_PATH,
        build_prompt,
        call_llm,
        make_mock_answer,
        retrieve_chunks,
    )
except ModuleNotFoundError:
    from rag_answer import (
        DEFAULT_COLLECTION,
        DEFAULT_EMBEDDING_MODEL,
        DEFAULT_QDRANT_PATH,
        build_prompt,
        call_llm,
        make_mock_answer,
        retrieve_chunks,
    )


SCENARIOS = ["知识问答", "JD解析", "能力诊断", "项目包装", "面试准备"]


def get_llm_api_key() -> Optional[str]:
    return os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY")


def get_llm_base_url() -> str:
    return os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")


def get_llm_model() -> str:
    return os.getenv("LLM_MODEL", "gpt-4o-mini")


app = FastAPI(
    title="AI 产品经理求职 RAG 助手 API",
    description="基于 JD 库、AI 技术知识库和能力模型库的场景化 RAG 回答服务。",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class RagAnswerRequest(BaseModel):
    query: str = Field(..., min_length=1, description="用户问题")
    scenario: str = Field("知识问答", description="场景：知识问答/JD解析/能力诊断/项目包装/面试准备")
    top_k: int = Field(8, ge=1, le=20, description="检索 Top-K")
    mock: bool = Field(False, description="是否只测试检索，不调用 LLM")

    source_type: Optional[List[str]] = Field(None, description="可选过滤：AI知识/JD/能力模型/项目案例/简历模板/面试题")
    role_type: Optional[str] = Field(None, description="可选过滤：AI产品经理/RAG产品经理/Agent产品经理等")
    ai_topic: Optional[List[str]] = Field(None, description="可选过滤：RAG/Agent/Prompt 等")

    collection: str = Field(DEFAULT_COLLECTION, description="Qdrant collection 名称")
    qdrant_mode: str = Field("local", description="local 或 http")
    qdrant_path: str = Field(DEFAULT_QDRANT_PATH, description="本地 Qdrant 路径")
    qdrant_url: str = Field("http://localhost:6333", description="HTTP Qdrant URL")
    embedding_model: str = Field(DEFAULT_EMBEDDING_MODEL, description="Embedding 模型名")
    temperature: float = Field(0.2, ge=0.0, le=2.0, description="LLM temperature")


class SourceItem(BaseModel):
    rank: int
    score: float
    title: str
    source_type: str
    ai_topic: List[str] = []
    source_name: str = ""
    source_url: str = ""
    reliability: str = ""
    chunk_id: str = ""


class RagAnswerResponse(BaseModel):
    query: str
    scenario: str
    answer: str
    sources: List[SourceItem]
    elapsed_seconds: float
    model: str
    mock: bool


@app.get("/health")
def health() -> Dict[str, Any]:
    return {
        "status": "ok",
        "service": "AI 产品经理求职 RAG 助手 API",
        "llm_base_url": get_llm_base_url(),
        "llm_model": get_llm_model(),
        "has_api_key": bool(get_llm_api_key()),
        "scenarios": SCENARIOS,
    }


@app.get("/scenarios")
def scenarios() -> Dict[str, List[str]]:
    return {"scenarios": SCENARIOS}


@app.post("/rag/answer", response_model=RagAnswerResponse)
def rag_answer(req: RagAnswerRequest) -> RagAnswerResponse:
    start = time.time()

    if req.scenario not in SCENARIOS:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的 scenario: {req.scenario}. 可选值：{SCENARIOS}",
        )

    try:
        chunks = retrieve_chunks(
            query=req.query,
            scenario=req.scenario,
            top_k=req.top_k,
            collection=req.collection,
            embedding_model_name=req.embedding_model,
            qdrant_mode=req.qdrant_mode,
            qdrant_path=req.qdrant_path,
            qdrant_url=req.qdrant_url,
            source_type=req.source_type,
            role_type=req.role_type,
            ai_topic=req.ai_topic,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"检索失败：{exc}") from exc

    if not chunks:
        raise HTTPException(
            status_code=404,
            detail="没有检索到任何 chunk。请确认已导入 Qdrant，或放宽过滤条件。",
        )

    try:
        if req.mock:
            answer = make_mock_answer(req.query, req.scenario, chunks)
        else:
            messages = build_prompt(req.query, req.scenario, chunks)
            answer = call_llm(
                messages=messages,
                api_key=get_llm_api_key(),
                base_url=get_llm_base_url(),
                model=get_llm_model(),
                temperature=req.temperature,
            )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"生成回答失败：{exc}") from exc

    sources = [
        SourceItem(
            rank=c.get("rank", 0),
            score=round(float(c.get("score", 0.0)), 6),
            title=c.get("title", ""),
            source_type=c.get("source_type", ""),
            ai_topic=c.get("ai_topic", []) or [],
            source_name=c.get("source_name", ""),
            source_url=c.get("source_url", ""),
            reliability=c.get("reliability", ""),
            chunk_id=c.get("chunk_id", ""),
        )
        for c in chunks
    ]

    return RagAnswerResponse(
        query=req.query,
        scenario=req.scenario,
        answer=answer,
        sources=sources,
        elapsed_seconds=round(time.time() - start, 3),
        model=get_llm_model(),
        mock=req.mock,
    )
