'use strict';
const $ = id => document.getElementById(id);
const categories = {horizzon:'Rotterdamse architectuurbron',enterprise:'Enterprise architectuur Platform Dienstverlening',project:'Projectdocument'};
const files = {enterprise:[],project:[]};
const horizzon = {snapshots:[],tools:[],busy:false};
const remote = {url:'https://github.com/ivorstenbosch-maker/EnterpriseArchitectuurCG/blob/main/Enterprisearchitectuur-GPT.md',text:null,selected:new Set(),chapters:[],sha256:null,retrieved_at:null};
let busy=false;
const isEnabled=category=>category==='project'||!!document.querySelector('.source-toggle[data-category="'+category+'"]')?.checked;
async function sha(text){return globalThis.crypto?.subtle?[...new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(text)))].map(b=>b.toString(16).padStart(2,'0')).join(''):null;}
function selectedText(){return remote.text||'';}
function selectedDocuments(){
 const result=[];
 if(isEnabled('enterprise')&&!files.enterprise.some(f=>f.selected)&&remote.text)result.push({name:'Enterprise-architectuur-volledig.md',category:'enterprise',url:remote.url,sha256:remote.sha256,retrieved_at:remote.retrieved_at,all_chapters:true});
 for(const [category,list]of Object.entries(files))if(isEnabled(category))for(const entry of list)if(entry.selected)result.push({name:entry.file.name,size:entry.file.size,category,reading:entry.reading,error:entry.error});
 if(isEnabled('horizzon'))for(const item of horizzon.snapshots)if(item.selected)result.push({name:item.name,category:'horizzon',sha256:item.sha256,retrieved_at:item.retrieved_at,url:item.url,tool:item.tool,arguments:item.arguments});
 return result;
}
function render(){
 const docs=selectedDocuments(),enabled=[...document.querySelectorAll('.source-toggle:checked')].map(c=>c.dataset.category),missing=enabled.filter(c=>!docs.some(d=>d.category===c));
 $('document-count').textContent=docs.length;$('category-count').textContent=enabled.length;$('missing-count').textContent=missing.length;
 for(const input of document.querySelectorAll('input[type=file][data-category]'))input.disabled=!isEnabled(input.dataset.category);
 $('connect-horizzon').disabled=!isEnabled('horizzon')||horizzon.busy;
 $('read-horizzon').disabled=!isEnabled('horizzon')||horizzon.busy||!horizzon.tools.length;
 $('horizzon-snapshots').replaceChildren();
 for(const item of horizzon.snapshots){const label=document.createElement('label'),check=document.createElement('input');check.type='checkbox';check.checked=item.selected;check.disabled=!isEnabled('horizzon');check.addEventListener('change',()=>{item.selected=check.checked;render();});label.append(check,document.createTextNode(item.name+' · '+new Date(item.retrieved_at).toLocaleString('nl-NL')));const details=document.createElement('details'),summary=document.createElement('summary'),content=document.createElement('pre');summary.textContent='Opgehaalde inhoud bekijken';content.textContent=item.text;content.style.whiteSpace='pre-wrap';details.append(summary,content);$('horizzon-snapshots').append(label,details);}
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
async function loadEnterprise(){
 if(busy)return;
 busy=true;render();const message=$('enterprise-message');message.textContent='Volledige openbare bron ophalen…';const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),30000);
 try{const response=await fetch('https://raw.githubusercontent.com/ivorstenbosch-maker/EnterpriseArchitectuurCG/main/Enterprisearchitectuur-GPT.md',{signal:controller.signal,credentials:'omit'});if(!response.ok)throw Error('HTTP '+response.status);const buffer=await response.arrayBuffer();if(buffer.byteLength>3000000)throw Error('Bron te groot');const text=new TextDecoder('utf-8',{fatal:true}).decode(buffer);if(!text.startsWith('# ')||!text.slice(0,1000).includes('Enterprise Architectuur'))throw Error('Onverwacht bronformaat');remote.text=text;remote.sha256=await sha(text);remote.retrieved_at=new Date().toISOString();remote.selected=new Set(['all']);message.textContent='Volledige bron opgehaald. Alle hoofdstukken worden meegenomen.';$('load-enterprise').textContent='Bron vernieuwen ↻';}
 catch(error){message.textContent='Ophalen is niet gelukt. Controleer je internetverbinding of upload een eigen versie. Een eerder geladen bron blijft bewaard.';}
 finally{clearTimeout(timer);busy=false;render();}
}
$('load-enterprise').addEventListener('click',loadEnterprise);
// Eerste render volgt nadat de PA-module is geïnitialiseerd.

async function horizzonRequest(action, payload={}) {
 let service;
 try{service=new URL($('horizzon-service').value);if(service.protocol!=='http:'||!['127.0.0.1','localhost'].includes(service.hostname)||service.port!=='8765'||service.username||service.password)throw Error();}
 catch(error){throw Error('Gebruik de lokale service op http://127.0.0.1:8765.');}
 if(!$('horizzon-service-token').value)throw Error('Vul de lokale service-sleutel in bij Verbinding instellen.');
 const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),180000);
 try{
  const response=await fetch(service.origin+'/horizzon/'+action,{method:'POST',headers:{'Content-Type':'application/json','Authorization':'Bearer '+$('horizzon-service-token').value},body:JSON.stringify(payload),signal:controller.signal});
  const result=await response.json();if(!response.ok)throw Error(result.error||'Horizzon ophalen is niet gelukt.');return result;
 }catch(error){if(error instanceof TypeError||error.name==='AbortError')throw Error('De lokale service is niet bereikbaar of antwoordt niet op tijd. Controleer of deze draait en probeer opnieuw.');throw error;}
 finally{clearTimeout(timer);}
}
function horizzonFields(){
 const tool=horizzon.tools.find(item=>item.name===$('horizzon-tool').value);
 const container=$('horizzon-parameters');container.replaceChildren();
 $('horizzon-tool-description').textContent=tool?.description||'';
 $('horizzon-confirm-label').hidden=tool?.annotations?.readOnlyHint===true;
 $('horizzon-read-only').checked=false;
 if(!tool)return;
 const schema=tool.inputSchema||{type:'object'};
 // Complex schemas stay editable without inventing a vendor-specific query API.
 const complex=Object.keys(schema).some(key=>['oneOf','anyOf','allOf','$ref'].includes(key))||(!schema.properties&&schema.additionalProperties!==false);
 if(complex){const label=document.createElement('label'),input=document.createElement('textarea');label.textContent='Leesparameters (JSON volgens de functie)';input.dataset.json='true';input.value='{}';label.append(input);container.append(label);const help=document.createElement('pre');help.textContent=JSON.stringify(schema,null,2);container.append(help);return;}
 for(const [key,property]of Object.entries(schema.properties||{})){
  const label=document.createElement('label');label.className='field';label.textContent=(property.title||key)+((schema.required||[]).includes(key)?' *':'');
  let input;
  if(property.enum){input=document.createElement('select');for(const value of property.enum){const option=document.createElement('option');option.value=JSON.stringify(value);option.textContent=String(value);input.append(option);}input.dataset.enum='true';}
  else if(property.type==='boolean'){input=document.createElement('select');for(const value of ['', 'true', 'false']){const option=document.createElement('option');option.value=value;option.textContent=value===''?'Niet opgegeven':value==='true'?'Ja':'Nee';input.append(option);}input.dataset.boolean='true';}
  else{input=document.createElement(property.type==='object'||property.type==='array'?'textarea':'input');if(input.tagName==='INPUT')input.type=['number','integer'].includes(property.type)?'number':'text';else input.dataset.json='true';if(property.default!==undefined)input.value=typeof property.default==='object'?JSON.stringify(property.default):String(property.default);}
  input.dataset.key=key;input.dataset.kind=property.type||'string';label.append(input);
  if(property.description){const description=document.createElement('small');description.textContent=property.description;label.append(description);}container.append(label);
 }
}
$('horizzon-tool').addEventListener('change',horizzonFields);
$('connect-horizzon').addEventListener('click',async()=>{
 horizzon.busy=true;render();$('horizzon-message').textContent='Verbinden en beschikbare leesfuncties ophalen…';
 try{const result=await horizzonRequest('connect');horizzon.tools=result.tools||[];$('horizzon-tool').replaceChildren();for(const tool of horizzon.tools){const option=document.createElement('option');option.value=tool.name;option.textContent=tool.title||tool.name;$('horizzon-tool').append(option);}horizzonFields();$('horizzon-actions').hidden=!horizzon.tools.length;$('horizzon-message').textContent=horizzon.tools.length?'Verbonden. Kies een leesfunctie en haal de relevante architectuurinhoud op.':'Verbonden, maar geen bruikbare leesfuncties beschikbaar.';}
 catch(error){horizzon.tools=[];$('horizzon-actions').hidden=true;$('horizzon-message').textContent=error.message;}
 finally{horizzon.busy=false;render();}
});
$('read-horizzon').addEventListener('click',async()=>{
 horizzon.busy=true;render();$('horizzon-message').textContent='Architectuurinhoud ophalen…';
 try{
  const fields=[...$('horizzon-parameters').querySelectorAll('input,select,textarea')];let args={};
  for(const input of fields){if(!input.dataset.key){args=JSON.parse(input.value);continue;}if(input.value==='')continue;args[input.dataset.key]=input.dataset.json||input.dataset.enum||input.dataset.boolean?JSON.parse(input.value):['number','integer'].includes(input.dataset.kind)?Number(input.value):input.value;}
  const result=await horizzonRequest('read',{tool:$('horizzon-tool').value,arguments:args,confirmed_read_only:$('horizzon-read-only').checked});
  if(!result.text||!result.sha256)throw Error('Geen leesbare Horizzon-bron ontvangen.');
  // Keep multiple object reads/searches; never silently replace an existing snapshot.
  horizzon.snapshots.push({...result,name:result.name.replace('.md','-'+String(horizzon.snapshots.length+1)+'.md'),selected:true});
  $('horizzon-message').textContent='Architectuurinhoud toegevoegd. Controleer of je selectie voldoende objecten en relaties bevat.';
 }catch(error){$('horizzon-message').textContent=error instanceof SyntaxError?'De leesparameters bevatten ongeldige JSON.':error.message;}
 finally{horizzon.busy=false;render();}
});
