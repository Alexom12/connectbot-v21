"""WSGI entrypoint for ConnectBot project.

This file provides the WSGI application object used by WSGI servers
like Gunicorn.
"""
import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

application = get_wsgi_application()
