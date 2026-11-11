#!/usr/bin/env python3
"""Воспроизводимая вёрстка поста 002 из пользовательских исходников Pexels."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps
P=Path(__file__).resolve().parent
W,H=1440,1800
CREAM='#f2e7d1'; GREEN='#214331'; RED='#823a32'; INK='#292720'; WHITE='#fbf3df'; LINE='#a28e70'
R='/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf'; B='/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf'
def F(size,b=False): return ImageFont.truetype(B if b else R,size)
def draw_text(d, text, x, y, width, size=41, color=INK, bold=False, line=1.32):
 f=F(size,bold); yy=y
 for para in text.split('\n'):
  words=para.split(); cur=''
  for word in words:
   t=(cur+' '+word).strip()
   if d.textlength(t,font=f)>width and cur:
    d.text((x,yy),cur,font=f,fill=color); yy+=int(size*line); cur=word
   else: cur=t
  if cur: d.text((x,yy),cur,font=f,fill=color); yy+=int(size*line)
  else: yy+=int(size*0.5)
 return yy
def page():
 im=Image.new('RGB',(W,H),CREAM); d=ImageDraw.Draw(im)
 d.rectangle((42,35,1398,148),fill=GREEN)
 d.text((71,55),'Поперёк волокон',font=F(57,True),fill=WHITE)
 d.rectangle((1165,35,1398,148),fill=RED)
 d.text((1188,53),'МАТЕРИАЛ',font=F(22,True),fill=WHITE)
 d.text((1201,88),'№ 002',font=F(33,True),fill=WHITE)
 d.line((55,1728,1385,1728),fill=LINE,width=2)
 d.text((62,1740),'КУХНЯ  •  ПРОДУКТ  •  ТЕХНИКА',font=F(20,True),fill=GREEN)
 return im,d
def photo(im,name,box,centering=(0.5,0.5)):
 img=ImageOps.exif_transpose(Image.open(P/'foto'/name)).convert('RGB')
 x,y,x2,y2=box; im.paste(ImageOps.fit(img,(x2-x,y2-y),method=Image.Resampling.LANCZOS,centering=centering),(x,y))
def save(im,n): im.save(P/f'stranica-{n:02}.png',optimize=True)
# 1 — the article's opening and the explanation, not a title-only cover
im,d=page()
d.text((65,177),'Зачем мясу',font=F(72,True),fill=GREEN)
d.text((58,261),'румяная корочка?',font=F(92,True),fill=RED)
d.text((69,396),'И почему сковороду не стоит забивать до краёв',font=F(34),fill=GREEN)
photo(im,'IMG_6270.jpeg',(65,472,1375,1040),(.5,.48))
y=draw_text(d,'У хорошо обжаренного мяса есть то, чего не даст простое тушение: тёмная корочка и насыщенный жареный аромат. Но дело не в том, что корочка «запечатывает» сок внутри. Это старый кухонный миф.',70,1081,1290,40)
d.text((69,y+22),'Откуда берётся корочка?',font=F(49,True),fill=GREEN)
y=draw_text(d,'За румяный цвет и большую часть характерного жареного аромата отвечает реакция Майяра. При сильном нагреве аминокислоты и сахара на поверхности мяса вступают в реакцию и образуют новые вкусовые и ароматические соединения.',70,y+93,1290,39)
assert y<1710,y
save(im,1)
# 2 — two distinct preparation frames
im,d=page()
d.text((65,189),'Почему мясо лучше',font=F(69,True),fill=GREEN)
d.text((65,273),'обсушить',font=F(84,True),fill=RED)
photo(im,'IMG_6267.jpeg',(65,410,695,1160),(.5,.35))
photo(im,'IMG_6268.jpeg',(715,410,1375,1160),(.5,.43))
d.text((72,1178),'ДО ПРИГОТОВЛЕНИЯ',font=F(24,True),fill=GREEN)
d.text((721,1178),'ПРОМОКНУТЬ ПОВЕРХНОСТЬ',font=F(24,True),fill=GREEN)
y=draw_text(d,'Влага на поверхности сначала должна испариться. Пока мясо активно отдаёт пар, поверхность хуже подрумянивается. Поэтому перед жаркой кусок можно промокнуть бумажным полотенцем — особенно если он был в маринаде или успел выделить сок.',70,1252,1285,44)
assert y<1710,y
save(im,2)
# 3 — pan and space
im,d=page()
d.text((65,192),'Не кладите',font=F(76,True),fill=GREEN)
d.text((65,285),'всё сразу',font=F(91,True),fill=RED)
photo(im,'IMG_6269.jpeg',(65,435,1375,1110),(.5,.5))
y=draw_text(d,'Если заполнить сковороду кусками вплотную, её температура может заметно снизиться, а влага будет испаряться медленнее. Вместо красивой корочки мясо начнёт скорее тушиться.',70,1150,1290,44)
y=draw_text(d,'Жарьте партиями, оставляя между кусками немного места. Если мяса много, лучше обжарить его в два захода.',70,y+30,1290,44,color=GREEN,bold=True)
assert y<1710,y
save(im,3)
# 4 — myth and ending
im,d=page()
d.text((65,190),'А что насчёт',font=F(68,True),fill=GREEN)
d.text((65,273),'«запечатать соки»?',font=F(73,True),fill=RED)
photo(im,'IMG_6271.jpeg',(65,395,1375,1045),(.5,.52))
y=draw_text(d,'Корочка не становится герметичной оболочкой. Влага всё равно уходит во время приготовления, поэтому обжарка сама по себе не делает мясо сочнее.',70,1081,1290,40)
y=draw_text(d,'Тогда зачем она нужна? Ради вкуса, цвета и аромата. А сочность зависит прежде всего от самого куска и того, насколько сильно его успели приготовить.',70,y+22,1290,40)
d.rectangle((65,y+40,1375,y+251),fill=GREEN)
y2=draw_text(d,'Коротко: обсушить поверхность, хорошо разогреть сковороду, не перегружать её и не передерживать мясо. Румяная корочка нужна не для того, чтобы запереть сок, а потому что она вкусная.',93,y+55,1230,33,color=WHITE,bold=True,line=1.25)
assert y2<y+251 and y+251<1715,(y,y2)
save(im,4)
