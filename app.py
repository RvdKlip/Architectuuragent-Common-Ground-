"""Streamlit-webinterface voor reproduceerbare Common Ground-solutionarchitectuur."""
from pathlib import Path
import io
import json
import os
import tempfile
import zipfile
import streamlit as st

from architect_agent.workflow import prepare,build
from architect_agent.schemas import validate

st.set_page_config(page_title='Common Ground Architectuuragent',page_icon='🏛️',layout='wide')
st.title('Common Ground · Architectuuragent')
st.caption('Van bronstukken naar concept-solutionarchitectuur, vijf-lagenplaat en ADR – met bronverwijzingen en verplichte review.')

with st.sidebar:
    st.header('Instellingen')
    model=st.text_input('OpenAI-model',os.getenv('OPENAI_MODEL','gpt-4.1'))
    api_key=st.text_input('OPENAI_API_KEY (optioneel)',type='password',help='Of stel de sleutel in als omgevingsvariabele. Wordt niet in outputbestanden bewaard.')
    st.info('Een API-aanroep is optioneel bij hergebruik van beoordeelde JSON. API-gebruik kan kosten veroorzaken.')
    st.warning('Gebruik alleen bronstukken die volgens het gemeentelijke informatiebeveiligingsbeleid naar de gekozen AI-dienst mogen. Bronbestanden worden bij genereren aan de API doorgegeven.')

st.subheader('1. Bronnen en opdracht')
base=st.file_uploader('Bestaande solutionarchitectuur (Word, verplicht)',type=['docx'],key='base')
uploads=st.file_uploader('Nieuwe onderbouwingen / Notion-export / ADR-overzicht (één of meer bestanden)',type=['pdf','docx','txt','md'],accept_multiple_files=True,key='sources')
col1,col2=st.columns([1,2])
with col1:
    scope=st.text_input('Onderwerp / epic','Signaalmanagement')
with col2:
    goals=st.text_input('Gewenste wijziging','Verwerk voortschrijdend inzicht, maak nieuwe architectuurplaat, concept-ADR en decision rules; respecteer bestaande ADR’s.')
style=st.file_uploader('Optioneel: visueel stijlvoorbeeld (alleen referentie op het scherm)',type=['png','jpg','jpeg'])
if style:
    st.image(style,caption='De gegenereerde diagrammen volgen het vaste Common Ground-vijflagensjabloon; dit voorbeeld wordt niet automatisch geïnterpreteerd.')

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
        st.success('Concept gereed. Controleer en bewerk de JSON hieronder vóór documentgeneratie.')
        for source in parsed:
            if 'WAARSCHUWING:' in source.text:
                st.warning(f'Controleer afbeeldingen in {source.filename}: PDF-pagina’s zonder uitleesbare tekst konden niet worden geanalyseerd.')
    except Exception as e:
        st.error(f'Analyse gestopt: {e}')

if 'agent_plan_json' in st.session_state:
    st.subheader('2. Review de voorgestelde architectuur')
    st.warning('Dit is een concept. Controleer de voorgestelde besluiten, nieuwe aannames en broncodes. Er worden geen formele ADR-besluiten genomen.')
    modified=st.text_area('Concept-JSON (bewerkbaar)',height=330,key='review_json')
    if st.button('2 · Maak bijgewerkte Word en diagrammen',type='primary'):
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
