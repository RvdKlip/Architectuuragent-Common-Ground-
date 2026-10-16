/* Lees uitsluitend expliciet geclassificeerde bouwstenen uit een aangeleverde Horizzon-export. */
const HorizzonCatalogue = (() => {
  function csv(text) {
    const first=text.split(/\r?\n/)[0], delimiter=(first.match(/;/g)||[]).length>(first.match(/,/g)||[]).length?';':',';
    const rows=[];let row=[],cell='',quoted=false;
    for(let i=0;i<text.length;i++) {
      const c=text[i];
      if(c==='"'){if(quoted&&text[i+1]==='"'){cell+='"';i++;}else quoted=!quoted;}
      else if(!quoted&&(c===delimiter||c==='\n')){row.push(cell.replace(/\r$/,''));cell='';if(c==='\n'){rows.push(row);row=[];}}
      else cell+=c;
    }
    if(quoted)throw Error('CSV bevat een niet-afgesloten aanhalingsteken.');
    row.push(cell.replace(/\r$/,''));if(row.some(Boolean))rows.push(row);
    const header=rows.shift()||[];
    return rows.filter(row=>row.some(Boolean)).map(row=>Object.fromEntries(header.map((key,index)=>[key,row[index]||''])));
  }
  function parse(text, filename) {
    text=text.replace(/^\uFEFF/,'');
    const data=filename.toLowerCase().endsWith('.json')?JSON.parse(text):csv(text);
    const rows=Array.isArray(data)?data:data.building_blocks||data.objects;
    if(!Array.isArray(rows)||rows.length>10000)throw Error('Gebruik een CSV of JSON-lijst met maximaal 10.000 bouwstenen.');
    const blocks=[],ids=new Set();let skipped=0;
    const norm=value=>String(value).trim().toLowerCase().replace(/[\s_-]/g,'');
    for(const raw of rows){
      if(!raw||typeof raw!=='object'){skipped++;continue;}
      const row=Object.fromEntries(Object.entries(raw).map(([key,value])=>[norm(key),value]));
      const get=(...keys)=>{for(const key of keys)if(row[key]!=null&&String(row[key]).trim())return String(row[key]).trim();return '';};
      const value=norm(get('buildingblocktype','bouwsteentype','classification','classificatie','type'));
      const type=['abb','architecturebuildingblock','architecturebuildingblocks'].includes(value)?'ABB':['sbb','solutionbuildingblock','solutionbuildingblocks'].includes(value)?'SBB':null;
      const id=get('id','objectid','identifier'),name=get('name','naam');
      if(!type||!id||!name){skipped++;continue;}
      if(ids.has(id))throw Error('Dubbel object-ID in de export: '+id);
      ids.add(id);blocks.push({id,name,type,description:get('description','beschrijving','documentation','documentatie'),layer:get('layer','laag')});
    }
    if(!blocks.length)throw Error('Geen ABB’s/SBB’s gevonden. Gebruik id, name en type (ABB of SBB); andere objecttypen worden niet als bouwsteen aangenomen.');
    return {blocks,skipped};
  }
  return {parse};
})();
if(typeof module!=='undefined')module.exports=HorizzonCatalogue;
