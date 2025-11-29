# app/utils/captcha.py
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import random
import os
from functools import lru_cache

# 使用缓存避免频繁加载字体
@lru_cache(maxsize=1)
def get_font(font_path=None, font_size=28):
    if not font_path:
        font_path = os.path.join(os.path.dirname(__file__), 'Monaco.ttf')
    return ImageFont.truetype(font_path, font_size)

def generate_captcha_image(width=120, height=30, char_length=5, font_size=28):
    code = []
    image = Image.new('RGB', (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(image)
    font = get_font(font_size=font_size)

    def rnd_char(): return chr(random.randint(65, 90))
    def rnd_color(): return (random.randint(64, 255), random.randint(64, 255), random.randint(64, 255))

    # 绘制验证码字符
    for i in range(char_length):
        char = rnd_char()
        code.append(char)
        draw.text((i * width / char_length, random.randint(0, 5)), char, font=font, fill=rnd_color())

    # 干扰点
    for _ in range(40):
        draw.point((random.randint(0, width), random.randint(0, height)), fill=rnd_color())

    # 干扰线
    for _ in range(3):
        draw.line([
            (random.randint(0, width), random.randint(0, height)),
            (random.randint(0, width), random.randint(0, height))
        ], fill=rnd_color(), width=1)

    image = image.filter(ImageFilter.EDGE_ENHANCE_MORE)
    return image, ''.join(code)

if __name__ == '__main__':
    image_object, code = generate_captcha_image()
    print(code)
    # 把图片写入文件
    """
    with open('code.png', 'wb') as f:
        image_object.save(f, format='png')
    """

    # 把图片的内容写到内存 stream
    """
    from io import BytesIO
    stream = BytesIO()
    image_object.save(stream, 'png')
    stream.getvalue()
    """
