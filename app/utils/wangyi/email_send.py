# app/utils/email_utils.py

import aiosmtplib
from email.mime.text import MIMEText
from email.header import Header
from app.core.config import settings


async def send_code_email(email: str, code: str, send_type: str = "register") -> dict:
    """
    异步发送邮件验证码
    :param email: 收件人邮箱
    :param code: 验证码
    :param send_type: register | retrieve | login
    :return: dict
    """
    # 构造邮件内容
    if send_type == "register":
        subject = "注册激活"
        body = f"您的邮箱注册验证码为：{code}，有效时间为两分钟，请及时验证。"
    elif send_type == "retrieve":
        subject = "找回密码"
        body = f"您的邮箱重置验证码为：{code}，有效时间为两分钟，请及时验证。"
    elif send_type == "login":
        subject = "登录验证"
        body = f"您的邮箱登录验证码为：{code}，有效时间为两分钟，请及时验证。"
    else:
        return {"result": 1, "errmsg": "未知的邮箱发送类型"}

    message = MIMEText(body, "plain", "utf-8")
    message["From"] = Header(settings.EMAIL_FROM, "utf-8")
    message["To"] = Header(email, "utf-8")
    message["Subject"] = Header(subject, "utf-8")

    try:
        ret = await aiosmtplib.send(
            message,
            hostname=settings.EMAIL_HOST,
            port=int(settings.EMAIL_PORT),
            username=settings.EMAIL_HOST_USER,
            password=settings.EMAIL_HOST_PASSWORD,
            start_tls=str(settings.EMAIL_USE_TLS).lower() == "true"
        )
        # print(ret)
        return {"result": 0, "errmsg": ""}
    except aiosmtplib.SMTPException as e:
        return {"result": 1, "errmsg": f"邮件发送失败: {str(e)}"}
