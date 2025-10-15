"""Business logic for Data API: query existing Django models and return
serialized data structures suitable for the Java matching service.
"""
from typing import Dict, Any, List
from datetime import datetime, timedelta
import logging

from django.db.models import Prefetch

from python_app.serializers.data_serializers import serialize_employee, serialize_interest

logger = logging.getLogger(__name__)


class DataAPIService:
    def __init__(self):
        # import models lazily to avoid startup ordering issues
        from employees.models import Employee, Department, Interest, EmployeeInterest
        self.Employee = Employee
        self.Department = Department
        self.Interest = Interest
        self.EmployeeInterest = EmployeeInterest
        try:
            from employees.models import SecretCoffeeMeeting
            self.SecretCoffeeMeeting = SecretCoffeeMeeting
        except Exception:
            # SecretCoffeeMeeting may not be importable in some test setups; handle gracefully
            self.SecretCoffeeMeeting = None

    def get_employees_for_matching(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Return employees payload according to spec. Accepts optional filters in params.

        params may contain:
          - algorithm_type: string (used to vary what fields to include)
          - department_ids: list
          - active_only: bool
        """
        qs = self.Employee.objects.select_related('department')

        if params.get('active_only', True):
            qs = qs.filter(is_active=True)

        dept_ids = params.get('department_ids')
        if dept_ids:
            qs = qs.filter(department_id__in=dept_ids)
        # prefetch interests via EmployeeInterest -> Interest (related_name='interests')
        qs = qs.prefetch_related(Prefetch('interests', queryset=self.EmployeeInterest.objects.select_related('interest')))

        employees = []
        for e in qs:
            employees.append(serialize_employee(e))

        return {'employees': employees, 'generated_at': datetime.utcnow().isoformat()}

    def get_previous_matches(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Return recent SecretCoffeeMeeting history.

        params may include 'since_days' to limit the window.
        """
        since_days = int(params.get('since_days', 90))
        since_date = datetime.utcnow().date() - timedelta(days=since_days)

        if not self.SecretCoffeeMeeting:
            return {'matches': [], 'count': 0}

        qs = self.SecretCoffeeMeeting.objects.select_related('employee1', 'employee2')
        qs = qs.filter(week_start__gte=since_date).order_by('-created_at')[:1000]

        out = []
        for m in qs:
            out.append({'employee1_id': str(m.employee1_id), 'employee2_id': str(m.employee2_id), 'created_at': m.created_at.isoformat(), 'week_start': m.week_start.isoformat()})

        return {'matches': out, 'count': len(out)}

    def get_employee_interests(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Return mapping of employee_id -> interests list.

        Optional params:
          - employee_ids: list
        """
        employee_ids = params.get('employee_ids')
        qs = self.EmployeeInterest.objects.select_related('interest')
        if employee_ids:
            qs = qs.filter(employee_id__in=employee_ids)

        mapping = {}
        for rel in qs:
            empid = str(rel.employee_id)
            mapping.setdefault(empid, []).append(serialize_interest(rel.interest))

        return {'interests': mapping}
