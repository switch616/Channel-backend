"""
测试模式中间件
当 APP_ENV=test 时，启用测试模式限制：
1. 禁止用户注册
2. 限制视频上传数量（在视频上传接口中处理）
3. 添加测试模式标识到响应头
4. 可选：IP白名单、访问频率限制等安全措施
"""
import os
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.types import ASGIApp
from app.core.config import settings
from app.schemas.http.response import ResponseSchema, BizCode


class TestModeMiddleware(BaseHTTPMiddleware):
    """
    测试模式中间件
    仅在 APP_ENV=test 时生效
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        # 检查是否为测试模式
        self.is_test_mode = os.getenv("APP_ENV", "dev") == "test"
        
        # 测试模式下的IP白名单（可选，从环境变量或配置读取，逗号分隔）
        # 优先级：环境变量 > 配置文件
        whitelist_str = os.getenv("TEST_MODE_IP_WHITELIST", "") or getattr(settings, "TEST_MODE_IP_WHITELIST", "")
        self.ip_whitelist = set(ip.strip() for ip in whitelist_str.split(",") if ip.strip()) if whitelist_str else None
        
        # 禁止注册的接口路径
        self.register_paths = [
            "/api/v1/user/auth/register",
        ]
        
        # 需要限制的接口路径（视频上传等）
        self.restricted_paths = [
            "/api/v1/video/upload_video",
        ]

    def _get_client_ip(self, request: Request) -> str:
        """获取客户端真实IP地址"""
        # 优先从 X-Forwarded-For 获取（代理/负载均衡场景）
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # X-Forwarded-For 可能包含多个IP，取第一个
            return forwarded_for.split(",")[0].strip()
        
        # 其次从 X-Real-IP 获取
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()
        
        # 最后使用客户端IP
        if request.client:
            return request.client.host
        
        return "unknown"

    def _is_whitelisted_ip(self, client_ip: str) -> bool:
        """检查IP是否在白名单中"""
        if self.ip_whitelist is None:
            return True  # 未设置白名单，允许所有IP
        return client_ip in self.ip_whitelist

    async def dispatch(self, request: Request, call_next):
        # 非测试模式，直接放行
        if not self.is_test_mode:
            response = await call_next(request)
            return response

        # 测试模式下的安全措施
        client_ip = self._get_client_ip(request)
        
        # 1. IP白名单检查（如果设置了白名单）
        if self.ip_whitelist is not None and not self._is_whitelisted_ip(client_ip):
            return JSONResponse(
                status_code=403,
                content=ResponseSchema.error(
                    code=BizCode.PERMISSION_DENIED,
                    msg="测试模式：您的IP地址不在白名单中，无法访问",
                ).model_dump()
            )

        # 2. 禁止注册接口
        if request.url.path in self.register_paths and request.method == "POST":
            return JSONResponse(
                status_code=403,
                content=ResponseSchema.error(
                    code=BizCode.PERMISSION_DENIED,
                    msg="测试模式：当前不允许注册新用户",
                ).model_dump()
            )

        # 3. 继续处理请求
        response = await call_next(request)

        # 4. 添加测试模式标识到响应头
        response.headers["X-Test-Mode"] = "true"
        response.headers["X-Environment"] = "test"
        
        # 5. 可选：添加测试模式提示信息到响应体（仅用于调试）
        # 注意：这里不修改响应体，因为可能影响前端解析
        # 如果需要，可以在响应头中添加更多信息
        
        return response


def add_test_mode_middleware(app):
    """
    添加测试模式中间件到应用
    """
    app.add_middleware(TestModeMiddleware)

