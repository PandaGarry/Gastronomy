#!/usr/bin/env python3
"""Собрать обложку 002: типографика отдельно от созданной ИИ иллюстрации."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
P = Path(__file__).resolve().parent
im = Image.open(P / 'oblozhka-illyustraciya.png').convert('RGB').resize((1440, 1800), Image.Resampling.LANCZOS)
d = ImageDraw.Draw(im)
green, burgundy, cream = '#214331', '#823A32', '#f6e9cd'
serif = '/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf'
bold = '/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf'
def font(path, size): return ImageFont.truetype(path, size)
def fit(text, path, size, width):
    while d.textlength(text, font=font(path, size)) > width: size -= 1
    return font(path,size)
# Masthead and material marker are intentionally independent of the artwork.
d.rectangle((34, 28, 1406, 163), fill=green)
d.rectangle((1165, 28, 1406, 163), fill=burgundy)
d.text((61, 43), 'Поперёк волокон', font=fit('Поперёк волокон', bold, 76, 1075), fill=cream, stroke_width=0)
d.text((1192, 55), 'МАТЕРИАЛ', font=font(bold, 24), fill=cream)
d.text((1203, 93), '№ 002', font=font(bold, 37), fill=cream)
d.text((64, 197), 'ЗАЧЕМ МЯСУ', font=font(bold, 57), fill=green)
d.text((60, 264), 'румяная', font=fit('румяная', bold, 146, 1300), fill=burgundy)
d.text((60, 417), 'корочка?', font=fit('корочка?', bold, 146, 1300), fill=burgundy)
d.line((70, 592, 885, 592), fill=burgundy, width=3)
d.text((70, 612), 'И почему сковороду не стоит', font=font(serif, 38), fill=green)
d.text((70, 663), 'забивать до краёв', font=font(serif, 38), fill=green)
im.save(P / 'oblozhka-002.png', optimize=True)
