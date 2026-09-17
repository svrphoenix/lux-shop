import logging

from django.db import connection
from django.http import JsonResponse
from rest_framework import status

logger = logging.getLogger(__name__)


# Create your views here.
def health_check(request) -> JsonResponse:
    """
    Endpoint for Liveness/Readiness checking.
    """
    health_data = {
        "status": "ok",
        "database": "ok",
    }
    http_status_code = status.HTTP_200_OK

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1;")
    except Exception as exc:
        logger.error("Health check DB failure: %s", exc)
        health_data["status"] = "unhealthy"
        health_data["database"] = "error"
        http_status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return JsonResponse(health_data, status=http_status_code)
