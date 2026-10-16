"""Epic selection for the Streamlit workspace."""
import os
import streamlit as st
from .epics import NOTION_EPICS_URL, list_epics, get_epic, epic_document, validate_epic_link
from .selection import SelectedDocument


def render_epic(token=''):
    st.subheader('Start vanuit een epic')
    provider = st.selectbox('Bron van de epic', ['none', 'notion', 'teams'], format_func=lambda v: {'none':'Geen epic selecteren','notion':'Notion','teams':'Microsoft Teams'}[v], key='epic_provider')
    current = st.session_state.get('selected_epic')
    if current and current['provider'] != provider:
        st.session_state.pop('selected_epic', None)
        current = None
    if provider == 'none':
        return None, None
    if provider == 'notion':
        st.link_button('Open de Notion-epiclijst', NOTION_EPICS_URL)
        env = {**os.environ, 'NOTION_TOKEN': token or os.getenv('NOTION_TOKEN', '')}
        if st.button('Haal epics uit Notion op', key='load_epics'):
            try:
                st.session_state['notion_epics'] = list_epics(provider, env)
            except ValueError as error:
                st.error(str(error))
        data = st.session_state.get('notion_epics', {'epics': [], 'next_cursor': None})
        if data['next_cursor'] and st.button('Meer epics laden'):
            try:
                more = list_epics(provider, env, data['next_cursor'])
                data = {'epics': data['epics']+more['epics'], 'next_cursor': more['next_cursor']}
                st.session_state['notion_epics'] = data
            except ValueError as error:
                st.error(str(error))
        entries = {item['id']:item for item in data['epics']}
        chosen = st.selectbox('Epic uit Notion', list(entries), index=None, format_func=lambda key: entries[key]['title'], placeholder='Haal eerst epics op en kies een epic')
        if st.button('Gebruik geselecteerde epic', disabled=chosen is None):
            try:
                current = {**get_epic(provider, chosen, env), 'mode': 'connector'}
                st.session_state['selected_epic'] = current
            except ValueError as error:
                st.error(str(error))
    else:
        st.link_button('Open Microsoft Teams', 'https://teams.microsoft.com/')
    st.caption('Of voeg zelf een epiclink en beschrijving toe. Een link alleen leest de afgeschermde inhoud niet in.')
    link = st.text_input('Link naar de epic', key='epic_link_'+provider)
    title = st.text_input('Naam van de epic', key='epic_title_'+provider)
    text = st.text_area('Epicbeschrijving', key='epic_description_'+provider)
    if st.button('Gebruik deze epic'):
        try:
            link = validate_epic_link(link, provider)
            if not title.strip():
                raise ValueError('Vul de naam van de epic in.')
            if len(text) > 250000:
                raise ValueError('De epicbeschrijving is te groot (maximaal 250.000 tekens).')
            current = {'provider': provider, 'id': link, 'url': link, 'title': title.strip(), 'text': text.strip(), 'mode':'link'}
            st.session_state['selected_epic'] = current
        except ValueError as error:
            st.error(str(error))
    if current:
        st.success('Geselecteerde epic: '+current['title'])
        st.caption('Beschrijving als bron opgenomen.' if current['text'].strip() else 'Alleen verwijzing; epicinhoud is niet ingelezen.')
        if st.button('Epic verwijderen'):
            st.session_state.pop('selected_epic', None)
            current = None
    if not current:
        return None, None
    return SelectedDocument('epic', 'Geselecteerde-epic.md', epic_document(current).encode('utf-8')), current
