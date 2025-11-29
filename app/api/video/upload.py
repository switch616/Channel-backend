from fastapi import APIRouter, UploadFile, File, Form, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, get_current_user
from app.schemas.response import ResponseSchema
from app.services.video import save_user_video

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
    """
    url = await save_user_video(
        db=db,
        video_file=video,
        cover_file=cover,
        uploader_id=current_user.id,
        title=title,
        description=description,
    )

    return ResponseSchema.success(data={"url": url})
