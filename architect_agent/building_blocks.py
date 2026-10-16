"""Herleidbaar trefwoordadvies op basis van de gepubliceerde ABB/SBB-mapping."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re

ASSETS = Path(__file__).resolve().parents[1]/'assets'
MAPPING_HEADING = '## Solution Building Blocks (SBB’s) en mapping op ABB’s'

# Zoektermen zijn lokale adviesregels, geen nieuwe architectuurkaders of mapping.
TERMS = {
    'NL Portal': ['portaal', 'portalen', 'selfservice', 'self-service', 'mijnomgeving', 'inwonerportaal'],
    'Open Formulieren': ['formulier', 'formulieren', 'aanvraag', 'aanvragen', 'intake'],
    'IKO': ['klantbeeld', 'objectbeeld', 'contactmoment', 'klantcontact', 'integraal klantbeeld'],
    'GZAC (UI)': ['werkvoorraad', 'medewerkerinterface', 'procesuitvoering'],
    'OpenBeheer': ['functioneel beheer', 'beheerinterface', 'configuratiebeheer'],
    'DMN Studio & Engine': ['dmn', 'beslisregel', 'beslisregels', 'business rules', 'bedrijfsregels'],
    'Taak & Workflow': ['werkvoorraad', 'taak', 'taken', 'workflow'],
    'OpenFSC': ['fsc', 'gegevensuitwisseling', 'ketenpartner', 'federatief', 'organisatie-overstijgend'],
    'OpenNotificaties': ['notificatie', 'notificaties', 'eventgedreven', 'events', 'gebeurtenis'],
    'NotifyNL OMC': ['omnichannel', 'communicatie', 'e-mail', 'sms', 'notify'],
    'Platform': ['logging', 'auditing', 'audittrail', 'tracing'],
    'OpenKlant API': ['klant', 'klanten', 'klantgegevens', 'klantcontact', 'contactmoment'],
    'OpenZaak API': ['zaak', 'zaken', 'zaakgericht', 'zaakgegevens', 'zaakafhandeling'],
    'OpenProduct API': ['productgegevens', 'productcatalogus', 'dienstencatalogus', 'pdc'],
    'Verzoeken (VTB)': ['verzoek', 'verzoeken', 'vtb'],
    'Taken (VTB)': ['taak', 'taken', 'vtb'],
    'Berichten (VTB)': ['bericht', 'berichten', 'vtb'],
    'Referentielijsten API': ['referentielijst', 'referentiegegevens', 'keuzelijst'],
    'Objects API': ['objects', 'objecten', 'objectregistratie', 'objectgegevens'],
    'OpenKlant Registratie': ['klant', 'klanten', 'persoonsgegevens', 'klantgegevens', 'contactmoment'],
    'OpenZaak Registratie': ['zaak', 'zaken', 'zaakgegevens', 'zaakafhandeling', 'zaakgericht'],
    'OpenProduct Registratie': ['productcatalogus', 'dienstencatalogus', 'productregistratie', 'pdc'],
    'OpenOrganisatie': ['openorganisatie', 'organisatieregister', 'medewerkersregister'],
    'Domeinregistraties': ['domeinregistratie', 'domeinspecifiek', 'domeinmodel'],
    'VTB-registraties': ['verzoek', 'verzoeken', 'taak', 'taken', 'bericht', 'berichten', 'vtb'],
    'Referentielijsten': ['referentielijst', 'referentiegegevens', 'keuzelijst'],
    'Registraties, OpenArchiefBeheer': ['archief', 'archiveren', 'archivering', 'bewaartermijn', 'duurzame toegankelijkheid', 'vernietiging'],
    'Keycloak / Autorisatieservice': ['authenticatie', 'autorisatie', 'keycloak', 'digid', 'inloggen', 'identity'],
    'Platformvoorzieningen': ['monitoring', 'observability', 'privacy', 'security', 'beveiliging', 'informatiebeveiliging', 'avg'],
}


def catalogue_from_snapshot(snapshot: dict) -> dict:
    text = snapshot['text']
    if MAPPING_HEADING not in text:
        return {'source': {k: snapshot.get(k) for k in ('url', 'sha256', 'retrieved_at')}, 'abbs': [], 'sbbs': []}
    start = text.index(MAPPING_HEADING)
    end = re.search(r'^## ', text[start+len(MAPPING_HEADING):], flags=re.M)
    section = text[start:start+len(MAPPING_HEADING)+end.start()] if end else text[start:]
    abbs = []
    sbbs = {}
    layer = ''
    for offset, line in enumerate(section.splitlines()):
        if line.startswith('#### '):
            layer = line[5:].strip()
        if not line.startswith('|'):
            continue
        cells = [cell.strip() for cell in line.strip('|').split('|')]
        if len(cells) != 2 or not all(cells) or '**' in cells[0] or re.fullmatch(r'[-: ]+', cells[0]):
            continue
        abb, sbb = cells
        abb_id = 'abb-' + hashlib.sha256((layer+'|'+abb).encode()).hexdigest()[:12]
        sbb_id = 'sbb-' + hashlib.sha256(sbb.encode()).hexdigest()[:12]
        terms = list(TERMS.get(sbb, []))
        if sbb == 'GZAC':
            if 'Procesflows' in abb:
                terms = ['proces', 'processen', 'workflow', 'bpmn', 'orkestratie']
            elif 'Besluitvorming' in abb:
                terms = ['besluitvorming', 'beschikking', 'besluiten']
            else:
                terms = ['casus', 'casusregie', 'dossier', 'zaakafhandeling']
        if sbb == 'Platformvoorzieningen':
            terms = ['monitoring', 'observability', 'metriek'] if 'Monitoring' in abb else ['privacy', 'security', 'beveiliging', 'informatiebeveiliging', 'avg']
        terms.append(sbb.lower())
        item = {'id': abb_id, 'type': 'ABB', 'name': abb, 'layer': layer, 'terms': list(dict.fromkeys(terms)),
                'sbb_ids': [sbb_id], 'quote': line, 'line': text[:start].count('\n')+offset+1,
                'section': MAPPING_HEADING[3:]+' / '+layer}
        abbs.append(item)
        if sbb_id not in sbbs:
            sbbs[sbb_id] = {'id': sbb_id, 'type': 'SBB', 'name': sbb, 'abb_ids': [], 'layer': layer}
        sbbs[sbb_id]['abb_ids'].append(abb_id)
    return {'source': {k: snapshot.get(k) for k in ('url', 'sha256', 'retrieved_at')},
            'method': 'Lokaal trefwoordadvies; ABB/SBB-relaties komen letterlijk uit de bronmapping.',
            'abbs': abbs, 'sbbs': list(sbbs.values())}


def load_catalogue() -> dict:
    return json.loads((ASSETS/'building-blocks.json').read_text(encoding='utf-8'))


def recommend(catalogue: dict, contexts: list[dict]) -> list[dict]:
    """Gebruik projectcontext, nooit de algemene enterprise-tekst als vraagcontext."""
    result = []
    for block in catalogue['abbs']:
        matches = []
        for context in contexts:
            text = context['text'].lower()
            hits = [term for term in block['terms'] if re.search(r'(?<!\w)'+re.escape(term.lower())+r'\w*', text)]
            if not hits:
                continue
            first = re.search(r'(?<!\w)'+re.escape(hits[0].lower())+r'\w*', text)
            matches.append({'source': context['source'], 'terms': hits,
                            'excerpt': context['text'][max(0, first.start()-45):first.end()+100].strip()})
        if matches:
            result.append({'id': block['id'], 'evidence': matches,
                           'score': sum(len(match['terms']) for match in matches)})
    return sorted(result, key=lambda item: -item['score'])


def selection_manifest(catalogue: dict, advice: list[dict], overrides: dict[str, bool]) -> dict:
    recommended = {item['id']: item for item in advice}
    abb_ids = {b['id'] for b in catalogue['abbs'] if overrides.get(b['id'], b['id'] in recommended)}
    mapped_sbb_ids = {i for b in catalogue['abbs'] if b['id'] in abb_ids for i in b['sbb_ids']}
    selected = []
    abb_by_id = {block['id']: block for block in catalogue['abbs']}
    for block in catalogue['abbs']+catalogue['sbbs']:
        default = block['id'] in (abb_ids if block['type'] == 'ABB' else mapped_sbb_ids)
        if not overrides.get(block['id'], default):
            continue
        parents = [abb_by_id[i] for i in block.get('abb_ids', []) if i in abb_ids]
        mappings = parents or [abb_by_id[i] for i in block.get('abb_ids', [])]
        evidence = recommended.get(block['id'], {}).get('evidence', []) if block['type'] == 'ABB' else [item for parent in parents for item in recommended.get(parent['id'], {}).get('evidence', [])]
        selected.append({'id': block['id'], 'type': block['type'], 'name': block['name'], 'layer': block['layer'],
                         'manual': block['id'] in overrides,
                         'evidence': evidence,
                         'mappings': [{k: parent[k] for k in ('id', 'name', 'quote', 'line', 'section')} for parent in mappings],
                         'abb_ids': block.get('abb_ids', []), 'quote': block.get('quote'),
                         'line': block.get('line'), 'section': block.get('section')})
    return {'status': 'Geadviseerd gebruik — te beoordelen door de architect',
            'method': catalogue['method'], 'catalogue_source': catalogue['source'], 'selected': selected,
            'recommendations': advice, 'overrides': dict(overrides)}


def advice_document(manifest: dict, catalogue: dict) -> str:
    """Geef generatie de gekozen voorstellen én de letterlijke bronmapping mee."""
    source = manifest['catalogue_source']
    lines = ['# Bouwblokkenadvies — VOORSTEL, geen vastgesteld besluit',
             'Broncatalogus: '+str(source['url']), 'SHA-256: '+str(source['sha256']),
             manifest['method'], 'Deze selectie is een advies en moet op toepasbaarheid worden beoordeeld.']
    abb_by_id = {b['id']: b for b in catalogue['abbs']}
    for block in manifest['selected']:
        lines.extend(['', f"## {block['type']}: {block['name']}", 'Laag: '+block['layer'],
                      'Selectie: '+('handmatig aangepast' if block['manual'] else 'automatisch geadviseerd')])
        mappings = [abb_by_id[block['id']]] if block['type'] == 'ABB' else [abb_by_id[i] for i in block['abb_ids']]
        for mapping in mappings:
            lines.append(f"Bronmapping ({mapping['section']}, regel {mapping['line']}): {mapping['quote']}")
        for evidence in block['evidence']:
            lines.append(f"Aanleiding uit {evidence['source']}: {', '.join(evidence['terms'])}; fragment: {evidence['excerpt']}")
    return '\n'.join(lines)
