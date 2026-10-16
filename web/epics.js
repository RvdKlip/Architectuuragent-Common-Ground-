/* Epic selection: read Notion via a local connector, or use an explicit source link. */
const Epic = (() => {
  const notionUrl='https://app.notion.com/p/platformvoordienstverlening/e9375da1960249bba23c49d038d3c888?v=2b078b5f4db4808da728000c21a96e11';
  let selected=null,items=[],cursor=null,revision=0;
  const status=text=>$('epic-status').textContent=text;
  function safeLink(value,provider){
    const url=new URL(value);
    const host=url.hostname.toLowerCase();
    const valid=provider==='notion'?['app.notion.com','notion.so','notion.site'].some(base=>host===base||host.endsWith('.'+base)):['teams.microsoft.com','teams.cloud.microsoft','teams.live.com'].includes(host);
    if(url.protocol!=='https:'||url.username||url.password||url.port||!valid)throw Error('Gebruik een geldige HTTPS-link naar '+(provider==='notion'?'Notion.':'Microsoft Teams.'));
    return url.href;
  }
  function refresh(){
    $('epic-selected').hidden=!selected;
    if(selected){$('epic-selected-title').textContent=selected.title;$('epic-selected-meta').textContent=(selected.provider==='notion'?'Notion':'Microsoft Teams')+' · '+(selected.text.trim()?'Beschrijving als bron opgenomen.':'Alleen een verwijzing; epicinhoud is niet ingelezen.')+' '+selected.url;}
    render();
  }
  function use(epic){
    selected=epic;
    if(!$('project-name').value.trim())$('project-name').value=epic.title;
    status('Epic geselecteerd. Je eigen projectnaam en afbakening blijven bewerkbaar.');refresh();
  }
  function options(){
    const select=$('epic-select'),previous=select.value,query=$('epic-search').value.toLocaleLowerCase('nl');select.replaceChildren();
    const empty=document.createElement('option');empty.value='';empty.textContent=items.length?'Selecteer een epic':'Geen epics geladen';select.append(empty);
    for(const item of items.filter(item=>item.title.toLocaleLowerCase('nl').includes(query))){const option=document.createElement('option');option.value=item.id;option.textContent=item.title;select.append(option);}
    select.value=previous;
  }
  async function service(path,payload){
    let url;
    try{url=new URL($('epic-service-url').value);if(url.protocol!=='http:'||!['127.0.0.1','localhost'].includes(url.hostname)||url.port!=='8765'||url.username||url.password)throw Error();}
    catch(error){throw Error('Start de lokale epicservice en gebruik http://127.0.0.1:8765.');}
    if(!$('epic-service-token').value)throw Error('Stel de Notion-koppeling en service-sleutel in, of voeg een epiclink met beschrijving toe.');
    const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),60000);
    try{
      const response=await fetch(url.origin+path,{method:'POST',signal:controller.signal,headers:{'Content-Type':'application/json','Authorization':'Bearer '+$('epic-service-token').value},body:JSON.stringify(payload)});
      const data=await response.json();if(!response.ok)throw Error(data.error||'Epics niet opgehaald.');return data;
    }catch(error){if(error.name==='TypeError'||error.name==='AbortError')throw Error('De lokale epicservice is niet bereikbaar. Start de service of gebruik een epiclink met beschrijving.');throw error;}
    finally{clearTimeout(timer);}
  }
  async function load(more){
    const ticket=++revision;$('epic-load').disabled=true;$('epic-more').disabled=true;status('Epics uit de ingestelde Notion-database ophalen…');
    try{const data=await service('/epics/list',{provider:'notion',cursor:more?cursor:null});if(ticket!==revision)return;
      if(!Array.isArray(data.epics))throw Error('Onverwachte respons van de epicservice.');
      const merged=new Map((more?items:[]).map(item=>[item.id,item]));for(const item of data.epics)merged.set(item.id,item);items=[...merged.values()];cursor=data.next_cursor||null;
      options();$('epic-more').hidden=!cursor;status(items.length+' epics geladen.'+(cursor?' Er zijn meer epics; kies Meer epics laden.':''));
    }catch(error){if(ticket===revision)status(error.message);}
    finally{$('epic-load').disabled=false;$('epic-more').disabled=false;}
  }
  $('epic-provider').addEventListener('change',()=>{
    revision++;selected=null;items=[];cursor=null;const provider=$('epic-provider').value;
    $('epic-fields').hidden=provider==='none';$('notion-epic-fields').hidden=provider!=='notion';$('epic-more').hidden=true;
    $('epic-open-source').href=provider==='notion'?notionUrl:'https://teams.microsoft.com/';$('epic-open-source').textContent=provider==='notion'?'Open de Notion-epiclijst ↗':'Open Microsoft Teams ↗';
    $('epic-link').value='';$('epic-title').value='';$('epic-description').value='';options();status('');refresh();
  });
  $('epic-load').addEventListener('click',()=>load(false));$('epic-more').addEventListener('click',()=>load(true));$('epic-search').addEventListener('input',options);
  $('epic-choose').addEventListener('click',async()=>{
    const item=items.find(item=>item.id===$('epic-select').value);if(!item){status('Selecteer eerst een epic uit de lijst.');return;}
    const ticket=++revision;$('epic-choose').disabled=true;status('Geselecteerde epic met inhoud ophalen…');
    try{const epic=await service('/epics/get',{provider:'notion',id:item.id});if(ticket!==revision)return;if(epic.provider!=='notion'||epic.id!==item.id||typeof epic.title!=='string'||typeof epic.text!=='string')throw Error('Onvolledige epicrespons.');epic.url=safeLink(epic.url,'notion');use({...epic,mode:'connector'});}
    catch(error){if(ticket===revision)status(error.message);}
    finally{$('epic-choose').disabled=false;}
  });
  $('epic-use-link').addEventListener('click',()=>{
    try{const provider=$('epic-provider').value;if(!['notion','teams'].includes(provider))throw Error('Kies Notion of Microsoft Teams.');const url=safeLink($('epic-link').value.trim(),provider),title=$('epic-title').value.trim(),text=$('epic-description').value.trim();if(!title)throw Error('Vul de naam van de epic in.');if(text.length>250000)throw Error('De epicbeschrijving is te groot (maximaal 250.000 tekens).');revision++;use({provider,id:url,url,title,text,mode:'link'});}
    catch(error){status(error.message);}
  });
  $('epic-remove').addEventListener('click',()=>{revision++;selected=null;status('Epic verwijderd uit de bronselectie.');refresh();});
  function sourceDocument(){
    if(!selected)return null;
    return {filename:'Geselecteerde-epic.md',pages:1,text:'# Epic — '+selected.title+'\n\nBron: '+selected.provider+'\nID: '+selected.id+'\nURL: '+selected.url+'\nInhoud: '+(selected.text.trim()?'Beschrijving toegevoegd':'Alleen verwijzing; inhoud niet ingelezen')+'\n\n'+selected.text};
  }
  return {get current(){return selected;},document:sourceDocument,safeLink};
})();
