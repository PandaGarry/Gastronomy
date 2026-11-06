"""Сборка журнальной страницы. Требуются Pillow и шрифты DejaVu."""
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
p=Path(__file__).resolve().parent
paper='#f5ecd7'; ink='#29291f'; green='#34472d'; red='#ae3024'
im=Image.new('RGB',(1440,1800),paper); d=ImageDraw.Draw(im)
fonts='/usr/share/fonts/truetype/dejavu/'
def f(size, face='sans'):
    return ImageFont.truetype(fonts+{'sans':'DejaVuSans.ttf','bold':'DejaVuSans-Bold.ttf','serif':'DejaVuSerif-Bold.ttf'}[face],size)
def draw(x,y,s,size,face='sans',fill=ink):
    d.text((x,y),s,font=f(size,face),fill=fill)
def fit(x,y,s,size,width,face,fill):
    while d.textlength(s,font=f(size,face))>width: size-=1
    draw(x,y,s,size,face,fill)
d.rectangle((27,27,1412,1772),outline=green,width=4)
d.line((44,40,1395,40),fill=red,width=3)
draw(63,53,'КУХОННОЕ ИЗДАНИЕ',25,'bold',green)
draw(1179,53,'ВЫПУСК 01',25,'bold',green)
d.line((63,96,1377,96),fill=green,width=3)
fit(63,102,'ПОПЕРЁК ВОЛОКОН',98,1314,'serif',green)
d.rectangle((63,220,1377,268),fill=green)
draw(82,226,'КУХНЯ БЕЗ ФИЛЬТРОВ',27,'bold',paper)
draw(63,293,'О ЕДЕ И О ТОМ,',89,'serif',red)
fit(63,393,'КАК ЕЁ ГОТОВЯТ',89,1314,'serif',green)
draw(66,505,'Домашняя и профессиональная кухня',34,'sans',ink)
# All objects, including the southwest-facing handle and fork, remain within the artwork.
a=Image.open(p/'illyustraciya.png').convert('RGB').crop((0,150,1024,1024))
a=a.resize((1314,1122),Image.Resampling.LANCZOS)
im.paste(a,(63,550)); d.rectangle((63,550,1376,1671),outline=green,width=3)
d.line((63,1680,1377,1680),fill=green,width=3)
draw(63,1699,'РЕЦЕПТЫ  •  ПРОФЕССИЯ  •  ОБЗОРЫ',31,'bold',green)
im.save(p/'post-znakomstvo.png',optimize=True)
