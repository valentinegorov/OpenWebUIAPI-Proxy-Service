"""Metrics endpoint for Prometheus-compatible monitoring."""

import logging

from flask import Blueprint

from app.extensions import limiter
from app.utils.metrics import get_metrics_response

metrics_bp = Blueprint("metrics", __name__)
logger = logging.getLogger(__name__)


@metrics_bp.route("/metrics", methods=["GET"])
@limiter.exempt
def metrics_endpoint():
    """
    Expose Prometheus-format metrics for monitoring.
    
    This endpoint is exempt from rate limiting to ensure monitoring
    systems can always collect metrics.
    
    Returns:
        Prometheus-format metrics text response.
    """
    logger.info("Metrics requested")
    return get_metrics_response()
