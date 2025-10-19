import os
import json
import hashlib
import logging
import secrets as _secrets
from time import perf_counter
from django.conf import settings

from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.csrf import csrf_exempt
from django.core.cache import cache

from python_app.services.data_api_service import DataAPIService
from python_app.serializers.data_serializers import sanitize_request_for_logging
from python_app.services.cache_utils import register_data_api_key

logger = logging.getLogger(__name__)

try:
    from prometheus_client import Counter, Histogram
    _HAS_PROM = True
except Exception:
    _HAS_PROM = False

if _HAS_PROM:
    REQ_COUNTER = Counter('data_api_requests_total', 'Total requests to Data API', ['endpoint', 'method'])
    REQ_ERRORS = Counter('data_api_errors_total', 'Total errors in Data API', ['endpoint'])
    REQ_LATENCY = Histogram('data_api_request_latency_seconds', 'Request latency', ['endpoint'])
    CACHE_HITS = Counter('data_api_cache_hits_total', 'Cache hits for Data API', ['endpoint'])
    CACHE_MISSES = Counter('data_api_cache_misses_total', 'Cache misses for Data API', ['endpoint'])
else:
    REQ_COUNTER = REQ_ERRORS = REQ_LATENCY = None
    CACHE_HITS = CACHE_MISSES = None


def _read_service_token_from_file():
    # Docker secrets are often mounted at /run/secrets/<name>
    token_file = os.getenv('SERVICE_AUTH_TOKEN_FILE', '/run/secrets/service_auth_token')
    try:
        if os.path.exists(token_file):
            with open(token_file, 'r', encoding='utf-8') as fh:
                data = fh.read()
                # strip BOM and whitespace/newlines
                return data.replace('\ufeff', '').strip()
    except Exception:
        logger.debug('Failed to read service token from file %s', token_file)
    return ''


def _auth_ok(request):
    header = request.headers.get('Authorization') or request.META.get('HTTP_AUTHORIZATION', '')
    if not header:
        return False
    parts = header.split(None, 1)
    if len(parts) != 2:
        return False
    scheme, token = parts
    if scheme.lower() != 'service':
        return False

    # Prefer Django settings.SERVICE_AUTH_TOKEN if set (useful in tests/CI)
    expected = getattr(settings, 'SERVICE_AUTH_TOKEN', None) or os.getenv('SERVICE_AUTH_TOKEN', '')
    if not expected:
        expected = _read_service_token_from_file()

    if not expected:
        # no configured token -> fail closed
        logger.warning('No service auth token configured for Data API')
        return False

    # Normalize token (strip BOM/newlines/spaces)
    token_norm = token.replace('\ufeff', '').strip()
    expected_norm = expected.replace('\ufeff', '').strip()

    # Masked logging for debugging: show first 8 chars and length only
    try:
        def _mask(s: str):
            if not s:
                return '<empty>'
            return s[:8] + '...' if len(s) > 8 else s

        if not _secrets.compare_digest(token_norm, expected_norm):
            logger.warning('Unauthorized request; Authorization header present repr=%r, token_mask=%s, token_len=%d, expected_mask=%s, expected_len=%d',
                           header, _mask(token_norm), len(token_norm), _mask(expected_norm), len(expected_norm))
            return False
    except Exception:
        logger.exception('Error during auth token comparison')
        return False

    return True


def _cache_key_for_request(prefix: str, body: dict) -> str:
    m = hashlib.sha256()
    m.update(prefix.encode('utf-8'))
    if body is not None:
        payload = json.dumps(body, sort_keys=True, default=str)
        m.update(payload.encode('utf-8'))
    return f"data_api:{prefix}:{m.hexdigest()}"


class _NoopContext:
    def __enter__(self):
        return None
    def __exit__(self, exc_type, exc, tb):
        return False


@csrf_exempt
@require_POST
def employees_for_matching(request):
    endpoint = 'employees_for_matching'
    if REQ_COUNTER:
        REQ_COUNTER.labels(endpoint=endpoint, method='POST').inc()

    if not _auth_ok(request):
        if REQ_ERRORS:
            REQ_ERRORS.labels(endpoint=endpoint).inc()
        return JsonResponse({'error': 'unauthorized'}, status=401)

    try:
        # capture raw bytes for debugging — sometimes the server logs a stray character
        # (e.g. "2") at the HTTP layer; log the raw bytes and some META fields
        raw_body = request.body if hasattr(request, 'body') else b''
        try:
            logger.info('Raw request.body bytes repr=%r', raw_body)
            # request.headers is available on Django HttpRequest for nicer view
            try:
                logger.info('Request headers: %s', dict(request.headers))
            except Exception:
                logger.info('Request headers unavailable')
            logger.info("Request META: CONTENT_LENGTH=%s, HTTP_TRANSFER_ENCODING=%s, REQUEST_METHOD=%s, HTTP_HOST=%s",
                         request.META.get('CONTENT_LENGTH'), request.META.get('HTTP_TRANSFER_ENCODING'),
                         request.method, request.META.get('HTTP_HOST'))
        except Exception:
            logger.exception('Failed to log raw request debug info')

        body = json.loads(raw_body.decode('utf-8') or '{}')
    except Exception:
        body = {}

    logger.info('Data API: employees_for_matching request', extra={'body': sanitize_request_for_logging(body)})

    cache_key = _cache_key_for_request(endpoint, body)
    ttl = int(os.getenv('DATA_API_TTL_EMPLOYEES', 300))
    cached = cache.get(cache_key)
    if cached is not None:
        if CACHE_HITS:
            CACHE_HITS.labels(endpoint=endpoint).inc()
        return JsonResponse(cached, safe=False)
    else:
        if CACHE_MISSES:
            CACHE_MISSES.labels(endpoint=endpoint).inc()

    start = perf_counter()
    ctx = (REQ_LATENCY.labels(endpoint=endpoint).time() if REQ_LATENCY else _NoopContext())
    with ctx:
        try:
            svc = DataAPIService()
            data = svc.get_employees_for_matching(body)
            cache.set(cache_key, data, ttl)
            try:
                register_data_api_key(endpoint, cache_key, ttl)
            except Exception:
                logger.debug('Failed to register cache key for endpoint %s', endpoint)
            elapsed = perf_counter() - start
            logger.info(f'employees_for_matching served in {elapsed:.3f}s, count={len(data.get("employees", []))}')
            return JsonResponse(data, safe=False)
        except Exception as e:
            logger.exception('employees_for_matching failed: %s', e)
            if REQ_ERRORS:
                REQ_ERRORS.labels(endpoint=endpoint).inc()
            return JsonResponse({'error': 'internal_error'}, status=500)


@csrf_exempt
@require_POST
def previous_matches(request):
    endpoint = 'previous_matches'
    if REQ_COUNTER:
        REQ_COUNTER.labels(endpoint=endpoint, method='POST').inc()

    if not _auth_ok(request):
        if REQ_ERRORS:
            REQ_ERRORS.labels(endpoint=endpoint).inc()
        return JsonResponse({'error': 'unauthorized'}, status=401)

    try:
        body = json.loads(request.body.decode('utf-8') or '{}')
    except Exception:
        body = {}

    logger.info('Data API: previous_matches request', extra={'body': sanitize_request_for_logging(body)})

    cache_key = _cache_key_for_request(endpoint, body)
    ttl = int(os.getenv('DATA_API_TTL_PREV_MATCHES', 900))
    cached = cache.get(cache_key)
    if cached is not None:
        if CACHE_HITS:
            CACHE_HITS.labels(endpoint=endpoint).inc()
        return JsonResponse(cached, safe=False)
    else:
        if CACHE_MISSES:
            CACHE_MISSES.labels(endpoint=endpoint).inc()

    start = perf_counter()
    ctx = (REQ_LATENCY.labels(endpoint=endpoint).time() if REQ_LATENCY else _NoopContext())
    with ctx:
        try:
            svc = DataAPIService()
            data = svc.get_previous_matches(body)
            cache.set(cache_key, data, ttl)
            try:
                register_data_api_key(endpoint, cache_key, ttl)
            except Exception:
                logger.debug('Failed to register cache key for endpoint %s', endpoint)
            elapsed = perf_counter() - start
            logger.info(f'previous_matches served in {elapsed:.3f}s, count={len(data.get("matches", []))}')
            return JsonResponse(data, safe=False)
        except Exception as e:
            logger.exception('previous_matches failed: %s', e)
            if REQ_ERRORS:
                REQ_ERRORS.labels(endpoint=endpoint).inc()
            return JsonResponse({'error': 'internal_error'}, status=500)


@csrf_exempt
@require_POST
def employee_interests(request):
    endpoint = 'employee_interests'
    if REQ_COUNTER:
        REQ_COUNTER.labels(endpoint=endpoint, method='POST').inc()

    if not _auth_ok(request):
        if REQ_ERRORS:
            REQ_ERRORS.labels(endpoint=endpoint).inc()
        return JsonResponse({'error': 'unauthorized'}, status=401)

    try:
        body = json.loads(request.body.decode('utf-8') or '{}')
    except Exception:
        body = {}

    logger.info('Data API: employee_interests request', extra={'body': sanitize_request_for_logging(body)})

    cache_key = _cache_key_for_request(endpoint, body)
    ttl = int(os.getenv('DATA_API_TTL_INTERESTS', 600))
    cached = cache.get(cache_key)
    if cached is not None:
        if CACHE_HITS:
            CACHE_HITS.labels(endpoint=endpoint).inc()
        return JsonResponse(cached, safe=False)
    else:
        if CACHE_MISSES:
            CACHE_MISSES.labels(endpoint=endpoint).inc()

    start = perf_counter()
    ctx = (REQ_LATENCY.labels(endpoint=endpoint).time() if REQ_LATENCY else _NoopContext())
    with ctx:
        try:
            svc = DataAPIService()
            data = svc.get_employee_interests(body)
            cache.set(cache_key, data, ttl)
            try:
                register_data_api_key(endpoint, cache_key, ttl)
            except Exception:
                logger.debug('Failed to register cache key for endpoint %s', endpoint)
            elapsed = perf_counter() - start
            logger.info(f'employee_interests served in {elapsed:.3f}s, count={len(data.get("interests", {}))}')
            return JsonResponse(data, safe=False)
        except Exception as e:
            logger.exception('employee_interests failed: %s', e)
            if REQ_ERRORS:
                REQ_ERRORS.labels(endpoint=endpoint).inc()
            return JsonResponse({'error': 'internal_error'}, status=500)


@require_GET
def health(request):
    payload = {
        'status': 'OK',
        'service': 'connectbot-data-api',
    }
    return JsonResponse(payload)
