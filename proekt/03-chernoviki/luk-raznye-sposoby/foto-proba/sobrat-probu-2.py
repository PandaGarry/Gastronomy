"""Пробные карточки: оригиналы требуются как аргументы, см. README."""
import argparse
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps

HERE=Path(__file__).resolve().parent
FONTS=Path('/usr/share/fonts/truetype/dejavu')
GREEN='#283b2a'; RED='#9e4131'; PAPER='#f4e9d3'

def font(size,kind='body'):
    return ImageFont.truetype(str(FONTS / {'body':'DejaVuSans.ttf','bold':'DejaVuSans-Bold.ttf','serif':'DejaVuSerif-Bold.ttf'}[kind]),size)

def line(draw,x,y,text,size,kind='body',color=GREEN,max_width=1280):
    ft=font(size,kind)
    assert draw.textlength(text,font=ft)<=max_width,text
    draw.text((x,y),text,fill=color,font=ft)

def card(source,filename,title,caption,how,uses,credit):
    im=Image.new('RGB',(1440,1800),PAPER); d=ImageDraw.Draw(im)
    d.rectangle((30,30,1410,1770),outline=GREEN,width=4)
    line(d,75,62,'ПОПЕРЁК ВОЛОКОН',39,'serif');line(d,75,115,'КУХНЯ БЕЗ ФИЛЬТРОВ',24,'bold',RED)
    logo=Image.open(HERE.parent.parent.parent/'07-upakovka-soobshchestva'/'logo-02.png').convert('RGB')
    logo=ImageOps.fit(logo,(110,110));mask=Image.new('L',(110,110));ImageDraw.Draw(mask).ellipse((0,0,109,109),fill=255);im.paste(logo,(1250,44),mask)
    d.line((75,165,1365,165),fill=GREEN,width=3)
    line(d,75,205,'НАРЕЗКА РЕПЧАТОГО ЛУКА',27,'bold',RED)
    line(d,75,255,title,82,'serif')
    line(d,75,365,caption,40)
    photo=Image.open(source).convert('RGB');photo=ImageOps.fit(photo,(1290,765),Image.Resampling.LANCZOS,centering=(.5,.55))
    im.paste(photo,(75,450));d=ImageDraw.Draw(im);d.rectangle((75,450,1365,1215),outline=GREEN,width=3)
    line(d,75,1250,'КАК ПОЛУЧИТЬ',27,'bold',RED)
    for i,s in enumerate(how):line(d,75,1303+i*57,s,41)
    line(d,75,1450,'ГДЕ ИСПОЛЬЗОВАТЬ',27,'bold',RED)
    for i,s in enumerate(uses):line(d,75,1501+i*57,s,41)
    d.line((75,1640,1365,1640),fill=GREEN,width=3)
    line(d,75,1660,credit,22);line(d,75,1705,'ПРОБА • НЕ ГОТОВО К ПУБЛИКАЦИИ',23,'bold',RED)
    im.save(HERE/filename,optimize=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('rings',type=Path);p.add_argument('half_rings',type=Path);a=p.parse_args()
    card(a.rings,'novaya-proba-kolca.png','КОЛЬЦА','На снимке видны отдельные кольца.',
         ['Срежьте концы луковицы и нарежьте её','поперёк. Разделите ломтики на кольца.'],
         ['В салате, сэндвиче или в кляре.','Толщину выбирайте под блюдо.'], 'Фото: Erbs55 / Pixabay')
    card(a.half_rings,'novaya-proba-polukolca.png','ПОЛУКОЛЬЦА','Поперечные ломтики разделяются на дуги.',
         ['Разрежьте луковицу пополам от корня к верхушке.','Положите срезом вниз и нарежьте поперёк.'],
         ['Тонкие — в салат или для маринования;','более крупные подойдут для тушения.'], 'Фото: Lebensmittelfotos / Pixabay')
