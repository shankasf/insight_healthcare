from functools import lru_cache

from openai import AsyncOpenAI

from app.core.config import settings


@lru_cache
def _get_client() -> AsyncOpenAI:
    return AsyncOpenAI(api_key=settings.OPENAI_API_KEY)


async def embed_text(text: str) -> list[float]:
    client = _get_client()
    resp = await client.embeddings.create(model=settings.EMBEDDING_MODEL, input=text)
    return list(resp.data[0].embedding)


async def embed_batch(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    client = _get_client()
    resp = await client.embeddings.create(model=settings.EMBEDDING_MODEL, input=texts)
    return [list(item.embedding) for item in resp.data]
