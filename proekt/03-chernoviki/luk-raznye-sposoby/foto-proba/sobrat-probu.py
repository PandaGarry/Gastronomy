"""Пробные макеты. Фото — уменьшенные превью Pexels, источники см. README."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageEnhance
P=Path(__file__).resolve().parent
F='/usr/share/fonts/truetype/dejavu/'
fonts={'serif':'DejaVuSerif-Bold.ttf','bold':'DejaVuSans-Bold.ttf','regular':'DejaVuSans.ttf'}
ink='#263b2c'; red='#a14330'; cream='#f3e7cf'; white='#faf3e1'
def f(n,k='regular'): return ImageFont.truetype(F+fonts[k],n)
def text(d,x,y,s,n,k='regular',color=ink,width=1250):
 ft=f(n,k); assert d.textlength(s,font=ft)<width,(s,d.textlength(s,font=ft),width); d.text((x,y),s,font=ft,fill=color)
def make(no,title,kicker,source,description,where,photo,credits):
 im=Image.new('RGB',(1440,1800),cream);d=ImageDraw.Draw(im)
 d.rectangle((30,30,1410,1770),outline=ink,width=4)
 text(d,75,65,'ПОПЕРЁК ВОЛОКОН',39,'serif');text(d,75,119,'КУХНЯ БЕЗ ФИЛЬТРОВ',24,'bold',red)
 logo=Image.open(P.parent.parent.parent/'07-upakovka-soobshchestva'/'logo-02.png').convert('RGB'); logo=ImageOps.fit(logo,(110,110));m=Image.new('L',(110,110));ImageDraw.Draw(m).ellipse((0,0,109,109),fill=255);im.paste(logo,(1250,44),m)
 d.line((75,165,1365,165),fill=ink,width=3)
 text(d,75,205,kicker,27,'bold',red)
 text(d,75,255,title,84,'serif')
 text(d,75,370,description,42,'regular',ink)
 img=Image.open(P/photo).convert('RGB'); img=ImageOps.fit(img,(1290,780),Image.Resampling.LANCZOS,centering=(.5,.52))
 img=ImageEnhance.Color(img).enhance(.8); img=ImageEnhance.Contrast(img).enhance(1.04)
 im.paste(img,(75,470)); d=ImageDraw.Draw(im);d.rectangle((75,470,1364,1249),outline=ink,width=3)
 text(d,75,1285,'ГДЕ ПРИГОДИТСЯ',27,'bold',red)
 for i,line in enumerate(where):text(d,75,1343+i*68,line,46,'regular',ink)
 d.line((75,1572,1365,1572),fill=ink,width=3)
 text(d,75,1603,credits,24,'regular',ink)
 text(d,75,1660,'ФОТОГРАФИЯ: PEXELS  ·  МАКЕТ ДЛЯ ОБСУЖДЕНИЯ',24,'bold',red)
 im.save(P/f'foto-proba-{no:02}.png',optimize=True)
make(1,'ЛУК КУБИКАМИ','МЕЛКАЯ НАРЕЗКА',None,'Мелкие кусочки распределяются в блюде.', ['Для супов, соусов и начинок, где лук','нужен как часть основы, а не крупный кусок.'], 'pexels-36895504-preview.jpg','Фото: Christina & Peter / Pexels')
make(2,'ПОЛУКОЛЬЦА','ПОПЕРЁК ЛУКОВИЦЫ',None,'Форма и толщина остаются заметными.', ['Полукольца добавляют в салат или маринуют.','Для этих блюд их можно нарезать тоньше.'], 'pexels-12181050-preview.jpg','Фото: Cihan Yüce / Pexels')
make(3,'ЛУК КОЛЬЦАМИ','ПОПЕРЁК ЛУКОВИЦЫ',None,'Поперечный срез можно разделить на кольца.', ['Кольца используют в салатах и сэндвичах;','для жарки в кляре их делают толще.'], 'pexels-4202502-preview.jpg','Фото: Kaboompics / Pexels')
print('Три демонстрационных макета готовы.')
