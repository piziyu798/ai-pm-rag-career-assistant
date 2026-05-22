#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
validate_sources.py

作用：
1. 校验 data/templates/*.csv 的表头是否符合知识库框架要求。
2. 校验已填写行是否缺少关键字段。
3. 支持新版 AI 技术知识库字段：
   source_id,title,concept_name,content,pm_relevance,use_cases,
   risks_or_misunderstandings,ai_topic,product_topic,difficulty,
   source_name,source_url,reliability,notes

使用：
  python backend/validate_sources.py

说明：
- 空模板只会 WARN，不会报错。
- source_url 可以为空。
- 如果字段内容确实无法解释，可以填 None，不会被判定为空。
"""

import csv
import sys
from pathlib import Path
from typing import Dict, List, Tuple


TEMPLATE_DIR = Path("data/templates")

# 每个模板必须具备的字段
REQUIRED_COLUMNS: Dict[str, List[str]] = {
    "jd_template.csv": [
        "source_id", "title", "company_name", "company_type", "job_title",
        "role_type", "seniority", "responsibilities", "requirements",
        "bonus_points", "skill_keywords", "product_keywords",
        "source_name", "source_url", "reliability", "notes"
    ],

    # 新版 AI 技术知识库字段
    "ai_knowledge_template.csv": [
        "source_id", "title", "concept_name", "content", "pm_relevance",
        "use_cases", "risks_or_misunderstandings", "ai_topic",
        "product_topic", "difficulty", "source_name", "source_url",
        "reliability", "notes"
    ],

    "capability_model_template.csv": [
        "source_id", "title", "capability_name", "level_l1", "level_l2",
        "level_l3", "level_l4", "level_l5", "diagnosis_rules",
        "improvement_suggestions", "role_type", "ai_topic",
        "career_topic", "reliability", "difficulty", "notes"
    ],

    "project_case_template.csv": [
        "source_id", "title", "project_name", "project_type", "target_user",
        "user_painpoint", "solution", "core_features", "ai_capability",
        "product_highlight", "metrics", "resume_bullets",
        "interview_questions", "role_type", "ai_topic", "career_topic",
        "source_name", "source_url", "reliability", "difficulty", "notes"
    ],

    "resume_template_template.csv": [
        "source_id", "title", "template_name", "applicable_project_type",
        "structure", "example_bullet", "usage_notes", "role_type",
        "ai_topic", "career_topic", "source_name", "source_url",
        "reliability", "difficulty", "notes"
    ],

    "interview_question_template.csv": [
        "source_id", "title", "question", "question_type", "tested_ability",
        "answer_framework", "sample_answer", "follow_up_questions",
        "bad_answer_warning", "related_concepts", "role_type",
        "ai_topic", "career_topic", "source_name", "source_url",
        "reliability", "difficulty", "notes"
    ],
}

# 每个模板中，已填写行必须有值的关键字段
# 注意：source_url 不强制填写；无法解释的字段允许填 None。
REQUIRED_VALUES: Dict[str, List[str]] = {
    "jd_template.csv": [
        "source_id", "title", "job_title", "role_type",
        "responsibilities", "requirements", "reliability"
    ],

    "ai_knowledge_template.csv": [
        "source_id", "title", "concept_name", "content",
        "ai_topic", "difficulty", "reliability"
    ],

    "capability_model_template.csv": [
        "source_id", "title", "capability_name", "level_l1",
        "level_l2", "role_type", "reliability"
    ],

    "project_case_template.csv": [
        "source_id", "title", "project_name", "project_type",
        "target_user", "user_painpoint", "solution",
        "role_type", "reliability"
    ],

    "resume_template_template.csv": [
        "source_id", "title", "template_name", "structure",
        "example_bullet", "role_type", "reliability"
    ],

    "interview_question_template.csv": [
        "source_id", "title", "question", "question_type",
        "tested_ability", "answer_framework", "role_type",
        "reliability"
    ],
}

ALLOWED_RELIABILITY = {"high", "medium", "low", "None", "none", "NONE"}
ALLOWED_DIFFICULTY = {"入门", "中级", "高级", "None", "none", "NONE", ""}


def read_csv(path: Path) -> Tuple[List[str], List[dict]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        header = reader.fieldnames or []
        rows = list(reader)
    return header, rows


def non_empty(value: str) -> bool:
    """
    判断字段是否有内容。
    注意：字符串 None 被视为有内容，因为用户可能故意表示无法解释。
    """
    if value is None:
        return False
    return str(value).strip() != ""


def row_is_blank(row: dict) -> bool:
    """整行完全为空则跳过。"""
    return all((v is None or str(v).strip() == "") for v in row.values())


def validate_file(filename: str) -> Tuple[bool, int]:
    path = TEMPLATE_DIR / filename
    ok = True

    if not path.exists():
        print(f"[ERROR] Missing file: {path}")
        return False, 0

    header, rows = read_csv(path)

    required_cols = REQUIRED_COLUMNS[filename]
    missing_cols = [c for c in required_cols if c not in header]
    extra_cols = [c for c in header if c not in required_cols]

    if missing_cols:
        print(f"[ERROR] {filename}: missing columns: {missing_cols}")
        ok = False

    if extra_cols:
        print(f"[WARN] {filename}: extra columns will be ignored by build_chunks.py: {extra_cols}")

    valid_rows = [r for r in rows if not row_is_blank(r)]

    if not valid_rows:
        print(f"[WARN] {filename}: no data rows, header only.")
        return ok, 0

    required_values = REQUIRED_VALUES[filename]

    seen_ids = set()
    for row_idx, row in enumerate(valid_rows, start=2):
        # source_id 唯一性
        source_id = (row.get("source_id") or "").strip()
        if source_id:
            if source_id in seen_ids:
                print(f"[ERROR] {filename}: row {row_idx} duplicate source_id: {source_id}")
                ok = False
            seen_ids.add(source_id)

        # 必填值检查
        for col in required_values:
            if col not in header:
                continue
            if not non_empty(row.get(col, "")):
                print(f"[ERROR] {filename}: row {row_idx} missing required value: {col}")
                ok = False

        # reliability 规范检查
        reliability = (row.get("reliability") or "").strip()
        if reliability and reliability not in ALLOWED_RELIABILITY:
            print(f"[WARN] {filename}: row {row_idx} unusual reliability='{reliability}', expected high/medium/low")

        # difficulty 规范检查
        difficulty = (row.get("difficulty") or "").strip()
        if difficulty not in ALLOWED_DIFFICULTY:
            print(f"[WARN] {filename}: row {row_idx} unusual difficulty='{difficulty}', expected 入门/中级/高级")

    print(f"[OK] {filename}: {len(valid_rows)} valid data rows")
    return ok, len(valid_rows)


def main():
    if not TEMPLATE_DIR.exists():
        print(f"[ERROR] Template directory not found: {TEMPLATE_DIR}")
        sys.exit(1)

    all_ok = True
    total_rows = 0

    print("Validating source templates...\n")

    for filename in REQUIRED_COLUMNS.keys():
        ok, count = validate_file(filename)
        all_ok = all_ok and ok
        total_rows += count

    print("\nValidation summary")
    print("-" * 60)
    print(f"Total valid rows: {total_rows}")

    if not all_ok:
        print("Validation failed. Please fix errors above.")
        sys.exit(1)

    print("All source templates passed validation.")


if __name__ == "__main__":
    main()
