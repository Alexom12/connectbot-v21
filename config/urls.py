"""
URL configuration for ConnectBot project.
"""
from django.contrib import admin
from django.urls import path, include
from . import metrics as metrics_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('metrics/', metrics_view.metrics_endpoint),
    path('metrics/internal/', metrics_view.metrics_internal),
    path('metrics/trigger/', metrics_view.metrics_trigger),
    path('api/v1/data/', include('python_app.api.urls_data')),
]
