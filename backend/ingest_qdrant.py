#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
把 data/processed/chunks.jsonl 导入 Qdrant。
"""

import argparse
import json
import uuid
from pathlib import Path
from typing import Dict, Any, List

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer


def stable_uuid(text: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, text))


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def make_payload(row: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "chunk_id": row["chunk_id"],
        "title": row.get("title", ""),
        "text": row["text"],
        "source_type": row.get("source_type", ""),
        "scenario": row.get("scenario", []),
        "role_type": row.get("role_type", []),
        "ai_topic": row.get("ai_topic", []),
        "career_topic": row.get("career_topic", []),
        "product_topic": row.get("product_topic", []),
        "difficulty": row.get("difficulty", ""),
        "reliability": row.get("reliability", "medium"),
        "source_name": row.get("source_name", ""),
        "source_url": row.get("source_url", ""),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", default="data/processed/chunks.jsonl")
    parser.add_argument("--url", default="http://localhost:6333")
    parser.add_argument("--collection", default="ai_pm_career_chunks")
    parser.add_argument("--model", default="BAAI/bge-small-zh-v1.5")
    parser.add_argument("--recreate", action="store_true")
    parser.add_argument("--batch-size", type=int, default=64)
    args = parser.parse_args()

    file_path = Path(args.file)
    if not file_path.exists():
        raise FileNotFoundError(f"Chunks file not found: {file_path}. Run python backend/build_chunks.py first.")

    rows = load_jsonl(file_path)
    if not rows:
        raise ValueError("No rows found in chunks file.")

    print(f"Loading embedding model: {args.model}")
    model = SentenceTransformer(args.model)

    sample_vec = model.encode(["测试"], normalize_embeddings=True)[0]
    vector_size = len(sample_vec)

    client = QdrantClient(path="qdrant_storage_local")

    existing = [c.name for c in client.get_collections().collections]
    if args.recreate and args.collection in existing:
        print(f"Deleting existing collection: {args.collection}")
        client.delete_collection(args.collection)

    existing = [c.name for c in client.get_collections().collections]
    if args.collection not in existing:
        print(f"Creating collection: {args.collection}")
        client.create_collection(
            collection_name=args.collection,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
        )

    texts = [r["text"] for r in rows]
    print(f"Encoding {len(texts)} chunks...")
    vectors = model.encode(texts, normalize_embeddings=True, batch_size=args.batch_size)

    points = []
    for row, vector in zip(rows, vectors):
        points.append(PointStruct(
            id=stable_uuid(row["chunk_id"]),
            vector=vector.tolist(),
            payload=make_payload(row),
        ))

    print(f"Upserting {len(points)} points...")
    client.upsert(collection_name=args.collection, points=points)
    print(f"Done. Collection={args.collection}, chunks={len(points)}")


if __name__ == "__main__":
    main()
