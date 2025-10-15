from django.http import HttpResponse

try:
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    _HAS_PROM = True
except Exception:
    _HAS_PROM = False

from django.http import JsonResponse
from bots.services.matching_service_client import MatchingServiceClient, get_default_client


def metrics_endpoint(request):
    if not _HAS_PROM:
        return HttpResponse('prometheus_client not installed', status=501)
    data = generate_latest()
    return HttpResponse(data, content_type=CONTENT_TYPE_LATEST)


def metrics_internal(request):
    """Возвращает комбинированный ответ: Prometheus-формат + in-memory метрики в JSON.

    Полезно для отладки: показывает как глобальные Prometheus-метрики, так
    и простые in-memory счётчики из `MatchingServiceClient.get_metrics()`.
    """
    prom_text = None
    if _HAS_PROM:
        try:
            prom_text = generate_latest()
        except Exception:
            prom_text = b''
    # try to get in-memory metrics from module-level singleton client so we
    # reflect the metrics that the running server process updates.
    in_memory = {}
    try:
        client = get_default_client()
        in_memory = client.get_metrics()
    except Exception:
        in_memory = {'error': 'failed to obtain default MatchingServiceClient or collect metrics'}

    # Return a JSON structure with both pieces; prom_text is included as base64-safe string
    return JsonResponse({
        'prometheus': prom_text.decode('utf-8') if prom_text else None,
        'in_memory': in_memory,
    })


def metrics_trigger(request):
    """Trigger to increment both Prometheus and in-memory metrics on the singleton.

    This is a temporary debug endpoint to exercise metrics inside the running
    server process. It increments some counters and returns the updated
    in-memory snapshot.
    """
    # Only allow POST
    from django.conf import settings

    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'error': 'method not allowed'}, status=405)

    # If no token configured, hide the endpoint (404) to avoid exposing a debug
    # trigger in production or on servers where a token hasn't been intentionally
    # set. This makes the endpoint invisible unless explicitly enabled.
    token = getattr(settings, 'METRICS_TRIGGER_TOKEN', '')
    if not token:
        # Return 404 so it's not obvious this endpoint exists
        return JsonResponse({'status': 'error', 'error': 'not found'}, status=404)

    # Restrict to localhost for an extra safety layer
    remote_addr = request.META.get('REMOTE_ADDR', '')
    if remote_addr not in ('127.0.0.1', '::1', 'localhost'):
        return JsonResponse({'status': 'error', 'error': 'forbidden'}, status=403)

    # Expect header 'X-METRICS-TRIGGER-TOKEN' to match configured token
    header_token = request.headers.get('X-METRICS-TRIGGER-TOKEN', '')
    if header_token != token:
        return JsonResponse({'status': 'error', 'error': 'invalid token'}, status=403)

    try:
        client = get_default_client()
        # increment in-memory counters
        client.metrics['matching_requests'] = client.metrics.get('matching_requests', 0) + 1
        client.metrics['matching_requests_success'] = client.metrics.get('matching_requests_success', 0) + 1
        client.metrics['matching_latency_ms_total'] = client.metrics.get('matching_latency_ms_total', 0.0) + 120.0

        # increment Prometheus metrics if available
        if getattr(client, 'prom_matching_requests', None):
            try:
                client.prom_matching_requests.inc()
            except Exception:
                pass
        if getattr(client, 'prom_matching_latency', None):
            try:
                client.prom_matching_latency.observe(0.12)
            except Exception:
                pass

        return JsonResponse({'status': 'ok', 'in_memory': client.get_metrics()})
    except Exception as e:
        return JsonResponse({'status': 'error', 'error': str(e)}, status=500)
