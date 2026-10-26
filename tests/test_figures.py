"""Plates must describe the selected design and survive the actual exports."""
import copy
import json
from pathlib import Path
from zipfile import ZipFile

from docx import Document
from lxml import etree
import pymupdf
import pytest

from architect_agent.figures import report_figures
from architect_agent.output import report_html, report_pdf
from architect_agent.schemas import validate
from architect_agent.sources import Source
from architect_agent.workflow import build

ROOT=Path(__file__).resolve().parents[1]


def designed_plan():
    plan=json.loads((ROOT/'examples/example_plan.json').read_text())
    plan['title']='Vergunningverlening — synthetische testarchitectuur'
    components={5:['Aanvraagportaal','Medewerkersportaal'],4:['Beoordelingsworkflow','Feedbackproces'],3:['API-koppelingen','Notificaties'],2:['Zaakregistratie-API','Beslisregelservice'],1:['Bestaand zakenregister','Regelcatalogus']}
    for layer in plan['layers']:layer['components']=components[layer['number']]
    plan['flow_steps']=['Aanvraag ontvangen','Zaak registreren','Beoordeling uitvoeren','Besluit versturen']

    def node(identifier,label,group,status='unknown'):
        return {'id':identifier,'label':label,'group':group,'status':status,'evidence':['B00 tekst']}
    def diagram(kind,title,nodes,edges=None,service=''):
        return {'kind':kind,'title':title,'nodes':nodes,'edges':edges or [],'service_id':service}
    def edge(a,b):return {'from':a,'to':b,'label':'ondersteunt','evidence':['B00 tekst']}
    plan['diagrams']=[
        diagram('customer_routes','Klantroute vergunningaanvraag',[node('vraag','Vergunning aanvragen','Klantbehoefte'),node('ontvangen','Ontvangen','Klantroutestappen')],[edge('vraag','ontvangen')]),
        diagram('business_services','Bedrijfsservices vergunningverlening',[node('registreren','Aanvraag registreren','Bestaand','existing'),node('beoordelen','Aanvraag beoordelen','Nieuw voorgesteld','new'),node('evalueren','Dienstverlening evalueren','Aanpassen','change')]),
        diagram('service_design','Realisatie aanvraag beoordelen',[node('workflow','Beoordelingsworkflow','Solutioncomponenten','new'),node('zaken','Bestaande zaakregistratie','Registers en gegevens','existing'),node('regels','Bevoegdheid toetsen','Processen en beslisregels','new')],[edge('workflow','regels')],service='beoordelen'),
        diagram('service_design','Realisatie evalueren',[node('feedback','Feedbackproces','Processen en beslisregels','change')],service='evalueren'),
    ]
    for ch in plan['changes']:ch['evidence']=['B00 tekst']
    for rule in plan['decision_rules']:rule['evidence']=['B00 tekst']
    return plan


def source():return [Source('B00','testbron.md','Fictieve testbron — geen echte dienstencatalogus.',1,'md')]


def test_figures_are_topic_specific_and_have_a_design_per_changed_service():
    plan=designed_plan();assert not validate(plan,source())
    figures=report_figures(plan,'Rotterdam')
    assert [f['chapter'] for f in figures]==[3,4,5,6,6,7]
    assert 'Aanvraag beoordelen' in figures[1]['svg']
    assert 'Beoordelingsworkflow' in figures[3]['svg']
    assert 'CONCEPT' in figures[0]['svg'] and 'Bronnen: B00 tekst' in figures[0]['caption']
    for f in figures:
        etree.fromstring(f['svg'].encode())
        assert f['png'].startswith(b'\x89PNG')
    assert figures[0]['svg'].count('marker-end=')==1
    assert figures[1]['svg'].count('marker-end=')==0
    changed=copy.deepcopy(plan);changed['title']='Andere projectnaam';changed['diagrams'][0]['nodes'][0]['label']='Andere klantvraag'
    other=report_figures(changed,'Rotterdam')[0]
    assert 'Andere projectnaam' in other['svg'] and 'Andere klantvraag' in other['svg']
    assert figures[0]['svg']!=other['svg']


def test_unsubstantiated_availability_and_missing_designs_are_rejected():
    plan=designed_plan();plan['diagrams'].pop()
    assert any('evalueren' in e for e in validate(plan,source()))
    plan=designed_plan();plan['diagrams'][1]['nodes'][0]['evidence']=[]
    assert any('bronbewijs' in e for e in validate(plan,source()))
    plan=designed_plan();plan['diagrams'][0]['edges'][0]['to']='bestaat-niet'
    assert any('diagramrelatie' in e for e in validate(plan,source()))
    plan=designed_plan();plan['diagrams'][0]['nodes']=[];plan['diagrams'][0]['edges']=[]
    assert any('open punten' in e for e in validate(plan,source()))
    plan=designed_plan();plan['diagrams'][0]['nodes'][0]['evidence']=['B99 tekst']
    assert any('Bron ontbreekt' in e for e in validate(plan,source()))


def test_real_images_are_embedded_in_python_word_pdf_html_and_zip_outputs(tmp_path):
    plan=designed_plan()
    html=report_html(plan,source(),'Rotterdam')
    assert html.count('data:image/png;base64,')==6
    assert 'Fictieve testbron' not in html
    pdf=report_pdf(plan,source(),'Rotterdam')
    with pymupdf.open(stream=pdf,filetype='pdf') as document:
        assert sum(len(page.get_image_info()) for page in document)>=6
    base=tmp_path/'base.docx';Document().save(base)
    output=tmp_path/'output';manifest=build(base,source(),plan,output)
    word=Document(output/manifest['document'])
    assert len(word.inline_shapes)==6
    assert len(manifest['figures'])==12
    with ZipFile(output/manifest['document']) as archive:
        assert len([n for n in archive.namelist() if n.startswith('word/media/')])==6
