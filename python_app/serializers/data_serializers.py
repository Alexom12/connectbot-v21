"""Serializers for Data API: convert Django models to safe JSON for Java service.

Do not include PII fields (telegram_id, telegram_username, email, phone, etc.).
"""
from typing import Dict, Any, List

def serialize_department(dept) -> Dict[str, Any]:
    if not dept:
        return None
    return {
        'id': str(getattr(dept, 'id', None)),
        'name': getattr(dept, 'name', None),
        'code': getattr(dept, 'code', None),
    }


def serialize_interest(interest) -> Dict[str, Any]:
    return {
        'id': str(getattr(interest, 'id', None)),
        'name': getattr(interest, 'name', None),
        'category': getattr(interest, 'category', None),
    }


def serialize_employee(emp) -> Dict[str, Any]:
    # Only include non-PII fields per spec
    deps = serialize_department(getattr(emp, 'department', None))
    # business_center has similar shape to Department; reuse serializer
    business_center = serialize_department(getattr(emp, 'business_center', None))
    # try related_name 'interests' first (EmployeeInterest related_name)
    interests_qs = getattr(emp, 'interests', None) or getattr(emp, 'employeeinterest_set', None)
    interests_list = []
    if interests_qs is not None:
        try:
            # allow both related manager and list
            for rel in interests_qs.all():
                interest = getattr(rel, 'interest', None) or rel
                interests_list.append(serialize_interest(interest))
        except Exception:
            # if emp.employee_interests exists as list of Interest objects
            try:
                for it in interests_qs:
                    interests_list.append(serialize_interest(it))
            except Exception:
                interests_list = []

    return {
        'id': str(getattr(emp, 'id', None)),
        'full_name': getattr(emp, 'full_name', None) or getattr(emp, 'display_name', None),
        'department': deps,
        'position': getattr(emp, 'position', None),
        'business_center': business_center,
        'interests': interests_list,
        'is_active': bool(getattr(emp, 'is_active', False)),
    }


def sanitize_request_for_logging(body: Dict[str, Any]) -> Dict[str, Any]:
    # keep only counts and non-PII summary for logs
    out = {}
    if not body:
        return out
    if 'employees' in body:
        out['employees_count'] = len(body.get('employees') or [])
    if 'since' in body:
        out['since'] = body.get('since')
    return out
