"""Собрать первую страницу: Pillow + шрифты DejaVu."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps
p=Path(__file__).resolve().parent
im=Image.new('RGB',(1440,1800),'#f3e8d0'); d=ImageDraw.Draw(im)
ink='#25251b'; green='#2b4029'; red='#a42e24'; cream='#f3e8d0'
F='/usr/share/fonts/truetype/dejavu/'
def font(n,k='bold'):
    return ImageFont.truetype(F+{'bold':'DejaVuSans-Bold.ttf','serif':'DejaVuSerif-Bold.ttf','body':'DejaVuSans.ttf'}[k],n)
def text(x,y,s,n,k='bold',color=ink,w=None):
    ft=font(n,k)
    if w is not None: assert d.textlength(s,font=ft)<=w,(s,d.textlength(s,font=ft),w)
    d.text((x,y),s,font=ft,fill=color)
def lines(x,y,arr,n=37,step=56,k='body',color=ink,w=600):
    for i,s in enumerate(arr): text(x,y+i*step,s,n,k,color,w)
# Header with edition-like typographic hierarchy
d.rectangle((29,29,1411,1770),outline=green,width=4)
d.line((47,44,1393,44),fill=red,width=3)
text(65,58,'КУХНЯ БЕЗ ФИЛЬТРОВ',25,'bold',green)
d.line((65,101,1375,101),fill=green,width=3)
text(65,112,'ПОПЕРЁК ВОЛОКОН',91,'serif',green,1310)
d.line((65,231,1375,231),fill=green,width=6)
# Main headline + distinctive small magazine sidebar
text(65,267,'О КУХНЕ',91,'serif',red,980)
text(65,378,'ДОМА И НА РАБОТЕ',75,'serif',green,1180)
# Reuse the approved avatar as a small circular brand mark.
logo=Image.open(p.parent.parent/'07-upakovka-soobshchestva'/'logo-02.png').convert('RGB')
logo=ImageOps.fit(logo,(180,180),Image.Resampling.LANCZOS)
mask=Image.new('L',(180,180)); ImageDraw.Draw(mask).ellipse((0,0,179,179),fill=255)
im.paste(logo,(1180,267),mask)
d.ellipse((1180,267,1359,446),outline=green,width=3)
text(68,488,'Рецепты, работа поваров, кухонные вещи',34,'body',ink,1300)
# Image has own frame; contain preserves whole composition.
src=Image.open(p/'vizual-01.png').convert('RGB')
src=src.crop((65,58,1310,686))
src=ImageOps.fit(src,(1310,660),Image.Resampling.LANCZOS)
im.paste(src,(65,553)); d.rectangle((65,553,1374,1212),outline=green,width=4)
# Separate independent story blocks, no fake ad copy.
d.line((65,1252,1375,1252),fill=green,width=4)
text(65,1278,'О ЧЁМ ЗДЕСЬ',35,'bold',red,610)
lines(65,1340,['О приготовлении еды, жизни', 'профессиональной кухни', 'и полезных приёмах для дома.'],35,54,w=610)
d.line((710,1274,710,1536),fill=green,width=2)
text(750,1278,'РАЗНЫЕ ВЗГЛЯДЫ',35,'bold',green,625)
lines(750,1340,['Здесь можно делиться опытом,', 'обсуждать разные способы', 'и узнавать что-то новое.'],35,54,w=625)
d.rectangle((65,1582,1375,1672),fill=green)
text(88,1605,'ДАЛЬШЕ: О ЧЁМ БУДЕМ ГОВОРИТЬ  →',29,'bold',cream,1260)
im.save(p/'stranica-01.png',optimize=True)
