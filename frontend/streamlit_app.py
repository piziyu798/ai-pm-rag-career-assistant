#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
streamlit_app.py

AI 产品经理求职 RAG 助手 Demo 前端。

运行前先启动后端：
  uvicorn backend.app_rag:app --reload --port 8000

再另开终端启动前端：
  streamlit run frontend/streamlit_app.py
"""

from typing import Dict, List

import requests
import streamlit as st


DEFAULT_API_URL = "http://127.0.0.1:8000"
SCENARIOS = ["知识问答", "JD解析", "能力诊断", "项目包装", "面试准备"]

EXAMPLE_QUERIES: Dict[str, str] = {
    "知识问答": "RAG产品经理需要懂什么技术？",
    "JD解析": "AI产品经理实习生通常需要具备哪些技术和产品能力？",
    "能力诊断": "我是经济统计专业学生，会一点Python和SQL，做过RAG项目，但不太懂Agent，我距离AI产品经理实习还差什么？",
    "项目包装": "我做了一个AI产品经理求职RAG助手，包含JD解析、技术知识问答、能力诊断和面试准备，我应该怎么包装成AI产品经理项目经历？",
    "面试准备": "面试官问我为什么适合AI产品经理实习生，我应该怎么结合RAG项目、Python、SQL和经济统计背景回答？",
}


st.set_page_config(
    page_title="AI 产品经理求职 RAG 助手",
    page_icon="🧠",
    layout="wide",
)


def call_backend(
    api_url: str,
    query: str,
    scenario: str,
    top_k: int,
    mock: bool,
    temperature: float,
) -> Dict:
    payload = {
        "query": query,
        "scenario": scenario,
        "top_k": top_k,
        "mock": mock,
        "temperature": temperature,
    }
    resp = requests.post(f"{api_url.rstrip('/')}/rag/answer", json=payload, timeout=180)
    if resp.status_code >= 400:
        raise RuntimeError(f"API Error {resp.status_code}: {resp.text}")
    return resp.json()


def render_sources(sources: List[Dict]) -> None:
    if not sources:
        st.info("暂无参考来源")
        return

    for src in sources:
        title = src.get("title", "")
        source_type = src.get("source_type", "")
        score = src.get("score", 0)
        reliability = src.get("reliability", "")
        ai_topic = ", ".join(src.get("ai_topic") or [])

        with st.expander(f"[{src.get('rank')}] {title} · {source_type} · score={score}"):
            st.write(f"**类型：** {source_type}")
            st.write(f"**可信度：** {reliability or '未填写'}")
            st.write(f"**AI Topic：** {ai_topic or '未填写'}")
            if src.get("source_name"):
                st.write(f"**来源名称：** {src.get('source_name')}")
            if src.get("source_url"):
                st.write(f"**来源链接：** {src.get('source_url')}")
            if src.get("chunk_id"):
                st.code(src.get("chunk_id"))


st.title(" AI 产品经理求职 RAG 助手")
st.caption("基于 JD 库、AI 技术知识库和能力模型库，支持知识问答、JD解析、能力诊断、项目包装和面试准备。")

with st.sidebar:
    st.header("配置")
    api_url = st.text_input("后端 API 地址", value=DEFAULT_API_URL)
    scenario = st.selectbox("使用场景", SCENARIOS, index=SCENARIOS.index("能力诊断"))
    top_k = st.slider("检索 Top-K", min_value=3, max_value=20, value=10, step=1)
    temperature = st.slider("生成温度 temperature", min_value=0.0, max_value=1.0, value=0.2, step=0.1)
    mock = st.toggle("Mock 模式：只检索，不调用大模型", value=False)
    show_sources = st.toggle("展示参考来源", value=True)

    st.divider()
    st.markdown("### 场景说明")
    st.markdown(
        """
- **知识问答**：解释 RAG、Agent、Prompt 等技术概念  
- **JD解析**：分析岗位要求和能力关键词  
- **能力诊断**：判断用户能力差距和补强路径  
- **项目包装**：把 AI 项目包装成简历/面试表达  
- **面试准备**：生成回答框架、示例回答和追问  
        """
    )

default_query = EXAMPLE_QUERIES.get(scenario, "")
query = st.text_area(
    "请输入你的问题 / 背景 / JD / 项目描述",
    value=default_query,
    height=180,
)

submit = st.button("生成回答", type="primary")

if submit:
    if not query.strip():
        st.warning("请输入问题后再生成。")
    else:
        with st.spinner("正在检索知识库并生成回答..."):
            try:
                data = call_backend(
                    api_url=api_url,
                    query=query.strip(),
                    scenario=scenario,
                    top_k=top_k,
                    mock=mock,
                    temperature=temperature,
                )
            except Exception as exc:
                st.error(str(exc))
                st.stop()

        st.success(f"生成完成，用时 {data.get('elapsed_seconds')} 秒，模型：{data.get('model')}")
        st.subheader("回答")
        st.markdown(data.get("answer", ""))

        if show_sources:
            st.subheader("参考来源")
            render_sources(data.get("sources", []))

        with st.expander("查看原始 JSON"):
            st.json(data)
else:
    st.info("选择场景并点击“生成回答”。第一次运行可能需要加载 embedding 模型，会稍慢。")
