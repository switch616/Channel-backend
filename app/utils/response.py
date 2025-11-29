from fastapi.responses import JSONResponse
from app.schemas.response import Response
from typing import Any

def success(data: Any = None, message: str = "操作成功", code: int = 200):
    return JSONResponse(
        status_code=code,
        content=Response(status_code=code, message=message, data=data).dict()
    )

def fail(message: str = "操作失败", code: int = 400, data: Any = None):
    return JSONResponse(
        status_code=code,
        content=Response(status_code=code, message=message, data=data).dict()
    )
