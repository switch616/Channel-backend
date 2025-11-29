import aiofiles
import os
from fastapi import UploadFile

CHUNK_SIZE = 1024 * 1024  # 每次读取写入的文件块大小，1MB

async def save_file_to_local(file: UploadFile, full_path: str):
    """
    异步将上传的文件保存到本地指定路径。

    Args:
        file: FastAPI 上传文件对象
        full_path: 文件保存的完整本地路径

    功能点：
    - 自动创建文件夹（如果不存在）
    - 分块读取上传文件，分块写入，避免内存占用过大
    """
    # 确保目标文件夹存在
    os.makedirs(os.path.dirname(full_path), exist_ok=True)

    # 异步打开目标文件，逐块写入内容
    async with aiofiles.open(full_path, "wb") as out_file:
        while True:
            chunk = await file.read(CHUNK_SIZE)  # 读取1MB数据块
            if not chunk:  # 读到文件末尾，停止循环
                break
            await out_file.write(chunk)  # 写入数据块
