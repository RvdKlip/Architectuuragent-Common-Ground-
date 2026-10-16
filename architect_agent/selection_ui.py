"""Streamlit-scherm om de bronset voor een PSA samen te stellen."""
import hashlib
import json

import streamlit as st

from .catalogue import (
    CACHE, ENTERPRISE_GITHUB, ENTERPRISE_GITBOOK,
    chapter_document, chapters, load_enterprise,
)
from .selection import SOURCE_OPTIONS, SelectedDocument, missing_sources


def render_selection() -> dict:
    st.title('Projectstartarchitectuur')
    st.caption('Stel je project samen. Kies de kaders en documenten die de architectuur moeten onderbouwen.')
    st.markdown('**1 · Project**　 →　 **2 · Bronnen selecteren**　 →　 **3 · Concept beoordelen**')
    with st.container(border=True):
        st.subheader('1. Welk project start je?')
        left, right = st.columns([2, 1])
        with left:
            scope = st.text_input('Projectnaam', placeholder='Bijvoorbeeld: Signaalmanagement', key='project_name')
        with right:
            mode = st.selectbox('Type architectuur', ['Nieuwe projectstartarchitectuur', 'Bestaande architectuur bijwerken'])
        goals = st.text_area('Doel en afbakening', placeholder='Wat wil het project bereiken? Welke processen en voorzieningen vallen binnen de scope?', key='project_goals', height=100)
    project_start = mode == 'Nieuwe projectstartarchitectuur'
    base = None
    if not project_start:
        base = st.file_uploader('Bestaande solutionarchitectuur (Word)', type=['docx'], key='base')

    st.subheader('2. Selecteer je bronnen')
    st.write('De enterprise architectuur staat voor je klaar. Vul deze naar behoefte aan met projectdocumenten en andere kaders.')
    documents = []
    selected = []
    enterprise_metadata = None
    columns = st.columns(2)
    for index, option in enumerate(SOURCE_OPTIONS):
        with columns[index % 2], st.container(border=True):
            enabled = st.checkbox(option.title, value=option.key == 'enterprise', key='use_'+option.key)
            st.caption(option.description)
            if enabled:
                selected.append(option.key)
            if option.key == 'enterprise':
                st.markdown(f'[Lees in GitBook]({ENTERPRISE_GITBOOK}) · [Bekijk Markdown op GitHub]({ENTERPRISE_GITHUB})')
                st.caption('Openbare bron · selecteer hieronder de relevante hoofdstukken')
                data = None
                if CACHE.exists():
                    try:
                        data = load_enterprise()
                    except (ValueError, KeyError, OSError):
                        st.warning('De lokale bron kan niet worden gelezen. Haal de bron opnieuw op.')
                if st.button('Bron vernieuwen' if data else 'Enterprise architectuur ophalen', key='refresh_enterprise', disabled=not enabled):
                    try:
                        with st.spinner('Openbare enterprise architectuur ophalen...'):
                            data = load_enterprise(refresh=True)
                        st.success('Bron opgehaald.')
                    except Exception:
                        st.error('Ophalen is niet gelukt. Controleer netwerktoegang tot raw.githubusercontent.com of upload een eigen versie.')
                enterprise_mode = st.radio('Versie van de enterprise architectuur', ['Openbare GitHub-bron', 'Eigen versie uploaden'], key='enterprise_mode', horizontal=True, disabled=not enabled)
                if enterprise_mode == 'Openbare GitHub-bron' and data:
                    sections = chapters(data['text'])
                    labels = {chapter.key: chapter.title for chapter in sections}
                    defaults = [c.key for c in sections if c.title in ('Managementsamenvatting', 'Visie, principes, scope')]
                    chosen = st.multiselect('Hoofdstukken om mee te nemen', list(labels), default=defaults,
                                            format_func=labels.get, key='enterprise_chapters_'+data['sha256'], disabled=not enabled)
                    st.caption(f"Momentopname {data['retrieved_at'][:10]} · bronkenmerk {data['sha256'][:12]} · {len(data['text']):,} tekens totaal")
                    if enabled and chosen:
                        text = chapter_document(data, chosen)
                        documents.append(SelectedDocument('enterprise', 'Enterprise-architectuur-selectie.md', text.encode('utf-8')))
                        enterprise_metadata = {k: data[k] for k in ('url', 'sha256', 'retrieved_at')}
                        enterprise_metadata['chapters'] = [labels[key] for key in chosen]
                        st.success(f'{len(chosen)} hoofdstukken geselecteerd · {len(text):,} tekens')
                        if len(text) > 155000:
                            st.warning('Deze selectie overschrijdt de bronlimiet. Kies minder hoofdstukken; er wordt niets automatisch afgekapt.')
                        with st.expander('Inhoud van de selectie bekijken'):
                            st.text_area('Geselecteerde brontekst', text, height=220, disabled=True)
                    elif enabled:
                        st.info('Selecteer minstens één hoofdstuk.')
                elif enterprise_mode == 'Openbare GitHub-bron' and enabled:
                    st.info('Haal de bron op om hoofdstukken te selecteren, of upload een eigen versie.')
                if enterprise_mode == 'Eigen versie uploaden':
                    files = st.file_uploader('Enterprise architectuur uploaden', type=['pdf', 'docx', 'txt', 'md'],
                                             accept_multiple_files=True, key='files_enterprise', disabled=not enabled)
                    if enabled:
                        documents.extend(SelectedDocument(option.key, f.name, f.getvalue()) for f in files or [])
            else:
                st.caption('Eigen bron toevoegen · ' + option.purpose)
                files = st.file_uploader('Documenten toevoegen', type=['pdf', 'docx', 'txt', 'md'],
                                         accept_multiple_files=True, key='files_'+option.key, disabled=not enabled)
                if enabled:
                    documents.extend(SelectedDocument(option.key, f.name, f.getvalue()) for f in files or [])
                    st.caption(f'{len(files or [])} bestanden toegevoegd' if files else 'Nog geen document toegevoegd')

    with st.container(border=True):
        st.markdown('**Projectdocumenten en overige bronnen**')
        st.caption('Bijvoorbeeld de projectopdracht, requirements, procesbeschrijvingen of een eerdere architectuur. Vink per bestand aan of het mee moet.')
        extra = st.file_uploader('Projectbronnen uploaden', type=['pdf', 'docx', 'txt', 'md'], accept_multiple_files=True, key='project_sources')
        for index, file in enumerate(extra or []):
            digest = hashlib.sha256(file.getvalue()).hexdigest()[:16]
            if st.checkbox(file.name, value=True, key=f'extra_{index}_{digest}'):
                documents.append(SelectedDocument('project', file.name, file.getvalue()))

    missing = missing_sources(selected, documents)
    st.subheader('Jouw bronselectie')
    a, b, c = st.columns(3)
    a.metric('Bronbestanden', len(documents) + int(base is not None))
    b.metric('Geselecteerde kaders', len(selected))
    c.metric('Nog aan te vullen', len(missing))
    rows = []
    offset = 0
    if base:
        rows.append({'Broncode': 'B00', 'Bron': base.name, 'Categorie': 'Bestaande architectuur'})
        offset = 1
    titles = {o.key: o.title for o in SOURCE_OPTIONS}
    for index, document in enumerate(documents, offset):
        rows.append({'Broncode': f'B{index:02d}', 'Bron': document.name,
                     'Categorie': titles.get(document.category, 'Projectdocument')})
    if rows:
        st.dataframe(rows, hide_index=True, width='stretch')
        st.caption('Alleen deze bestanden worden gebruikt, in deze volgorde. Andere documenten en niet-geselecteerde hoofdstukken worden niet ingelezen.')
    else:
        st.info('Selecteer een bron en voeg de bijbehorende inhoud toe om te beginnen.')
    if missing:
        st.warning('Nog inhoud nodig voor: ' + '; '.join(missing))
    manifest = {'project': scope, 'goals': goals, 'type': mode, 'sources': rows,
                'missing': missing, 'enterprise_architecture': enterprise_metadata}
    st.download_button('Download bronselectie', json.dumps(manifest, ensure_ascii=False, indent=2),
                       file_name='bronselectie.json', mime='application/json')
    return {'project_start': project_start, 'scope': scope, 'goals': goals, 'base': base,
            'documents': documents, 'missing': missing, 'manifest': manifest}
