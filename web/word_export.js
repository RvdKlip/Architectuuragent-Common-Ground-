/* Genuine DOCX export, entirely local, using the same sections as preview and PDF. */
const WordExport = (() => {
  // XML 1.0 excludes these characters, including lone UTF-16 surrogates.
  // Keep tabs, line endings, accents and complete supplementary Unicode characters.
  function cleanText(value){
    return String(value??'').replace(/[\u0000-\u0008\u000B\u000C\u000E-\u001F\uD800-\uDFFF\uFFFE\uFFFF]/gu,'');
  }
  function filename(project,extension='docx'){
    let name=cleanText(project).normalize('NFC').replace(/[<>:"/\\|?*\u0000-\u001F\u007F-\u009F]/g,'_').trim();
    name=name.replace(/\.(docx|pdf|html)$/i,'').replace(/[. ]+$/g,'');
    name=[...name].slice(0,120).join('').replace(/[. ]+$/g,'')||'Projectarchitectuur';
    if(/^(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\.|$)/i.test(name))name='Project-'+name;
    return name+'.'+extension;
  }
  async function create(title, sections, brand, style, figures=[]) {
    title=cleanText(title);brand=cleanText(brand);
    const {Document, Paragraph, TextRun, HeadingLevel, Footer, Packer, PageNumber, ImageRun, PageOrientation, SectionType}=docx;
    const color=style.primary.replace('#',''),ink=style.ink.replace('#','');
    let children=[
      new Paragraph({text:title,heading:HeadingLevel.TITLE}),
      new Paragraph({children:[new TextRun({text:'CONCEPT — ter beoordeling · Huisstijl: '+brand,bold:true,color})],spacing:{after:240}})
    ];
    const documentSections=[];
    function section(content,landscape=false){
      return {properties:{type:SectionType.NEXT_PAGE,page:{size:{width:11906,height:16838,orientation:landscape?PageOrientation.LANDSCAPE:PageOrientation.PORTRAIT},margin:{top:850,right:850,bottom:850,left:850}}},
        footers:{default:new Footer({children:[new Paragraph({children:[new TextRun({text:brand+' | CONCEPT | ',color,size:16}),new TextRun({children:[PageNumber.CURRENT],color,size:16})]})]})},children:content};
    }
    for(const [index,[heading,lines]] of sections.entries()){
      children.push(new Paragraph({text:cleanText(heading),heading:HeadingLevel.HEADING_1}));
      for(const line of lines){
        const runs=cleanText(line).split(/\r\n|\r|\n/).map((text,index)=>new TextRun({text,break:index?1:0}));
        children.push(new Paragraph({children:runs,spacing:{after:120}}));
      }
      for(const figure of figures.filter(f=>f.chapter===index+1)){
        if(children.length){documentSections.push(section(children));children=[];}
        const bytes=Uint8Array.from(atob(figure.png.split(',')[1]),c=>c.charCodeAt(0));
        const scale=Math.min(1000/figure.width,560/figure.height);
        documentSections.push(section([
          new Paragraph({children:[new TextRun({text:cleanText(figure.title),bold:true,color,size:28})]}),
          new Paragraph({alignment:docx.AlignmentType.CENTER,children:[new ImageRun({type:'png',data:bytes,transformation:{width:Math.round(figure.width*scale),height:Math.round(figure.height*scale)},altText:{title:cleanText(figure.title),description:cleanText(figure.caption),name:'Architectuurplaat'}})]}),
          new Paragraph({children:[new TextRun({text:cleanText(figure.caption),italics:true,size:16})]})
        ],true));
      }
    }
    if(children.length)documentSections.push(section(children));
    const document=new Document({
      creator:'Architectuuragent',title,description:'Concept-projectarchitectuur — '+brand,
      styles:{default:{document:{run:{font:'Arial',size:22,color:ink},paragraph:{spacing:{line:276}}},
        title:{run:{font:'Arial',size:44,bold:true,color}},
        heading1:{run:{font:'Arial',size:30,bold:true,color},paragraph:{spacing:{before:280,after:160},keepNext:true}}}},
      sections:documentSections
    });
    return Packer.toBlob(document);
  }
  return {create,filename};
})();
