#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
build_chunks.py

作用：
把 data/templates/*.csv 转换为 data/processed/chunks.jsonl。

支持：
1. JD 库：jd_template.csv
2. 新版 AI 技术知识库：ai_knowledge_template.csv
3. 能力模型库：capability_model_template.csv
4. 项目案例库：project_case_template.csv
5. 简历模板库：resume_template_template.csv
6. 面试题库：interview_question_template.csv

使用：
  python backend/build_chunks.py

输出：
  data/processed/chunks.jsonl

注意：
- 本脚本只做结构化转换，不判断资料真实性。
- 新版 AI 技术知识库字段为：
  source_id,title,concept_name,content,pm_relevance,use_cases,
  risks_or_misunderstandings,ai_topic,product_topic,difficulty,
  source_name,source_url,reliability,notes
"""

import csv
import json
import re
from pathlib import Path
from typing import Dict, List, Iterable, Optional


TEMPLATE_DIR = Path("data/templates")
OUT_PATH = Path("data/processed/chunks.jsonl")


def clean_text(value: Optional[str]) -> str:
    if value is None:
        return ""
    text = str(value).replace("\r\n", "\n").replace("\r", "\n").strip()
    # 压缩过多空行
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text


def split_list(value: Optional[str]) -> List[str]:
    """
    把 CSV 中的多值字段切成 list。
    支持英文逗号、中文逗号、顿号、分号、换行。
    """
    if value is None:
        return []
    raw = str(value).strip()
    if not raw:
        return []
    if raw.lower() == "none":
        return []

    for sep in ["，", "、", "；", ";", "\n", " / ", "/"]:
        raw = raw.replace(sep, ",")
    return [x.strip() for x in raw.split(",") if x.strip()]


def read_csv(filename: str) -> List[Dict[str, str]]:
    path = TEMPLATE_DIR / filename
    if not path.exists():
        print(f"[WARN] Missing template file, skipped: {path}")
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    # 跳过完全空白行
    return [r for r in rows if any((v or "").strip() for v in r.values())]


def section(title: str, body: Optional[str]) -> str:
    body = clean_text(body)
    if not body:
        return ""
    return f"{title}：\n{body}"


def join_sections(*parts: str) -> str:
    return "\n\n".join([p for p in parts if p.strip()]).strip()


def base_payload(
    row: Dict[str, str],
    source_type: str,
    scenarios: List[str],
    text: str,
    title: Optional[str] = None,
    role_type: Optional[Iterable[str]] = None,
    ai_topic: Optional[Iterable[str]] = None,
    career_topic: Optional[Iterable[str]] = None,
    product_topic: Optional[Iterable[str]] = None,
) -> Dict:
    source_id = clean_text(row.get("source_id"))
    if not source_id:
        raise ValueError(f"Missing source_id in source_type={source_type}, title={row.get('title')}")

    return {
        "chunk_id": f"{source_type}_{source_id}",
        "source_id": source_id,
        "title": clean_text(title or row.get("title")),
        "text": clean_text(text),
        "source_type": source_type,
        "scenario": scenarios,
        "role_type": list(role_type or split_list(row.get("role_type")) or ["AI产品经理"]),
        "ai_topic": list(ai_topic or split_list(row.get("ai_topic"))),
        "career_topic": list(career_topic or split_list(row.get("career_topic"))),
        "product_topic": list(product_topic or split_list(row.get("product_topic"))),
        "difficulty": clean_text(row.get("difficulty")) or "入门",
        "reliability": clean_text(row.get("reliability")) or "medium",
        "source_name": clean_text(row.get("source_name")),
        "source_url": clean_text(row.get("source_url")),
        "notes": clean_text(row.get("notes")),
    }


def build_jd_chunks() -> List[Dict]:
    chunks = []
    for row in read_csv("jd_template.csv"):
        source_id = clean_text(row.get("source_id"))
        if not source_id:
            continue

        text = join_sections(
            f"岗位标题：{clean_text(row.get('title'))}",
            f"公司名称：{clean_text(row.get('company_name'))}",
            f"公司类型：{clean_text(row.get('company_type'))}",
            f"岗位名称：{clean_text(row.get('job_title'))}",
            f"岗位类型：{clean_text(row.get('role_type'))}",
            f"岗位级别：{clean_text(row.get('seniority'))}",
            section("岗位职责", row.get("responsibilities")),
            section("任职要求", row.get("requirements")),
            section("加分项", row.get("bonus_points")),
            section("技术关键词", row.get("skill_keywords")),
            section("产品关键词", row.get("product_keywords")),
            section("备注", row.get("notes")),
        )

        # JD 中 skill_keywords 可作为 ai_topic 的弱标签，product_keywords 可作为 product_topic 的弱标签
        chunks.append(base_payload(
            row=row,
            source_type="JD",
            scenarios=["JD解析", "能力诊断", "面试准备"],
            text=text,
            role_type=split_list(row.get("role_type")) or ["AI产品经理"],
            ai_topic=split_list(row.get("skill_keywords")),
            career_topic=["JD", "面试"],
            product_topic=split_list(row.get("product_keywords")),
        ))

    return chunks


def build_ai_knowledge_chunks() -> List[Dict]:
    """
    新版 AI 技术知识库字段：
    source_id,title,concept_name,content,pm_relevance,use_cases,
    risks_or_misunderstandings,ai_topic,product_topic,difficulty,
    source_name,source_url,reliability,notes
    """
    chunks = []
    for row in read_csv("ai_knowledge_template.csv"):
        source_id = clean_text(row.get("source_id"))
        if not source_id:
            continue

        text = join_sections(
            f"知识点标题：{clean_text(row.get('title'))}",
            f"概念名称：{clean_text(row.get('concept_name'))}",
            section("核心知识", row.get("content")),
            section("AI 产品经理相关性", row.get("pm_relevance")),
            section("典型应用场景", row.get("use_cases")),
            section("风险、误区或边界", row.get("risks_or_misunderstandings")),
            section("技术主题", row.get("ai_topic")),
            section("产品主题", row.get("product_topic")),
            section("备注", row.get("notes")),
        )

        chunks.append(base_payload(
            row=row,
            source_type="AI知识",
            scenarios=["知识问答", "JD解析", "能力诊断", "项目包装", "面试准备"],
            text=text,
            role_type=["AI产品经理"],
            ai_topic=split_list(row.get("ai_topic")),
            career_topic=["知识问答", "面试", "项目包装"],
            product_topic=split_list(row.get("product_topic")),
        ))

    return chunks


def build_capability_model_chunks() -> List[Dict]:
    chunks = []
    for row in read_csv("capability_model_template.csv"):
        source_id = clean_text(row.get("source_id"))
        if not source_id:
            continue

        text = join_sections(
            f"能力项：{clean_text(row.get('capability_name'))}",
            section("L1", row.get("level_l1")),
            section("L2", row.get("level_l2")),
            section("L3", row.get("level_l3")),
            section("L4", row.get("level_l4")),
            section("L5", row.get("level_l5")),
            section("诊断规则", row.get("diagnosis_rules")),
            section("提升建议", row.get("improvement_suggestions")),
            section("备注", row.get("notes")),
        )

        chunks.append(base_payload(
            row=row,
            source_type="能力模型",
            scenarios=["能力诊断", "JD解析", "项目包装", "面试准备"],
            text=text,
            role_type=split_list(row.get("role_type")) or ["AI产品经理"],
            ai_topic=split_list(row.get("ai_topic")),
            career_topic=split_list(row.get("career_topic")) or ["能力诊断"],
            product_topic=[],
        ))

    return chunks


def build_project_case_chunks() -> List[Dict]:
    chunks = []
    for row in read_csv("project_case_template.csv"):
        source_id = clean_text(row.get("source_id"))
        if not source_id:
            continue

        text = join_sections(
            f"项目名称：{clean_text(row.get('project_name'))}",
            f"项目类型：{clean_text(row.get('project_type'))}",
            section("目标用户", row.get("target_user")),
            section("用户痛点", row.get("user_painpoint")),
            section("解决方案", row.get("solution")),
            section("核心功能", row.get("core_features")),
            section("AI 能力", row.get("ai_capability")),
            section("产品亮点", row.get("product_highlight")),
            section("指标", row.get("metrics")),
            section("简历表达", row.get("resume_bullets")),
            section("面试追问", row.get("interview_questions")),
            section("备注", row.get("notes")),
        )

        chunks.append(base_payload(
            row=row,
            source_type="项目案例",
            scenarios=["项目包装", "面试准备", "能力诊断", "知识问答"],
            text=text,
            role_type=split_list(row.get("role_type")) or ["AI产品经理"],
            ai_topic=split_list(row.get("ai_topic")),
            career_topic=split_list(row.get("career_topic")) or ["项目包装", "面试"],
            product_topic=[],
        ))

    return chunks


def build_resume_template_chunks() -> List[Dict]:
    chunks = []
    for row in read_csv("resume_template_template.csv"):
        source_id = clean_text(row.get("source_id"))
        if not source_id:
            continue

        text = join_sections(
            f"模板名称：{clean_text(row.get('template_name'))}",
            section("适用项目类型", row.get("applicable_project_type")),
            section("表达结构", row.get("structure")),
            section("示例 bullet", row.get("example_bullet")),
            section("使用注意事项", row.get("usage_notes")),
            section("备注", row.get("notes")),
        )

        chunks.append(base_payload(
            row=row,
            source_type="简历模板",
            scenarios=["项目包装", "面试准备"],
            text=text,
            role_type=split_list(row.get("role_type")) or ["AI产品经理"],
            ai_topic=split_list(row.get("ai_topic")),
            career_topic=split_list(row.get("career_topic")) or ["简历", "项目包装"],
            product_topic=[],
        ))

    return chunks


def build_interview_question_chunks() -> List[Dict]:
    chunks = []
    for row in read_csv("interview_question_template.csv"):
        source_id = clean_text(row.get("source_id"))
        if not source_id:
            continue

        text = join_sections(
            section("问题", row.get("question")),
            section("问题类型", row.get("question_type")),
            section("考察能力", row.get("tested_ability")),
            section("回答框架", row.get("answer_framework")),
            section("示例回答", row.get("sample_answer")),
            section("可能追问", row.get("follow_up_questions")),
            section("错误回答提醒", row.get("bad_answer_warning")),
            section("关联概念", row.get("related_concepts")),
            section("备注", row.get("notes")),
        )

        chunks.append(base_payload(
            row=row,
            source_type="面试题",
            scenarios=["面试准备", "知识问答", "项目包装"],
            text=text,
            role_type=split_list(row.get("role_type")) or ["AI产品经理"],
            ai_topic=split_list(row.get("ai_topic")),
            career_topic=split_list(row.get("career_topic")) or ["面试"],
            product_topic=[],
        ))

    return chunks


def build_all_chunks() -> List[Dict]:
    chunks = []
    builders = [
        build_jd_chunks,
        build_ai_knowledge_chunks,
        build_capability_model_chunks,
        build_project_case_chunks,
        build_resume_template_chunks,
        build_interview_question_chunks,
    ]

    for builder in builders:
        built = builder()
        print(f"[OK] {builder.__name__}: {len(built)} chunks")
        chunks.extend(built)

    return chunks


def main():
    if not TEMPLATE_DIR.exists():
        raise FileNotFoundError(f"Template directory not found: {TEMPLATE_DIR}")

    chunks = build_all_chunks()

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with OUT_PATH.open("w", encoding="utf-8") as f:
        for item in chunks:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    print("-" * 60)
    print(f"Generated {len(chunks)} chunks -> {OUT_PATH}")

    if not chunks:
        print("[WARN] No chunks generated. Please check CSV templates under data/templates/.")


if __name__ == "__main__":
    main()
