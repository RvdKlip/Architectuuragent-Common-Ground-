"""Resolve epic details from a platform link for the Streamlit workspace."""
import os
import streamlit as st
from .epics import resolve_epic_link, epic_document
from .selection import SelectedDocument


def render_epic(token=''):
    st.subheader('Start vanuit een epic')
    link = st.text_input('Link naar epic', key='epic_link')
    current = st.session_state.get('selected_epic')
    if current and current['url'] != link.strip():
        st.session_state.pop('selected_epic', None)
        current = None
    if st.button('Epic ophalen'):
        st.session_state.pop('selected_epic', None)
        current = None
        try:
            current = resolve_epic_link(link, {**os.environ, 'NOTION_TOKEN': token or os.getenv('NOTION_TOKEN', '')})
            st.session_state['selected_epic'] = current
        except ValueError as error:
            st.error(str(error))
    st.text_input('Naam van de epic', value=current['title'] if current else '', disabled=True)
    st.text_area('Epicbeschrijving', value=current['text'] if current else '', disabled=True)
    st.caption('Naam en beschrijving worden uit de link opgehaald. Afgeschermde bronnen vereisen toegang op de lokale service.')
    if not current:
        return None, None
    if st.button('Epic verwijderen'):
        st.session_state.pop('selected_epic', None)
        st.rerun()
    return SelectedDocument('epic', 'Geselecteerde-epic.md', epic_document(current).encode('utf-8')), current
