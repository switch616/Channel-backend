# -*- coding:utf-8 -*-
import uuid
import hashlib
from random import Random  # 用于生成随机码
from Crypto.Cipher import AES
import base64
from django.conf import settings
from Crypto.Util.Padding import unpad


def decrypt_password(encrypted_password, key="Switch6161234567", iv="Switch6161234567"):
    """
        AES解密函数
    :param encrypted_password: 加密后的密码（Base64编码）
    :param key: AES加密使用的密钥
    :param iv: AES加密使用的初始化向量 (IV)
    :return: 解密后的密码
    """
    # Base64解码
    encrypted_password_bytes = base64.b64decode(encrypted_password)

    # 创建AES解密器
    cipher = AES.new(key.encode('utf-8'), AES.MODE_CBC, iv.encode('utf-8'))

    # 解密数据
    decrypted_bytes = cipher.decrypt(encrypted_password_bytes)

    # 去除填充 (使用PKCS7填充)
    try:
        decrypted_password = unpad(decrypted_bytes, AES.block_size).decode('utf-8')
    except ValueError as e:
        # 解密出错时处理
        raise ValueError("AES解密失败，填充不正确或数据被篡改") from e

    return decrypted_password


def encrypt_u(username, last_login_timestamp):
    """
    使用 AES 对用户名和时间戳进行加密
    """
    key = settings.LOGIN_AES_KEY.encode('utf-8')
    iv = settings.LOGIN_AES_IV.encode('utf-8')
    cipher = AES.new(key, AES.MODE_CBC, iv)

    # 拼接username和last_login_timestamp
    data = f'{username}|{last_login_timestamp}'
    # 填充数据到16字节对齐
    pad_len = 16 - len(data) % 16
    data += chr(pad_len) * pad_len

    encrypted_data = cipher.encrypt(data.encode('utf-8'))
    return base64.b64encode(encrypted_data).decode('utf-8')


def decrypt_u(encrypted_u):
    """
    解密u值，返回(username, last_login_timestamp)
    """
    key = settings.LOGIN_AES_KEY.encode('utf-8')
    iv = settings.LOGIN_AES_IV.encode('utf-8')
    cipher = AES.new(key, AES.MODE_CBC, iv)

    # 解密并去掉填充
    encrypted_data = base64.b64decode(encrypted_u)
    decrypted_data = cipher.decrypt(encrypted_data).decode('utf-8')
    decrypted_data = decrypted_data.rstrip(decrypted_data[-1])  # 去掉填充字符

    # 拆分username和last_login_timestamp
    username, last_login_timestamp = decrypted_data.split('|')
    return username, int(last_login_timestamp)


def md5(string):
    """ MD5加密 """
    hash_object = hashlib.md5(settings.SECRET_KEY.encode('utf-8'))
    hash_object.update(string.encode('utf-8'))
    return hash_object.hexdigest()


def md5_encrypt_password(password):
    return hashlib.md5(password.encode('utf-8')).hexdigest()


def uid(string):
    data = "{}-{}".format(str(uuid.uuid4()), string)
    return md5(data)


# 生成随机6位数字字符串
def random_code(length=6):
    """
    生成指定长度的随机数字字符串
    :param length: 字符串长度
    :return: 生成的随机数字字符串
    """
    random = Random()
    return ''.join(str(random.randint(0, 9)) for _ in range(length))
