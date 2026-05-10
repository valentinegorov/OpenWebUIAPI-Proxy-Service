from flask import Flask, request, jsonify
import requests
import os
import logging
from logging.handlers import RotatingFileHandler
import sys
from datetime import datetime

# Load environment variables from .env file if it exists
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed, rely on system environment variables

app = Flask(__name__)

# Configuration for OpenWebUI - loaded from environment variable
OPENWEBUI_BASE_URL = os.environ.get("OPENWEBUI_BASE_URL", "http://localhost:3000")

# Configure structured logging
def setup_logging():
    """Set up structured logging with both file and console handlers."""
    log_format = logging.Formatter(
        '%(asctime)s | %(levelname)s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # File handler with rotation
    file_handler = RotatingFileHandler(
        'proxy_server.log',
        maxBytes=10*1024*1024,  # 10 MB
        backupCount=5
    )
    file_handler.setFormatter(log_format)
    file_handler.setLevel(logging.INFO)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_format)
    console_handler.setLevel(logging.INFO)
    
    # Configure app logger
    app.logger.addHandler(file_handler)
    app.logger.addHandler(console_handler)
    app.logger.setLevel(logging.INFO)
    
    return app.logger

logger = setup_logging()

@app.route('/v1/models', methods=['GET'])
def get_models():
    auth_header = request.headers.get('Authorization')
    client_ip = request.remote_addr
    
    logger.info(
        f"Request received | endpoint=/v1/models | method=GET | client_ip={client_ip}"
    )
    
    headers = {
        'Authorization': auth_header,
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(f"{OPENWEBUI_BASE_URL}/api/models", headers=headers, timeout=30)
        
        logger.info(
            f"Response from OpenWebUI | status={response.status_code} | latency_ms={response.elapsed.total_seconds()*1000:.2f}"
        )
        
        if response.status_code == 200:
            logger.info("Successfully retrieved models")
            return jsonify(response.json())
        else:
            logger.warning(f"Failed to retrieve models | status={response.status_code}")
            return jsonify({"error": "Failed to retrieve models"}), response.status_code
    except requests.exceptions.Timeout:
        logger.error("Request timed out | endpoint=/api/models")
        return jsonify({"error": "Request timed out"}), 504
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed | error={str(e)}")
        return jsonify({"error": str(e)}), 502

@app.route('/v1/chat/completions', methods=['POST'])
def chat_completions():
    auth_header = request.headers.get('Authorization')
    client_ip = request.remote_addr
    
    logger.info(
        f"Request received | endpoint=/v1/chat/completions | method=POST | client_ip={client_ip}"
    )
    
    headers = {
        'Authorization': auth_header,
        'Content-Type': 'application/json'
    }
    
    data = request.get_json()
    
    # Log request payload summary (avoid logging full messages for privacy)
    model_name = data.get("model", "unknown") if data else "unknown"
    message_count = len(data.get("messages", [])) if data else 0
    logger.info(
        f"Request payload | model={model_name} | message_count={message_count}"
    )
    
    openwebui_payload = {
        "model": data.get("model"),
        "messages": data.get("messages")
    }
    
    try:
        response = requests.post(f"{OPENWEBUI_BASE_URL}/api/chat/completions", headers=headers, json=openwebui_payload, timeout=120)  # Increased to 120 seconds
        
        logger.info(
            f"Response from OpenWebUI | status={response.status_code} | latency_ms={response.elapsed.total_seconds()*1000:.2f}"
        )
        
        if response.status_code == 200:
            logger.info("Successfully retrieved chat completion")
            return jsonify(response.json())
        else:
            logger.warning(f"Failed to get chat completion | status={response.status_code}")
            return jsonify({"error": "Failed to get chat completion"}), response.status_code
    except requests.exceptions.Timeout:
        logger.error("Request timed out | endpoint=/api/chat/completions")
        return jsonify({"error": "Request timed out"}), 504
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed | error={str(e)}")
        return jsonify({"error": str(e)}), 502

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for monitoring and load balancer probes."""
    logger.info("Health check requested")
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }), 200

@app.route('/ready', methods=['GET'])
def readiness_check():
    """Readiness check to verify backend connectivity."""
    logger.info("Readiness check requested")
    try:
        response = requests.get(f"{OPENWEBUI_BASE_URL}/api/models", timeout=5)
        if response.status_code == 200:
            logger.info("Backend OpenWebUI is reachable")
            return jsonify({
                "status": "ready",
                "backend": "connected",
                "timestamp": datetime.utcnow().isoformat()
            }), 200
        else:
            logger.warning(f"Backend returned non-200 status: {response.status_code}")
            return jsonify({
                "status": "not_ready",
                "backend": f"unhealthy (status {response.status_code})",
                "timestamp": datetime.utcnow().isoformat()
            }), 503
    except requests.exceptions.RequestException as e:
        logger.error(f"Backend unreachable | error={str(e)}")
        return jsonify({
            "status": "not_ready",
            "backend": "unreachable",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }), 503

if __name__ == '__main__':
    # Determine debug mode from environment variable (default to False for production)
    debug_mode = os.environ.get("FLASK_DEBUG", "false").lower() in ("true", "1", "yes")
    
    if debug_mode:
        logger.warning("Running in DEBUG mode - NOT suitable for production!")
    
    logger.info(f"Starting proxy server on 0.0.0.0:5001 | debug={debug_mode}")
    logger.info(f"OpenWebUI backend URL: {OPENWEBUI_BASE_URL}")
    
    app.run(debug=debug_mode, host='0.0.0.0', port=5001)
