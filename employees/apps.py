from django.apps import AppConfig


class EmployeesConfig(AppConfig):
    name = 'employees'
    verbose_name = 'Employees'

    def ready(self):
        # Import signals to register them
        try:
            from . import signals  # noqa: F401
        except Exception:
            # avoid raising on import-time errors
            import logging
            logging.getLogger(__name__).exception('Failed to import employees.signals')
