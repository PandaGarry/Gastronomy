from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,ImageOps
P=Path(__file__).resolve().parent
W,H=1440,1800
paper='#f2e7cd'; green='#263d2b'; red='#a72920'; ink='#241f19'
im=Image.new('RGB',(W,H),paper); d=ImageDraw.Draw(im)
fontdir='/usr/share/fonts/truetype/dejavu/'
def f(n,kind='sans'):
 return ImageFont.truetype(fontdir+{'sans':'DejaVuSans.ttf','bold':'DejaVuSans-Bold.ttf','serif':'DejaVuSerif-Bold.ttf','cond':'DejaVuSans-Bold.ttf'}[kind],n)
def text(x,y,s,n,kind='sans',color=ink): d.text((x,y),s,font=f(n,kind),fill=color)
def fit(x,y,s,maxwidth,n,kind='bold',color=ink):
 while d.textlength(s,font=f(n,kind))>maxwidth: n-=1
 text(x,y,s,n,kind,color)
def lines(x,y,ss,n=41,step=58,kind='sans',color=ink):
 for i,s in enumerate(ss):text(x,y+i*step,s,n,kind,color)
d.rectangle((30,30,1409,1769),outline=green,width=4)
d.line((45,44,1395,44),fill=red,width=3)
text(67,58,'КУХОННОЕ ИЗДАНИЕ',25,'bold',green)
text(1170,58,'ВЫПУСК 01',25,'bold',green)
d.line((67,99,1373,99),fill=green,width=3)
fit(67,110,'ПОПЕРЁК ВОЛОКОН',1306,96,'serif',green)
d.rectangle((67,235,1373,289),fill=green)
text(88,242,'КУХНЯ БЕЗ ФИЛЬТРОВ   •   ПЕРВОЕ ЗНАКОМСТВО',28,'bold',paper)
fit(67,317,'РЕЦЕПТЫ, НОЖИ',1306,105,'cond',red)
fit(67,430,'И ЖИЗНЬ НА КУХНЕ',1306,105,'cond',green)
text(70,565,'От домашнего ужина до профессиональной кухни.',35,'bold',ink)
# Use the full composition rather than slicing an object across the edge.
art=Image.open(P/'illustraciya.png').convert('RGB')
art=ImageOps.fit(art,(1306,680),method=Image.Resampling.LANCZOS)
im.paste(art,(67,631));d.rectangle((67,631,1372,1310),outline=green,width=4)
d.rectangle((68,1250,505,1310),fill=red)
text(86,1259,'ЗАХОДИТЕ НА КУХНЮ',26,'bold',paper)
# Two editorial columns, no decorative filler or invented facts.
d.line((720,1340,720,1582),fill=green,width=2)
text(67,1338,'ДОМА И НА РАБОТЕ',31,'bold',red)
lines(67,1394,['Почему картошка румянится','не всегда? Как выбрать нож,','который удобно держать?'],34,52)
text(757,1338,'БУДЕМ РАЗБИРАТЬСЯ',31,'bold',green)
lines(757,1394,['Рецепты, кухонные приёмы,','профессия и честные обзоры','кухонных вещей.'],34,52)
d.line((67,1608,1373,1608),fill=green,width=3)
text(67,1633,'С чего начнём: продукты, приёмы или инвентарь?',34,'serif',green)
text(67,1710,'ПОПЕРЁК ВОЛОКОН  •  КУХНЯ БЕЗ ФИЛЬТРОВ',23,'bold',green)
im.save(P/'post-znakomstvo.png',optimize=True)
