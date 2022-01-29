import os
import string
import random
from image_captcha import ImageCaptcha

# 中文字符集
with open("data/text.txt", 'r', encoding="utf-8") as f:
    captcha_cn = f.read()

# 英文、数字字符集，排除数字0，1和字母O
captcha_en = string.digits[2:] + \
    string.ascii_uppercase[:14] + string.ascii_uppercase[16:]


def random_captcha_text(num):
    have_cn = random.randint(0, 9)
    if have_cn <= 2:  # 含中文，控制比例为0.3
        cn_num = random.randint(1, 3)
        en_num = num - cn_num
        example_cn = random.sample(captcha_cn, cn_num)
        example_en = random.sample(captcha_en, en_num)
        example = example_cn + example_en
        return "".join(example)
    else:  # 不含中文
        example_en = random.sample(captcha_en, num)
        return "".join(example_en)


def generate_captcha_image(path="fake_captcha", num=1):
    imc = ImageCaptcha(width=120,
                       height=50,
                       fonts=["data/actionj.ttf", "data/simsun.ttf"],
                       font_sizes=(30, 30),
                       text_colors=["black", "yellow", "blue", "red"],
                       noise_line_color="green")

    if not os.path.exists(path):
        os.makedirs(path)
    for _ in range(num):
        captcha_text = random_captcha_text(6)
        image, colors = imc.generate_image(captcha_text)
        image.save(os.path.join(path, captcha_text + "_" + colors) + ".png")


if __name__ == "__main__":
    generate_captcha_image(num=1000)
