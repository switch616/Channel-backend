import time
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

# 自定义 logger，避免与 uvicorn logger 冲突
logger = logging.getLogger("middleware.logger")
logger.setLevel(logging.INFO)

if not logger.hasHandlers():
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '[%(asctime)s] [%(levelname)s] %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        start_time = time.time()

        try:
            response = await call_next(request)
        except Exception as e:
            process_time = (time.time() - start_time) * 1000
            logger.error(
                self._format_log(request, 500, process_time, error=str(e))
            )
            raise

        process_time = (time.time() - start_time) * 1000

        logger_method = logger.error if response.status_code >= 500 else logger.info
        logger_method(
            self._format_log(request, response.status_code, process_time)
        )

        return response

    def _format_log(self, request: Request, status: int, duration: float, error: str = None) -> str:
        log = {
            "method": request.method,
            "path": request.url.path,
            "status": status,
            "duration_ms": round(duration, 2),
            "client_ip": request.client.host,
        }

        if error:
            log["error"] = error

        # 可以拓展成 JSON 输出结构日志
        return " | ".join(f"{k}={v}" for k, v in log.items())


def add_logging_middleware(app):
    app.add_middleware(RequestLoggingMiddleware)
