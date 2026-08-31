from app.database import get_db
from api.v1.auth.dependencies import get_current_user, require_admin, require_roles
from typing import Optional
import redis
import logging
from app.config import settings

logger = logging.getLogger("moneybeing.dependencies")

_redis_pool: Optional[redis.ConnectionPool] = None


def get_redis_client() -> Optional[redis.Redis]:
    global _redis_pool
    if not settings.REDIS_ENABLED:
        return None
    try:
        if _redis_pool is None:
            _redis_pool = redis.ConnectionPool.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                socket_timeout=2.0,
                socket_connect_timeout=2.0,
            )
        client = redis.Redis(connection_pool=_redis_pool)
        client.ping()
        return client
    except Exception as e:
        logger.warning(f"Redis not reachable, operating in cache-bypass mode: {e}")
        return None
