/* Deterministic architecture figures. Only supplied relationships become arrows. */
const ArchitectureFigures=(()=>{
  const clean=value=>String(value??'').replace(/[\u0000-\u0008\u000B\u000C\u000E-\u001F\uD800-\uDFFF\uFFFE\uFFFF]/gu,'');
  const esc=value=>clean(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&apos;'}[c]));
  function wrap(value,limit){
    const lines=[];
    for(const paragraph of clean(value).split(/\r?\n/)){
      let line='';
      for(const word of paragraph.split(/\s+/).filter(Boolean)){
        if(line&&(line+' '+word).length>limit){lines.push(line);line='';}
        if(word.length>limit){if(line){lines.push(line);line='';}const chars=[...word];while(chars.length>limit)lines.push(chars.splice(0,limit).join(''));line=chars.join('');}
        else line+=(line?' ':'')+word;
      }
      lines.push(line);
    }
    return lines;
  }
  function models(plan,reference){
    const result=[];
    for(const [kind,layout] of Object.entries(reference.layouts)){
      const supplied=(plan.diagrams||[]).filter(d=>d.kind===kind);
      if(supplied.length){for(const d of supplied)result.push({...d,chapter:layout.chapter});}
      else result.push({kind,chapter:layout.chapter,title:layout.title,service_id:'',
        nodes:layout.groups.map((group,i)=>({id:'pending-'+i,label:'Nog te bepalen uit de projectbronnen',group,status:'unknown',evidence:[]})),edges:[]});
    }
    result.push({kind:'layers',chapter:5,title:'Oplossing in vijf lagen',nodes:[...plan.layers].sort((a,b)=>b.number-a.number).flatMap(layer=>
      (layer.components.length?layer.components:['Nog te bepalen uit de projectbronnen']).map((label,i)=>({id:'layer-'+layer.number+'-'+i,label,group:'L'+layer.number+' — '+layer.name,status:'unknown',evidence:[]}))),edges:[]});
    const steps=plan.flow_steps||[];
    result.push({kind:'flows',chapter:7,title:'Proces- en gegevensstromen',nodes:steps.map((label,i)=>({id:'step-'+i,label,group:'Stap '+(i+1),status:'unknown',evidence:[]})),edges:steps.slice(1).map((_,i)=>({from:'step-'+i,to:'step-'+(i+1),label:'',evidence:[]}))});
    return result.sort((a,b)=>a.chapter-b.chapter);
  }
  function render(model,plan,style,reference,index){
    const width=1440,margin=32,gap=20,primary=style.primary,ink=style.ink;
    const groups=[...new Set(model.nodes.map(n=>n.group))];
    const titleLines=wrap(model.title,85),projectLines=wrap(plan.title,110);
    const rows=[],cards=[],positions=new Map();let y=45+titleLines.length*34+projectLines.length*23+50;const headerY=y;
    function card(node,x,cy,w){
      const lines=wrap(node.label,Math.max(12,Math.floor((w-32)/11))),refs=wrap((node.evidence||[]).join(' · '),Math.max(12,Math.floor((w-32)/8)));
      const h=52+lines.length*24+(node.evidence?.length?refs.length*18:0);
      cards.push({node,x,y:cy,w,h,lines,refs});positions.set(node.id,{x,y:cy,w,h});return h;
    }
    if(model.kind==='layers'){
      for(const group of groups){
        const nodes=model.nodes.filter(n=>n.group===group),w=(width-margin*2-250-gap*2)/3;
        const start=y;let rowY=y+20,maxH=0;
        nodes.forEach((node,i)=>{if(i&&i%3===0){rowY+=maxH+14;maxH=0;}maxH=Math.max(maxH,card(node,margin+240+(i%3)*(w+gap),rowY,w));});
        const h=rowY-start+maxH+20;rows.push({x:margin,y:start,w:width-margin*2,h,label:group,side:true});y+=h+gap;
      }
    }else{
      for(let offset=0;offset<groups.length;offset+=4){
        const batch=groups.slice(offset,offset+4),w=(width-margin*2-gap*(batch.length-1))/batch.length;let maxH=0;
        batch.forEach((group,i)=>{const x=margin+i*(w+gap),heading=wrap(group,Math.max(12,Math.floor((w-32)/11)));let cy=y+28+heading.length*25;
          for(const node of model.nodes.filter(n=>n.group===group))cy+=card(node,x+12,cy,w-24)+14;
          const h=Math.max(170,cy-y+4);maxH=Math.max(maxH,h);rows.push({x,y,w,h,label:group,side:false});});
        y+=maxH+gap;
      }
    }
    const height=Math.max(y+112+model.edges.length*28,380),marker='arrow-'+index;
    const text=(x,ty,value,size=20,bold=false,color=ink)=>`<text x="${x}" y="${ty}" font-family="Arial,DejaVu Sans,sans-serif" font-size="${size}" font-weight="${bold?700:400}" fill="${esc(color)}">${esc(value)}</text>`;
    const box=(x,by,w,h,fill,stroke,extra='')=>`<rect x="${x}" y="${by}" width="${w}" height="${h}" rx="14" fill="${fill}" stroke="${stroke}" stroke-width="1.7" ${extra}/>`;
    let svg=`<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}"><defs><linearGradient id="bg-${index}" x2="0" y2="1"><stop stop-color="#F7FBFD"/><stop offset="1" stop-color="#EEF5F0"/></linearGradient><marker id="${marker}" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto"><path d="M0,0 L0,6 L9,3 z" fill="${primary}"/></marker></defs><rect width="100%" height="100%" fill="url(#bg-${index})"/>`;
    titleLines.forEach((line,i)=>{svg+=text(margin,44+i*34,line,29,true,primary);});
    projectLines.forEach((line,i)=>{svg+=text(margin,44+titleLines.length*34+i*23,line,21,true);});
    svg+=text(margin,headerY-25,'CONCEPT · '+(model.kind==='layers'?'Logische positionering; beschikbaarheid en koppelingen toetsen.':'Bestaand, voorstel en open punten blijven afzonderlijk herkenbaar.'),17,false);
    for(const row of rows){svg+=box(row.x,row.y,row.w,row.h,'#E5F1DE','#88B46B');
      if(row.side){svg+=`<circle cx="${row.x+35}" cy="${row.y+42}" r="23" fill="${primary}"/>`;svg+=text(row.x+28,row.y+50,row.label.match(/^L(\d)/)?.[1]||'',23,true,'#FFFFFF');}
      wrap(row.side?row.label.replace(/^L\d+\s*—\s*/,''):row.label,row.side?13:Math.max(12,Math.floor((row.w-32)/11))).forEach((line,i)=>{svg+=text(row.x+(row.side?72:16),row.y+32+i*25,line,21,true,primary);});}

    model.edges.forEach((edge,edgeIndex)=>{const a=positions.get(edge.from),b=positions.get(edge.to);if(!a||!b)throw Error('Diagramrelatie verwijst naar een onbekend onderdeel.');
      let path,labelX,labelY;
      if(Math.abs(a.x-b.x)<2){const x=a.x-8;path=`M${a.x},${a.y+a.h/2} H${x} V${b.y+b.h/2} H${b.x}`;labelX=a.x+8;labelY=y+edgeIndex*28;}
      else{const routeY=y+edgeIndex*28;const x1=a.x+a.w/2,x2=b.x+b.w/2;path=`M${x1},${a.y+a.h} V${routeY} H${x2} V${b.y+b.h}`;labelX=(x1+x2)/2;labelY=routeY-5;}
      svg+=`<path d="${path}" fill="none" stroke="${primary}" stroke-width="2" marker-end="url(#${marker})"/>`;
      if(edge.label)svg+=text(labelX,labelY,edge.label,14,false);
    });
    for(const c of cards){const status=reference.statuses[c.node.status]||reference.statuses.unknown;
      svg+=box(c.x,c.y,c.w,c.h,status.fill,status.color,c.node.status==='unknown'?'stroke-dasharray="6 4"':'');
      c.lines.forEach((line,i)=>{svg+=text(c.x+16,c.y+29+i*24,line,20,true);});
      const ty=c.y+35+c.lines.length*24;svg+=text(c.x+16,ty,status.label,14,false,status.color);
      if(c.node.evidence?.length)c.refs.forEach((line,i)=>{svg+=text(c.x+16,ty+19+i*18,line,13,false);});
    }
    Object.values(reference.statuses).forEach((status,i)=>{const x=margin+i*275;svg+=box(x,height-85,12,12,status.fill,status.color);svg+=text(x+20,height-74,status.label,13,false);});
    svg+=text(margin,height-31,model.edges.length?'Pijlen volgen het uitgewerkte model; controleer bronverwijzingen en besluitstatus.':'Geen relaties vastgesteld: verbindingslijnen zijn niet ingevuld op basis van aannames.',16,false);
    svg+='</svg>';
    const refs=[...new Set(model.nodes.flatMap(n=>n.evidence||[]).concat(model.edges.flatMap(e=>e.evidence||[])))];
    return {chapter:model.chapter,title:model.title,width,height,svg,caption:'Concept — '+model.title+'. '+(refs.length?'Bronnen: '+refs.join('; '):'Beschikbaarheid, toepasbaarheid en open punten toetsen aan de projectbronnen.')};
  }
  function dataUrl(svg){const bytes=new TextEncoder().encode(svg);let binary='';for(let i=0;i<bytes.length;i+=8192)binary+=String.fromCharCode(...bytes.subarray(i,i+8192));return 'data:image/svg+xml;base64,'+btoa(binary);}
  function generate(plan,style,reference){return models(plan,reference).map((m,i)=>{const f=render(m,plan,style,reference,i);return {...f,url:dataUrl(f.svg)};});}
  async function rasterize(figure){
    const image=new Image();image.src=figure.url;await image.decode();
    const canvas=document.createElement('canvas');canvas.width=figure.width;canvas.height=figure.height;
    const context=canvas.getContext('2d');context.fillStyle='#FFFFFF';context.fillRect(0,0,canvas.width,canvas.height);context.drawImage(image,0,0);
    return {...figure,png:canvas.toDataURL('image/png')};
  }
  return {generate,rasterize};
})();
