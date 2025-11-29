from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import traceback
import logging
import sys

logger = logging.getLogger(__name__)


class GlobalExceptionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except Exception as exc:
            # 格式化完整堆栈信息
            tb_exc = traceback.TracebackException(type(exc), exc, exc.__traceback__)
            stack_summary = traceback.extract_tb(exc.__traceback__)

            # 获取最后一条调用记录（最关键的报错位置）
            if stack_summary:
                last_call = stack_summary[-1]
                file_info = f"{last_call.filename}:{last_call.lineno} in {last_call.name}"
            else:
                file_info = "Unknown location"

            logger.error(f"Unhandled exception: {exc} at {file_info}")
            logger.debug("".join(tb_exc.format()))

            return JSONResponse(
                status_code=500,
                content={
                    "code": 500,
                    "message": "服务器内部错误，请稍后再试",
                    "detail": str(exc),
                    "location": file_info
                }
            )


def add_exception_handler(app):
    app.add_middleware(GlobalExceptionMiddleware)
