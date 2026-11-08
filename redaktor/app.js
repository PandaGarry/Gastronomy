'use strict';
const $ = id => document.getElementById(id);
const presets = {
  cover: [['Утверждённая обложка', 'oblozhka-zhivaya.png']],
  post: Array.from({length: 5}, (_, i) => [`Рамка ${i + 1}`, `../proekt/07-upakovka-soobshchestva/ramka-vybor-0${i + 1}.png`])
};
const MAX_FILE = 20 * 1024 * 1024, MAX_PROJECT = 60 * 1024 * 1024, MAX_LAYERS = 20;
let mode = 'cover', drag = null, loadGeneration = 0, photoGeneration = 0;
const editor = $('editor'), ctx = editor.getContext('2d'), clean = document.createElement('canvas');
function textLayer(text, x, y, size, width) {
  return {text, x, y, size, width, color:'#344923', font:'bold-serif', align:'left'};
}
function defaults(m) {
  return m === 'cover'
    ? {w:1920,h:768,format:'cover',layers:[textLayer('',580,250,96,1100)],selected:0,photoX:1000,photoY:210,photoWidth:600,bgSrc:presets.cover[0][1],photoSrc:null,bg:null,photo:null}
    : {w:1024,h:1024,format:'square',layers:[textLayer('ЗАГОЛОВОК\nВАШЕГО ПОСТА',160,320,66,700)],selected:0,photoX:190,photoY:500,photoWidth:640,bgSrc:presets.post[0][1],photoSrc:null,bg:null,photo:null};
}
const states = {cover:defaults('cover'), post:defaults('post')};
let s = states.cover;
const layer = () => s.layers[s.selected];
function status(message) { $('status').textContent = message; }
function imageFrom(src) {
  return new Promise((resolve,reject) => {
    const image = new Image();
    image.onload = () => { if (image.width > 12000 || image.height > 12000 || image.width * image.height > 50000000) reject(Error('Изображение слишком велико: максимум 50 мегапикселей и 12000 пикселей по стороне.')); else resolve(image); };
    image.onerror = () => reject(new Error('Не удалось открыть изображение.'));
    image.src = src;
  });
}
function readData(file) {
  if (!file || file.size > MAX_FILE) throw Error('Файл слишком большой: максимум 20 МБ.');
  if (!['image/png','image/jpeg','image/webp'].includes(file.type)) throw Error('Выберите PNG, JPEG или WebP.');
  return new Promise((resolve,reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result);
    reader.onerror = () => reject(Error('Не удалось прочитать файл.'));
    reader.readAsDataURL(file);
  });
}
async function setBackground(src) {
  const current = s, generation = ++loadGeneration;
  current.loading = true;
  try {
    const img = await imageFrom(src);
    if (generation !== loadGeneration || current !== s) return;
    current.bg = img; current.bgSrc = src; status(''); draw();
  } catch (e) { if (generation === loadGeneration) { status(e.message); syncUI(); } }
  finally { if(generation===loadGeneration) current.loading = false; }
}
function fitBackground(c, image) {
  // Preserve aspect ratio: a square template stays square in a vertical layout.
  const scale = Math.min(s.w / image.width, s.h / image.height);
  const w = image.width * scale, h = image.height * scale;
  c.drawImage(image, (s.w-w)/2, (s.h-h)/2, w, h);
}
function fontFor(l) { return `${l.font === 'sans' ? '' : 'bold '}${l.size}px ${l.font === 'bold-serif' ? 'Georgia, serif' : 'Arial, sans-serif'}`; }
function getLines(c, text, maxWidth) {
  const lines = [];
  for (const para of text.split('\n')) {
    if (!para) { lines.push(''); continue; }
    let row = '';
    for (const word of para.split(/\s+/)) {
      const next = row ? row + ' ' + word : word;
      if (row && c.measureText(next).width > maxWidth) { lines.push(row); row = word; } else row = next;
    }
    lines.push(row);
  }
  return lines;
}
function drawContent(c) {
  c.clearRect(0,0,s.w,s.h); c.fillStyle='#f8eed7'; c.fillRect(0,0,s.w,s.h);
  if (s.bg) fitBackground(c,s.bg);
  if (s.photo) c.drawImage(s.photo,s.photoX,s.photoY,s.photoWidth,s.photoWidth*s.photo.height/s.photo.width);
  for (const l of s.layers) {
    c.fillStyle=l.color; c.font=fontFor(l); c.textBaseline='top'; c.textAlign=l.align;
    const anchor=l.x+(l.align==='center'?l.width/2:l.align==='right'?l.width:0);
    getLines(c,l.text,l.width).forEach((line,i)=>c.fillText(line,anchor,l.y+i*l.size*1.23));
  }
}
function draw() {
  editor.width=clean.width=s.w; editor.height=clean.height=s.h;
  const c=clean.getContext('2d'); drawContent(c); ctx.drawImage(clean,0,0);
  if ($('guides').checked) {
    ctx.save(); ctx.setLineDash([12,8]); ctx.lineWidth=3; ctx.strokeStyle='#3c72d2';
    if (mode==='cover') {ctx.strokeRect(2,132,s.w-4,634);ctx.fillStyle='rgba(110,130,190,.25)';ctx.beginPath();ctx.arc(332,768,248,0,2*Math.PI);ctx.fill();ctx.stroke();}
    const l=layer(); c.font=fontFor(l);
    if (l.text) {ctx.strokeStyle='#d83729';ctx.strokeRect(l.x,l.y,l.width,Math.max(getLines(c,l.text,l.width).length*l.size*1.23,l.size));}
    if(s.photo){ctx.strokeStyle='#3c72d2';ctx.strokeRect(s.photoX,s.photoY,s.photoWidth,s.photoWidth*s.photo.height/s.photo.width);}
    ctx.restore();
  }
  const warnings=[];
  s.layers.forEach((l,i)=>{ if(!l.text)return; c.font=fontFor(l); const rows=getLines(c,l.text,l.width); if(l.x+l.width>s.w||l.y+rows.length*l.size*1.23>s.h)warnings.push(`Текст ${i+1} может выходить за край.`); if(l.text.split(/\s+/).some(word=>c.measureText(word).width>l.width))warnings.push(`В тексте ${i+1} есть слово шире блока.`); });
  if(s.photo && (s.photoX+s.photoWidth>s.w || s.photoY+s.photoWidth*s.photo.height/s.photo.width>s.h)) warnings.push('Фото может выходить за край.');
  $('warnings').textContent=warnings.join(' ');
  if(mode==='cover'){
    const m=$('mobile'),d=$('desktop');m.width=960;m.height=384;m.getContext('2d').drawImage(clean,0,0,960,384);
    d.width=960;d.height=318;d.getContext('2d').drawImage(clean,0,132,1920,636,0,0,960,318);
  }
}
function updateInputs() {
  const l=layer(); $('textLayer').replaceChildren(...s.layers.map((item,i)=>new Option(`${i+1}. ${item.text.replace(/\s+/g,' ').slice(0,28)||'Пустой текст'}`,String(i))));
  $('textLayer').value=String(s.selected);$('text').value=l.text;$('size').value=l.size;$('color').value=l.color;
  $('font').value=l.font;$('align').value=l.align;$('textWidth').max=s.w;$('textWidth').value=l.width;
  $('photoWidth').max=s.w;$('photoWidth').value=s.photoWidth; $('textX').max=s.w; $('textY').max=s.h; $('textX').value=l.x; $('textY').value=l.y; $('photoX').max=s.w; $('photoY').max=s.h; $('photoX').value=s.photoX; $('photoY').value=s.photoY;$('postFormat').value=s.format==='portrait'?'portrait':'square';
}
function syncUI() {
  $('coverMode').classList.toggle('active',mode==='cover');$('postMode').classList.toggle('active',mode==='post');
  $('previews').style.display=mode==='cover'?'grid':'none';$('postFormatLabel').hidden=mode!=='post';
  $('workspaceTitle').textContent=mode==='cover'?'Обложка · 1920 × 768':`Карточка · ${s.w} × ${s.h}`;
  $('template').replaceChildren(...presets[mode].map(([label,path])=>new Option(label,path)));
  if(!presets[mode].some(([,path])=>path===s.bgSrc)){const option=new Option('Своя загруженная основа','');option.disabled=true;$('template').prepend(option);}
  $('template').value=presets[mode].some(([,path])=>path===s.bgSrc)?s.bgSrc:'';
  updateInputs();
}
async function changeMode(m) {
  s.loading=false; ++loadGeneration; ++photoGeneration; mode=m;s=states[m];drag=null;syncUI();
  if(!s.bg) await setBackground(s.bgSrc); else draw();
}
function download(blob,name) {
  const a=document.createElement('a'),url=URL.createObjectURL(blob);a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),10000);
}
$('template').addEventListener('change',e=>setBackground(e.target.value));
$('backgroundFile').addEventListener('change',async e=>{
  const current=s, generation=++loadGeneration; current.loading=true;
  try {const src=await readData(e.target.files[0]);const image=await imageFrom(src);if(current!==s||generation!==loadGeneration)return;current.bgSrc=src;current.bg=image;syncUI();status('Основа загружена.');draw();}
  catch(err){if(generation===loadGeneration)status(err.message);}finally{if(generation===loadGeneration)current.loading=false;e.target.value='';}
});
$('photoFile').addEventListener('change',async e=>{
  const current=s, generation=++photoGeneration;
  try {const src=await readData(e.target.files[0]);const image=await imageFrom(src);if(current!==s||generation!==photoGeneration)return;current.photoSrc=src;current.photo=image;status('Фото добавлено.');draw();}
  catch(err){status(err.message);}finally{e.target.value='';}
});
$('textLayer').onchange=e=>{s.selected=Number(e.target.value);updateInputs();draw();};
$('addText').onclick=()=>{if(s.layers.length>=MAX_LAYERS){status('Можно добавить не более 20 текстовых слоёв.');return;}s.layers.push(textLayer('Новый текст',Math.round(s.w*.15),Math.round(s.h*.2),Math.round(s.w*.06),Math.round(s.w*.7)));s.selected=s.layers.length-1;updateInputs();draw();};
$('removeText').onclick=()=>{if(s.layers.length===1){s.layers[0].text='';}else{s.layers.splice(s.selected,1);s.selected=Math.max(0,s.selected-1);}updateInputs();draw();};
function moveLayer(delta){const next=s.selected+delta;if(next<0||next>=s.layers.length)return;[s.layers[s.selected],s.layers[next]]=[s.layers[next],s.layers[s.selected]];s.selected=next;updateInputs();draw();}
$('layerUp').onclick=()=>moveLayer(1);$('layerDown').onclick=()=>moveLayer(-1);
for (const id of ['text','size','color','font','align','textWidth','textX','textY']) $(id).addEventListener('input',e=>{
  const l=layer(),key=({textWidth:'width',textX:'x',textY:'y'})[id]||id;
  let value=['size','textWidth','textX','textY'].includes(id)?Number(e.target.value):e.target.value;
  if(id==='size') value=Math.max(12,Math.min(250,value||12));
  if(id==='textWidth') value=Math.max(100,Math.min(s.w,value||100));
  if(id==='textX'||id==='textY')value=Math.max(0,Math.min(id==='textX'?s.w:s.h,value||0));
  l[key]=value;if(id==='text'){$('textLayer').options[s.selected].text=`${s.selected+1}. ${value.replace(/\s+/g,' ').slice(0,28)||'Пустой текст'}`;}draw();
});
for(const id of ['photoX','photoY'])$(id).oninput=e=>{s[id]=Math.max(0,Math.min(id==='photoX'?s.w:s.h,Number(e.target.value)||0));draw();};
$('photoWidth').oninput=e=>{s.photoWidth=Math.max(80,Math.min(s.w,Number(e.target.value)||80));draw();};
$('guides').onchange=draw;$('coverMode').onclick=()=>changeMode('cover');$('postMode').onclick=()=>changeMode('post');
$('removePhoto').onclick=()=>{++photoGeneration;s.photo=null;s.photoSrc=null;$('photoFile').value='';draw();};
$('postFormat').onchange=e=>{
  if(mode!=='post')return;
  const nw=e.target.value==='portrait'?1440:1024,nh=e.target.value==='portrait'?1800:1024;
  const sx=nw/s.w,sy=nh/s.h;
  for(const l of s.layers){l.x=Math.round(l.x*sx);l.y=Math.round(l.y*sy);l.width=Math.min(nw,Math.round(l.width*sx));l.size=Math.min(250,Math.round(l.size*sx));}
  s.photoX=Math.round(s.photoX*sx);s.photoY=Math.round(s.photoY*sy);s.photoWidth=Math.min(nw,Math.round(s.photoWidth*sx));
  s.w=nw;s.h=nh;s.format=e.target.value;syncUI();draw();
};
$('download').onclick=()=>{if(!s.bg||s.loading){status('Подождите, пока загрузится основа.');return;}clean.toBlob(blob=>{if(!blob){status('Не удалось сохранить PNG.');return;}download(blob,mode==='cover'?'oblozhka-vk.png':'kartochka-posta.png');status('PNG сохранён без вспомогательных линий.');},'image/png');};
$('reset').onclick=()=>{if(s.loading){status('Подождите, пока загрузится основа.');return;}if(!confirm('Сбросить текст, фото и формат текущей композиции? Основа останется.'))return;++photoGeneration;const old=s, fresh=defaults(mode);fresh.bg=old.bg;fresh.bgSrc=old.bgSrc;states[mode]=fresh;s=fresh;syncUI();draw();status('Композиция сброшена.');};
function coords(e){const r=editor.getBoundingClientRect();return{x:(e.clientX-r.left)*s.w/r.width,y:(e.clientY-r.top)*s.h/r.height};}
editor.addEventListener('pointerdown',e=>{
  const p=coords(e),c=clean.getContext('2d');let found=-1;
  for(let i=s.layers.length-1;i>=0;i--){let l=s.layers[i];c.font=fontFor(l);const h=getLines(c,l.text,l.width).length*l.size*1.23;if(l.text&&p.x>=l.x&&p.x<=l.x+l.width&&p.y>=l.y&&p.y<=l.y+h){found=i;break;}}
  const hitPhoto=s.photo&&p.x>=s.photoX&&p.x<=s.photoX+s.photoWidth&&p.y>=s.photoY&&p.y<=s.photoY+s.photoWidth*s.photo.height/s.photo.width;
  if(found>=0){s.selected=found;updateInputs();const l=layer();drag={kind:'text',x:p.x,y:p.y,ox:l.x,oy:l.y};draw();}
  else if(hitPhoto)drag={kind:'photo',x:p.x,y:p.y,ox:s.photoX,oy:s.photoY};
  if(drag)editor.setPointerCapture(e.pointerId);
});
editor.addEventListener('pointermove',e=>{if(!drag)return;const p=coords(e),x=Math.round(Math.max(0,Math.min(s.w,drag.ox+p.x-drag.x))),y=Math.round(Math.max(0,Math.min(s.h,drag.oy+p.y-drag.y)));if(drag.kind==='text'){layer().x=x;layer().y=y;$('textX').value=x;$('textY').value=y;}else{s.photoX=x;s.photoY=y;$('photoX').value=x;$('photoY').value=y;}draw();});
editor.addEventListener('pointerup',()=>drag=null);editor.addEventListener('pointercancel',()=>drag=null);
// Projects are explicitly saved locally; no server-side storage or automatic restore.
$('saveProject').onclick=()=>{
  if(!s.bg||s.loading){status('Подождите, пока загрузится основа.');return;}
  const data={version:1,mode,format:s.format,w:s.w,h:s.h,layers:s.layers,selected:s.selected,photoX:s.photoX,photoY:s.photoY,photoWidth:s.photoWidth,bgSrc:s.bgSrc,photoSrc:s.photoSrc};
  download(new Blob([JSON.stringify(data,null,2)],{type:'application/json'}),'proekt-pv.json');status('Проект сохранён. Он может содержать личные изображения и текст.');
};
function validateProject(data) {
  if(!data||data.version!==1||!['cover','post'].includes(data.mode))throw Error('Неподдерживаемый формат проекта.');
  const allowed=data.mode==='cover'?[[1920,768,'cover']]:[[1024,1024,'square'],[1440,1800,'portrait']];
  if(!allowed.some(([w,h,format])=>data.w===w&&data.h===h&&data.format===format))throw Error('Недопустимый размер холста.');
  const sourceOK=src=>typeof src==='string'&&src.length<=MAX_FILE*1.4&&(/^data:image\/(png|jpeg|webp);base64,/i.test(src)||presets[data.mode].some(([,p])=>p===src));
  if(!sourceOK(data.bgSrc)||(data.photoSrc!==null&&(!sourceOK(data.photoSrc)||!/^data:image\//i.test(data.photoSrc))))throw Error('Недопустимый источник изображения.');
  const finite=(x,min,max)=>typeof x==='number'&&Number.isFinite(x)&&x>=min&&x<=max;
  if(!Array.isArray(data.layers)||data.layers.length<1||data.layers.length>MAX_LAYERS||!Number.isInteger(data.selected)||data.selected<0||data.selected>=data.layers.length)throw Error('Недопустимые текстовые слои.');
  for(const l of data.layers){if(!l||typeof l.text!=='string'||l.text.length>10000||!finite(l.x,0,data.w)||!finite(l.y,0,data.h)||!finite(l.size,12,250)||!finite(l.width,100,data.w)||!/^#[0-9a-f]{6}$/i.test(l.color)||!['bold-serif','bold-sans','sans'].includes(l.font)||!['left','center','right'].includes(l.align))throw Error('Недопустимые параметры текста.');}
  if(!finite(data.photoX,0,data.w)||!finite(data.photoY,0,data.h)||!finite(data.photoWidth,80,data.w))throw Error('Недопустимые параметры фото.');
}
$('projectFile').onchange=async e=>{
  const file=e.target.files[0];if(!file)return;
  try{
    if(file.size>MAX_PROJECT)throw Error('Проект слишком большой: максимум 60 МБ.');
    const data=JSON.parse(await file.text());validateProject(data);
    const [bg,photo]=await Promise.all([imageFrom(data.bgSrc),data.photoSrc?imageFrom(data.photoSrc):Promise.resolve(null)]);
    if(!confirm('Заменить текущий проект загруженным? Несохранённые изменения этого режима будут потеряны.'))return;
    ++loadGeneration; ++photoGeneration; const target=data.mode; states[target]={...data,bg,photo}; mode=target;s=states[target];drag=null;syncUI();draw();status('Проект открыт.');
  }catch(err){status(err instanceof SyntaxError?'Файл проекта не является корректным JSON.':err.message);}finally{e.target.value='';}
};
changeMode('cover');
