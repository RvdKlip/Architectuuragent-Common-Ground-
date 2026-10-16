'use strict';
const $ = id => document.getElementById(id);
const categories = {enterprise:'Enterprise architectuur Platform Dienstverlening', horizon:'Horizon Rotterdam', adrs:'Bestaande architectuurbesluiten (ADR’s)', policy:'Privacy- en beveiligingskaders', project:'Projectdocument'};
const files = {enterprise:[], horizon:[], adrs:[], policy:[], project:[]};
const catalogue = JSON.parse($('block-catalogue').textContent);
const blockOverrides = {};
let buildingBlocks = BuildingBlockAdvice.selection(catalogue, [], blockOverrides);
const remote = {url:'https://github.com/ivorstenbosch-maker/EnterpriseArchitectuurCG/blob/main/Enterprisearchitectuur-GPT.md', text:null, chapters:[], selected:new Set(), sha256:null, retrieved_at:null};
let busy = false;
const isEnabled = category => category === 'project' || document.querySelector('.source-toggle[data-category="'+category+'"]').checked;

function parseChapters(text) {
  let result=[], title='Inleiding', lines=[], fence=null;
  for (const line of text.match(/[^\n]*\n|[^\n]+$/g) || []) {
    const marker = line.match(/^\s{0,3}(`{3,}|~{3,})/);
    if (marker) {
      if (!fence) fence=marker[1];
      else if (marker[1][0]===fence[0] && marker[1].length>=fence.length) fence=null;
    }
    const heading = !fence && line.match(/^#\s+(.+?)\s*#*\s*$/);
    if (heading) {
      if (lines.length) result.push({key:String(result.length), title, text:lines.join('')});
      title=heading[1].trim(); lines=[];
    }
    lines.push(line);
  }
  if (lines.length) result.push({key:String(result.length), title, text:lines.join('')});
  return result;
}

function selectedDocuments() {
  const result=[];
  if (isEnabled('enterprise') && !files.enterprise.some(f=>f.selected) && remote.text && remote.selected.size) {
    result.push({name:'Enterprise-architectuur-selectie.md', category:'enterprise', url:remote.url,
      sha256:remote.sha256, retrieved_at:remote.retrieved_at,
      chapters:remote.chapters.filter(c=>remote.selected.has(c.key)).map(c=>c.title)});
  }
  for (const [category,list] of Object.entries(files)) {
    if (isEnabled(category)) for (const entry of list) if (entry.selected) {
      result.push({name:entry.file.name, size:entry.file.size, category, sha256:entry.sha256 || null,
        analysis:category==='enterprise' ? 'Catalogus/kader, niet als projectvraag gebruikt' : entry.reading ? 'Inhoud wordt gelezen' : entry.error || 'Inhoud lokaal gelezen'});
    }
  }
  return result;
}
function selectedText() { return remote.chapters.filter(c=>remote.selected.has(c.key)).map(c=>c.text).join('\n\n'); }

function selectedContexts() {
  const contexts = [{source:'Projectonderwerp en afbakening', text:$('project-name').value+'\n'+$('project-goals').value}];
  for (const [category,list] of Object.entries(files)) {
    if (category==='enterprise' || !isEnabled(category)) continue;
    for (const entry of list) if (entry.selected) {
      contexts.push({source:'Bestandsnaam: '+entry.file.name, text:entry.file.name});
      if (!entry.reading && !entry.error) contexts.push(...entry.contexts);
    }
  }
  return contexts;
}

function blockChoice(block, adviceMap, related, selectedIds) {
  const row=document.createElement('div'); row.className='block-choice'; row.dataset.blockId=block.id;
  const label=document.createElement('label'), check=document.createElement('input');
  check.type='checkbox'; check.checked=selectedIds.has(block.id); check.dataset.blockId=block.id;
  check.addEventListener('change',()=>{blockOverrides[block.id]=check.checked; render();});
  label.append(check,document.createTextNode(block.name)); row.append(label);
  const layer=document.createElement('small');
  layer.textContent=block.layer+(Object.hasOwn(blockOverrides,block.id)?' · Zelf aangepast':adviceMap.has(block.id)||related.has(block.id)?' · Geadviseerd gebruik':' · Niet automatisch geadviseerd'); row.append(layer);
  if (block.type==='ABB' && adviceMap.has(block.id)) {
    const evidence=adviceMap.get(block.id).evidence;
    const reason=document.createElement('small');
    reason.textContent='Aanleiding: '+evidence.map(match=>match.source+' — '+match.terms.join(', ')).join('; '); row.append(reason);
    const details=document.createElement('details'), summary=document.createElement('summary');
    summary.textContent='Waarom dit advies?'; details.append(summary);
    for (const match of evidence) {
      const quote=document.createElement('blockquote'); quote.textContent=match.source+': “'+match.excerpt+'”'; details.append(quote);
    }
    const mapping=document.createElement('code'); mapping.textContent='Bronmapping: '+block.quote+' ('+block.section+', regel '+block.line+')'; details.append(mapping); row.append(details);
  } else if (block.type==='SBB') {
    const parents=catalogue.abbs.filter(abb=>block.abb_ids.includes(abb.id) && selectedIds.has(abb.id));
    const reason=document.createElement('small'); reason.textContent='Bronmapping bij: '+(parents.map(abb=>abb.name).join('; ') || 'handmatige keuze; bijpassende ABB beoordelen'); row.append(reason);
  }
  return row;
}

function renderBuildingBlocks() {
  const advice=BuildingBlockAdvice.recommend(catalogue, selectedContexts());
  buildingBlocks=BuildingBlockAdvice.selection(catalogue, advice, blockOverrides);
  const selectedIds=new Set(buildingBlocks.selected.map(block=>block.id));
  const adviceMap=new Map(advice.map(item=>[item.id,item]));
  const related=new Set(catalogue.abbs.filter(abb=>selectedIds.has(abb.id)).flatMap(abb=>abb.sbb_ids));
  for (const [type,blocks] of [['abb',catalogue.abbs],['sbb',catalogue.sbbs]]) {
    const visible=$(type+'-list'), other=$(type+'-other'); visible.replaceChildren(); other.replaceChildren();
    for (const block of blocks) {
      const isVisible=adviceMap.has(block.id)||related.has(block.id)||Object.hasOwn(blockOverrides,block.id);
      (isVisible?visible:other).append(blockChoice(block,adviceMap,related,selectedIds));
    }
    if (!visible.children.length) {
      const empty=document.createElement('p'); empty.className='empty'; empty.textContent='Vul een onderwerp in of voeg documenten toe voor automatisch advies.'; visible.append(empty);
    }
  }
  const warnings=[], reading=[];
  for (const [category,list] of Object.entries(files)) {
    if (category==='enterprise'||!isEnabled(category)) continue;
    for (const entry of list) if (entry.selected) {
      if (entry.reading) reading.push(entry.file.name);
      if (entry.error) warnings.push(entry.file.name+': '+entry.error+' Alleen de bestandsnaam is gebruikt.');
      for (const warning of entry.warnings) warnings.push(entry.file.name+': '+warning);
    }
  }
  $('blocks-progress').textContent=reading.length?'Documentinhoud wordt lokaal gelezen; advies is voorlopig: '+reading.join(', '):buildingBlocks.selected.length?buildingBlocks.selected.filter(b=>b.type==='ABB').length+' ABB’s · '+buildingBlocks.selected.filter(b=>b.type==='SBB').length+' SBB’s geselecteerd.':'Advies verschijnt automatisch zodra er relevante projectcontext is.';
  $('blocks-warnings').replaceChildren();
  for (const warning of warnings) { const note=document.createElement('p'); note.className='block-warning'; note.textContent=warning; $('blocks-warnings').append(note); }
  buildingBlocks.warnings=warnings; buildingBlocks.analysis_pending=reading;
  const source=catalogue.source; $('blocks-provenance').replaceChildren();
  const link=document.createElement('a'); link.href=source.url; link.target='_blank'; link.rel='noopener noreferrer'; link.textContent='ABB/SBB-mapping in enterprise architectuur ↗';
  $('blocks-provenance').append(link,document.createTextNode(' · momentopname '+source.retrieved_at.slice(0,10)+' · '+source.sha256.slice(0,12)));
}

function render() {
  const docs=selectedDocuments();
  const enabled=[...document.querySelectorAll('.source-toggle:checked')].map(c=>c.dataset.category);
  const missing=enabled.filter(c=>!docs.some(d=>d.category===c));
  $('document-count').textContent=docs.length; $('category-count').textContent=enabled.length; $('missing-count').textContent=missing.length;
  for (const input of document.querySelectorAll('input[type=file]')) input.disabled=!isEnabled(input.dataset.category);
  $('load-enterprise').disabled=!isEnabled('enterprise')||busy;
  for (const input of $('chapter-list').querySelectorAll('input')) input.disabled=!isEnabled('enterprise');
  for (const [category,list] of Object.entries(files)) {
    const container=$(category+'-files'); container.replaceChildren();
    for (const entry of list) {
      const label=document.createElement('label'), check=document.createElement('input');
      check.type='checkbox'; check.checked=entry.selected; check.disabled=!isEnabled(category);
      check.addEventListener('change',()=>{entry.selected=check.checked;render();});
      label.append(check,document.createTextNode(entry.file.name)); container.append(label);
      if (category!=='enterprise') {
        const status=document.createElement('span'); status.className='reading-status';
        status.textContent=entry.reading?'Inhoud wordt lokaal gelezen…':entry.error?'Inhoud niet gelezen; zie toelichting bij bouwblokken.':'Inhoud lokaal gelezen voor bouwblokkenadvies.'; container.append(status);
      }
    }
  }
  $('selected-sources').replaceChildren();
  docs.forEach((entry,index)=>{
    const row=document.createElement('div'); row.className='source-row';
    const code=document.createElement('code'); code.textContent='B'+String(index).padStart(2,'0');
    const name=document.createElement('span'); name.textContent=entry.name+(entry.chapters?' · '+entry.chapters.length+' hoofdstukken':'');
    row.append(code,name); $('selected-sources').append(row);
  });
  const message=$('selection-message'); const oversized=docs.some(d=>d.chapters)&&selectedText().length>155000;
  message.classList.toggle('warning',missing.length>0||!docs.length||oversized);
  message.textContent=missing.length?'Nog inhoud nodig voor: '+missing.map(c=>categories[c]).join('; '):!docs.length?'Selecteer een bron en voeg de inhoud toe.':oversized?'De hoofdstukselectie is groter dan 155.000 tekens. Kies minder hoofdstukken voor AI-generatie.':'Je bronselectie is samengesteld. Bewaar je selectie om hiermee verder te werken.';
  $('enterprise-status').textContent=remote.text?(isEnabled('enterprise')?'Geselecteerd':'Niet geselecteerd')+' · '+remote.selected.size+' hoofdstukken · '+selectedText().length.toLocaleString('nl-NL')+' tekens':files.enterprise.some(f=>f.selected)?'Eigen versie toegevoegd':'Openbare bron nog niet opgehaald';
  renderBuildingBlocks();
  if(typeof PSA!=='undefined')PSA.checkFreshness();
}

document.querySelectorAll('.source-toggle').forEach(check=>check.addEventListener('change',render));
document.querySelectorAll('input[type=file]').forEach(input=>input.addEventListener('change',()=>{
  const category=input.dataset.category;
  files[category]=[...input.files].map(file=>({file,selected:true,reading:true,contexts:[],warnings:[],error:null}));
  render();
  for (const entry of files[category]) {
    (async()=>{
      try {
        const result=await DocumentReader.read(entry.file); entry.contexts=result.contexts; entry.warnings=result.warnings;entry.pages=result.pages||1;
      } catch (error) { entry.error=error.message || 'Dit bestand kon niet worden gelezen.'; }
      finally { entry.reading=false; render(); }
    })();
  }
}));
let inputTimer;
for (const field of [$('project-name'),$('project-goals')]) field.addEventListener('input',()=>{clearTimeout(inputTimer);inputTimer=setTimeout(render,250);});
$('reset-blocks').addEventListener('click',()=>{for(const key of Object.keys(blockOverrides))delete blockOverrides[key];render();});

$('load-enterprise').addEventListener('click',async()=>{
  busy=true; render(); const message=$('enterprise-message'); message.textContent='Openbare bron ophalen…';
  const controller=new AbortController(); const timer=setTimeout(()=>controller.abort(),30000);
  try {
    const response=await fetch('https://raw.githubusercontent.com/ivorstenbosch-maker/EnterpriseArchitectuurCG/main/Enterprisearchitectuur-GPT.md',{signal:controller.signal,credentials:'omit'});
    if (!response.ok) throw Error('HTTP '+response.status);
    const buffer=await response.arrayBuffer(); if (buffer.byteLength>3000000) throw Error('Bron te groot');
    const text=new TextDecoder('utf-8',{fatal:true}).decode(buffer);
    if (!text.startsWith('# ')||!text.slice(0,1000).includes('Enterprise Architectuur')) throw Error('Onverwacht bronformaat');
    let digest=null;
    if (globalThis.crypto?.subtle) digest=[...new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(text)))].map(b=>b.toString(16).padStart(2,'0')).join('');
    remote.text=text; remote.chapters=parseChapters(text); remote.selected=new Set(remote.chapters.filter(c=>['Managementsamenvatting','Visie, principes, scope'].includes(c.title)).map(c=>c.key));
    remote.sha256=digest; remote.retrieved_at=new Date().toISOString(); $('chapter-list').replaceChildren();
    for (const chapter of remote.chapters) {
      const label=document.createElement('label'), checkbox=document.createElement('input');
      checkbox.type='checkbox'; checkbox.checked=remote.selected.has(chapter.key);
      checkbox.addEventListener('change',()=>{if(checkbox.checked)remote.selected.add(chapter.key);else remote.selected.delete(chapter.key);render();});
      label.append(checkbox,document.createTextNode(chapter.title)); $('chapter-list').append(label);
    }
    $('chapter-details').hidden=false; message.textContent='Bron opgehaald. Alleen de geselecteerde hoofdstukken worden meegenomen.'; $('load-enterprise').textContent='Bron vernieuwen ↻';
  } catch (error) { message.textContent='Ophalen is niet gelukt. Controleer je internetverbinding, of upload een eigen versie. Je bestaande selectie blijft bewaard.'; }
  finally {clearTimeout(timer);busy=false;render();}
});

$('download-selection').addEventListener('click',()=>{
  renderBuildingBlocks();
  const docs=selectedDocuments(); const selected=[...document.querySelectorAll('.source-toggle:checked')].map(c=>c.dataset.category);
  const manifest={project:$('project-name').value,goals:$('project-goals').value,type:$('project-type').value,created_at:new Date().toISOString(),
    sources:docs.map((d,i)=>({code:'B'+String(i).padStart(2,'0'),...d})),missing:selected.filter(c=>!docs.some(d=>d.category===c)).map(c=>categories[c]),
    building_blocks:buildingBlocks,output:{brand:document.querySelector('input[name=brand]:checked').value,destinations:[...document.querySelectorAll('input[name=destination]:checked')].map(input=>input.value)},horizon:{url:'https://rotterdam.horizzon.cloud/sites/8579a6d6-9680-4fee-959c-4793130eef6f/views/e059f7c1-e164-f111-bb43-025a1dd2f359',content_loaded:isEnabled('horizon')&&files.horizon.some(f=>f.selected&&!f.error&&!f.reading)},note:'Bronselectie en bouwblokkenadvies, geen gegenereerde projectstartarchitectuur. Lokale bestanden zijn niet opgenomen; adviesonderbouwing kan korte tekstfragmenten uit die bestanden bevatten.'};
  const url=URL.createObjectURL(new Blob([JSON.stringify(manifest,null,2)],{type:'application/json'}));
  const anchor=document.createElement('a'); anchor.href=url; anchor.download='bronselectie.json'; anchor.click(); setTimeout(()=>URL.revokeObjectURL(url),1000);
});
// Eerste render volgt na het initialiseren van de PSA-module.
