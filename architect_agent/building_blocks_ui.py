"""Lokale documentanalyse en aanpasbaar bouwblokkenadvies in Streamlit."""
import hashlib
from pathlib import Path
import tempfile

import streamlit as st

from .building_blocks import load_catalogue, recommend, selection_manifest
from .sources import extract


def _contexts(scope, goals, documents, base):
    contexts = [{'source': 'Projectonderwerp en afbakening', 'text': scope+'\n'+goals}]
    cache = st.session_state.setdefault('building_block_extractions', {})
    uploaded = [(doc.name, doc.content) for doc in documents if doc.category != 'enterprise']
    if base:
        uploaded.append((base.name, base.getvalue()))
    warnings = []
    for name, content in uploaded:
        key = hashlib.sha256(content).hexdigest()+name
        if key not in cache:
            try:
                if len(content) > 20_000_000:
                    raise ValueError('Bestand is groter dan de advieslimiet van 20 MB.')
                with tempfile.TemporaryDirectory(prefix='cg_building_blocks_') as temporary:
                    path = Path(temporary)/Path(name.replace('\\', '/')).name
                    path.write_bytes(content)
                    source = extract(path, 'ADVIES')
                cache[key] = {'text': source.text, 'warning': None,
                              'note': 'PDF-pagina’s met afbeeldingen zonder uitleesbare tekst zijn niet inhoudelijk geanalyseerd.'
                              if 'WAARSCHUWING:' in source.text else None}
            except Exception as error:
                cache[key] = {'text': '', 'warning': str(error)}
        result = cache[key]
        contexts.append({'source': 'Bestandsnaam: '+name, 'text': name})
        if result['warning']:
            warnings.append(name+': inhoud niet gebruikt voor advies. '+result['warning'])
        else:
            contexts.append({'source': name, 'text': result['text']})
            if result.get('note'):
                warnings.append(name+': '+result['note'])
    return contexts, warnings


def render_building_blocks(scope, goals, documents, base=None):
    catalogue = load_catalogue()
    contexts, warnings = _contexts(scope, goals, documents, base)
    advice = recommend(catalogue, contexts)
    overrides = st.session_state.setdefault('building_block_overrides', {})
    result = selection_manifest(catalogue, advice, overrides)
    selected_ids = {b['id'] for b in result['selected']}
    recommended = {r['id']: r for r in advice}
    related = {sbb for abb in catalogue['abbs'] if abb['id'] in selected_ids for sbb in abb['sbb_ids']}
    st.markdown('### Toe te passen bouwblokken')
    st.caption('Geadviseerd gebruik · automatisch op basis van onderwerp en geselecteerde documentinhoud. Controleer het advies; je kunt iedere keuze aanpassen.')
    st.caption('ABB = generieke capability · SBB = concrete invulling volgens de bronmapping.')
    st.caption('Lokaal trefwoordadvies, geen semantische AI-beoordeling. De algemene enterprise-tekst wordt niet als projectvraag meegeteld.')

    def reset():
        st.session_state['building_block_overrides'] = {}

    st.button('Volg automatisch advies', on_click=reset, key='reset_building_blocks')

    def draw(block):
        key = 'building_block_'+block['id']
        default = block['id'] in (recommended if block['type'] == 'ABB' else related)
        st.session_state[key] = overrides.get(block['id'], default)

        def changed(block_id=block['id'], widget_key=key):
            st.session_state['building_block_overrides'][block_id] = st.session_state[widget_key]

        st.checkbox(block['name'], key=key, on_change=changed)
        st.caption(block['layer']+(' · Zelf aangepast' if block['id'] in overrides else ''))
        if block['type'] == 'ABB' and block['id'] in recommended:
            for evidence in recommended[block['id']]['evidence']:
                st.caption('Aanleiding: '+evidence['source']+' — '+', '.join(evidence['terms']))
            with st.expander('Toon aanleiding en bronmapping', key='proof_'+block['id']):
                for evidence in recommended[block['id']]['evidence']:
                    st.text(evidence['excerpt'])
                st.text(block['quote'])
                st.caption(f"Bron: {block['section']}, regel {block['line']}")
        elif block['type'] == 'SBB':
            names = [b['name'] for b in catalogue['abbs'] if b['id'] in block['abb_ids'] and b['id'] in selected_ids]
            st.caption('Volgens bronmapping bij: '+('; '.join(names) if names else 'handmatige keuze; bijpassende ABB beoordelen'))

    for label, blocks in [('ABB’s · Architecture Building Blocks', catalogue['abbs']),
                          ('SBB’s · Solution Building Blocks', catalogue['sbbs'])]:
        st.markdown('**'+label+'**')
        visible = [b for b in blocks if b['id'] in recommended or b['id'] in related or b['id'] in overrides]
        if not visible:
            st.info('Vul een onderwerp in of voeg documenten toe voor automatisch advies.')
        for block in visible:
            draw(block)
        with st.expander('Overige '+label[:4]+' handmatig toevoegen'):
            for block in blocks:
                if block not in visible:
                    draw(block)
    for warning in warnings:
        st.warning(warning)
    source = catalogue['source']
    st.caption('Broncatalogus: enterprise architectuur · momentopname '+source['retrieved_at'][:10]+' · '+source['sha256'][:12])
    st.markdown('[Bekijk de ABB/SBB-bronmapping]('+source['url']+')')
    result = selection_manifest(catalogue, advice, st.session_state['building_block_overrides'])
    result['warnings'] = warnings
    return result, catalogue
