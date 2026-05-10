"""WSGI entry point for gunicorn.

This module provides a module-level ``app`` callable that gunicorn can
discover.  It uses the application factory from ``app.main`` so the
same configuration, logging and blueprint registration path is used
in production as in development.
"""

from app.main import create_app

app = create_app()
