from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import ORJSONResponse
from io import BytesIO
import base64
import uuid
from pydantic import EmailStr

from app.utils import generate_captcha_image, encrypt, send_code_email
from app.db.redis import get_redis_aioredis_client
from app.core.config import settings

router = APIRouter(prefix="/captcha", tags=["验证码"])

# 图形验证码有效期：30分钟
EXPIRE_TIME = 60 * 30

# 邮箱验证码有效期：2分钟
CODE_EXPIRE_TIME = 120


@router.get("/image_verification_code")
async def get_captcha(redis_client=Depends(get_redis_aioredis_client)):
    """
    获取图形验证码（Base64格式）:
    - 自动生成验证码图片并返回 captcha_id
    - 将验证码文本缓存到 Redis 中
    - 客户端需携带 captcha_id 和用户输入一起提交校验
    """
    image, code = generate_captcha_image()
    captcha_id = str(uuid.uuid4())

    # DEBUG 用：打印验证码（正式上线建议关闭）
    print(code)

    # Redis 存储验证码（异步管道优化）
    pipeline = redis_client.pipeline()
    pipeline.setex(captcha_id, EXPIRE_TIME, code)
    await pipeline.execute()

    # 转为 Base64 字符串（JPEG 格式，兼容性好）
    stream = BytesIO()
    image.save(stream, 'jpeg', quality=70)
    img_str = base64.b64encode(stream.getvalue()).decode('utf-8')

    return ORJSONResponse({
        "captcha_id": captcha_id,
        "image_base64": f"data:image/jpeg;base64,{img_str}"
    })


@router.post("/image_code_verify")
async def verify_captcha(
    captcha_id: str = Query(..., description="验证码唯一标识"),
    user_captcha: str = Query(..., description="用户输入的验证码"),
    redis_client=Depends(get_redis_aioredis_client)
):
    """
    验证图形验证码：
    - 从 Redis 获取对应验证码
    - 对比用户输入是否匹配
    - 验证通过即删除 Redis 缓存
    """
    stored_captcha = await redis_client.get(captcha_id)

    if not stored_captcha:
        raise HTTPException(status_code=400, detail="Captcha expired or invalid.")

    if stored_captcha.decode("utf-8") != user_captcha:
        raise HTTPException(status_code=400, detail="Invalid captcha.")

    await redis_client.delete(captcha_id)

    return ORJSONResponse({"message": "Captcha verified successfully."})


@router.post("/send_email")
async def send_email_code(
    email: EmailStr = Query(..., description="邮箱地址"),
    type: str = Query(..., description="验证码类型：0=注册，1=登录，2=找回密码"),
    redis_client=Depends(get_redis_aioredis_client)
):
    """
    发送邮箱验证码：
    - 通过类型选择邮件模板（注册、登录、找回密码）
    - 自动生成6位数字验证码
    - 异步发送邮件 + Redis 存储验证码
    """
    email_template = settings.WANGYI_EMAIL_TEMPLATE.get(type)
    if not email_template:
        raise HTTPException(status_code=400, detail="非法的邮件模板类型")

    # 生成验证码
    code = encrypt.random_code(6)
    print(code)

    # 发送邮件
    result = await send_code_email(email, code, email_template)
    if result["result"] != 0:
        raise HTTPException(status_code=500, detail=f"发送失败: {result['errmsg']}")

    # Redis 缓存验证码（键为邮箱地址）
    pipeline = redis_client.pipeline()
    pipeline.setex(email, CODE_EXPIRE_TIME, code)
    await pipeline.execute()

    return ORJSONResponse({"message": "验证码发送成功"})
