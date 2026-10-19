"""Selecteer bronnen voor een projectarchitectuur; enterprise architectuur altijd volledig."""
import hashlib
import streamlit as st
from .catalogue import CACHE, ENTERPRISE_GITHUB, ENTERPRISE_GITBOOK, load_enterprise
from .selection import SOURCE_OPTIONS, SelectedDocument, missing_sources
from .presentation import render_hero, render_steps


def render_selection() -> dict:
    st.title('Projectarchitectuur')
    st.caption('Jouw project. Jouw bronnen. Eén helder vertrekpunt.')
    render_hero()
    render_steps()
    st.markdown('<div id="project"></div>', unsafe_allow_html=True)
    with st.container(border=True):
        st.subheader('1. Voor welk project wil je een architectuur opstellen')
        left, right = st.columns([2, 1])
        with left:
            scope = st.text_input('Projectnaam', placeholder='Bijvoorbeeld: Signaalmanagement', key='project_name')
        with right:
            mode = st.selectbox('Type architectuur', ['Nieuwe projectarchitectuur', 'Bestaande architectuur bijwerken'])
        goals = st.text_area('Doel en afbakening', key='project_goals', height=100)
        st.subheader('Projectdocumenten en overige bronnen')
        st.caption('Voeg één of meerdere PDF-, DOCX-, TXT- of Markdown-bestanden toe. Vink per bestand aan of het mee moet.')
        extra = st.file_uploader('Projectbronnen uploaden', type=['pdf', 'docx', 'txt', 'md'], accept_multiple_files=True, key='project_sources')
        retained = st.session_state.setdefault('retained_project_sources', {})
        for file in extra or []:
            content = file.getvalue()
            digest = hashlib.sha256(file.name.encode('utf-8') + b'\0' + content).hexdigest()
            retained.setdefault(digest, SelectedDocument('project', file.name, content))
        project_documents = []
        for digest, document in retained.items():
            if st.checkbox(document.name, value=True, key=f'extra_{digest}'):
                project_documents.append(document)
    project_start = mode == 'Nieuwe projectarchitectuur'
    base = None if project_start else st.file_uploader('Bestaande solutionarchitectuur (Word)', type=['docx'], key='base')
    st.markdown('<div id="bronnen"></div>', unsafe_allow_html=True)
    st.subheader('2. Bouw je fundament')
    documents, selected = project_documents, []
    enterprise_metadata = None
    with st.container(border=True):
        enabled = st.checkbox(SOURCE_OPTIONS[0].title, value=True, key='use_enterprise')
        if enabled:
            selected.append('enterprise')
        st.caption('Alle hoofdstukken worden volledig meegenomen.')
        st.markdown(f'[Lees in GitBook]({ENTERPRISE_GITBOOK}) · [Bekijk op GitHub]({ENTERPRISE_GITHUB})')
        data = None
        if CACHE.exists():
            try:
                data = load_enterprise()
            except (ValueError, KeyError, OSError):
                st.warning('De lokale bron is niet leesbaar. Haal de bron opnieuw op.')
        if st.button('Bron vernieuwen' if data else 'Enterprise architectuur ophalen', key='refresh_enterprise', disabled=not enabled):
            try:
                data = load_enterprise(refresh=True)
            except Exception:
                st.error('Ophalen is niet gelukt. Upload een eigen versie of controleer de verbinding.')
        enterprise_mode = st.radio('Versie van de enterprise architectuur', ['Openbare GitHub-bron', 'Eigen versie uploaden'], horizontal=True, disabled=not enabled)
        if enterprise_mode == 'Openbare GitHub-bron':
            if data and enabled:
                documents.append(SelectedDocument('enterprise', 'Enterprise-architectuur-volledig.md', data['text'].encode('utf-8')))
                enterprise_metadata = {k: data[k] for k in ('url', 'sha256', 'retrieved_at')}
                enterprise_metadata['all_chapters'] = True
                st.success(f"Volledige bron · {len(data['text']):,} tekens")
            elif enabled:
                st.info('Haal de volledige bron op of upload een eigen versie.')
        else:
            uploaded = st.file_uploader('Eigen versie uploaden', type=['pdf', 'docx', 'txt', 'md'], key='files_enterprise', disabled=not enabled)
            if uploaded and enabled:
                documents.append(SelectedDocument('enterprise', uploaded.name, uploaded.getvalue()))
    missing = missing_sources(selected, documents)
    st.subheader('Jouw bronselectie')
    a, b, c = st.columns(3)
    a.metric('Bronbestanden', len(documents) + int(base is not None))
    b.metric('Geselecteerde kaders', len(selected))
    c.metric('Nog aan te vullen', len(missing))
    rows = [{'Broncode': 'B00', 'Bron': base.name, 'Categorie': 'Bestaande architectuur'}] if base else []
    titles = {o.key: o.title for o in SOURCE_OPTIONS}
    for index, document in enumerate(documents, int(base is not None)):
        rows.append({'Broncode': f'B{index:02d}', 'Bron': document.name, 'Categorie': titles.get(document.category, 'Projectdocument')})
    if rows:
        st.dataframe(rows, hide_index=True, width='stretch')
    if missing:
        st.warning('Nog inhoud nodig voor: ' + '; '.join(missing))
    manifest = {'project': scope, 'goals': goals, 'type': mode, 'sources': rows, 'missing': missing,
                'enterprise_architecture': enterprise_metadata}
    return {'project_start': project_start, 'scope': scope, 'goals': goals, 'base': base, 'documents': documents, 'missing': missing, 'manifest': manifest}
