import logging

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        logger.info(
            "Request: %s %s from %s - User-Agent: %s",
            request.method,
            request.path,
            request.META.get("REMOTE_ADDR"),
            request.META.get("HTTP_USER_AGENT", "Unknown"),
        )
        response = self.get_response(request)
        return response
