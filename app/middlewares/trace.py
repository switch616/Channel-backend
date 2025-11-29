import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.types import ASGIApp
from starlette.responses import Response
import contextvars

# 使用 ContextVar 支持异步环境中获取当前请求的 trace_id
trace_id_ctx_var: contextvars.ContextVar[str] = contextvars.ContextVar("trace_id", default=None)

def get_trace_id() -> str:
    return trace_id_ctx_var.get()

class TraceIDMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        # 优先使用客户端提供的 trace_id
        trace_id = request.headers.get("X-Trace-Id", str(uuid.uuid4()))
        trace_id_ctx_var.set(trace_id)

        # 加入请求日志上下文（兼容 logging 使用）
        request.state.trace_id = trace_id

        response: Response = await call_next(request)
        response.headers["X-Trace-Id"] = trace_id  # 返回给客户端

        return response

def add_trace_middleware(app):
    app.add_middleware(TraceIDMiddleware)
