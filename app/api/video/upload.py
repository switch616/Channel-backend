import os
from fastapi import APIRouter, UploadFile, File, Form, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, get_current_user
from app.schemas.http.response import ResponseSchema, BizCode
from app.services.video import save_user_video
from app.crud.video.video import count_user_videos
from app.core.config import settings

router = APIRouter()


@router.post("/upload_video", response_model=ResponseSchema)
async def upload_video(
    title: str = Form(..., description="视频标题，必填"),
    description: str = Form("", description="视频描述，可选"),
    video: UploadFile = File(..., description="上传的视频文件"),
    cover: UploadFile = File(..., description="视频封面图"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    上传用户视频接口：
    - 接收视频文件和封面图片
    - 校验、保存文件，生成唯一文件名
    - 将视频元信息写入数据库
    - 返回视频播放地址或资源路径
    
    测试模式限制：
    - 每个用户最多上传10个视频
    """
    # 测试模式：检查用户视频数量限制
    is_test_mode = os.getenv("APP_ENV", "dev") == "test"
    if is_test_mode:
        max_videos = getattr(settings, "TEST_MODE_MAX_VIDEOS", 10)
        current_video_count = await count_user_videos(db, current_user.id)
        if current_video_count >= max_videos:
            return ResponseSchema.error(
                code=BizCode.PERMISSION_DENIED,
                msg=f"测试模式：每个用户最多只能上传 {max_videos} 个视频，您当前已有 {current_video_count} 个视频",
            )
    
    url = await save_user_video(
        db=db,
        video_file=video,
        cover_file=cover,
        uploader_id=current_user.id,
        title=title,
        description=description,
    )

    return ResponseSchema.success(data={"url": url})
