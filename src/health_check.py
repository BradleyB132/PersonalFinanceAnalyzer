"""Simple health check endpoint for PersonalFinanceAnalyzer.

This runs on a separate port (8502) to provide a dedicated health endpoint
for monitoring services like UpTimeRobot.
"""

import json
import logging
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from datetime import datetime

logger = logging.getLogger(__name__)


class HealthHandler(BaseHTTPRequestHandler):
    """HTTP request handler for health check endpoint."""

    def do_GET(self):
        """Handle GET requests.

        Responds to `/health` with a small JSON payload describing status and
        timestamp. Other paths return 404.
        """
        if self.path == "/health":
            response = {
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "service": "PersonalFinanceAnalyzer",
            }
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
            logger.info("Health check request successful")
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        """Suppress default logging."""
        pass


def run_health_server(port: int = 8502) -> None:
    """Start a simple HTTP server that serves the health endpoint.

    This function blocks and runs the server in the current thread. It is
    intended to be used in a dedicated process or thread for monitoring.
    """
    server_address = ("0.0.0.0", port)
    httpd = HTTPServer(server_address, HealthHandler)
    logger.info(f"Health check server listening on port {port}")
    httpd.serve_forever()


if __name__ == "__main__":
    port = int(os.getenv("HEALTH_CHECK_PORT", "8502"))
    run_health_server(port)
