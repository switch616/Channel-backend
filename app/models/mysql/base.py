from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, DateTime,func

#  ORM 模型继承
class Base(DeclarativeBase):
    # 时间戳
    created_at = Column(DateTime, default=func.now())  # 创建时间
    updated_at = Column(DateTime, onupdate=func.now())  # 最后更新时间
