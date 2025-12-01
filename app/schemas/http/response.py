from enum import IntEnum
from typing import Generic, Optional, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")  # 泛型类型变量，用于指定响应数据类型


class BizCode(IntEnum):
    """
    业务状态码约定：

    - 0：成功
    - 1xxx：客户端 / 业务侧可预期错误（参数、认证、权限、资源不存在等）
    - 2xxx：服务端内部错误（非预期异常）

    这样做的原因：
    1. 通过「首位数字」可以快速区分错误大类（前端/运维统计更方便）；
    2. 同一类错误预留足够区间（1000 ~ 1999）给后续子模块扩展；
    3. 与 HTTP 状态码解耦，不会被 4xx/5xx 的含义限制，可以灵活演进。
    """

    SUCCESS = 0  # 通用成功

    # 1xxx：客户端 / 业务错误（参数校验、认证失败、权限不足、资源不存在等）
    VALIDATION_ERROR = 1000  # 参数、验证码等校验失败
    AUTH_FAILED = 1001  # 认证失败（账号或密码错误、token 非法等）
    PERMISSION_DENIED = 1003  # 已认证，但没有访问该资源的权限
    NOT_FOUND = 1004  # 资源不存在（用户、视频、记录等）

    # 2xxx：服务端内部错误
    SERVER_ERROR = 2000  # 未捕获异常、依赖服务异常等统一归类


class Response(BaseModel, Generic[T]):
    """
    通用响应模型（与 HTTP 状态码强相关的简单包装）。

    主要用于内部工具（如 app.utils.response），不强制所有接口直接使用。
    """

    status_code: int = Field(..., description="HTTP 状态码或业务状态码")
    message: str = Field(..., description="返回信息描述")
    data: Optional[T] = Field(default=None, description="响应数据")


class ResponseSchema(BaseModel, Generic[T]):
    """
    企业级统一 API 响应模型：所有对外接口建议统一返回该结构。

    - code: 业务状态码（0 成功，非 0 为错误）
    - msg: 用户可读的提示信息
    - data: 具体业务数据
    - success: 是否成功的显式布尔值，方便前端判断
    - trace_id: 链路追踪 ID，可由中间件注入（预留字段）
    """

    code: int = Field(
        default=int(BizCode.SUCCESS),
        description="业务状态码，0 表示成功，非 0 表示错误",
    )
    msg: str = Field(default="success", description="提示信息")
    data: Optional[T] = Field(default=None, description="响应数据")
    # 使用 is_success 作为内部字段名，输出仍然是 success，避免与 classmethod success 冲突
    is_success: bool = Field(
        default=True,
        serialization_alias="success",
        description="是否成功",
    )
    trace_id: Optional[str] = Field(
        default=None, description="链路追踪 ID（可选，由中间件注入）"
    )

    @classmethod
    def success(
        cls,
        data: Optional[T] = None,
        msg: str = "success",
        code: int | BizCode = BizCode.SUCCESS,
        trace_id: Optional[str] = None,
    ) -> "ResponseSchema[T]":
        """
        成功响应工厂方法。
        """
        return cls(
            code=int(code),
            msg=msg,
            data=data,
            is_success=True,
            trace_id=trace_id,
        )

    @classmethod
    def error(
        cls,
        code: int | BizCode = BizCode.SERVER_ERROR,
        msg: str = "error",
        data: Optional[T] = None,
        trace_id: Optional[str] = None,
    ) -> "ResponseSchema[T]":
        """
        失败响应工厂方法。
        """
        return cls(
            code=int(code),
            msg=msg,
            data=data,
            is_success=False,
            trace_id=trace_id,
        )

    # 为已有代码中使用的 ResponseSchema.fail 提供兼容别名
    @classmethod
    def fail(
        cls,
        msg: str = "error",
        code: int | BizCode = BizCode.SERVER_ERROR,
        data: Optional[T] = None,
        trace_id: Optional[str] = None,
    ) -> "ResponseSchema[T]":
        """
        兼容旧代码的 fail 方法，语义等同于 error。
        """
        return cls.error(code=code, msg=msg, data=data, trace_id=trace_id)
