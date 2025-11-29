from pydantic import BaseModel
from typing import Any, Optional, Generic, TypeVar

T = TypeVar("T")  # 泛型类型变量，用于指定响应数据类型

# 通用响应模型，支持泛型数据字段
class Response(BaseModel, Generic[T]):
    status_code: int  # HTTP状态码或业务状态码
    message: str  # 返回信息描述
    data: Optional[T] = None  # 泛型数据，支持任意类型，默认为空

# 统一API响应格式模型，支持泛型，默认成功结构
class ResponseSchema(BaseModel, Generic[T]):
    code: int = 0  # 业务状态码，0表示成功，非0表示错误
    msg: str = "success"  # 提示信息，默认成功
    data: Optional[T] = None  # 响应数据，泛型，支持任意结构

    # 成功响应工厂方法，简化成功响应构造
    @classmethod
    def success(cls, data: Optional[T] = None, msg: str = "success") -> "ResponseSchema":
        return cls(code=0, msg=msg, data=data)

    # 错误响应工厂方法，简化错误响应构造
    @classmethod
    def error(cls, code: int = 1, msg: str = "error", data: Optional[T] = None) -> "ResponseSchema":
        return cls(code=code, msg=msg, data=data)
