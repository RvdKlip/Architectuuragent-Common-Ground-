"""Selecteer bronnen voor een projectarchitectuur; enterprise architectuur altijd volledig."""
import hashlib
import json
import streamlit as st
from .catalogue import CACHE, ENTERPRISE_GITHUB, ENTERPRISE_GITBOOK, load_enterprise
from .selection import HORIZON_URL, SOURCE_OPTIONS, SelectedDocument, missing_sources
from .presentation import render_hero, render_steps
from .horizzon import parse_export
from .epics_ui import render_epic


def render_selection(notion_token="") -> dict:
    st.title('Projectarchitectuur')
    st.caption('Jouw project. Jouw bronnen. Eén helder vertrekpunt.')
    render_hero()
    render_steps()
    st.markdown('<div id="project"></div>', unsafe_allow_html=True)
    with st.container(border=True):
        st.subheader('1. Welk project start je?')
        left, right = st.columns([2, 1])
        with left:
            scope = st.text_input('Projectnaam', placeholder='Bijvoorbeeld: Signaalmanagement', key='project_name')
        with right:
            mode = st.selectbox('Type architectuur', ['Nieuwe projectarchitectuur', 'Bestaande architectuur bijwerken'])
        goals = st.text_area('Doel en afbakening', key='project_goals', height=100)
        epic_source, epic = render_epic(notion_token)
    project_start = mode == 'Nieuwe projectarchitectuur'
    base = None if project_start else st.file_uploader('Bestaande solutionarchitectuur (Word)', type=['docx'], key='base')
    st.markdown('<div id="bronnen"></div>', unsafe_allow_html=True)
    st.subheader('2. Bouw je fundament')
    documents, selected = [], []
    enterprise_metadata = None
    building_blocks = {'selected': [], 'source': {'url': HORIZON_URL}}
    left, right = st.columns(2)
    with left, st.container(border=True):
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
    with right, st.container(border=True):
        enabled = st.checkbox('Bouwstenen Rotterdam', key='use_horizon')
        if enabled:
            selected.append('horizon')
        st.markdown('[Open bouwstenen in Horizzon ↗]('+HORIZON_URL+')')
        st.caption('Een ingelogde Horizzon-sessie kan niet worden overgenomen. Importeer een CSV- of JSON-export om echte Rotterdamse ABB’s en SBB’s te selecteren.')
        uploaded = st.file_uploader('Bouwstenencatalogus uit Horizzon', type=['csv', 'json'], key='horizzon_catalogue', disabled=not enabled)
        if uploaded and enabled:
            try:
                blocks, skipped = parse_export(uploaded.getvalue(), uploaded.name)
                digest = hashlib.sha256(uploaded.getvalue()).hexdigest()
                st.caption(f'{len(blocks)} bouwstenen geladen; {skipped} objecten zonder bruikbare ABB/SBB-classificatie overgeslagen.')
                chosen = []
                for kind in ('ABB', 'SBB'):
                    candidates = {b['id']: b for b in blocks if b['type'] == kind}
                    ids = st.multiselect(kind+'’s', list(candidates), format_func=lambda key: candidates[key]['name'], key='horizzon_'+kind+'_'+digest)
                    chosen.extend(candidates[key] for key in ids)
                building_blocks = {'selected': chosen, 'source': {'url': HORIZON_URL, 'export': uploaded.name, 'sha256': digest}, 'method': 'Handmatige selectie uit aangeleverde Horizzon-export.'}
                if chosen:
                    text = '# Geselecteerde Rotterdamse bouwstenen — VOORSTEL, te beoordelen\n\n'+f'Bron: {HORIZON_URL}\nExport: {uploaded.name}\nSHA-256: {digest}\n\n'+'\n\n'.join(b['type']+': '+b['name']+'\nObject-ID: '+b['id']+'\n'+b['description'] for b in chosen)
                    documents.append(SelectedDocument('horizon', 'Bouwstenen-Rotterdam-selectie.md', text.encode('utf-8')))
            except (ValueError, UnicodeError, TypeError, AttributeError) as error:
                st.error(str(error))
        with st.expander('Welke exportvelden zijn nodig?'):
            st.caption('CSV (komma of puntkomma) of JSON-lijst: id, name, type (ABB of SBB), optioneel description. Ook naam, beschrijving en bouwsteentype worden herkend. Andere objecttypen worden overgeslagen.')
    with st.container(border=True):
        st.subheader('Projectdocumenten en overige bronnen')
        extra = st.file_uploader('Projectbronnen uploaden', type=['pdf', 'docx', 'txt', 'md'], accept_multiple_files=True, key='project_sources')
        for index, file in enumerate(extra or []):
            digest = hashlib.sha256(file.getvalue()).hexdigest()[:16]
            if st.checkbox(file.name, value=True, key=f'extra_{index}_{digest}'):
                documents.append(SelectedDocument('project', file.name, file.getvalue()))
    if epic_source:
        documents.append(epic_source)
    missing = missing_sources(selected, documents)
    st.subheader('Jouw bronselectie')
    a, b, c = st.columns(3)
    a.metric('Bronbestanden', len(documents) + int(base is not None))
    b.metric('Geselecteerde kaders', len(selected))
    c.metric('Nog aan te vullen', len(missing))
    rows = [{'Broncode': 'B00', 'Bron': base.name, 'Categorie': 'Bestaande architectuur'}] if base else []
    titles = {o.key: o.title for o in SOURCE_OPTIONS}
    titles['epic'] = 'Geselecteerde epic'
    for index, document in enumerate(documents, int(base is not None)):
        rows.append({'Broncode': f'B{index:02d}', 'Bron': document.name, 'Categorie': titles.get(document.category, 'Projectdocument')})
    if rows:
        st.dataframe(rows, hide_index=True, width='stretch')
    if missing:
        st.warning('Nog inhoud nodig voor: ' + '; '.join(missing))
    manifest = {'project': scope, 'goals': goals, 'type': mode, 'sources': rows, 'missing': missing,
                'epic': epic, 'enterprise_architecture': enterprise_metadata, 'building_blocks': building_blocks,
                'horizon': {'url': HORIZON_URL, 'content_loaded': bool(building_blocks['selected'])}}
    st.download_button('Download bronselectie', json.dumps(manifest, ensure_ascii=False, indent=2), file_name='bronselectie.json', mime='application/json')
    return {'project_start': project_start, 'scope': scope, 'goals': goals, 'base': base, 'documents': documents, 'missing': missing, 'manifest': manifest}
