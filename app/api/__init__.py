from fastapi import APIRouter

from .user import user_router
from .video import video_router
from .comment import comment_router
from .interaction import interaction_router
from .analytics import analytics_router

api_router_v1 = APIRouter(prefix="/api/v1", tags=["API V1"])

api_router_v1.include_router(user_router)
api_router_v1.include_router(video_router)
api_router_v1.include_router(comment_router)
api_router_v1.include_router(interaction_router)
api_router_v1.include_router(analytics_router)
