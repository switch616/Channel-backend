from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import timedelta

from app import crud, schemas
from app.db.mysql import get_db  # 异步数据库依赖
from app.db.redis import get_redis_aioredis_client  # Redis 客户端依赖
from app.utils.security import create_access_token  # JWT 创建函数
from app.schemas.http.response import ResponseSchema, BizCode

router = APIRouter(prefix="/auth", tags=["用户认证"])


@router.post("/login", response_model=ResponseSchema[dict])
async def login(
    email: str = Body(..., description="邮箱或用户名"),
    password: str = Body(..., description="登录密码"),
    captcha_id: str = Body(..., description="验证码唯一标识"),
    captcha_text: str = Body(..., description="用户输入的验证码"),
    db: AsyncSession = Depends(get_db),
    redis_client=Depends(get_redis_aioredis_client),
):
    """
    用户登录接口：
    - 验证图形验证码
    - 支持邮箱或用户名登录
    - 返回统一格式的 JWT Token 响应
    """
    # 验证码校验
    real_code = await redis_client.get(captcha_id)
    if not real_code:
        # 验证码已过期（业务错误，但 HTTP 仍返回 200，前端根据 code 判断）
        return ResponseSchema.error(
            code=BizCode.VALIDATION_ERROR,
            msg="验证码已过期",
        )
    if captcha_text.strip().lower() != real_code.strip().lower():
        return ResponseSchema.error(
            code=BizCode.VALIDATION_ERROR,
            msg="验证码错误",
        )

    # 尝试使用邮箱登录
    user = await crud.authenticate_user(db, email=email, password=password)
    # 尝试用户名登录（兼容）
    if not user:
        user = await crud.authenticate_user(db, email=email, password=password, by_username=True)

    if not user:
        return ResponseSchema.error(
            code=BizCode.AUTH_FAILED,
            msg="账号或密码错误",
        )

    # 清理验证码缓存
    await redis_client.delete(captcha_id)

    # 生成 JWT token
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=access_token_expires
    )

    # 统一响应结构
    return ResponseSchema.success(
        data={
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": access_token_expires.total_seconds(),
        }
    )


@router.post("/register", response_model=ResponseSchema[schemas.UserResponse])
async def register(
    user: schemas.RegisterRequest,
    db: AsyncSession = Depends(get_db),
    redis_client=Depends(get_redis_aioredis_client),
):
    """
    用户注册接口：
    - 验证邮箱验证码
    - 创建新用户
    - 返回统一格式的用户信息
    """
    # 校验验证码是否存在
    stored_code = await redis_client.get(user.email)
    if not stored_code:
        return ResponseSchema.error(
            code=BizCode.VALIDATION_ERROR,
            msg="验证码已过期或未发送",
        )

    if user.code != stored_code:
        return ResponseSchema.error(
            code=BizCode.VALIDATION_ERROR,
            msg="验证码错误",
        )

    # 判断邮箱是否已注册
    existing_user = await crud.get_user_by_email(db, user.email)
    if existing_user:
        return ResponseSchema.error(
            code=BizCode.VALIDATION_ERROR,
            msg="邮箱已注册",
        )

    # 创建用户
    user_create = schemas.UserCreate(**user.model_dump(exclude={"code"}, exclude_none=True))
    db_user = await crud.create_user(db, user_create)

    # 删除验证码缓存
    await redis_client.delete(user.email)

    return ResponseSchema.success(data=db_user, msg="注册成功")
