"""Publiceer een gereviewd concept als nieuwe Notion-subpagina, zonder Word-export."""
from __future__ import annotations

import json
import re
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from uuid import UUID

from .schemas import validate


class NotionPublishError(RuntimeError):
    """Een publicatie kan onvolledig zijn; page_url verwijst dan naar het concept."""

    def __init__(self, message: str, page_url: str | None = None):
        super().__init__(message)
        self.page_url = page_url


def page_id(value: str) -> str:
    value = value.strip()
    if value.startswith('https://'):
        url = urlparse(value)
        host = url.hostname or ''
        if not (host == 'notion.so' or host.endswith('.notion.so')
                or host == 'notion.site' or host.endswith('.notion.site')):
            raise ValueError('Gebruik een Notion-paginalink of pagina-ID.')
        value = url.path.rstrip('/').rsplit('/', 1)[-1]
        match = re.search(r'([0-9a-fA-F]{32}|[0-9a-fA-F-]{36})$', value)
        value = match.group(1) if match else ''
    try:
        return str(UUID(value))
    except (ValueError, AttributeError):
        raise ValueError('Ongeldige Notion-pagina-ID. Kopieer de link van de bovenliggende pagina.') from None


def rich_text(text: str) -> list[dict]:
    # Notion beperkt iedere text.content tot 2.000 tekens.
    return [{'type': 'text', 'text': {'content': text[i:i+2000]}}
            for i in range(0, len(text), 2000)]


def blocks_for_plan(plan: dict, sources: list) -> list[dict]:
    errors = validate(plan, sources)
    if errors:
        raise ValueError('Concept-JSON bevat fouten: ' + '; '.join(errors))
    blocks = []

    def add(kind, text):
        # Houd ook het aantal rich-text-elementen per blok ruim onder de API-limiet.
        for offset in range(0, max(1, len(text)), 10000):
            blocks.append({'object': 'block', 'type': kind,
                           kind: {'rich_text': rich_text(text[offset:offset+10000])}})

    def heading(text):
        add('heading_2', text)

    def paragraph(text):
        add('paragraph', text)

    def bullets(items):
        for item in items:
            add('bulleted_list_item', item)

    paragraph('CONCEPT — ter review en besluitvorming. Publicatie in Notion stelt dit voorstel niet formeel vast.')
    paragraph('Onderwerp: ' + plan['scope'])
    heading('Managementsamenvatting')
    paragraph(plan['management_summary'])
    heading('Voorgestelde wijzigingen')
    for change in plan['changes']:
        add('heading_3', change['section'])
        paragraph(change['change'])
        paragraph('Onderbouwing: ' + change['rationale'])
        paragraph('Bron: ' + ', '.join(change['evidence']))
    heading('Architectuur in vijf lagen')
    for layer in sorted(plan['layers'], key=lambda x: x['number'], reverse=True):
        add('heading_3', f"{layer['number']}. {layer['name']}")
        bullets(layer['components'])
    heading('Gegevensstroom')
    for step in plan['flow_steps']:
        add('numbered_list_item', step)
    heading('ADR — CONCEPT: ' + plan['adr']['title'])
    adr = plan['adr']
    paragraph('Status: ' + adr['status'])
    for title, key in [('Context', 'context'), ('Besluit (voorgesteld)', 'decision'),
                       ('Principe', 'principles'), ('Implicatie', 'implications'),
                       ('Eventuele zorgen', 'concerns'), ('Implementatie', 'implementation'),
                       ('Samenhang met bestaande ADR’s', 'relation_existing_adrs')]:
        add('heading_3', title)
        if isinstance(adr[key], list):
            bullets(adr[key])
        else:
            paragraph(adr[key])
    heading('Architectuurregels')
    for rule in plan['decision_rules']:
        paragraph(f"{rule['id']} — {rule['rule']}\nBron: {', '.join(rule['evidence'])}\nStatus: {rule['status']}")
    heading('Openstaande besluiten')
    bullets(plan['open_decisions'])
    heading('Aannames en controlepunten')
    bullets(plan['assumptions'])
    heading('Bronnen en herleidbaarheid')
    bullets([s.reference for s in sources])
    paragraph('Verifieer de bronverwijzingen handmatig. Bronbestanden en volledige bronteksten zijn niet meegestuurd naar Notion.')
    return blocks


def _request(method: str, path: str, token: str, payload: dict) -> dict:
    request = Request('https://api.notion.com/v1/' + path,
                      data=json.dumps(payload, ensure_ascii=False).encode('utf-8'),
                      headers={'Authorization': 'Bearer ' + token,
                               'Notion-Version': '2022-06-28',
                               'Content-Type': 'application/json'}, method=method)
    try:
        with urlopen(request, timeout=30) as response:
            return json.load(response)
    except HTTPError as error:
        messages = {
            401: 'De Notion-integratiesleutel is ongeldig.',
            403: 'De Notion-integratie heeft onvoldoende rechten.',
            404: 'De Notion-pagina is niet gevonden of niet gedeeld met de integratie.',
            429: 'Notion begrenst het aantal verzoeken. Controleer eerst of de pagina is aangemaakt.',
        }
        raise NotionPublishError(messages.get(error.code, f'Notion gaf HTTP {error.code}. Controleer de doelpagina voordat je opnieuw publiceert.')) from None
    except (URLError, TimeoutError, OSError, ValueError):
        # Geen automatische retries: een time-out kan optreden ná het aanmaken.
        raise NotionPublishError('Geen bevestiging van Notion ontvangen. Controleer de doelpagina voordat je opnieuw publiceert; de pagina kan al zijn aangemaakt.') from None


def publish_plan(plan: dict, sources: list, parent: str, token: str) -> dict:
    """Maak een nieuwe subpagina. Alleen aanroepen na expliciete publicatieactie."""
    parent = page_id(parent)
    token = token.strip()
    if not token or '\n' in token or '\r' in token:
        raise ValueError('Vul een geldige Notion-integratiesleutel in.')
    blocks = blocks_for_plan(plan, sources)
    title = plan['title'] + ' — CONCEPT'
    if len(title) > 2000:
        raise ValueError('De paginatitel is te lang voor Notion (maximaal 2.000 tekens).')
    page = _request('POST', 'pages', token, {
        'parent': {'type': 'page_id', 'page_id': parent},
        'properties': {'title': {'type': 'title', 'title': rich_text(title)}},
        'children': blocks[:100],
    })
    try:
        for offset in range(100, len(blocks), 100):
            _request('PATCH', f"blocks/{page['id']}/children", token,
                     {'children': blocks[offset:offset+100]})
    except NotionPublishError as error:
        raise NotionPublishError('De Notion-pagina is gedeeltelijk gevuld. ' + str(error), page['url']) from None
    return {'id': page['id'], 'url': page['url']}
