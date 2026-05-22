#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
命令行检索测试。
"""

import argparse
from typing import Optional, List

from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchAny
from sentence_transformers import SentenceTransformer


def build_filter(scenario: Optional[str], source_type: Optional[List[str]], role_type: Optional[str]):
    must = []
    if scenario:
        must.append(FieldCondition(key="scenario", match=MatchAny(any=[scenario])))
    if source_type:
        must.append(FieldCondition(key="source_type", match=MatchAny(any=source_type)))
    if role_type:
        must.append(FieldCondition(key="role_type", match=MatchAny(any=[role_type])))
    return Filter(must=must) if must else None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", required=True)
    parser.add_argument("--url", default="http://localhost:6333")
    parser.add_argument("--collection", default="ai_pm_career_chunks")
    parser.add_argument("--model", default="BAAI/bge-small-zh-v1.5")
    parser.add_argument("--scenario", default=None)
    parser.add_argument("--source-type", nargs="*", default=None)
    parser.add_argument("--role-type", default=None)
    parser.add_argument("--top-k", type=int, default=5)
    args = parser.parse_args()

    model = SentenceTransformer(args.model)
    client = QdrantClient(path="qdrant_storage_local")

    vector = model.encode([args.query], normalize_embeddings=True)[0].tolist()
    query_filter = build_filter(args.scenario, args.source_type, args.role_type)

    try:
        response = client.query_points(
            collection_name=args.collection,
            query=vector,
            query_filter=query_filter,
            limit=args.top_k,
            with_payload=True,
        )
        hits = response.points
    except AttributeError:
        hits = client.search(
            collection_name=args.collection,
            query_vector=vector,
            query_filter=query_filter,
            limit=args.top_k,
            with_payload=True,
        )

    print(f"\nQuery: {args.query}\n")
    for i, hit in enumerate(hits, start=1):
        payload = hit.payload or {}
        print("=" * 80)
        print(f"[{i}] score={getattr(hit, 'score', None)}")
        print(f"Title: {payload.get('title')}")
        print(f"Source Type: {payload.get('source_type')}")
        print(f"Scenario: {payload.get('scenario')}")
        print(f"Role Type: {payload.get('role_type')}")
        print(f"AI Topic: {payload.get('ai_topic')}")
        print("-" * 80)
        print((payload.get("text") or "")[:1200])
        print()


if __name__ == "__main__":
    main()
