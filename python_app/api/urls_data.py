from django.urls import path
from python_app.api import data_api

urlpatterns = [
    path('employees-for-matching', data_api.employees_for_matching, name='employees_for_matching'),
    path('previous-matches', data_api.previous_matches, name='previous_matches'),
    path('employee-interests', data_api.employee_interests, name='employee_interests'),
    path('health', data_api.health, name='data_api_health'),
]
