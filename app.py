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

st.set_page_config(page_title='Common Ground Architectuuragent',page_icon='🏛️',layout='wide')
st.title('Common Ground · Architectuuragent')
st.caption('Van bronstukken naar concept-solutionarchitectuur, vijf-lagenplaat en ADR – met bronverwijzingen en verplichte review.')

with st.sidebar:
    st.header('Instellingen')
    model=st.text_input('OpenAI-model',os.getenv('OPENAI_MODEL','gpt-4.1'))
    api_key=st.text_input('OPENAI_API_KEY (optioneel)',type='password',help='Of stel de sleutel in als omgevingsvariabele. Wordt niet in outputbestanden bewaard.')
    st.info('Een API-aanroep is optioneel bij hergebruik van beoordeelde JSON. API-gebruik kan kosten veroorzaken.')
    st.warning('Gebruik alleen bronstukken die volgens het gemeentelijke informatiebeveiligingsbeleid naar de gekozen AI-dienst mogen. Bronbestanden worden bij genereren aan de API doorgegeven.')
    st.header('Publiceren in Notion')
    notion_token=st.text_input('Notion-integratiesleutel',type='password',value=os.getenv('NOTION_TOKEN',''),help='Geef de integratie toegang tot de bovenliggende pagina. Bewaar deze sleutel niet in Git.')
    notion_parent=st.text_input('Bovenliggende Notion-pagina (link of ID)',value=os.getenv('NOTION_PARENT_PAGE_ID',''))
    st.caption('Elke publicatie maakt een nieuwe subpagina. Alleen het gereviewde resultaat en bronverwijzingen worden verstuurd; bronbestanden blijven lokaal.')

st.subheader('1. Bronnen en opdracht')
base=st.file_uploader('Bestaande solutionarchitectuur (Word; nodig bij nieuwe AI-analyse)',type=['docx'],key='base')
uploads=st.file_uploader('Nieuwe onderbouwingen / Notion-export / ADR-overzicht (één of meer bestanden)',type=['pdf','docx','txt','md'],accept_multiple_files=True,key='sources')
col1,col2=st.columns([1,2])
with col1:
    scope=st.text_input('Onderwerp / epic','Signaalmanagement')
with col2:
    goals=st.text_input('Gewenste wijziging','Verwerk voortschrijdend inzicht, maak nieuwe architectuurplaat, concept-ADR en decision rules; respecteer bestaande ADR’s.')
style=st.file_uploader('Optioneel: visueel stijlvoorbeeld (alleen referentie op het scherm)',type=['png','jpg','jpeg'])
if style:
    st.image(style,caption='De gegenereerde diagrammen volgen het vaste Common Ground-vijflagensjabloon; dit voorbeeld wordt niet automatisch geïnterpreteerd.')

review_upload=st.file_uploader('Optioneel: bestaand concept_review.json laden zonder AI-aanroep',type=['json'])
if st.button('Laad bestaand concept',disabled=not (review_upload and uploads)):
    try:
        root=Path(tempfile.mkdtemp(prefix='cg_architectuur_'))
        b=None
        if base:
            b=root/'basis.docx';b.write_bytes(base.getvalue())
        paths=[]
        for idx,upload in enumerate(uploads):
            path=root/f'bron_{idx+1:02d}_{Path(upload.name).name}'
            path.write_bytes(upload.getvalue());paths.append(path)
        parsed=collect(paths,base_doc=b)
        plan=json.loads(review_upload.getvalue())
        errors=validate(plan,parsed)
        if errors: raise ValueError('; '.join(errors))
        st.session_state.update(agent_root=str(root),agent_base=str(b) if b else None,
                                agent_sources=parsed,agent_plan_json=json.dumps(plan,ensure_ascii=False,indent=2))
        st.session_state['review_json']=st.session_state['agent_plan_json']
        for k in ('result_zip','result_docx','result_png','result_manifest'):
            st.session_state.pop(k,None)
        st.success('Concept geladen zonder AI-aanroep. Controleer de inhoud en de bronvolgorde vóór publicatie.')
    except Exception as e:
        st.error(f'Laden gestopt: {e}')

if st.button('1 · Analyseer bronnen en maak concept',type='primary',disabled=not (base and uploads)):
    try:
        if api_key: os.environ['OPENAI_API_KEY']=api_key
        root=Path(tempfile.mkdtemp(prefix='cg_architectuur_'))
        b=root/'basis.docx';b.write_bytes(base.getvalue())
        source_paths=[]
        for idx,upload in enumerate(uploads):
            target=root/f'bron_{idx+1:02d}_{Path(upload.name).name}'
            target.write_bytes(upload.getvalue())
            source_paths.append(target)
        with st.spinner('Bronstukken analyseren en concept opstellen...'):
            parsed,plan=prepare(b,source_paths,scope,goals,model)
        st.session_state['agent_root']=str(root)
        st.session_state['agent_base']=str(b)
        st.session_state['agent_sources']=parsed
        st.session_state['agent_plan_json']=json.dumps(plan,ensure_ascii=False,indent=2)
        st.session_state['review_json']=st.session_state['agent_plan_json']
        for k in ('result_zip','result_docx','result_png','result_manifest'):
            st.session_state.pop(k,None)
        st.success('Concept gereed. Controleer en bewerk de JSON hieronder vóór publicatie.')
        for source in parsed:
            if 'WAARSCHUWING:' in source.text:
                st.warning(f'Controleer afbeeldingen in {source.filename}: PDF-pagina’s zonder uitleesbare tekst konden niet worden geanalyseerd.')
    except Exception as e:
        st.error(f'Analyse gestopt: {e}')

if 'agent_plan_json' in st.session_state:
    st.subheader('2. Review de voorgestelde architectuur')
    st.warning('Dit is een concept. Controleer de voorgestelde besluiten, nieuwe aannames en broncodes. Er worden geen formele ADR-besluiten genomen.')
    modified=st.text_area('Concept-JSON (bewerkbaar)',height=330,key='review_json')
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
st.caption('Herhaalbaar: een volgende run op een eerder gegenereerd document vervangt uitsluitend de herkenbare agent-aanvulling. Oorspronkelijke hoofdstukken en goedgekeurde ADR’s blijven onaangetast.')
