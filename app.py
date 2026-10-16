"""Streamlit-webinterface voor reproduceerbare Common Ground-solutionarchitectuur."""
from pathlib import Path
import io
import hashlib
import json
import os
import tempfile
import zipfile
import streamlit as st

from architect_agent.workflow import prepare,build
from architect_agent.schemas import validate
from architect_agent.notion import publish_plan, NotionPublishError
from architect_agent.sources import collect
from architect_agent.selection import write_documents
from architect_agent.selection_ui import render_selection
from architect_agent.presentation import apply_style

st.set_page_config(page_title='Projectstartarchitectuur · Common Ground',page_icon='🏛️',layout='wide')
apply_style()

with st.sidebar:
    st.markdown('''<div class="sidebar-brand"><span class="brand-monogram">CG</span><div><strong>Common Ground</strong><small>ARCHITECT WORKSPACE</small></div></div>
<nav class="workspace-nav" aria-label="Werkruimte"><a href="#project" target="_self"><span>◈</span> Projectstartarchitectuur</a><a href="#bronnen" target="_self"><span>▤</span> Bronselectie</a><a href="#concept" target="_self"><span>◇</span> Concept & review</a></nav>''',unsafe_allow_html=True)
    with st.expander('AI-instellingen'):
        model=st.text_input('OpenAI-model',os.getenv('OPENAI_MODEL','gpt-4.1'))
        api_key=st.text_input('OPENAI_API_KEY (optioneel)',type='password',help='Of stel de sleutel in als omgevingsvariabele. Wordt niet in outputbestanden bewaard.')
        st.caption('AI-analyse kan kosten veroorzaken. Gebruik uitsluitend bronnen die naar deze AI-dienst mogen worden verzonden.')
    with st.expander('Notion · later instellen'):
        notion_token=st.text_input('Notion-integratiesleutel',type='password',value=os.getenv('NOTION_TOKEN',''),help='Geef de integratie toegang tot de bovenliggende pagina. Bewaar deze sleutel niet in Git.')
        notion_parent=st.text_input('Bovenliggende Notion-pagina (link of ID)',value=os.getenv('NOTION_PARENT_PAGE_ID',''))
        st.caption('Publiceren gebeurt uitsluitend via een expliciete publicatieactie na review.')
    st.markdown('<div class="workspace-note"><strong>Ontworpen voor onderbouwing.</strong>Van enterprise architectuur tot projectopdracht. Jij kiest de bronnen en beoordeelt het concept.</div>',unsafe_allow_html=True)

selection=render_selection()
base=selection['base']
documents=selection['documents']
scope=selection['scope']
goals=selection['goals']
selection_ready=bool(documents) and not selection['missing']
budget_ok=(not selection['manifest']['enterprise_architecture']
           or len(documents[0].content.decode('utf-8'))<=155000)
st.markdown('<div id="concept"></div>',unsafe_allow_html=True)
st.subheader('3. Maak een concept ter review')
st.caption('De bronselectie wordt eerst lokaal gecontroleerd. Alleen als je op de analyseknop klikt, worden de geselecteerde bronteksten naar het ingestelde AI-model verstuurd.')

review_upload=st.file_uploader('Optioneel: bestaand concept_review.json laden zonder AI-aanroep',type=['json'])
if st.button('Laad bestaand concept',disabled=not (review_upload and selection_ready and budget_ok)):
    try:
        root=Path(tempfile.mkdtemp(prefix='cg_architectuur_'))
        b=None
        if base:
            b=root/'basis.docx';b.write_bytes(base.getvalue())
        paths=write_documents(documents,root)
        parsed=collect(paths,base_doc=b)
        plan=json.loads(review_upload.getvalue())
        errors=validate(plan,parsed)
        if errors: raise ValueError('; '.join(errors))
        st.session_state.update(agent_root=str(root),agent_base=str(b) if b else None,
                                agent_sources=parsed,agent_plan_json=json.dumps(plan,ensure_ascii=False,indent=2))
        st.session_state['review_json']=st.session_state['agent_plan_json']
        st.session_state['agent_selection']=selection['manifest']
        for k in ('result_zip','result_docx','result_png','result_manifest'):
            st.session_state.pop(k,None)
        st.success('Concept geladen zonder AI-aanroep. Controleer de inhoud en de bronvolgorde vóór publicatie.')
    except Exception as e:
        st.error(f'Laden gestopt: {e}')

can_generate=selection_ready and budget_ok and bool(scope.strip()) and bool(goals.strip()) and (selection['project_start'] or base is not None)
if not scope.strip() or not goals.strip():
    st.info('Vul een projectnaam en doel/afbakening in om een concept te maken.')
if st.button('Maak concept-projectstartarchitectuur' if selection['project_start'] else 'Analyseer bronnen en maak concept-update',type='primary',disabled=not can_generate):
    try:
        if api_key: os.environ['OPENAI_API_KEY']=api_key
        root=Path(tempfile.mkdtemp(prefix='cg_architectuur_'))
        b=None
        if base:
            b=root/'basis.docx';b.write_bytes(base.getvalue())
        source_paths=write_documents(documents,root)
        with st.spinner('Bronstukken analyseren en concept opstellen...'):
            parsed,plan=prepare(b,source_paths,scope,goals,model,project_start=selection['project_start'])
        st.session_state['agent_root']=str(root)
        st.session_state['agent_base']=str(b) if b else None
        st.session_state['agent_sources']=parsed
        st.session_state['agent_plan_json']=json.dumps(plan,ensure_ascii=False,indent=2)
        st.session_state['review_json']=st.session_state['agent_plan_json']
        st.session_state['agent_selection']=selection['manifest']
        for k in ('result_zip','result_docx','result_png','result_manifest'):
            st.session_state.pop(k,None)
        st.success('Concept gereed. Controleer en bewerk de JSON hieronder vóór publicatie.')
        for source in parsed:
            if 'WAARSCHUWING:' in source.text:
                st.warning(f'Controleer afbeeldingen in {source.filename}: PDF-pagina’s zonder uitleesbare tekst konden niet worden geanalyseerd.')
    except Exception as e:
        st.error(f'Analyse gestopt: {e}')

if 'agent_plan_json' in st.session_state:
    st.subheader('Concept beoordelen')
    if st.session_state.get('agent_selection') and st.session_state['agent_selection']!=selection['manifest']:
        st.info('Je project of bronselectie is gewijzigd. Het onderstaande concept hoort nog bij de eerdere selectie; genereer een nieuw concept om de wijzigingen mee te nemen.')
    st.warning('Dit is een concept. Controleer de voorgestelde besluiten, nieuwe aannames en broncodes. Er worden geen formele ADR-besluiten genomen.')
    modified=st.text_area('Concept-JSON (bewerkbaar)',height=330,key='review_json')
    st.download_button('Download concept-JSON',modified,file_name='concept_review.json',mime='application/json')
    st.caption('Notion krijgt bewerkbare tekst: samenvatting, wijzigingen, vijf lagen, gegevensstroom, ADR, regels en bronoverzicht. Diagramafbeeldingen worden in deze eerste versie niet geüpload.')
    publication_key=hashlib.sha256((modified+notion_parent+repr(st.session_state['agent_sources'])).encode()).hexdigest()
    approved=st.checkbox('Ik heb dit concept gereviewd en mag deze inhoud in de gekozen Notion-pagina publiceren.',key='approve_'+publication_key)
    publications=st.session_state.setdefault('notion_publications',{})
    if publication_key in publications:
        st.link_button('Open het gepubliceerde concept in Notion',publications[publication_key]['url'])
        st.info('Dit concept is in deze sessie al gepubliceerd.')
    if st.button('2 · Publiceer concept in Notion',type='primary',disabled=not (approved and notion_token and notion_parent) or publication_key in publications):
        try:
            plan=json.loads(modified)
            with st.spinner('Concept publiceren in Notion...'):
                result=publish_plan(plan,st.session_state['agent_sources'],notion_parent,notion_token)
            publications[publication_key]=result
            st.success('Concept gepubliceerd als nieuwe Notion-subpagina.')
            st.link_button('Open het concept in Notion',result['url'])
        except NotionPublishError as e:
            st.error(str(e))
            if e.page_url: st.link_button('Controleer de gedeeltelijke Notion-pagina',e.page_url)
        except Exception:
            st.error('Publicatie gestopt. Controleer het concept, de pagina-ID en de integratie-instellingen.')
    if st.button('Optioneel · Maak Word en diagrammen',disabled=not st.session_state.get('agent_base')):
        try:
            plan=json.loads(modified)
            errors=validate(plan,st.session_state['agent_sources'])
            if errors: raise ValueError('; '.join(errors))
            output=Path(st.session_state['agent_root'])/'output'
            with st.spinner('Document en SVG/PNG-architectuurplaten genereren...'):
                manifest=build(Path(st.session_state['agent_base']),st.session_state['agent_sources'],plan,output)
            zip_buffer=io.BytesIO()
            with zipfile.ZipFile(zip_buffer,'w',compression=zipfile.ZIP_DEFLATED) as z:
                for file in output.iterdir():
                    if file.is_file():z.write(file,file.name)
            st.session_state['result_zip']=zip_buffer.getvalue()
            st.session_state['result_docx']=(output/manifest['document']).read_bytes()
            st.session_state['result_png']=(output/'architectuur_vijflagen.png').read_bytes()
            st.session_state['result_manifest']=manifest
            st.success('Bestanden opgebouwd. Het oude Word-document is niet overschreven.')
        except Exception as e:
            st.error(f'Genereren gestopt: {e}')

if 'result_zip' in st.session_state:
    st.subheader('3. Bestanden ophalen')
    a,b,c=st.columns(3)
    a.download_button('Word · conceptupdate',st.session_state['result_docx'],'Solutionarchitectuur_bijgewerkt_concept.docx',mime='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
    b.download_button('Architectuurplaat PNG',st.session_state['result_png'],'architectuur_vijflagen.png',mime='image/png')
    c.download_button('Alle bestanden ZIP',st.session_state['result_zip'],'architectuuragent_resultaat.zip',mime='application/zip')
    st.image(st.session_state['result_png'],caption='Architectuurplaat (ook beschikbaar als bewerkbare SVG in ZIP)')

st.divider()
st.caption('Elk resultaat blijft een concept. Controleer de onderbouwing en laat architectuurbesluiten via de afgesproken governance vaststellen.')
