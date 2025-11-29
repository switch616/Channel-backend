from .upload import *
from .video import *

video_router = APIRouter(prefix="/video", tags=["视频"])

video_router.include_router(upload.router)
video_router.include_router(video.router)
