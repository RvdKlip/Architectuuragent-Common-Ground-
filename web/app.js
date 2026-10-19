'use strict';
const $ = id => document.getElementById(id);
const categories = {enterprise:'Enterprise architectuur Platform Dienstverlening',project:'Projectdocument'};
const files = {enterprise:[],project:[]};
const remote = {url:'https://github.com/ivorstenbosch-maker/EnterpriseArchitectuurCG/blob/main/Enterprisearchitectuur-GPT.md',text:null,selected:new Set(),chapters:[],sha256:null,retrieved_at:null};
let busy=false;
const isEnabled=category=>category==='project'||!!document.querySelector('.source-toggle[data-category="'+category+'"]')?.checked;
async function sha(text){return globalThis.crypto?.subtle?[...new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(text)))].map(b=>b.toString(16).padStart(2,'0')).join(''):null;}
function selectedText(){return remote.text||'';}
function selectedDocuments(){
 const result=[];
 if(isEnabled('enterprise')&&!files.enterprise.some(f=>f.selected)&&remote.text)result.push({name:'Enterprise-architectuur-volledig.md',category:'enterprise',url:remote.url,sha256:remote.sha256,retrieved_at:remote.retrieved_at,all_chapters:true});
 for(const [category,list]of Object.entries(files))if(isEnabled(category))for(const entry of list)if(entry.selected)result.push({name:entry.file.name,size:entry.file.size,category,reading:entry.reading,error:entry.error});
 return result;
}
function render(){
 const docs=selectedDocuments(),enabled=[...document.querySelectorAll('.source-toggle:checked')].map(c=>c.dataset.category),missing=enabled.filter(c=>!docs.some(d=>d.category===c));
 $('document-count').textContent=docs.length;$('category-count').textContent=enabled.length;$('missing-count').textContent=missing.length;
 for(const input of document.querySelectorAll('input[type=file][data-category]'))input.disabled=!isEnabled(input.dataset.category);
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
 const category=input.dataset.category;
 const incoming=[...input.files].filter(file=>category!=='project'||!files.project.some(entry=>entry.file.name===file.name&&entry.file.size===file.size&&entry.file.lastModified===file.lastModified)).map(file=>({file,selected:true,reading:true,contexts:[],warnings:[],error:null}));
 files[category]=category==='project'?[...files.project,...incoming]:incoming;
 if(category==='project')input.value='';
 render();
 for(const entry of incoming)(async()=>{try{const result=await DocumentReader.read(entry.file);entry.contexts=result.contexts;entry.warnings=result.warnings;entry.pages=result.pages||1;}catch(error){entry.error=error.message;}finally{entry.reading=false;render();}})();
}));
for(const id of ['project-name','project-goals','project-type'])$(id).addEventListener('input',render);
$('load-enterprise').addEventListener('click',async()=>{
 busy=true;render();const message=$('enterprise-message');message.textContent='Volledige openbare bron ophalen…';const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),30000);
 try{const response=await fetch('https://raw.githubusercontent.com/ivorstenbosch-maker/EnterpriseArchitectuurCG/main/Enterprisearchitectuur-GPT.md',{signal:controller.signal,credentials:'omit'});if(!response.ok)throw Error('HTTP '+response.status);const buffer=await response.arrayBuffer();if(buffer.byteLength>3000000)throw Error('Bron te groot');const text=new TextDecoder('utf-8',{fatal:true}).decode(buffer);if(!text.startsWith('# ')||!text.slice(0,1000).includes('Enterprise Architectuur'))throw Error('Onverwacht bronformaat');remote.text=text;remote.sha256=await sha(text);remote.retrieved_at=new Date().toISOString();remote.selected=new Set(['all']);message.textContent='Volledige bron opgehaald. Alle hoofdstukken worden meegenomen.';$('load-enterprise').textContent='Bron vernieuwen ↻';}
 catch(error){message.textContent='Ophalen is niet gelukt. Controleer je internetverbinding of upload een eigen versie. Een eerder geladen bron blijft bewaard.';}
 finally{clearTimeout(timer);busy=false;render();}
});
// Eerste render volgt nadat de PA-module is geïnitialiseerd.
