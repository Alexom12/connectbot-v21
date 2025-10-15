import logging
import requests
from typing import List, Dict, Any, Optional, Tuple
import time
import random
import json
from time import perf_counter

from django.conf import settings
from django.db import models
from employees.models import Employee, CoffeePair

# Optional Prometheus integration
try:
    from prometheus_client import Counter, Histogram
    _HAS_PROM = True
except Exception:
    _HAS_PROM = False

logger = logging.getLogger(__name__)

class MatchingServiceClient:
    """
    Клиент для взаимодействия с внешним Java-сервисом подбора пар.
    """

    def __init__(self):
        self.base_url = settings.MATCHING_SERVICE_URL
        if not self.base_url:
            raise ValueError("MATCHING_SERVICE_URL не определен в настройках Django.")
        self.timeout = settings.MATCHING_SERVICE_TIMEOUT
        # Простые in-memory метрики
        # counters: health_checks, health_failures, matching_requests, matching_failures
        # timing: matching_latency_ms_total, matching_requests_success
        self.metrics = {
            'health_checks': 0,
            'health_failures': 0,
            'matching_requests': 0,
            'matching_failures': 0,
            'matching_latency_ms_total': 0.0,
            'matching_requests_success': 0,
        }

        # Prometheus metrics (optional). Register only if prometheus_client is available.
        self.prom = None
        if _HAS_PROM:
            try:
                # Use safe registration: if already created elsewhere, this may raise; ignore then
                self.prom_health_checks = Counter('matching_service_health_checks_total', 'Total health checks performed')
                self.prom_health_failures = Counter('matching_service_health_failures_total', 'Total health check failures')
                self.prom_matching_requests = Counter('matching_service_matching_requests_total', 'Total matching requests')
                self.prom_matching_failures = Counter('matching_service_matching_failures_total', 'Total matching failures')
                # histogram for latency in seconds
                self.prom_matching_latency = Histogram('matching_service_matching_latency_seconds', 'Matching request latency in seconds')
                self.prom = True
            except Exception:
                # If metrics are already registered or any other error, fall back to in-memory only
                self.prom = False
                self.prom_health_checks = None
                self.prom_health_failures = None
                self.prom_matching_requests = None
                self.prom_matching_failures = None
                self.prom_matching_latency = None
        else:
            self.prom_health_checks = None
            self.prom_health_failures = None
            self.prom_matching_requests = None
            self.prom_matching_failures = None
            self.prom_matching_latency = None

    def check_health(self) -> bool:
        """
        Проверяет состояние здоровья Java-сервиса.

        Returns:
            bool: True, если сервис доступен и отвечает "OK".
        """
        try:
            url = f"{self.base_url}/api/v1/matching/health"
            self.metrics['health_checks'] += 1
            if self.prom_health_checks:
                try:
                    self.prom_health_checks.inc()
                except Exception:
                    pass
            response = self._request_with_retry('get', url, timeout=self.timeout)
            if response is None:
                logger.error("Ошибка при проверке состояния сервиса подбора пар: нет ответа после retry")
                self.metrics['health_failures'] += 1
                if self.prom_health_failures:
                    try:
                        self.prom_health_failures.inc()
                    except Exception:
                        pass
                return False
            response.raise_for_status()
            data = response.json()
            is_healthy = data.get("status") == "OK"
            if not is_healthy:
                logger.warning(f"Сервис подбора пар ответил нездоровым статусом: {data}")
            return is_healthy
        except requests.RequestException as e:
            logger.error(f"Ошибка при проверке состояния сервиса подбора пар: {e}")
            self.metrics['health_failures'] += 1
            return False

    def run_secret_coffee_matching(self, employees: List[Employee]) -> Optional[List[Dict[str, int]]]:
        """
        Запускает алгоритм подбора "Секретный кофе" через Java-сервис.

        Args:
            employees: Список объектов Django-модели Employee для подбора.

        Returns:
            Список словарей с ID пар, например, [{'employee1_id': 1, 'employee2_id': 2}],
            или None в случае ошибки.
        """
        if not self.check_health():
            logger.error("Запуск подбора невозможен: сервис подбора пар недоступен.")
            return None

        try:
            request_data = self._prepare_request_data(employees)
            url = f"{self.base_url}/api/v1/matching/match/secret-coffee"

            # metrics/logging
            self.metrics['matching_requests'] += 1
            if self.prom_matching_requests:
                try:
                    self.prom_matching_requests.inc()
                except Exception:
                    pass
            sanitized = self._sanitize_request_for_logging(request_data)
            logger.info(f"Отправка запроса на подбор для {len(employees)} сотрудников в Java-сервис.")
            logger.debug(f"Outgoing matching request payload (sanitized): {json.dumps(sanitized, ensure_ascii=False)}")

            start = perf_counter()
            response = self._request_with_retry('post', url, json=request_data, timeout=self.timeout)
            elapsed_ms = (perf_counter() - start) * 1000.0

            if response is None:
                logger.error("Сервис подбора пар не ответил после нескольких попыток.")
                self.metrics['matching_failures'] += 1
                if self.prom_matching_failures:
                    try:
                        self.prom_matching_failures.inc()
                    except Exception:
                        pass
                return None

            response.raise_for_status()
            response_data = response.json()
            pairs = response_data.get("pairs")

            # update timing metrics
            self.metrics['matching_latency_ms_total'] += elapsed_ms
            if pairs:
                self.metrics['matching_requests_success'] += 1
            # observe Prometheus histogram (convert ms to seconds)
            if self.prom_matching_latency:
                try:
                    self.prom_matching_latency.observe(elapsed_ms / 1000.0)
                except Exception:
                    pass

            # Sanitize and log response summary
            resp_summary = {'pairs_count': len(pairs) if pairs else 0}
            logger.info(f"Сервис подбора пар вернул {resp_summary['pairs_count']} пар.")
            logger.debug(f"Incoming matching response summary: {json.dumps(resp_summary)}")

            return pairs

        except requests.RequestException as e:
            logger.error(f"Ошибка при вызове API сервиса подбора пар: {e}")
            return None
        except Exception as e:
            logger.error(f"Неожиданная ошибка при обработке ответа от сервиса подбора пар: {e}")
            return None

    def _prepare_request_data(self, employees: List[Employee]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Преобразует список Django-моделей в структуру для JSON-запроса.
        """
        employee_dtos = []
        for emp in employees:
            # Получаем ID партнеров, с которыми сотрудник уже был в паре (история CoffeePair)
            partner_ids = set()
            related_pairs = CoffeePair.objects.filter(models.Q(employee1_id=emp.id) | models.Q(employee2_id=emp.id))
            for cp in related_pairs:
                if cp.employee1_id and cp.employee1_id != emp.id:
                    partner_ids.add(cp.employee1_id)
                if cp.employee2_id and cp.employee2_id != emp.id:
                    partner_ids.add(cp.employee2_id)
            excluded_partners = list(partner_ids)
            
            # position may contain a full title; send a simple level indicator if available
            position_level = None
            if getattr(emp, 'position', None):
                # naive mapping: look for keywords in position to determine level
                pos = emp.position.lower()
                if 'senior' in pos or 'lead' in pos or 'principal' in pos:
                    position_level = 'SENIOR'
                elif 'junior' in pos or 'intern' in pos:
                    position_level = 'JUNIOR'
                else:
                    position_level = 'MID'

            preferences_with_newcomers = False
            profile = getattr(emp, 'profile', None)
            if profile is not None and hasattr(profile, 'with_newcomers'):
                try:
                    preferences_with_newcomers = bool(getattr(profile, 'with_newcomers'))
                except Exception:
                    preferences_with_newcomers = False

            dto = {
                "id": emp.id,
                "department": emp.department.id if getattr(emp, 'department', None) else None,
                "position_level": position_level or 'UNKNOWN',
                "excluded_partners": excluded_partners,
                "preferences": {
                    "with_newcomers": preferences_with_newcomers
                }
            }
            employee_dtos.append(dto)
        
        return {"employees": employee_dtos}

    def _request_with_retry(self, method: str, url: str, max_retries: int = 3, backoff_factor: float = 0.5, **kwargs):
        """
        Простая реализация retry с экспоненциальным бэкоффом и jitter.
        Возвращает объект Response при успешном ответе или None, если все попытки провалились.
        """
        attempt = 0
        while attempt < max_retries:
            try:
                if method.lower() == 'get':
                    resp = requests.get(url, **kwargs)
                elif method.lower() == 'post':
                    resp = requests.post(url, **kwargs)
                else:
                    raise ValueError(f"Unsupported method for retry: {method}")
                return resp
            except Exception as e:
                # Любое исключение (включая RequestException и мок-исключения) должно обрабатываться
                attempt += 1
                if attempt >= max_retries:
                    logger.error(f"Request to {url} failed after {attempt} attempts: {e}")
                    return None
                # backoff with jitter
                sleep_time = backoff_factor * (2 ** (attempt - 1))
                jitter = random.uniform(0, sleep_time * 0.1)
                time.sleep(sleep_time + jitter)

    def _sanitize_request_for_logging(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Возвращает безопасную для логирования версию payload: удаляет/сводит к минимуму PII.
        Для наших DTO оставляем только id, department (id), position_level, counts of excluded partners.
        """
        out = {'employees': []}
        for emp in request_data.get('employees', []):
            out_emp = {
                'id': emp.get('id'),
                'department': emp.get('department'),
                'position_level': emp.get('position_level'),
                'excluded_partners_count': len(emp.get('excluded_partners') or [])
            }
            out['employees'].append(out_emp)
        return out

    def get_metrics(self) -> Dict[str, Any]:
        """Возвращает текущее состояние простых in-memory метрик."""
        # Небольшая копия, чтобы внешний код не мог изменять внутренний словарь напрямую
        return dict(self.metrics)

def run_matching_for_active_employees() -> Optional[List[Tuple[int, int]]]:
    """
    Основная функция-фасад для запуска подбора.
    Собирает активных сотрудников и вызывает клиент.
    """
    logger.info("Запуск процесса подбора пар 'Секретный кофе'...")
    
    # 1. Собираем всех активных сотрудников, которые участвуют в 'secret_coffee'
    # Пока выбираем всех активных сотрудников — фильтрацию по участию в сессии
    # можно сделать позже, используя ActivityParticipant/SecretCoffeePreference
    active_employees = Employee.objects.filter(is_active=True)

    if not active_employees:
        logger.warning("Нет активных сотрудников для подбора. Процесс завершен.")
        return []

    # 2. Создаем клиент и вызываем сервис
    client = MatchingServiceClient()
    pairs_data = client.run_secret_coffee_matching(list(active_employees))

    if pairs_data is None:
        logger.error("Не удалось получить результат от сервиса подбора пар.")
        return None

    # 3. Преобразуем результат в список кортежей
    result_pairs = [(p['employee1_id'], p['employee2_id']) for p in pairs_data]
    
    # 4. Сохраняем результат (этот шаг будет реализован отдельно)
    # Например, можно создать новую модель для хранения истории встреч
    
    logger.info(f"Процесс подбора завершен. Сформировано {len(result_pairs)} пар.")
    return result_pairs


# Module-level singleton helper. Use get_default_client() to obtain a shared
# instance within the process so in-memory metrics are visible across callers.
_DEFAULT_CLIENT = None


def get_default_client() -> MatchingServiceClient:
    global _DEFAULT_CLIENT
    if _DEFAULT_CLIENT is None:
        _DEFAULT_CLIENT = MatchingServiceClient()
    return _DEFAULT_CLIENT
