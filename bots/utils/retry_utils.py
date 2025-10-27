from tenacity import AsyncRetrying, retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import asyncio
import random

class RetryConfig:
    def __init__(self, attempts=5, min_wait=1, max_wait=30):
        self.attempts = attempts
        self.min_wait = min_wait
        self.max_wait = max_wait


def async_retry_decorator(attempts=5, min_wait=1, max_wait=30, retry_exceptions=(Exception,)):
    """Return a decorator to retry an async function with exponential backoff and jitter."""
    def _decorator(fn):
        @retry(
            reraise=True,
            stop=stop_after_attempt(attempts),
            wait=wait_exponential(multiplier=min_wait, max=max_wait),
            retry=retry_if_exception_type(tuple(retry_exceptions)),
        )
        async def _wrapped(*args, **kwargs):
            return await fn(*args, **kwargs)

        return _wrapped

    return _decorator


def sync_retry_decorator(attempts=5, min_wait=1, max_wait=30, retry_exceptions=(Exception,)):
    """Return a decorator to retry a sync function with exponential backoff and jitter."""
    def _decorator(fn):
        @retry(
            reraise=True,
            stop=stop_after_attempt(attempts),
            wait=wait_exponential(multiplier=min_wait, max=max_wait),
            retry=retry_if_exception_type(tuple(retry_exceptions)),
        )
        def _wrapped(*args, **kwargs):
            return fn(*args, **kwargs)

        return _wrapped

    return _decorator
