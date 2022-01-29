import random
import numpy as np
from PIL import Image
from PIL.ImageDraw import Draw
from PIL.ImageFont import truetype

Colors = {
    "red": (255, 0, 0),
    "yellow": (255, 255, 0),
    "blue": (0, 0, 255),
    "green": (0, 255, 0),
    "black": (0, 0, 0)
}

Colorsymbols = {
    "red": "R",
    "yellow": "Y",
    "blue": "U",
    "black": "B"
}


def random_color(start, end, opacity=None):
    red = random.randint(start, end)
    green = random.randint(start, end)
    blue = random.randint(start, end)
    if opacity is None:
        return (red, green, blue)
    return (red, green, blue, opacity)


class ImageCaptcha:
    def __init__(self, width=120, height=50, fonts=None, font_sizes=None,
                 text_colors=None, noise_line_color="green"):
        self._width = width
        self._height = height
        self._fonts = fonts
        self._font_sizes = font_sizes or (30, 30)
        self._text_colors = text_colors or ["black"]
        self._noise_line_color = Colors[noise_line_color]

    @staticmethod
    def create_noise_line(image, color, number=2):
        w, h = image.size
        num = random.randint(0, number)
        while num:
            x1 = random.randint(0, w)
            x2 = random.randint(0, h)
            y1 = random.randint(0, w)
            y2 = random.randint(0, h)
            points = [x1, y1, x2, y2]
            Draw(image).line(points, fill=color)
            num -= 1
        return image

    @staticmethod
    def create_noise_dots(image, number=150):
        w, h = image.size
        while number:
            x1 = random.randint(0, w)
            y1 = random.randint(0, h)
            Draw(image).point((x1, y1), fill=random_color(0, 255))
            number -= 1
        return image

    def random_sin_fill(self, image):
        """
        用正弦函数图像填充背景
        周期和振幅随机，周期为0.5-2之间，振幅为5-23个像素
        """
        x = np.linspace(-3*np.pi, 3*np.pi, 101)
        y = np.around(np.sin(x), decimals=2)
        x = x + random.uniform(0.6, 0.74) * 2 * np.pi  # 图像平移，保证生成的验证码左上角是曲线颜色
        color = random_color(100, 255)
        t = random.uniform(0.5, 2)  # 周期
        enlarge = round(self._width / t * 3 / (6*np.pi))  # 扩大倍数
        amplitude = 10 / t  # 振幅

        # 上曲线
        upper = np.asarray(np.stack((x*enlarge, y*amplitude), axis=1), dtype=int)
        upper = list(map(tuple, upper))
        Draw(image).polygon(upper, fill=color)

        # 下曲线
        lower = np.asarray(np.stack((x*enlarge, y*amplitude+self._height), axis=1), dtype=int)
        lower = list(map(tuple, lower))
        Draw(image).polygon(lower, fill=color)

    def font_choice(self, c):
        if "\u4e00" <= c <= "\u9fff":
            return truetype(self._fonts[1], self._font_sizes[0])
        else:
            return truetype(self._fonts[0], self._font_sizes[1])

    def create_captcha_image(self, chars, background):
        """Create the CAPTCHA image itself.

        :param chars: text to be generated.
        :param background: color of the background.
        """
        image = Image.new('RGB', (self._width, self._height), background)
        self.random_sin_fill(image)
        draw = Draw(image)

        def _draw_character(c, color=(255, 255, 255)):
            font = self.font_choice(c)
            w, h = draw.textsize(c, font=font)

            im = Image.new('RGBA', (w, h))
            Draw(im).text((0, 0), c, font=font, fill=color)

            # 中文做剪切变换
            if "\u4e00" <= c <= "\u9fff":
                im = im.transform(im.size, Image.PERSPECTIVE, [
                                  1, 0, 0, 0.2, 1, 0, 0, 0, 1])

            # 旋转
            im = im.crop(im.getbbox())
            im = im.rotate(random.uniform(-45, 45), expand=1)

            return im

        images = []
        ischinese = []
        colors = ""
        for c in chars:  # 单个字符图片生成
            index = random.randint(0, len(self._text_colors)-1)
            color = self._text_colors[index]
            images.append(_draw_character(c, Colors[color]))
            ischinese.append(True if "\u4e00" <= c <= "\u9fff" else False)
            colors += Colorsymbols[color]

        start = random.randint(0, 6)
        last_w, _ = images[-1].size  # 最后一个字符的宽度
        max_interval = (self._width - last_w - start) // (len(images) - 1)
        offset = start

        # 字符图片拼接到大图上，中文和字母的上下间距不一样
        for im, flag in zip(images, ischinese):
            w, h = im.size
            image.paste(im, (offset, (self._height - h) // 2 +
                             (random.randint(-6, 6) if flag else random.randint(-12, 12))), im)
            offset = offset + \
                min(max_interval, max(int(0.7 * w), 18)) + random.randint(-2, 0)

        return image, colors

    def generate_image(self, chars):
        """Generate the image of the given characters.

        :param chars: text to be generated.
        """
        background = random_color(100, 255, 255)
        im, colors = self.create_captcha_image(chars, background)
        self.create_noise_line(im, self._noise_line_color)
        self.create_noise_dots(im)
        return im, colors


if __name__ == "__main__":
    imc = ImageCaptcha(width=120,
                       height=50,
                       fonts=["data/actionj.ttf", "data/simsun.ttf"],
                       font_sizes=(30, 30),
                       text_colors=["black", "yellow", "blue", "red"],
                       noise_line_color="green")
    chars = "届议衷2TH"
    image, colors = imc.generate_image(chars)
    image.save("test_captcha.png")
