"""Черновые карточки о луке. Pillow, DejaVu, иллюстрация и утверждённый знак."""
from pathlib import Path
import math
from PIL import Image, ImageDraw, ImageFont, ImageOps
import random
P=Path(__file__).resolve().parent
FONT='/usr/share/fonts/truetype/dejavu/'
F={'sans':'DejaVuSans.ttf','bold':'DejaVuSans-Bold.ttf','serif':'DejaVuSerif-Bold.ttf'}
cream='#f4e9d2'; ink='#243524'; red='#a9432f'; gold='#d9a857'; light='#fff8e7'; pale='#e4d4af'
def font(sz,kind='sans'): return ImageFont.truetype(FONT+F[kind],sz)
def txt(d,xy,text,sz,kind='sans',color=ink,maxw=1260):
    f=font(sz,kind); assert d.textlength(text,font=f)<=maxw,(text,d.textlength(text,font=f),maxw); d.text(xy,text,font=f,fill=color)
def lines(d,x,y,items,sz=46,step=69,kind='sans',color=ink,maxw=1200):
    for i,s in enumerate(items): txt(d,(x,y+i*step),s,sz,kind,color,maxw)
def base(title,tag='НАРЕЗКА ЛУКА'):
    im=Image.new('RGB',(1440,1800),cream); d=ImageDraw.Draw(im)
    d.rectangle((28,28,1411,1771),outline=ink,width=4)
    txt(d,(70,60),'ПОПЕРЁК ВОЛОКОН',39,'serif',ink,920)
    txt(d,(70,115),'КУХНЯ БЕЗ ФИЛЬТРОВ',23,'bold',red)
    d.line((70,160,1370,160),fill=ink,width=3)
    logo=Image.open(P.parent.parent/'07-upakovka-soobshchestva'/'logo-02.png').convert('RGB')
    logo=ImageOps.fit(logo,(110,110)); mask=Image.new('L',(110,110)); ImageDraw.Draw(mask).ellipse((0,0,109,109),fill=255)
    im.paste(logo,(1255,43),mask)
    txt(d,(70,205),tag,26,'bold',red)
    txt(d,(70,260),title,72,'serif',ink,1250)
    return im,d
def footer(d):
    d.line((70,1690,1370,1690),fill=ink,width=3)
    txt(d,(70,1713),'ПРОДУКТ • ПРИЁМ • РЕЗУЛЬТАТ',25,'bold',ink)
def panel(d, heading, how, use, note):
    # Right-hand instructions and full-width purpose block
    txt(d,(795,424),'КАК НАРЕЗАТЬ',29,'bold',red,500)
    lines(d,795,490,how,38,62,maxw=520)
    d.line((70,1085,1370,1085),fill=ink,width=3)
    txt(d,(70,1130),'ДЛЯ ЧЕГО',29,'bold',red)
    txt(d,(70,1190),heading,62,'serif',ink)
    lines(d,70,1280,use,47,55,maxw=1260)
    d.rounded_rectangle((70,1515,1370,1645),radius=5,fill=ink)
    lines(d,100,1540,note,34,48,'bold',cream,1200)
def artpanel(d):
    d.rectangle((70,412,735,1040),fill='#e8d3a7',outline=ink,width=3)
    d.line((94,930,710,930),fill='#a7926d',width=3)
    txt(d,(100,957),'УСЛОВНАЯ ФОРМА НАРЕЗКИ',22,'bold',ink,600)
def cubes(d):
    random.seed(4)
    for row in range(3):
      for col in range(4):
        x=160+col*122+(row%2)*13; y=555+row*119+(col%2)*9
        d.polygon([(x,y+25),(x+64,y),(x+113,y+30),(x+49,y+56)],fill='#f7eed2',outline=ink,width=3)
        d.polygon([(x,y+25),(x+49,y+56),(x+49,y+114),(x,y+83)],fill='#dfba77',outline=ink,width=3)
        d.polygon([(x+49,y+56),(x+113,y+30),(x+113,y+86),(x+49,y+114)],fill='#efdbad',outline=ink,width=3)
def arcs(d):
    # Crosswise pieces, translucent concentric arcs, the open edge downward.
    for x,y,sc in [(150,560,1),(310,600,0.95),(465,555,1.03)]:
      w=int(185*sc);h=int(220*sc)
      for off in range(0,65,16):
       d.arc((x+off,y+off//2,x+w-off,y+h-off//2),180,360,fill='#b36a3b',width=9)
      d.line((x,y+h//2,x+w,y+h//2),fill=ink,width=3)
def rings(d):
    for x,y in [(190,575),(365,650),(290,475)]:
      for off in range(0,70,20):d.ellipse((x+off,y+off,x+250-off,y+250-off),outline='#b16b3d',width=10)
def strips(d):
    for k in range(5):
      x=140+k*78; y=540+(k%2)*45
      d.arc((x,y,x+230,y+340),195,330,fill='#aa6938',width=19)
      d.arc((x+12,y+12,x+218,y+328),195,330,fill=light,width=6)
def wedges(d):
    for x,y,rot in [(185,535,5),(410,570,25),(250,700,-12)]:
      angles=[math.radians(rot+a) for a in range(12,75,3)]
      def arc(radius): return [(int(x+radius*math.cos(a)),int(y+radius*math.sin(a))) for a in angles]
      outer=arc(180)
      d.polygon([(x,y),*outer],fill='#f9efd5',outline=ink,width=4)
      for radius in (60,90,120,150): d.line(arc(radius),fill='#b78650',width=5)
      d.line([(x,y),outer[0]],fill=ink,width=4);d.line([(x,y),outer[-1]],fill=ink,width=4)
def save(im,n):
    footer(ImageDraw.Draw(im)); im.save(P/f'stranica-{n:02d}.png',optimize=True)
# Cover
im,d=base('КАК НАРЕЗАТЬ ЛУК?', 'ОДИН ПРОДУКТ — РАЗНЫЕ ЗАДАЧИ')
txt(d,(70,370),'Форма влияет на текстуру',50,'bold',ink)
txt(d,(70,438),'и на то, как лук ощущается в блюде.',43,'sans',ink)
src=Image.open(P/'illyustraciya-luk.png').convert('RGB'); src=ImageOps.fit(src,(1300,960),Image.Resampling.LANCZOS,centering=(.5,.66))
im.paste(src,(70,535));d=ImageDraw.Draw(im);d.rectangle((70,535,1369,1494),outline=ink,width=3)
d.rectangle((70,1530,1370,1640),fill=ink);txt(d,(100,1560),'НАРЕЗКА, ПРИМЕНЕНИЕ И КАК УМЕНЬШИТЬ СЛЁЗЫ',31,'bold',cream,1220);save(im,1)
# Dice
im,d=base('КУБИКИ');artpanel(d);cubes(d)
panel(d,'Для основы блюда', ['Половинку положите','срезом вниз. Надрежьте','вдоль, не доходя до','корня, затем поперёк.'], ['Небольшие кусочки удобно распределить','в супе, соусе или начинке. При долгом','приготовлении они менее заметны.'], ['Для более ровных кусочков можно','нарезать лук четвертинками.']);save(im,2)
# rings
im,d=base('КОЛЬЦА И ПОЛУКОЛЬЦА');artpanel(d);arcs(d)
panel(d,'Когда лук остаётся заметным', ['Для колец нарежьте','луковицу поперёк.','Для полуколец сначала','разрежьте её пополам.'], ['Тонкие полукольца — в салат или маринад.','Толстые кольца подойдут для жарки','в кляре. Толщину выбирайте под блюдо.'], ['Для устойчивости половинку кладут','на доску плоским срезом вниз.']);save(im,3)
# lengthwise
im,d=base('ЛОМТИКИ ВДОЛЬ');artpanel(d);strips(d)
panel(d,'Для супа и тушения', ['Разрежьте луковицу','от корня к верхушке.','Половинку положите','срезом вниз и нарежьте','в том же направлении.'], ['Получатся полоски: их удобно тушить','и добавлять в луковый суп. У сырого лука','аромат может быть мягче, чем при','поперечной нарезке той же толщины.'], ['Сорт, свежесть и способ приготовления','тоже влияют на вкус.']);save(im,4)
# wedges
im,d=base('КРУПНЫЕ ДОЛЬКИ');artpanel(d);wedges(d)
panel(d,'Для запекания', ['Разрежьте луковицу','от корня к верхушке','пополам, затем каждую','половину — на дольки.'], ['Добавьте к овощам или мясу в духовке.','Крупные куски будут заметны в блюде;','их готовность зависит от размера,','времени и температуры.'], ['Дольки могут разделиться на слои —','это нормально.']);save(im,5)
# size
im,d=base('КАК ВЫБРАТЬ РАЗМЕР?', 'ФОРМА И ТЕКСТУРА')
d.rectangle((70,405,1370,665),fill='#e7d3aa'); txt(d,(105,445),'МЕЛЬЧЕ',49,'serif',red);lines(d,105,520,['Кусочки распределяются в основе','и при приготовлении становятся мягче.'],45,62,maxw=1190)
d.rectangle((70,700,1370,960),fill=light,outline=ink,width=2);txt(d,(105,740),'КРУПНЕЕ',49,'serif',red);lines(d,105,815,['Лук заметнее в блюде. Крупным кускам','обычно нужно больше времени до мягкости.'],45,62,maxw=1190)
d.rectangle((70,995,1370,1255),fill='#e7d3aa');txt(d,(105,1035),'РОВНЕЕ',49,'serif',red);lines(d,105,1110,['Кусочки похожего размера удобнее','готовить равномерно.'],45,62,maxw=1190)
d.line((70,1320,1370,1320),fill=ink,width=3);lines(d,70,1370,['Не существует одной обязательной','нарезки для каждого блюда. Выбирайте','под нужную текстуру и свой вкус.'],50,77,'bold',ink,1260);save(im,6)
# tears
im,d=base('КАК УМЕНЬШИТЬ СЛЁЗЫ?', 'КОГДА РЕЖЕМ ЛУК')
lines(d,70,390,['При нарезке образуется летучее вещество,','которое раздражает глаза. Что попробовать:'],48,72,maxw=1260)
items=[('ОХЛАДИТЬ','Положите луковицу в холодильник','примерно на 30 минут перед нарезкой.'),('РЕЗАТЬ СПОКОЙНО','Острый нож и неторопливые движения','помогают уменьшить разбрызгивание.'),('ЗАЩИТИТЬ ГЛАЗА','Отведите поток воздуха от лица или','попробуйте плотно прилегающие очки.')]
for j,(head,a,b) in enumerate(items):
 y=605+j*278;d.rectangle((70,y,1370,y+230),fill=light,outline=ink,width=2);txt(d,(100,y+23),head,34,'bold',red);lines(d,100,y+84,[a,b],43,60,maxw=1200)
d.rectangle((70,1460,1370,1635),fill=ink);lines(d,100,1490,['Эти способы могут помочь, но не обещают','полного отсутствия слёз.'],39,60,'bold',cream,1200);save(im,7)
print('Собрано: 7 карточек, 1440 × 1800.')
