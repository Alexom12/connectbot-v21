import logging
from typing import List

from django.core.cache import cache

try:
    from django_redis import get_redis_connection
except Exception:  # pragma: no cover - optional runtime
    get_redis_connection = None

logger = logging.getLogger(__name__)


def _delete_pattern_with_redis(pattern: str) -> int:
    """Delete keys matching pattern using redis connection. Returns number of deleted keys."""
    if not get_redis_connection:
        logger.warning('django_redis.get_redis_connection not available; skipping pattern delete for %s', pattern)
        return 0

    try:
        conn = get_redis_connection('default')
        deleted = 0
        for key in conn.scan_iter(match=pattern):
            try:
                conn.delete(key)
                deleted += 1
            except Exception:
                logger.exception('failed to delete redis key %s', key)
        logger.info('Deleted %d keys matching pattern %s', deleted, pattern)
        return deleted
    except Exception:
        logger.exception('Error while deleting keys by pattern %s', pattern)
        return 0


def _index_set_name(prefix: str) -> str:
    return f"data_api_index:{prefix}"


def register_data_api_key(prefix: str, full_key: str, ttl: int = None) -> bool:
    """Register a data_api cache key into a Redis set index for the prefix.

    Returns True on success (best-effort). If redis connection not available, no-op.
    """
    if not get_redis_connection:
        logger.debug('register_data_api_key: redis not available; skipping registry for %s', full_key)
        return False

    try:
        conn = get_redis_connection('default')
        set_name = _index_set_name(prefix)
        conn.sadd(set_name, full_key)
        if ttl:
            try:
                # set expiration for index slightly longer than item ttl
                conn.expire(set_name, max(60, int(ttl) * 2))
            except Exception:
                logger.debug('Failed to set expire on index %s', set_name)
        return True
    except Exception:
        logger.exception('register_data_api_key failed for %s', full_key)
        return False


def get_registered_data_api_keys(prefix: str):
    """Return list of registered keys for a prefix (or empty list)."""
    if not get_redis_connection:
        return []
    try:
        conn = get_redis_connection('default')
        set_name = _index_set_name(prefix)
        members = conn.smembers(set_name) or []
        # members are bytes in redis-py, convert to str
        return [m.decode('utf-8') if isinstance(m, (bytes, bytearray)) else str(m) for m in members]
    except Exception:
        logger.exception('get_registered_data_api_keys failed for %s', prefix)
        return []


def delete_registered_data_api_keys(prefix: str) -> int:
    """Delete all registered keys for a prefix and remove index. Returns deleted count."""
    if not get_redis_connection:
        # fallback to SCAN deletion
        return _delete_pattern_with_redis(f"data_api:{prefix}:*")

    try:
        conn = get_redis_connection('default')
        set_name = _index_set_name(prefix)
        members = conn.smembers(set_name) or []
        deleted = 0
        for key in members:
            try:
                conn.delete(key)
                deleted += 1
            except Exception:
                logger.exception('failed to delete registered key %s', key)
        try:
            conn.delete(set_name)
        except Exception:
            logger.debug('failed to delete index set %s', set_name)
        logger.info('Deleted %d registered keys for prefix %s', deleted, prefix)
        return deleted
    except Exception:
        logger.exception('delete_registered_data_api_keys failed for %s', prefix)
        return 0


def invalidate_data_api_prefixes(prefixes: List[str]) -> int:
    """Invalidate Data API cache for given list of prefix names.

    Data API cache keys: data_api:{prefix}:{sha256}
    We delete keys by pattern: data_api:{prefix}:*
    Returns total deleted keys count (best-effort).
    """
    total = 0
    for p in prefixes:
        # prefer registry-based deletion
        deleted = delete_registered_data_api_keys(p)
        total += deleted
    return total


def invalidate_all_data_api() -> int:
    """Invalidate all Data API related caches (employees, previous_matches, employee_interests)."""
    prefixes = ['employees_for_matching', 'previous_matches', 'employee_interests']
    return invalidate_data_api_prefixes(prefixes)
