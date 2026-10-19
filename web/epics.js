/* Read epic details from a link through the authenticated local service. */
const Epic = (() => {
  let selected=null,revision=0;
  function status(text){$('epic-status').textContent=text;$('epic-status').hidden=!text;}
  function refresh(){
    $('epic-selected').hidden=!selected;
    $('epic-title').value=selected?.title||'';
    $('epic-description').value=selected?.text||'';
    if(selected){$('epic-selected-title').textContent=selected.title;$('epic-selected-meta').textContent='Inhoud opgehaald uit '+selected.url;}
    render();
  }
  $('epic-link').addEventListener('input',()=>{revision++;selected=null;status('');refresh();});
  $('epic-use-link').addEventListener('click',async()=>{
    const ticket=++revision;selected=null;refresh();status('Epic ophalen…');$('epic-use-link').disabled=true;
    const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),60000);
    try{
      const link=new URL($('epic-link').value.trim());
      if(link.protocol!=='https:'||link.username||link.password||link.port)throw Error('Gebruik een geldige HTTPS-link naar de epic.');
      const service=new URL($('epic-service-url').value);
      if(service.protocol!=='http:'||!['127.0.0.1','localhost'].includes(service.hostname)||service.port!=='8765'||service.username||service.password)throw Error('Gebruik de lokale epicservice http://127.0.0.1:8765.');
      if(!$('epic-service-token').value){$('epic-connection').open=true;throw Error('Epic niet opgehaald: de koppeling is niet ingesteld. Start de lokale epicservice met toegang tot Notion of Teams en vul hieronder de service-sleutel in. De GitHub-website kan jouw ingelogde Notion-sessie niet gebruiken.');}
      const response=await fetch(service.origin+'/epics/get',{method:'POST',signal:controller.signal,headers:{'Content-Type':'application/json','Authorization':'Bearer '+$('epic-service-token').value},body:JSON.stringify({url:link.href})});
      const epic=await response.json();if(ticket!==revision)return;
      if(!response.ok)throw Error(epic.error||'Epic niet opgehaald.');
      if(!['notion','teams'].includes(epic.provider)||typeof epic.title!=='string'||!epic.title.trim()||typeof epic.text!=='string'||!epic.text.trim()||epic.text.length>250000)throw Error('Geen leesbare epicnaam en beschrijving ontvangen.');
      selected={...epic,url:link.href};
      if(!$('project-name').value.trim())$('project-name').value=epic.title;
      status('Naam en beschrijving opgehaald.');refresh();
    }catch(error){if(ticket===revision){$('epic-connection').open=true;status(['TypeError','AbortError'].includes(error.name)?'De lokale epicservice is niet bereikbaar. Controleer of deze draait en toegang tot de epic heeft.':error.message);$('epic-status').scrollIntoView({block:'nearest'});}}
    finally{clearTimeout(timer);$('epic-use-link').disabled=false;}
  });
  $('epic-remove').addEventListener('click',()=>{revision++;selected=null;status('Epic verwijderd.');refresh();});
  function sourceDocument(){return selected?{filename:'Geselecteerde-epic.md',pages:1,text:'# Epic — '+selected.title+'\n\nBron: '+selected.provider+'\nID: '+selected.id+'\nURL: '+selected.url+'\n\n'+selected.text}:null;}
  return {get current(){return selected;},document:sourceDocument};
})();
