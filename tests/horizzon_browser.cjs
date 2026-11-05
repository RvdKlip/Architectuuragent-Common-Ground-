// Run from repository root: node tests/horizzon_browser.cjs
// Synthetic sources and mocked MCP bridge only; no remote or AI calls.
const {chromium}=require('playwright');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const http=require('node:http');
(async()=>{
 fs.mkdirSync('/workspace/onboarding-validation',{recursive:true});
 const server=http.createServer((req,res)=>{res.setHeader('Content-Type','text/html');res.end(fs.readFileSync('index.html'));});
 await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
 const browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||'/usr/bin/chromium',headless:true,args:['--no-sandbox']});
 try{
 const page=await browser.newPage({viewport:{width:1440,height:1100}}),errors=[];
 page.on('pageerror',e=>errors.push(e.message));
 const synthetic='# Enterprise Architectuur\n\nHet platform bewaart gegevens bij de bron en ontsluit deze via geautoriseerde APIs voor dienstverlening.';
 await page.addInitScript(text=>{
  const nativeFetch=globalThis.fetch.bind(globalThis);
  globalThis.fetch=(input,options)=>{
   const url=String(input);
   if(url.startsWith('https://raw.githubusercontent.com/ivorstenbosch-maker/EnterpriseArchitectuurCG/'))return Promise.resolve(new Response(text,{status:200}));
   if(url.startsWith('http://127.0.0.1:8765/'))return nativeFetch(input,options);
   return Promise.reject(new Error('Unexpected external fetch in browser test'));
  };
 },synthetic);
 await page.route('https://**',route=>{
  if(route.request().url().startsWith('https://raw.githubusercontent.com/ivorstenbosch-maker/EnterpriseArchitectuurCG/'))return route.fulfill({status:200,body:'# Enterprise Architectuur\n\nHet platform bewaart gegevens bij de bron en ontsluit deze via geautoriseerde APIs voor dienstverlening.',headers:{'Access-Control-Allow-Origin':'*'}});
  return route.abort();
 });
 const calls=[];let readCount=0;
 await page.route('http://127.0.0.1:8765/**',route=>{
  const req=route.request();calls.push(req.url());
  assert.equal(req.headers().authorization,'Bearer local-test-only-service-key');
  const headers={'Access-Control-Allow-Origin':'*','Access-Control-Allow-Headers':'Authorization, Content-Type','Access-Control-Allow-Private-Network':'true'};
  if(req.url().endsWith('/connect'))return route.fulfill({status:200,json:{tools:[{name:'read_architecture',description:'Lees architectuur',annotations:{readOnlyHint:true},inputSchema:{type:'object',properties:{query:{type:'string',title:'Zoekvraag'}},required:['query']}}]},headers});
  assert.equal(req.url(),'http://127.0.0.1:8765/horizzon/read');
  assert.equal(req.postDataJSON().arguments.query,'Zaakgericht werken');
  readCount++;
  return route.fulfill({status:200,json:{name:'Horizzon.md',url:'https://rotterdam.mcp.horizzon.cloud/mcp',tool:'read_architecture',arguments:{query:'Zaakgericht werken'},sha256:String(readCount).repeat(64),retrieved_at:'2026-11-05T15:00:00Z',text:'Object R-17: bestaande zaakregistratie voor gemeentelijke dienstverlening. Relatie naar bedrijfsservice S-2 en API-dienst voor zaken.'},headers});
 });
 await page.goto('http://127.0.0.1:'+server.address().port);
 await page.waitForFunction(()=>remote.text!==null);
 assert.ok(await page.evaluate(()=>remote.text)===synthetic,'Synthetic enterprise source required');
 const left=await page.locator('.source-grid > article').first().boundingBox(),right=await page.locator('#rotterdamse-architectuurbron').boundingBox();
 assert.ok(right.x>left.x+left.width,'Rotterdamse bron staat rechts naast de enterprise architectuur');
 assert.ok(Math.abs(right.y-left.y)<2,'Bronkaarten beginnen op dezelfde hoogte');
 assert.match(await page.textContent('#rotterdamse-architectuurbron .source-title'),/Rotterdamse architectuurbron/);
 await page.fill('#project-name','Zaakgericht werken');await page.fill('#project-goals','Toets beide architecturen.');
 await page.click('#generate-psa');await page.click('#confirm-generate');
 assert.match(await page.textContent('#psa-options-error'),/Rotterdamse architectuurbron/);
 await page.click('#close-psa-dialog');
 await page.locator('#horizzon-service-token').evaluate(el=>el.closest('details').open=true);
 await page.fill('#horizzon-service-token','local-test-only-service-key');await page.click('#connect-horizzon');
 await page.waitForFunction(()=>!document.getElementById('horizzon-actions').hidden);
 await page.fill('#horizzon-parameters input','Zaakgericht werken');await page.click('#read-horizzon');
 await page.waitForFunction(()=>horizzon.snapshots.length===1);
 assert.equal(await page.textContent('#document-count'),'2');
 await page.click('#read-horizzon');await page.waitForFunction(()=>horizzon.snapshots.length===2);
 assert.equal(await page.textContent('#document-count'),'3');
 await page.locator('input[data-category=project]').setInputFiles({name:'Projectopdracht.txt',mimeType:'text/plain',buffer:Buffer.from('Projectopdracht: benut bestaande zaakregistratie voor toegankelijke dienstverlening en controleer architectuurkaders.')});
 await page.waitForFunction(()=>!files.project[0].reading);
 await page.click('#generate-psa');await page.click('#confirm-generate');
 await page.waitForFunction(()=>PA.current!==null);
 const sources=await page.evaluate(()=>PA.current.sources);
 assert.deepEqual(sources.map(s=>s.key),['B00','B01','B02','B03']);
 const listed=await page.locator('#selected-sources .source-row span').allTextContents();
 assert.deepEqual(listed.map(name=>name.replace(' · alle hoofdstukken','')),sources.map(s=>s.filename));
 assert.match(sources[0].text,/gegevens bij de bron/);assert.match(sources[1].text,/Projectopdracht/);assert.match(sources[2].text,/R-17/);assert.match(sources[3].text,/R-17/);
 const downloadPromise=page.waitForEvent('download');await page.click('#download-psa-word');const download=await downloadPromise;
 await download.saveAs('/workspace/onboarding-validation/Horizzon-browser-proef.docx');
 await page.uncheck('#use-horizzon');assert.equal(await page.locator('#psa-stale').isVisible(),true);
 assert.equal(await page.textContent('#document-count'),'2');
 await page.check('#use-horizzon');
 await page.locator('#bronnen').scrollIntoViewIfNeeded();
 await page.locator('#bronnen').screenshot({path:'/workspace/onboarding-validation/horizzon-foundations.png'});
 assert.deepEqual(errors,[]);
 assert.equal(calls.length,3);
 console.log('PASS: missing source blocked; MCP discovery/read; multiple snapshots; both foundations generated; DOCX exported; stale detection; no JS errors.');
 }finally{await browser.close();await new Promise(resolve=>server.close(resolve));}
})().catch(error=>{console.error(error);process.exit(1)});
