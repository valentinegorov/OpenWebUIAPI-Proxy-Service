"""Route handlers for the OpenWebUI Proxy Server."""

from app.routes.models import models_bp
from app.routes.chat import chat_bp
from app.routes.health import health_bp
from app.routes.metrics import metrics_bp

__all__ = ["models_bp", "chat_bp", "health_bp", "metrics_bp"]
