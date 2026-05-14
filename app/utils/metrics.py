"""OpenTelemetry metrics configuration for Prometheus export."""

import logging
from typing import Optional

from opentelemetry import metrics
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.view import View
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from flask import Response


logger = logging.getLogger(__name__)

# Global meter provider instance
_meter_provider: Optional[MeterProvider] = None
_meter: Optional[metrics.Meter] = None


def setup_metrics() -> None:
    """
    Set up OpenTelemetry metrics with Prometheus exporter.
    
    Creates counters, histograms, and gauges for monitoring:
    - Request count (total requests)
    - Request latency (histogram)
    - Error count (by status code)
    - Active connections (gauge)
    """
    global _meter_provider, _meter
    
    # Create Prometheus metric reader
    reader = PrometheusMetricReader()
    
    # Configure metric views for custom aggregations
    views = [
        # Histogram view for request latency with custom buckets
        View(
            instrument_name="request_latency",
            description="Request latency in milliseconds",
        ),
        View(
            instrument_name="request_count",
            description="Total number of requests",
        ),
        View(
            instrument_name="error_count",
            description="Number of errors by status code",
        ),
    ]
    
    # Create meter provider with Prometheus reader
    _meter_provider = MeterProvider(
        metric_readers=[reader],
        views=views,
    )
    
    # Set as global meter provider
    metrics.set_meter_provider(_meter_provider)
    
    # Get meter for creating instruments
    _meter = _meter_provider.get_meter("openwebui-proxy")
    
    logger.info("OpenTelemetry metrics initialized with Prometheus exporter")


def get_meter() -> Optional[metrics.Meter]:
    """Get the configured meter instance."""
    return _meter


def get_metrics_response() -> Response:
    """
    Generate Prometheus-format metrics response.
    
    Returns:
        Flask Response with Prometheus metrics in text format.
    """
    if _meter_provider is None:
        logger.warning("Metrics not initialized")
        return Response("Metrics not initialized", status=503)
    
    try:
        # Generate Prometheus format metrics
        metrics_data = generate_latest()
        
        return Response(
            metrics_data,
            mimetype=CONTENT_TYPE_LATEST,
        )
    except Exception as e:
        logger.error("Error generating metrics: %s", e)
        return Response(f"Error generating metrics: {e}", status=500)


def record_request_latency(latency_ms: float, endpoint: str, method: str) -> None:
    """
    Record request latency histogram observation.
    
    Args:
        latency_ms: Request latency in milliseconds.
        endpoint: Request endpoint path.
        method: HTTP method.
    """
    if _meter is None:
        return
    
    try:
        histogram = _meter.create_histogram(
            name="request_latency",
            description="Request latency in milliseconds",
            unit="ms",
        )
        histogram.record(
            latency_ms,
            attributes={
                "endpoint": endpoint,
                "method": method,
            }
        )
    except Exception as e:
        logger.debug("Failed to record latency metric: %s", e)


def increment_request_count(endpoint: str, method: str, status_code: int) -> None:
    """
    Increment request counter.
    
    Args:
        endpoint: Request endpoint path.
        method: HTTP method.
        status_code: HTTP response status code.
    """
    if _meter is None:
        return
    
    try:
        counter = _meter.create_counter(
            name="request_count",
            description="Total number of requests",
            unit="1",
        )
        counter.add(
            1,
            attributes={
                "endpoint": endpoint,
                "method": method,
                "status_code": str(status_code),
            }
        )
    except Exception as e:
        logger.debug("Failed to increment request count: %s", e)


def increment_error_count(endpoint: str, error_type: str) -> None:
    """
    Increment error counter.
    
    Args:
        endpoint: Request endpoint path.
        error_type: Type of error (timeout, backend_error, etc.).
    """
    if _meter is None:
        return
    
    try:
        counter = _meter.create_counter(
            name="error_count",
            description="Number of errors by type",
            unit="1",
        )
        counter.add(
            1,
            attributes={
                "endpoint": endpoint,
                "error_type": error_type,
            }
        )
    except Exception as e:
        logger.debug("Failed to increment error count: %s", e)


def shutdown_metrics() -> None:
    """Shut down the meter provider and clean up resources."""
    global _meter_provider, _meter
    
    if _meter_provider is not None:
        try:
            _meter_provider.shutdown()
        except Exception as e:
            try:
                logger.error("Error shutting down metrics provider: %s", e)
            except (ValueError, OSError):
                pass
        finally:
            _meter_provider = None
            _meter = None
