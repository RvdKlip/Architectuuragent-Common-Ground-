"""Validate the local browser DOCX exporter using a real Word reader."""
import json
from pathlib import Path
import shutil
import subprocess
from zipfile import ZipFile

from docx import Document
from lxml import etree
import pytest

from architect_agent.output import STYLES, report_sections
from architect_agent.schemas import ARCHITECTURE_STRUCTURE
from architect_agent.sources import Source

ROOT = Path(__file__).resolve().parents[1]
pytestmark = pytest.mark.skipif(shutil.which('node') is None, reason='Browserexportcontrole vereist Node.js.')
LOAD_EXPORTER = '''
const fs=require('fs'),vm=require('vm');
vm.runInThisContext(fs.readFileSync('assets/vendor/docx/docx.iife.js','utf8'));
vm.runInThisContext(fs.readFileSync('web/word_export.js','utf8'));
'''


def export(tmp_path, title, sections, brand='Rotterdam',figures=None):
    target = tmp_path/'architectuur.docx'
    script = LOAD_EXPORTER + '''
(async()=>{const data=JSON.parse(fs.readFileSync(0,'utf8'));
 const blob=await WordExport.create(data.title,data.sections,data.brand,data.style,data.figures||[]);
 fs.writeFileSync(process.argv[1],Buffer.from(await blob.arrayBuffer()));
})().catch(e=>{console.error(e);process.exit(1)});
'''
    subprocess.run(['node','-e',script,str(target)],cwd=ROOT,input=json.dumps({
        'title':title,'sections':sections,'brand':brand,'style':STYLES[brand],'figures':figures or []
    }),text=True,check=True,capture_output=True)
    return target


def validate_package(target):
    with ZipFile(target) as archive:
        assert archive.testzip() is None
        assert 'word/document.xml' in archive.namelist()
        for name in archive.namelist():
            if name.endswith(('.xml','.rels')):
                etree.fromstring(archive.read(name))


@pytest.mark.parametrize('brand', ['Rotterdam', 'Common Ground'])
def test_browser_docx_preserves_every_section_and_unicode(tmp_path, brand):
    plan = json.loads((ROOT/'examples/example_plan.json').read_text())
    sources = [Source(f'B{i:02}',f'bron{i}.pdf','Volledige bron niet publiceren',30,'pdf') for i in range(3)]
    sections = report_sections(plan, sources)
    sections[2][1].append('Letterlijke tekst: <voorstel> & “klant” — één.')
    target = export(tmp_path,plan['title'],sections,brand)
    validate_package(target)
    doc = Document(target)
    assert doc.paragraphs[0].text == plan['title']
    assert [p.text for p in doc.paragraphs if p.style.name=='Heading 1'] == [c['title'] for c in ARCHITECTURE_STRUCTURE]
    text='\n'.join(p.text for p in doc.paragraphs)
    assert all(line in text for title,lines in sections for line in lines)
    assert 'Letterlijke tekst: <voorstel> & “klant” — één.' in text
    assert all(source.text not in text for source in sources)
    assert brand in text and brand in doc.sections[0].footer.paragraphs[0].text
    assert str(next(p.style for p in doc.paragraphs if p.style.name == 'Heading 1').font.color.rgb) == STYLES[brand]['primary'][1:]


def test_hidden_source_characters_cannot_corrupt_word_package(tmp_path):
    invalid=''.join(chr(n) for n in range(32) if n not in (9,10,13))+'\ufffe\uffff\udfff\ud800'
    target=export(tmp_path,'Project'+invalid+'naam',[
        ['Hoofdstuk'+invalid+'titel',['Bron'+invalid+'tekst','Accenten: één. Emoji: 🏛️. & < >','Regel één\r\nRegel twee\nRegel drie\tmet tab']]
    ])
    validate_package(target)
    doc=Document(target)
    assert doc.paragraphs[0].text=='Projectnaam'
    assert doc.paragraphs[2].text=='Hoofdstuktitel'
    assert doc.paragraphs[3].text=='Brontekst'
    assert 'Emoji: 🏛️.' in doc.paragraphs[4].text
    assert doc.paragraphs[5].text=='Regel één\nRegel twee\nRegel drie\tmet tab'


def test_download_names_use_project_name_and_are_windows_compatible():
    cases=[
        ['Signaalmanagement','docx','Signaalmanagement.docx'],
        ['Signaalmanagement','pdf','Signaalmanagement.pdf'],
        ['Signaalmanagement','html','Signaalmanagement.html'],
        ['  Mijn project: fase 1/2?  ','docx','Mijn project_ fase 1_2_.docx'],
        ['één project','docx','één project.docx'],
        ['CON','docx','Project-CON.docx'],
        ['..','docx','Projectarchitectuur.docx'],
        ['Mijn project.docx','docx','Mijn project.docx'],
        ['Project\nnaam','docx','Project_naam.docx'],
        ['Project'+chr(0)+'naam','docx','Projectnaam.docx'],
    ]
    script=LOAD_EXPORTER+"const cases=JSON.parse(fs.readFileSync(0,'utf8'));process.stdout.write(JSON.stringify(cases.map(([name,ext])=>WordExport.filename(name,ext))));"
    result=subprocess.run(['node','-e',script],cwd=ROOT,input=json.dumps(cases),text=True,capture_output=True,check=True)
    assert json.loads(result.stdout)==[expected for _,_,expected in cases]


def test_browser_word_embeds_figure_and_keeps_landscape_page_valid(tmp_path):
    import base64
    from architect_agent.figures import report_figures
    plan=json.loads((ROOT/'examples/example_plan.json').read_text())
    sources=[Source(f'B{i:02}',f'bron{i}.pdf','Testbron',30,'pdf') for i in range(3)]
    figure=report_figures(plan,'Rotterdam')[0]
    picture={key:figure[key] for key in ('chapter','title','caption','width','height')}
    picture['png']='data:image/png;base64,'+base64.b64encode(figure['png']).decode()
    target=export(tmp_path,plan['title'],report_sections(plan,sources),figures=[picture])
    validate_package(target)
    doc=Document(target)
    assert len(doc.inline_shapes)==1
    assert sum(section.page_width>section.page_height for section in doc.sections)==1
    with ZipFile(target) as archive:
        assert any(name.startswith('word/media/') and name.endswith('.png') for name in archive.namelist())
