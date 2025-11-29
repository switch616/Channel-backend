from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from app.core.config import settings
from app.db.mysql import get_db
from app.models.mysql.user import User
from app.crud.user import get_user_by_email

# 定义OAuth2密码模式的token获取路径
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/user/auth/login")

# 获取当前登录用户的依赖函数
async def get_current_user(
    token: str = Depends(oauth2_scheme),  # 自动从请求头Authorization解析Bearer token
    db: Session = Depends(get_db),        # 获取数据库会话
) -> User:
    # 定义认证失败时抛出的异常
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证身份",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # 解码JWT token，校验签名和有效性
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")  # 从payload中获取用户标识（通常为邮箱）
        token_iat = payload.get("iat")
        if email is None:
            raise credentials_exception
    except JWTError:
        # 解码失败或token无效时抛出异常
        raise credentials_exception

    # 根据邮箱查询用户
    user = await get_user_by_email(db, email=email)
    if user is None:
        # 用户不存在，抛出认证失败异常
        raise credentials_exception

    # 校验token签发时间是否早于密码更新时间
    if token_iat is not None and user.password_updated_at is not None:
        from datetime import datetime, timezone
        try:
            # 兼容int/float/str
            if isinstance(token_iat, (int, float)):
                token_iat_dt = datetime.fromtimestamp(token_iat, tz=timezone.utc)
            elif isinstance(token_iat, str):
                try:
                    token_iat_dt = datetime.fromisoformat(token_iat)
                    if token_iat_dt.tzinfo is None:
                        token_iat_dt = token_iat_dt.replace(tzinfo=timezone.utc)
                except Exception:
                    token_iat_dt = None
            else:
                token_iat_dt = None
        except Exception:
            token_iat_dt = None

        pwd_updated_at = user.password_updated_at
        if hasattr(pwd_updated_at, 'tzinfo') and pwd_updated_at.tzinfo is None:
            pwd_updated_at = pwd_updated_at.replace(tzinfo=timezone.utc)
        # 只有token_iat_dt和pwd_updated_at都为datetime类型时才比较
        from datetime import timedelta, datetime as dt_type
        if (
            isinstance(token_iat_dt, dt_type)
            and isinstance(pwd_updated_at, dt_type)
            and token_iat_dt < (pwd_updated_at - timedelta(seconds=2))
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="登录状态已失效，请重新登录",
                headers={"WWW-Authenticate": "Bearer"},
            )

    # 返回当前登录用户对象
    return user
