/* Genuine DOCX export, entirely local, using the same sections as preview and PDF. */
const WordExport = (() => {
  async function create(title, sections, brand, style) {
    const {Document, Paragraph, TextRun, HeadingLevel, Footer, Packer, PageNumber}=docx;
    const color=style.primary.replace('#',''),ink=style.ink.replace('#','');
    const children=[
      new Paragraph({text:title,heading:HeadingLevel.TITLE}),
      new Paragraph({children:[new TextRun({text:'CONCEPT — ter beoordeling · Huisstijl: '+brand,bold:true,color})],spacing:{after:240}})
    ];
    for(const [heading,lines] of sections){
      children.push(new Paragraph({text:heading,heading:HeadingLevel.HEADING_1}));
      for(const line of lines){
        const runs=String(line).split('\n').map((text,index)=>new TextRun({text,break:index?1:0}));
        children.push(new Paragraph({children:runs,spacing:{after:120}}));
      }
    }
    const document=new Document({
      creator:'Architectuuragent',title,description:'Concept-projectarchitectuur — '+brand,
      styles:{default:{document:{run:{font:'Arial',size:22,color:ink},paragraph:{spacing:{line:276}}},
        title:{run:{font:'Arial',size:44,bold:true,color}},
        heading1:{run:{font:'Arial',size:30,bold:true,color},paragraph:{spacing:{before:280,after:160},keepNext:true}}}},
      sections:[{properties:{page:{size:{width:11906,height:16838},margin:{top:1134,right:1134,bottom:1134,left:1134}}},
        footers:{default:new Footer({children:[new Paragraph({children:[new TextRun({text:brand+' | CONCEPT | ',color,size:16}),new TextRun({children:[PageNumber.CURRENT],color,size:16})]})]})},children}]
    });
    return Packer.toBlob(document);
  }
  return {create};
})();
