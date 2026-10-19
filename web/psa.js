/* Brongetrouw eerste concept en PDF-uitvoer; geen AI- of publicatieaanroep bij genereren. */
const PA = (() => {
  const styles = JSON.parse(document.getElementById('house-styles').textContent);
  const structure = JSON.parse(document.getElementById('architecture-structure').textContent);
  let current = null;
  const escape = text => String(text).replace(/[&<>"']/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
  function signature() {
    return JSON.stringify({project:$('project-name').value,goals:$('project-goals').value,type:$('project-type').value,
      documents:selectedDocuments(), chapters:[...remote.selected],
      files:Object.values(files).flat().map(entry=>({name:entry.file.name,size:entry.file.size,modified:entry.file.lastModified,selected:entry.selected}))});
  }
  function stale() { return !!current && current.signature !== signature(); }
  function checkFreshness() {
    if (!current) return;
    $('psa-stale').hidden=!stale(); $('publish-psa').disabled=stale()||!$('approve-publication').checked;
    if (stale()) $('approve-publication').checked=false;
  }
  function inputs() {
    const sources=[];
    if(isEnabled('enterprise') && !files.enterprise.some(entry=>entry.selected) && remote.text) {
      sources.push({filename:'Enterprise-architectuur-volledig.md',pages:1,text:selectedText(),contexts:[{source:'Enterprise-architectuur-volledig.md',text:selectedText()}]});
    }
    for(const [category,list] of Object.entries(files)) if(isEnabled(category)) for(const entry of list) if(entry.selected) {
      if(entry.reading) throw Error('Wacht totdat de documentinhoud is gelezen: '+entry.file.name);
      if(entry.error) throw Error('Deze geselecteerde bron is niet leesbaar: '+entry.file.name+'. Kies een leesbare versie of vink de bron uit.');
      sources.push({filename:entry.file.name,pages:entry.pages||1,text:entry.contexts.map(item=>item.text).join('\n'),contexts:entry.contexts});
    }
    const missing=[...document.querySelectorAll('.source-toggle:checked')].map(input=>input.dataset.category).filter(category=>!selectedDocuments().some(doc=>doc.category===category));
    if(missing.length) throw Error('Voeg eerst inhoud toe voor: '+missing.map(category=>categories[category]).join(', '));

    if(sources.length>97) throw Error('Selecteer maximaal 97 bronbestanden voor één PA.');
    if(!sources.length)throw Error('Selecteer minstens één leesbare bron.');
    return sources.map((source,index)=>({...source,key:'B'+String(index).padStart(2,'0')}));
  }
  function excerpts(source, subject) {
    const terms=subject.toLowerCase().match(/[\p{L}\p{N}]{5,}/gu)||[];
    const candidates=source.contexts.flatMap(context=>context.text.split(/\n\s*\n|(?<=[.!?])\s+/).map(text=>({text:text.trim(),source:context.source})));
    const ranked=candidates.filter(item=>item.text.length>=45 && !item.text.startsWith('|')).map(item=>({...item,score:terms.filter(term=>item.text.toLowerCase().includes(term)).length})).sort((a,b)=>b.score-a.score);
    return ranked.slice(0,2).map(item=>({...item,text:item.text.length>600?item.text.slice(0,600)+' […]':item.text}));
  }
  function makePlan(sources) {
    const project=$('project-name').value.trim(), goals=$('project-goals').value.trim();
    const changes=[];
    for(const source of sources) {
      for(const excerpt of excerpts(source,project+' '+goals)) {
        const page=excerpt.source.match(/ p\.(\d+)$/);
        changes.push({section:'Bronuitgangspunt — '+source.filename,change:'Bronfragment: “'+excerpt.text+'”',
          rationale:'Letterlijk fragment uit de geselecteerde bron. Interpretatie en toepasselijkheid moeten nog worden beoordeeld.',evidence:[source.key+(page?' p.'+page[1]:' tekst')]});
      }
    }
    const names={5:'Interactie',4:'Procesinrichting',3:'Connectiviteit',2:'Diensten',1:'Registraties'};
    const layers=[5,4,3,2,1].map(number=>({number,name:names[number],components:[]}));
    for(const layer of layers) if(!layer.components.length) layer.components=['Nog te bepalen op basis van inhoudelijke architectuurreview.'];
    const chapter_content=Object.fromEntries(structure.map(chapter=>[chapter.key,[{text:'Nog te bepalen op basis van bronanalyse en architectuurreview: '+chapter.requirements,evidence:[]}]]));
    return {chapter_content,title:'Projectarchitectuur — '+project,scope:goals,
      management_summary:'Eerste concept-PA voor '+project+'. Projectdoel en afbakening: '+goals+'. Samengesteld uit '+sources.length+' geselecteerde bronnen. De bronfragmenten zijn geordend voor review; er is geen semantische AI-synthese uitgevoerd.',
      changes,layers,flow_steps:['Bron en bronhouder: inhoudelijk vast te stellen','Verwerking en gegevensuitwisseling: inhoudelijk vast te stellen','Afnemer en gebruik: inhoudelijk vast te stellen'],
      adr:{title:'Voorgenomen architectuurkeuzes voor '+project,status:'Concept – ter besluitvorming',context:goals,
        decision:'VOORSTEL: beoordeel de geselecteerde bronuitgangspunten op toepasbaarheid voordat architectuurkeuzes worden vastgesteld.',principles:['Pas uitsluitend aantoonbaar geldende kaders uit de geselecteerde bronnen toe.'],
        implications:['Toepasselijkheid, gegevensstromen, verantwoordelijkheden en randvoorwaarden vragen inhoudelijke review.'],concerns:['De automatische conceptversie gebruikt bronfragmenten; volledige inhoudelijke synthese ontbreekt nog.'],implementation:['Controleer de bronverwijzingen.','Bespreek open besluiten met de verantwoordelijke architect.'],relation_existing_adrs:'Bestaande ADR’s en hun oorspronkelijke status blijven van kracht; er wordt geen herroeping verondersteld.'},
      decision_rules:[],open_decisions:['Welke bronhouders, koppelingen en gegevensstromen zijn nodig?','Welke aanvullende kaders en bestaande besluiten zijn op dit project van toepassing?'],
      assumptions:['Deze PA is een automatisch samengesteld eerste concept, geen vastgesteld architectuurbesluit.','De weergegeven bronfragmenten zijn een expliciete selectie, geen volledige samenvatting van alle documenten.','De huisstijlprofielen gebruiken kleur, typografie en documentstructuur; er zijn geen officiële logo’s of gelicenseerde huisstijlfonts meegeleverd.']};
  }
  function sections(plan,sources) {
    return structure.map(chapter=>{
      const key=chapter.key;
      const lines=(plan.chapter_content?.[key]||[]).map(entry=>entry.text+(entry.evidence.length?'\nBron: '+entry.evidence.join(', '):''));
      if(!lines.length&&!['summary','scope','layers','flows','decisions'].includes(key))lines.push('Nog te bepalen op basis van bronanalyse en architectuurreview: '+chapter.requirements);
      if(key==='summary')lines.unshift(plan.management_summary);
      else if(key==='scope'){
        lines.unshift('Opdracht en afbakening: '+plan.scope);
        for(const change of plan.changes)lines.push('Architectuurkeuze: '+change.section,change.change,'Onderbouwing: '+change.rationale,'Bron: '+change.evidence.join(', '));
        lines.push('Bronnen en herleidbaarheid:',...sources.map(source=>source.key+' — '+source.filename));
      }else if(key==='layers'){
        for(const layer of [...plan.layers].sort((a,b)=>b.number-a.number))lines.push('Laag '+layer.number+' — '+layer.name,...layer.components);
      }else if(key==='flows')lines.push(...plan.flow_steps);
      else if(key==='decisions'){
        const adr=plan.adr;
        lines.push('ADR — '+adr.title,'Status: '+adr.status,'Context: '+adr.context,'Besluit (voorgesteld): '+adr.decision);
        for(const [title,field] of [['Principe','principles'],['Implicatie','implications'],['Eventuele zorgen','concerns'],['Implementatie','implementation']])lines.push(title+':',...adr[field]);
        lines.push('Samenhang met bestaande ADR’s: '+adr.relation_existing_adrs,'Architectuurregels:',...plan.decision_rules.map(rule=>rule.id+': '+rule.rule+' — '+rule.status+'; bron: '+rule.evidence.join(', ')));
      }else if(key==='acceptance')lines.push('Open besluiten:',...plan.open_decisions,'Aannames en controlepunten:',...plan.assumptions);
      return [chapter.title,lines];
    });
  }

  function html(report,whole=true) {
    const style=styles[report.brand];
    const body='<h1 class="result-heading" style="color:'+style.primary+'">'+escape(report.plan.title)+'</h1><div class="result-banner" style="background:'+style.pale+';border-color:'+style.primary+'">CONCEPT — ter beoordeling · Huisstijl: '+escape(report.brand)+'</div>'+sections(report.plan,report.sources).map(([title,lines])=>'<section class="result-section"><h2 style="color:'+style.primary+'">'+escape(title)+'</h2>'+lines.map(line=>'<p>'+escape(line)+'</p>').join('')+'</section>').join('');
    if(!whole) return body;
    return '<!doctype html><html lang="nl"><head><meta charset="utf-8"><title>'+escape(report.plan.title)+'</title><style>body{font-family:'+style.font+';color:'+style.ink+';line-height:1.55;max-width:900px;margin:40px auto;padding:25px}h1{font-size:30px}h2{font-size:20px;break-after:avoid}p{white-space:pre-wrap}.result-banner{padding:15px;border-left:5px solid}.result-section{margin-top:24px}@media print{body{margin:0}section{break-inside:auto}}</style></head><body>'+body+'</body></html>';
  }
  function pdf(report) {
    const doc=new jspdf.jsPDF({unit:'mm',format:'a4'}),style=styles[report.brand];
    const color=hex=>[1,3,5].map(index=>parseInt(hex.slice(index,index+2),16));
    const primary=color(style.primary),ink=color(style.ink);let y=24;
    function newPage(){doc.addPage();y=24;}
    function text(value,size=10,bold=false){doc.setFont('helvetica',bold?'bold':'normal');doc.setFontSize(size);doc.setTextColor(...ink);const lines=doc.splitTextToSize(String(value).replace(/\u00a0/g,' '),174);for(const line of lines){if(y>272)newPage();doc.text(line,18,y);y+=size*.47;}y+=3;}
    doc.setFillColor(...primary);doc.rect(0,0,210,5,'F');text(report.plan.title,21,true);text('CONCEPT — ter beoordeling · Huisstijl: '+report.brand,10,true);
    for(const [title,lines] of sections(report.plan,report.sources)){if(y>254)newPage();y+=3;doc.setDrawColor(...primary);doc.line(18,y,192,y);y+=7;text(title,13,true);for(const line of lines)text(line);}
    const pages=doc.getNumberOfPages();for(let page=1;page<=pages;page++){doc.setPage(page);doc.setFillColor(...primary);doc.rect(0,0,210,5,'F');doc.setTextColor(...primary);doc.setFontSize(8);doc.text(report.brand+' | CONCEPT | '+page+'/'+pages,18,287);}
    return doc.output('arraybuffer');
  }
  function download(content,type,name){const url=URL.createObjectURL(new Blob([content],{type}));const link=document.createElement('a');link.href=url;link.download=name;link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
  function open(){ $('psa-options-error').textContent='';$('psa-dialog').showModal(); }
  $('generate-psa').addEventListener('click',open);$('change-psa-options').addEventListener('click',open);
  $('close-psa-dialog').addEventListener('click',()=>$('psa-dialog').close());
  $('psa-options').addEventListener('submit',async event=>{
    event.preventDefault();
    $('confirm-generate').disabled=true;
    try {
      if(!$('project-name').value.trim()||!$('project-goals').value.trim())throw Error('Vul eerst een projectnaam en doel/afbakening in.');
      const brand=document.querySelector('input[name=brand]:checked').value;
      const destinations=[...document.querySelectorAll('input[name=destination]:checked')].map(input=>input.value);
      if(!destinations.length)throw Error('Kies PDF, Confluence en/of Notion.');
      const sources=inputs(),sourceSignature=signature();let plan=makePlan(sources),method='Brongetrouw eerste concept zonder AI.';
      if($('generation-ai').checked){
        if(!$('generation-consent').checked)throw Error('Bevestig dat deze bronnen naar de ingestelde AI-dienst mogen.');
        let service;
        try{service=new URL($('generation-url').value);if(service.protocol!=='http:'||!['127.0.0.1','localhost'].includes(service.hostname)||service.port!=='8765'||service.username||service.password)throw Error();}
        catch(error){throw Error('Stel de lokale AI-service in: http://127.0.0.1:8765.');}
        if(!$('generation-token').value)throw Error('Vul de service-sleutel in. Deze wordt niet in het index-bestand bewaard.');
        $('psa-options-error').textContent='AI-concept wordt gemaakt uit de geselecteerde bronnen…';
        const response=await fetch(service.origin+'/generate',{method:'POST',headers:{'Content-Type':'application/json','Authorization':'Bearer '+$('generation-token').value},body:JSON.stringify({allow_ai:true,brand,project:$('project-name').value.trim(),goals:$('project-goals').value.trim(),sources:sources.map(source=>({key:source.key,filename:source.filename,pages:source.pages,text:source.contexts.map(context=>'['+source.key+(context.source.match(/ p\.(\d+)$/)?' p.'+context.source.match(/ p\.(\d+)$/)[1]:' tekst')+']\n'+context.text).join('\n\n')}))})});
        const result=await response.json();if(!response.ok)throw Error(result.error||'AI-generatie niet bevestigd.');
        if(!result.plan||!Array.isArray(result.plan.layers)||!result.plan.adr)throw Error('Geen geldige PA van de AI-service ontvangen.');
        plan=result.plan;method='AI-synthese van de geselecteerde bronnen — ter review.';
      }
      const candidate={brand,destinations,sources,plan,signature:sourceSignature};
      const preview=html(candidate,false);
      current=candidate;
      $('psa-preview').innerHTML=preview;$('psa-preview').style.color=styles[brand].ink;
      $('psa-result-meta').textContent='Huisstijl: '+brand+' · Gekozen uitvoer: '+destinations.join(', ')+' · '+method;
      $('download-psa-pdf').hidden=!destinations.includes('PDF');
      $('publication-section').hidden=!destinations.some(target=>target!=='PDF');
      $('approve-publication').checked=false;$('publish-psa').disabled=true;$('publication-results').replaceChildren();
      $('publication-status').textContent='Nog niet gepubliceerd. Gekozen: '+destinations.filter(target=>target!=='PDF').join(', ')+'. Stel de koppeling in en bevestig de review.';
      $('psa-stale').hidden=true;$('psa-result').hidden=false;checkFreshness();$('psa-dialog').close();$('psa-result').scrollIntoView({behavior:'smooth'});
    } catch(error){$('psa-options-error').textContent=error.message;}
    finally{$('confirm-generate').disabled=false;}
  });
  $('download-psa-pdf').addEventListener('click',()=>{if(current&&!stale())download(pdf(current),'application/pdf','PA-'+current.brand.replace(/ /g,'-')+'.pdf');else $('psa-stale').hidden=false;});
  $('download-psa-html').addEventListener('click',()=>{if(current&&!stale())download(html(current),'text/html','PA-'+current.brand.replace(/ /g,'-')+'.html');else $('psa-stale').hidden=false;});
  $('approve-publication').addEventListener('change',checkFreshness);
  $('publish-psa').addEventListener('click',async()=>{
    if(!current||stale()||!$('approve-publication').checked)return;
    const status=$('publication-status');let url;
    try{url=new URL($('publication-url').value);if(url.protocol!=='http:'||!['127.0.0.1','localhost'].includes(url.hostname)||url.port!=='8765'||url.username||url.password)throw Error();}
    catch(error){status.textContent='Nog niet gepubliceerd. Stel de lokale publicatieservice in: http://127.0.0.1:8765. Zie de README.';return;}
    if(!$('publication-token').value){status.textContent='Nog niet gepubliceerd. Vul de publicatieservice-sleutel in; platformtokens blijven op de server.';return;}
    $('publish-psa').disabled=true;status.textContent='Publicatie wordt aangevraagd…';
    try{
      const response=await fetch(url.origin+'/publish',{method:'POST',headers:{'Content-Type':'application/json','Authorization':'Bearer '+$('publication-token').value},body:JSON.stringify({plan:current.plan,brand:current.brand,sources:current.sources.map(source=>({key:source.key,filename:source.filename,pages:source.pages})),reviewed:true,destinations:current.destinations.filter(target=>target!=='PDF')})});
      const result=await response.json();if(!response.ok)throw Error(result.error||'Publicatie niet bevestigd.');
      $('publication-results').replaceChildren();let count=0;
      for(const [target,item] of Object.entries(result.results)){
        const line=document.createElement('p');
        if(item.status==='published'){
          const link=document.createElement('a');const targetUrl=new URL(item.url);if(targetUrl.protocol!=='https:')throw Error('Ongeldige publicatiebevestiging.');link.href=targetUrl.href;link.target='_blank';link.rel='noopener noreferrer';link.textContent=target+' — gepubliceerd ↗';line.append(link);count++;
        }else line.textContent=target+' — niet gepubliceerd: '+item.message;
        $('publication-results').append(line);
      }
      status.textContent=count+' publicatie(s) bevestigd. Controleer de status per bestemming.';
    }catch(error){status.textContent='Geen volledige publicatiebevestiging: '+error.message+' Controleer de bestemmingen voordat je opnieuw publiceert.';}
    finally{checkFreshness();}
  });
  return {checkFreshness,get current(){return current;},pdf,html};
})();
render();
if(isEnabled('enterprise'))loadEnterprise();
