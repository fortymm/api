from arq import create_pool
from arq.connections import ArqRedis, RedisSettings

from app.config import settings

_pool: ArqRedis | None = None


async def init_queue() -> None:
    global _pool
    _pool = await create_pool(RedisSettings.from_dsn(settings.redis_url))


async def close_queue() -> None:
    global _pool
    if _pool is not None:
        await _pool.aclose()
        _pool = None


def get_queue() -> ArqRedis:
    if _pool is None:
        raise RuntimeError("Queue not initialized; init_queue() must run during lifespan startup")
    return _pool
