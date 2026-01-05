from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta
from app.core.config import settings
from app.db.mysql import get_db
from app.models.mysql.user import User
from app.crud.user import get_user_by_email

# 不再声明 OAuth2，只声明 Bearer
security = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """
    当前登录用户依赖
    - 支持 Authorization: Bearer <token>
    - 也支持 Cookie: access_token
    """

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证身份",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # 统一拿 token（Header 优先，其次 Cookie）
    token: str | None = None

    if credentials:
        token = credentials.credentials
    else:
        token = request.cookies.get("access_token")

    if not token:
        raise credentials_exception

    # 解码 JWT
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        email: str | None = payload.get("sub")
        token_iat = payload.get("iat")

        if not email:
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    # 查用户
    user = await get_user_by_email(db, email=email)
    if not user:
        raise credentials_exception

    # token 是否早于密码更新时间（踢下线逻辑）
    if token_iat and user.password_updated_at:
        token_iat_dt: datetime | None = None

        try:
            if isinstance(token_iat, (int, float)):
                token_iat_dt = datetime.fromtimestamp(token_iat, tz=timezone.utc)
            elif isinstance(token_iat, str):
                token_iat_dt = datetime.fromisoformat(token_iat)
                if token_iat_dt.tzinfo is None:
                    token_iat_dt = token_iat_dt.replace(tzinfo=timezone.utc)
        except Exception:
            token_iat_dt = None

        pwd_updated_at = user.password_updated_at
        if pwd_updated_at.tzinfo is None:
            pwd_updated_at = pwd_updated_at.replace(tzinfo=timezone.utc)

        if token_iat_dt and token_iat_dt < (pwd_updated_at - timedelta(seconds=2)):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="登录状态已失效，请重新登录",
                headers={"WWW-Authenticate": "Bearer"},
            )

    # 返回用户
    return user
