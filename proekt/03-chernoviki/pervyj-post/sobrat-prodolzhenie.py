"""Создать две страницы продолжения: Pillow и системные шрифты DejaVu."""
from PIL import Image, ImageDraw, ImageFont, ImageOps
from pathlib import Path
P=Path(__file__).resolve().parent
paper='#f3e8d0'; ink='#25251b'; green='#2b4029'; red='#a42e24'; F='/usr/share/fonts/truetype/dejavu/'
def f(n,k='sans'): return ImageFont.truetype(F+{'sans':'DejaVuSans.ttf','bold':'DejaVuSans-Bold.ttf','serif':'DejaVuSerif-Bold.ttf'}[k],n)
def t(d,x,y,s,n=36,k='sans',col=ink,maxw=1310):
    assert d.textlength(s,font=f(n,k)) <= maxw,(s,d.textlength(s,font=f(n,k)),maxw)
    d.text((x,y),s,font=f(n,k),fill=col)
def block(d,x,y,arr,n=37,step=55,k='sans',col=ink,maxw=1310):
    for i,s in enumerate(arr): t(d,x,y+step*i,s,n,k,col,maxw)
def page():
    im=Image.new('RGB',(1440,1800),paper); d=ImageDraw.Draw(im)
    d.rectangle((29,29,1411,1770),outline=green,width=4); d.line((47,44,1393,44),fill=red,width=3)
    t(d,65,58,'КУХНЯ БЕЗ ФИЛЬТРОВ',25,'bold',green); d.line((65,101,1375,101),fill=green,width=3)
    t(d,65,112,'ПОПЕРЁК ВОЛОКОН',91,'serif',green); d.line((65,231,1375,231),fill=green,width=6)
    return im,d
def artwork(im,d,name,rect):
    x,y,w,h=rect; src=Image.open(P/name).convert('RGB')
    # Crop only the blank outer illustration margins and preserve the central scene.
    src=src.crop((35,20,1340,745))
    src=ImageOps.fit(src,(w,h),Image.Resampling.LANCZOS,centering=(0.5,0.5))
    im.paste(src,(x,y));d.rectangle((x,y,x+w-1,y+h-1),outline=green,width=4)
def band(d,y,s):
    d.rectangle((65,y,1375,y+90),fill=green); t(d,88,y+22,s,29,'bold',paper,1260)
# Page two: visual story, followed by distinct specific subject blocks.
im,d=page()
t(d,65,270,'ЧТО ЗДЕСЬ',83,'serif',red)
t(d,65,371,'МОЖНО НАЙТИ',83,'serif',green)
artwork(im,d,'vizual-02.png',(65,493,1310,635))
t(d,65,1165,'РЕЦЕПТЫ И ПРОДУКТЫ',35,'bold',red)
block(d,65,1221,['Что приготовить, как сочетать продукты', 'и что меняется от способа готовки.'],36,52)
d.line((65,1342,1375,1342),fill=green,width=2)
t(d,65,1370,'РАБОТА ПОВАРОВ',35,'bold',green,620)
block(d,65,1425,['Как устроена кухня и какие', 'задачи решают повара.'],32,48,maxw=610)
d.line((710,1368,710,1545),fill=green,width=2)
t(d,750,1370,'ПОСУДА И ТЕХНИКА',35,'bold',red,625)
block(d,750,1425,['Кухонный инвентарь и товары', 'с маркетплейсов: впечатления', 'от использования.'],32,48,maxw=625)
band(d,1600,'ДАЛЬШЕ: ДАВАЙТЕ ОБСУЖДАТЬ  →')
im.save(P/'stranica-02.png',optimize=True)
# Page three: an invitation rather than a staged opinion or a product verdict.
im,d=page()
t(d,65,270,'ДАВАЙТЕ',83,'serif',green)
t(d,65,371,'ОБСУЖДАТЬ',83,'serif',red)
artwork(im,d,'vizual-03.png',(65,495,1310,635))
t(d,65,1170,'У КАЖДОГО СВОЯ КУХНЯ',43,'bold',green)
block(d,65,1245,['Кто-то готовит ужин после работы, кто-то', 'проводит день на профессиональной кухне.', 'У каждого найдутся свои вопросы и находки.'],37,56)
d.line((65,1445,1375,1445),fill=red,width=4)
block(d,65,1482,['Здесь можно поделиться рецептом, обсудить', 'приём или рассказать, чем удобна посуда', 'и техника, которой вы пользуетесь.'],37,56)
band(d,1660,'БУДЕМ РАДЫ ВАШИМ ИСТОРИЯМ И ВОПРОСАМ')
im.save(P/'stranica-03.png',optimize=True)
