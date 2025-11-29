from fastapi import UploadFile, HTTPException

def validate_image(file: UploadFile):
    if file.content_type not in ["image/jpeg", "image/png"]:
        raise HTTPException(status_code=400, detail="仅支持 JPG/PNG 格式")
    if file.size and file.size > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="图片不能超过 5MB")


def validate_video(file: UploadFile, max_size_mb=100):
    allowed_types = ['video/mp4', 'video/webm', 'video/quicktime']
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="仅支持 MP4、WebM、MOV 格式")

    file.file.seek(0, 2)  # Move to end of file
    size = file.file.tell()
    file.file.seek(0)  # Reset cursor

    if size > max_size_mb * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"视频大小不能超过 {max_size_mb}MB")

