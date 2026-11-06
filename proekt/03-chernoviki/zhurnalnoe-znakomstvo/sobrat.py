"""Сборка трёх демонстрационных страниц. Нужны Pillow и шрифты DejaVu."""
from PIL import Image, ImageDraw, ImageFont, ImageOps
from pathlib import Path
P=Path(__file__).resolve().parent
CREAM='#f9f1dd'; INK='#26291e'; GREEN='#354b29'; RED='#b92e21'
FONT='/usr/share/fonts/truetype/dejavu/'
def font(size,bold=False,serif=False):
 return ImageFont.truetype(FONT+('DejaVuSerif-Bold.ttf' if serif else 'DejaVuSans-Bold.ttf' if bold else 'DejaVuSans.ttf'),size)
def base(number):
 im=Image.new('RGB',(1080,1350),CREAM); d=ImageDraw.Draw(im)
 d.text((58,32),'ПОПЕРЁК ВОЛОКОН',font=font(24,True),fill=GREEN)
 d.text((957,32),f'0{number}',font=font(25,True),fill=GREEN)
 d.line((58,75,1022,75),fill=GREEN,width=3)
 d.line((58,1290,1022,1290),fill=GREEN,width=3)
 d.text((58,1302),'КУХНЯ БЕЗ ФИЛЬТРОВ',font=font(20,True),fill=GREEN)
 return im,d
def pic(im,n,box):
 x,y,w,h=box;img=Image.open(P/f'illust-0{n}.png').convert('RGB');im.paste(ImageOps.fit(img,(w,h),method=Image.Resampling.LANCZOS),(x,y));ImageDraw.Draw(im).rectangle((x,y,x+w-1,y+h-1),outline=INK,width=3)
def lines(d,x,y,items,size=40,spacing=58,color=INK,bold=False):
 for i,line in enumerate(items): d.text((x,y+i*spacing),line,font=font(size,bold),fill=color)
# Первая страница — обложка журнала, иллюстрация и короткое введение.
im,d=base(1)
d.text((58,112),'МЕСТО, ГДЕ',font=font(71,serif=True),fill=RED)
d.text((58,205),'ГОВОРЯТ О КУХНЕ',font=font(67,serif=True),fill=GREEN)
pic(im,1,(58,325,964,615))
d.text((58,982),'Давайте знакомиться.',font=font(47,True),fill=INK)
lines(d,58,1058,['Готовите дома или работаете поваром?','Здесь найдётся тема для разговора.'],37,57)
im.save(P/'stranica-01.png',optimize=True)
# Вторая страница — темы, а не выдуманный опыт.
im,d=base(2);pic(im,2,(58,110,964,560))
d.text((58,710),'О ЧЁМ БУДЕМ ГОВОРИТЬ',font=font(46,True),fill=GREEN)
d.line((58,782,260,782),fill=RED,width=7)
lines(d,58,815,['О готовке дома и работе поваров.','О приёмах, которые помогают на кухне,','и вопросах, на которые нет одного ответа.'],38,58)
im.save(P/'stranica-02.png',optimize=True)
# Третья страница — предметный разговор и вопрос читателям.
im,d=base(3);pic(im,3,(58,110,964,560))
d.text((58,710),'ВЕЩИ — В ДЕЛЕ',font=font(50,True),fill=RED)
d.line((58,782,260,782),fill=GREEN,width=7)
lines(d,58,815,['Будем разбираться, что удобно на кухне','и за что действительно стоит платить.','Выводы — после проверки, не до неё.'],38,58)
d.text((58,1055),'С чего начнём?',font=font(46,True),fill=GREEN)
lines(d,58,1120,['Приёмы, профессия или инвентарь?'],37,55)
im.save(P/'stranica-03.png',optimize=True)
