from .comment import *

comment_router = APIRouter(prefix="/comment", tags=["评论"])

comment_router.include_router(comment.router)
