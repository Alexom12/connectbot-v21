from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
import logging

from python_app.services import cache_utils

from .models import Employee, EmployeeInterest, Interest

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Employee)
def _employee_saved(sender, instance: Employee, **kwargs):
    """Invalidate Data API caches related to employees when employee is changed."""
    try:
        # Employee.save() already invalidates per-employee Redis keys; here invalidate Data API aggregated caches
        deleted = cache_utils.invalidate_data_api_prefixes(['employees_for_matching', 'employee_interests'])
        logger.info('Signals: invalidated %d Data API keys for Employee %s', deleted, getattr(instance, 'id', None))
    except Exception:
        logger.exception('Error invalidating Data API cache on employee save')


@receiver(post_delete, sender=Employee)
def _employee_deleted(sender, instance: Employee, **kwargs):
    try:
        deleted = cache_utils.invalidate_data_api_prefixes(['employees_for_matching', 'employee_interests'])
        logger.info('Signals: invalidated %d Data API keys for deleted Employee %s', deleted, getattr(instance, 'id', None))
    except Exception:
        logger.exception('Error invalidating Data API cache on employee delete')


@receiver(post_save, sender=EmployeeInterest)
@receiver(post_delete, sender=EmployeeInterest)
def _employee_interest_changed(sender, instance: EmployeeInterest, **kwargs):
    try:
        # when interests change, invalidate employee_interests and employees_for_matching caches
        deleted = cache_utils.invalidate_data_api_prefixes(['employee_interests', 'employees_for_matching'])
        logger.info('Signals: invalidated %d Data API keys for EmployeeInterest change (employee=%s)', deleted, getattr(instance.employee, 'id', None))
    except Exception:
        logger.exception('Error invalidating Data API cache on employee interest change')


@receiver(post_save, sender=Interest)
@receiver(post_delete, sender=Interest)
def _interest_changed(sender, instance: Interest, **kwargs):
    try:
        deleted = cache_utils.invalidate_all_data_api()
        logger.info('Signals: invalidated %d Data API keys for Interest change id=%s', deleted, getattr(instance, 'id', None))
    except Exception:
        logger.exception('Error invalidating Data API cache on interest change')
