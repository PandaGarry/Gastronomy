// Optional integration test: npm install --no-save playwright-core; set CHROMIUM_PATH and EDITOR_URL.
const {chromium} = require('playwright-core');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
(async () => {
  const browser = await chromium.launch({executablePath:process.env.CHROMIUM_PATH || '/usr/bin/chromium',headless:true,args:['--no-sandbox']});
  const page = await browser.newPage({acceptDownloads:true});
  const errors=[]; page.on('pageerror', error=>errors.push(error.message)); page.on('dialog', dialog=>dialog.accept());
  const base=process.env.EDITOR_URL || 'http://127.0.0.1:8001';
  await page.goto(base+'/redaktor/');
  await page.waitForFunction(()=>document.querySelector('#editor').width===1920);
  assert.equal(await page.locator('#postFormatLabel').isVisible(),false);
  assert.equal((await page.request.get(base+'/proekt/01-strategiya/PROEKT.md')).status(),404);
  assert.equal((await page.request.get(base+'/proekt/07-upakovka-soobshchestva/ramka-vybor-01.png')).status(),200);
  await page.click('#postMode'); await page.waitForFunction(()=>document.querySelector('#editor').width===1024);
  for (let i=1;i<=5;i++) {await page.selectOption('#template',`../proekt/07-upakovka-soobshchestva/ramka-vybor-0${i}.png`); await page.waitForFunction(()=>document.querySelector('#status').textContent==='');}
  await page.fill('#text','Первый слой'); await page.click('#addText'); await page.fill('#text','Второй слой'); await page.fill('#textX','155');
  await page.selectOption('#postFormat','portrait'); assert.equal(await page.locator('#editor').evaluate(el=>el.width),1440);
  await page.locator('#photoFile').setInputFiles(path.resolve('proekt/07-upakovka-soobshchestva/logo-02.png')); await page.waitForFunction(()=>document.querySelector('#status').textContent==='Фото добавлено.');
  await page.click('#coverMode'); await page.click('#postMode'); assert.equal(await page.locator('#text').inputValue(),'Второй слой'); assert.equal(await page.locator('#textLayer option').count(),2);
  const downloadPromise=page.waitForEvent('download'); await page.click('#saveProject'); const download=await downloadPromise;
  const project=JSON.parse(fs.readFileSync(await download.path(),'utf8'));
  assert.equal(project.layers.length,2);assert.equal(project.layers[1].text,'Второй слой');assert.ok(project.photoSrc.startsWith('data:image/'));
  await page.fill('#text','ИСПОРЧЕНО'); await page.locator('#projectFile').setInputFiles({name:'project.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(project))});
  await page.waitForFunction(()=>document.querySelector('#status').textContent==='Проект открыт.'); assert.equal(await page.locator('#text').inputValue(),'Второй слой');
  const before=await page.locator('#text').inputValue(); await page.locator('#projectFile').setInputFiles({name:'bad.json',mimeType:'application/json',buffer:Buffer.from('{broken')});
  await page.waitForFunction(()=>document.querySelector('#status').textContent.includes('корректным JSON')); assert.equal(await page.locator('#text').inputValue(),before);
  const pngPromise=page.waitForEvent('download'); await page.click('#download');const png=await pngPromise;const bytes=fs.readFileSync(await png.path());
  assert.equal(bytes.readUInt32BE(16),1440);assert.equal(bytes.readUInt32BE(20),1800);
  assert.deepEqual(errors,[]); console.log('Browser tests passed: templates, layers, persistence, format, upload, export, server boundaries.');
  await browser.close();
})().catch(error=>{console.error(error);process.exitCode=1});
