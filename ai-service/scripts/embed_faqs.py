"""Backfill clinic_faqs.embedding for any rows missing it.

Run with:  python -m scripts.embed_faqs
"""
from __future__ import annotations

import asyncio

from app.core.db import session_scope
from app.repositories import faq_repo
from app.services import embedding_service


async def main() -> None:
    async with session_scope() as session:
        rows = await faq_repo.list_faqs_missing_embedding(session)
        if not rows:
            print("All FAQ rows already have embeddings.")
            return

        questions = [r.question for r in rows]
        print(f"Embedding {len(rows)} FAQ row(s)...")
        vectors = await embedding_service.embed_batch(questions)

        for row, vec in zip(rows, vectors, strict=True):
            row.embedding = vec
        await session.flush()

        print(f"Updated {len(rows)} FAQ embedding(s).")


if __name__ == "__main__":
    asyncio.run(main())
