'use strict';
const $ = id => document.getElementById(id);
const HORIZZON_URL='https://rotterdam.horizzon.cloud/sites/8579a6d6-9680-4fee-959c-4793130eef6f/views/e059f7c1-e164-f111-bb43-025a1dd2f359';
const categories = {enterprise:'Enterprise architectuur Platform Dienstverlening',horizon:'Bouwstenen Rotterdam',project:'Projectdocument'};
const files = {enterprise:[],project:[]};
const catalogue={source:{url:HORIZZON_URL,sha256:null},abbs:[],sbbs:[]};
let buildingBlocks={selected:[]};
const horizon={blocks:[],selected:new Set(),filename:null,sha256:null,error:null,reading:false};
const remote = {url:'https://github.com/ivorstenbosch-maker/EnterpriseArchitectuurCG/blob/main/Enterprisearchitectuur-GPT.md',text:null,selected:new Set(),chapters:[],sha256:null,retrieved_at:null};
let busy=false;
const isEnabled=category=>category==='project'||!!document.querySelector('.source-toggle[data-category="'+category+'"]')?.checked;
async function sha(text){return globalThis.crypto?.subtle?[...new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(text)))].map(b=>b.toString(16).padStart(2,'0')).join(''):null;}
function selectedText(){return remote.text||'';}
function selectedDocuments(){
 const result=[];
 if(isEnabled('enterprise')&&!files.enterprise.some(f=>f.selected)&&remote.text)result.push({name:'Enterprise-architectuur-volledig.md',category:'enterprise',url:remote.url,sha256:remote.sha256,retrieved_at:remote.retrieved_at,all_chapters:true});
 for(const [category,list]of Object.entries(files))if(isEnabled(category))for(const entry of list)if(entry.selected)result.push({name:entry.file.name,size:entry.file.size,category,reading:entry.reading,error:entry.error});
 if(isEnabled('horizon')&&horizon.blocks.some(block=>horizon.selected.has(block.id)))result.push({name:'Bouwstenen-Rotterdam-selectie.md',category:'horizon',export:horizon.filename,sha256:horizon.sha256,url:HORIZZON_URL,ids:[...horizon.selected]});
 return result;
}
function renderBuildingBlocks(){
 buildingBlocks={selected:isEnabled('horizon')?horizon.blocks.filter(block=>horizon.selected.has(block.id)):[],source:{url:HORIZZON_URL,export:horizon.filename,sha256:horizon.sha256},method:'Handmatige selectie uit aangeleverde Horizzon-export; niet als verplicht besluit vastgesteld.'};
 const query=$('horizon-search').value.toLocaleLowerCase('nl');
 for(const type of ['ABB','SBB']){
  const container=$(type==='ABB'?'horizon-abbs':'horizon-sbbs');container.replaceChildren();
  const blocks=horizon.blocks.filter(block=>block.type===type&&(block.name+' '+block.description).toLocaleLowerCase('nl').includes(query));
  for(const block of blocks){
   const row=document.createElement('div');row.className='block-choice';const label=document.createElement('label'),check=document.createElement('input');
   check.type='checkbox';check.checked=horizon.selected.has(block.id);check.disabled=!isEnabled('horizon');check.dataset.blockId=block.id;
   check.addEventListener('change',()=>{if(check.checked)horizon.selected.add(block.id);else horizon.selected.delete(block.id);render();});
   label.append(check,document.createTextNode(block.name));row.append(label);
   const description=document.createElement('small');description.textContent=block.id+(block.description?' · '+block.description:'');row.append(description);container.append(row);
  }
  if(!blocks.length){const p=document.createElement('p');p.className='empty';p.textContent=horizon.blocks.length?'Geen bouwstenen gevonden voor deze zoekopdracht.':'Importeer een Horizzon-export om bouwstenen te selecteren.';container.append(p);}
 }
}
function render(){
 renderBuildingBlocks();
 const docs=selectedDocuments(),enabled=[...document.querySelectorAll('.source-toggle:checked')].map(c=>c.dataset.category),missing=enabled.filter(c=>!docs.some(d=>d.category===c));
 $('document-count').textContent=docs.length;$('category-count').textContent=enabled.length;$('missing-count').textContent=missing.length;
 for(const input of document.querySelectorAll('input[type=file][data-category]'))input.disabled=!isEnabled(input.dataset.category);
 $('horizon-catalogue').disabled=!isEnabled('horizon');$('horizon-search').disabled=!isEnabled('horizon')||!horizon.blocks.length;
 $('load-enterprise').disabled=!isEnabled('enterprise')||busy;
 for(const[category,list]of Object.entries(files)){
  const container=$(category+'-files');container.replaceChildren();
  for(const entry of list){const label=document.createElement('label'),check=document.createElement('input');check.type='checkbox';check.checked=entry.selected;check.disabled=!isEnabled(category);check.addEventListener('change',()=>{entry.selected=check.checked;render();});label.append(check,document.createTextNode(entry.file.name));container.append(label);const status=document.createElement('small');status.className='reading-status';status.textContent=entry.reading?'Inhoud wordt gelezen…':entry.error||'Inhoud lokaal gelezen.';container.append(status);}
 }
 $('selected-sources').replaceChildren();docs.forEach((entry,index)=>{const row=document.createElement('div');row.className='source-row';const code=document.createElement('code'),name=document.createElement('span');code.textContent='B'+String(index).padStart(2,'0');name.textContent=entry.name+(entry.all_chapters?' · alle hoofdstukken':'');row.append(code,name);$('selected-sources').append(row);});
 const message=$('selection-message');message.classList.toggle('warning',!!missing.length||!docs.length);message.textContent=missing.length?'Nog inhoud nodig voor: '+missing.map(c=>categories[c]).join('; '):!docs.length?'Selecteer een bron en voeg de inhoud toe.':'Je bronselectie is samengesteld. De volledige inhoud van geselecteerde bronbestanden wordt meegenomen.';
 $('enterprise-status').textContent=remote.text?(isEnabled('enterprise')?'Geselecteerd':'Niet geselecteerd')+' · alle hoofdstukken · '+remote.text.length.toLocaleString('nl-NL')+' tekens':files.enterprise.some(f=>f.selected)?'Eigen versie toegevoegd · volledige inhoud':'Openbare bron nog niet opgehaald';
 if(typeof PA!=='undefined')PA.checkFreshness();
}
document.querySelectorAll('.source-toggle').forEach(check=>check.addEventListener('change',render));
document.querySelectorAll('input[type=file][data-category]').forEach(input=>input.addEventListener('change',()=>{
 const category=input.dataset.category;files[category]=[...input.files].map(file=>({file,selected:true,reading:true,contexts:[],warnings:[],error:null}));render();
 for(const entry of files[category])(async()=>{try{const result=await DocumentReader.read(entry.file);entry.contexts=result.contexts;entry.warnings=result.warnings;entry.pages=result.pages||1;}catch(error){entry.error=error.message;}finally{entry.reading=false;render();}})();
}));
$('horizon-catalogue').addEventListener('change',async event=>{
 const file=event.target.files[0];horizon.blocks=[];horizon.selected.clear();horizon.filename=null;horizon.sha256=null;horizon.error=null;horizon.reading=!!file;render();if(!file)return;
 $('horizon-status').textContent='Horizzon-export wordt gelezen…';
 try{if(file.size>5000000)throw Error('De export mag maximaal 5 MB zijn.');const text=new TextDecoder('utf-8',{fatal:true}).decode(await file.arrayBuffer()),result=HorizzonCatalogue.parse(text,file.name);horizon.blocks=result.blocks;horizon.filename=file.name;horizon.sha256=await sha(text);catalogue.source.sha256=horizon.sha256;$('horizon-status').textContent=result.blocks.length+' bouwstenen geladen uit '+file.name+'. '+result.skipped+' objecten zonder bruikbare ABB/SBB-classificatie overgeslagen. Selecteer hieronder wat je wilt gebruiken.';}
 catch(error){horizon.error=error.message;$('horizon-status').textContent=error.message;}
 finally{horizon.reading=false;render();}
});
$('horizon-search').addEventListener('input',renderBuildingBlocks);
for(const id of ['project-name','project-goals','project-type'])$(id).addEventListener('input',render);
$('load-enterprise').addEventListener('click',async()=>{
 busy=true;render();const message=$('enterprise-message');message.textContent='Volledige openbare bron ophalen…';const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),30000);
 try{const response=await fetch('https://raw.githubusercontent.com/ivorstenbosch-maker/EnterpriseArchitectuurCG/main/Enterprisearchitectuur-GPT.md',{signal:controller.signal,credentials:'omit'});if(!response.ok)throw Error('HTTP '+response.status);const buffer=await response.arrayBuffer();if(buffer.byteLength>3000000)throw Error('Bron te groot');const text=new TextDecoder('utf-8',{fatal:true}).decode(buffer);if(!text.startsWith('# ')||!text.slice(0,1000).includes('Enterprise Architectuur'))throw Error('Onverwacht bronformaat');remote.text=text;remote.sha256=await sha(text);remote.retrieved_at=new Date().toISOString();remote.selected=new Set(['all']);message.textContent='Volledige bron opgehaald. Alle hoofdstukken worden meegenomen.';$('load-enterprise').textContent='Bron vernieuwen ↻';}
 catch(error){message.textContent='Ophalen is niet gelukt. Controleer je internetverbinding of upload een eigen versie. Een eerder geladen bron blijft bewaard.';}
 finally{clearTimeout(timer);busy=false;render();}
});
$('download-selection').addEventListener('click',()=>{
 const manifest={project:$('project-name').value,goals:$('project-goals').value,type:$('project-type').value,created_at:new Date().toISOString(),sources:selectedDocuments(),building_blocks:buildingBlocks,note:'Bronselectie voor een projectarchitectuur. Lokale bronbestanden zijn niet opgenomen.'};const url=URL.createObjectURL(new Blob([JSON.stringify(manifest,null,2)],{type:'application/json'})),anchor=document.createElement('a');anchor.href=url;anchor.download='bronselectie.json';anchor.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
});
// Eerste render volgt nadat de PA-module is geïnitialiseerd.
