from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.mysql.user import User
from app.utils.security import verify_password


async def authenticate_user(
    db: AsyncSession,
    email: str,
    password: str,
    by_username: bool = False
):
    """
    用户身份认证函数

    参数：
    - db: 异步数据库会话对象
    - email: 用户输入的邮箱地址或用户名（根据 by_username 决定字段）
    - password: 明文密码
    - by_username: 是否通过用户名进行查询（默认通过邮箱）

    返回：
    - 匹配成功的用户对象（User 模型实例），否则返回 None
    """

    # 根据用户名或邮箱生成对应查询语句
    if by_username:
        stmt = select(User).filter(User.username == email)
    else:
        stmt = select(User).filter(User.email == email)

    # 执行查询
    result = await db.execute(stmt)
    user = result.scalars().first()

    # 校验密码是否匹配
    if user and verify_password(password, user.password):
        return user

    return None
