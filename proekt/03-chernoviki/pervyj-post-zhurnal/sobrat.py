"""Собрать три страницы из отдельных иллюстраций; нужны Pillow и DejaVu."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,ImageOps
P=Path(__file__).resolve().parent
C='#f4ead4'; G='#2e422d'; R='#a42e24'; K='#29251f'; W=1440; H=1800
FP='/usr/share/fonts/truetype/dejavu/'
def font(size,kind='body'):
    return ImageFont.truetype(FP+{'body':'DejaVuSans.ttf','bold':'DejaVuSans-Bold.ttf','serif':'DejaVuSerif-Bold.ttf'}[kind],size)
def start(n,section):
    im=Image.new('RGB',(W,H),C); d=ImageDraw.Draw(im)
    d.rectangle((30,30,1409,1769),outline=G,width=3)
    d.line((47,43,1393,43),fill=R,width=3)
    d.text((65,54),'ПОПЕРЁК ВОЛОКОН',font=font(29,'serif'),fill=G)
    d.text((1110,60),f'ВЫПУСК 01  /  {n}',font=font(24,'bold'),fill=G)
    d.line((65,103,1375,103),fill=G,width=3)
    d.line((65,1713,1375,1713),fill=G,width=3)
    d.text((65,1724),section,font=font(23,'bold'),fill=G)
    d.text((1303,1724),f'0{n}',font=font(23,'bold'),fill=G)
    return im,d
def t(d,x,y,s,sz=40,kind='body',color=K,maxw=None):
    face=font(sz,kind)
    assert maxw is None or d.textlength(s,font=face)<=maxw, (s, d.textlength(s,font=face),maxw)
    d.text((x,y),s,font=face,fill=color)
def block(d,x,y,lines,sz=39,step=58,kind='body',color=K,maxw=1300):
    for i,s in enumerate(lines): t(d,x,y+i*step,s,sz,kind,color,maxw)
def image(im,d,name,box,crop=None):
    x,y,w,h=box; src=Image.open(P/name).convert('RGB')
    if crop: src=src.crop(crop)
    img=ImageOps.contain(src,(w,h),Image.Resampling.LANCZOS)
    # Canvas from the artwork's own background color makes its margins seamless.
    bg=src.getpixel((0,0)); canvas=Image.new('RGB',(w,h),bg)
    canvas.paste(img,((w-img.width)//2,(h-img.height)//2))
    im.paste(canvas,(x,y)); d.rectangle((x,y,x+w-1,y+h-1),outline=G,width=3)
def band(d,x,y,w,label):
    d.rectangle((x,y,x+w,y+47),fill=G); t(d,x+16,y+7,label,25,'bold',C,w-30)
# Page 1: introduce publication without making an individual ingredient the subject.
im,d=start(1,'ЗНАКОМСТВО  •  1 ИЗ 3')
t(d,65,132,'О ЕДЕ И О ТОМ,',83,'serif',R,1310)
t(d,65,235,'КАК ЕЁ ГОТОВЯТ',83,'serif',G,1310)
band(d,65,355,1310,'ДОМАШНЯЯ И ПРОФЕССИОНАЛЬНАЯ КУХНЯ')
image(im,d,'illust-01.png',(65,426,1310,870),(0,145,1024,1024))
t(d,65,1332,'ПРИВЕТ!',46,'bold',R)
block(d,65,1403,['Это «Поперёк волокон». Здесь будут рецепты,', 'разговоры о работе поваров и обзоры вещей,', 'которыми мы пользуемся на кухне.'],40,61,maxw=1310)
d.rectangle((65,1620,1375,1678),fill=G)
t(d,85,1631,'НА СЛЕДУЮЩЕЙ СТРАНИЦЕ  →  ПРОСТОЙ ПРИМЕР',26,'bold',C,1270)
im.save(P/'stranica-01.png',optimize=True)
# Page 2: one complete explanation and practical response.
im,d=start(2,'ПРИЁМЫ  •  2 ИЗ 3')
t(d,65,132,'ПОЧЕМУ КАРТОШКА',74,'serif',R,1310)
t(d,65,225,'НЕ РУМЯНИТСЯ?',74,'serif',G,1310)
t(d,68,344,'Один кухонный вопрос — несколько причин.',35,'body',K,1300)
image(im,d,'illust-02.png',(65,410,1310,700))
t(d,65,1145,'ВЛАГА',38,'bold',R)
block(d,65,1200,['Мокрая поверхность сначала', 'теряет воду. Пока она влажная,', 'румяная корочка образуется', 'медленнее. Обсушите кусочки', 'перед жаркой.'],34,52,maxw=615)
d.line((715,1147,715,1550),fill=G,width=2)
t(d,760,1145,'ТЕСНОТА',38,'bold',G)
block(d,760,1200,['Большая порция охлаждает', 'сковороду, а лишняя влага', 'испаряется медленнее.', 'Попробуйте жарить порциями,', 'в один слой.'],34,52,maxw=615)
d.rectangle((65,1578,1375,1666),outline=R,width=3)
t(d,85,1598,'Это не единственные причины: важны и нагрев, и сорт.',29,'bold',G,1270)
im.save(P/'stranica-02.png',optimize=True)
# Page 3: a different composition and concrete editorial commitments.
im,d=start(3,'О ПРОЕКТЕ  •  3 ИЗ 3')
t(d,65,132,'ЧТО ЕЩЁ БУДЕТ',76,'serif',G,1310)
t(d,65,229,'НА НАШЕЙ КУХНЕ',76,'serif',R,1310)
image(im,d,'illust-03.png',(65,344,1310,755))
t(d,65,1135,'РАБОТА ПОВАРОВ',37,'bold',G)
block(d,65,1190,['Как устроена работа на кухне,', 'какие задачи стоят перед', 'поварами и какие приёмы', 'можно применить дома.'],33,50,maxw=615)
d.line((715,1135,715,1470),fill=G,width=2)
t(d,760,1135,'ОБЗОРЫ',37,'bold',R)
block(d,760,1190,['Посуда, техника и находки', 'на маркетплейсах: что удобно,', 'а что нет. Личный опыт —', 'только после проверки.'],33,50,maxw=615)
d.rectangle((65,1510,1375,1664),fill=G)
block(d,91,1534,['Для тех, кто готовит дома,', 'и для тех, кто работает на кухне.'],36,52,'bold',C,1250)
im.save(P/'stranica-03.png',optimize=True)
