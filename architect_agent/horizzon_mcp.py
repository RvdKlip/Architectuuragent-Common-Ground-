"""Read-only MCP snapshots from Rotterdam Horizzon; credentials stay server-side."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os

import httpx

MCP_URL = 'https://rotterdam.mcp.horizzon.cloud/mcp'
MAX_BYTES = 4_000_000


class HorizzonError(ValueError):
    pass


class Client:
    def __init__(self, environment=None, transport=None):
        environment = os.environ if environment is None else environment
        # Never accept a browser-supplied URL or send credentials to another host.
        if environment.get('HORIZZON_MCP_URL', MCP_URL).rstrip('/') != MCP_URL:
            raise HorizzonError('Gebruik https://rotterdam.mcp.horizzon.cloud/mcp als HORIZZON_MCP_URL.')
        headers = {'Accept': 'application/json, text/event-stream'}
        if environment.get('HORIZZON_MCP_TOKEN'):
            headers['Authorization'] = 'Bearer ' + environment['HORIZZON_MCP_TOKEN']
        self.http = httpx.Client(headers=headers, timeout=30, follow_redirects=False, transport=transport)
        self.number = 0

    def __enter__(self):
        try:
            result = self.rpc('initialize', {'protocolVersion': '2025-03-26', 'capabilities': {},
                                            'clientInfo': {'name': 'common-ground-architectuuragent', 'version': '1.0'}})
            version = result.get('protocolVersion')
            if version not in ('2024-11-05', '2025-03-26', '2025-06-18', '2025-11-25'):
                raise HorizzonError('Horizzon gebruikt een niet-ondersteunde MCP-protocolversie.')
            self.http.headers['MCP-Protocol-Version'] = version
            self.rpc('notifications/initialized', notification=True)
            return self
        except Exception:
            self.http.close()
            raise

    def __exit__(self, *args):
        self.http.close()

    def rpc(self, method, params=None, notification=False):
        self.number += 1
        body = {'jsonrpc': '2.0', 'method': method}
        if params is not None:
            body['params'] = params
        if not notification:
            body['id'] = self.number
        try:
            with self.http.stream('POST', MCP_URL, json=body) as response:
                if response.status_code in (401, 403):
                    raise HorizzonError('Horizzon weigert toegang. Controleer netwerktoegang en de door Bizzdesign vereiste authenticatie op de lokale service.')
                if response.status_code != (202 if notification else 200):
                    # Some MCP servers acknowledge notifications with an empty 200/204.
                    if not (notification and response.status_code in (200, 204)):
                        raise HorizzonError(f'Horizzon antwoordt met HTTP {response.status_code}.')
                if response.headers.get('Mcp-Session-Id'):
                    self.http.headers['Mcp-Session-Id'] = response.headers['Mcp-Session-Id']
                if notification:
                    return {}
                raw = bytearray()
                sse = 'text/event-stream' in response.headers.get('content-type', '')
                for chunk in response.iter_bytes():
                    raw.extend(chunk)
                    if len(raw) > MAX_BYTES:
                        raise HorizzonError('Horizzon-antwoord te groot; verklein de selectie. Er wordt niets afgekapt.')
                    if sse:
                        # Process complete SSE events, including multi-line data fields.
                        normalized = bytes(raw).replace(b'\r\n', b'\n')
                        events = normalized.split(b'\n\n')[:-1]
                        for event in events:
                            data = b'\n'.join(line[5:].lstrip(b' ') for line in event.split(b'\n') if line.startswith(b'data:'))
                            if data:
                                message = json.loads(data)
                                if message.get('id') == body['id']:
                                    return self.result(message)
                if sse:
                    raise HorizzonError('Geen volledig MCP-antwoord van Horizzon ontvangen.')
                message = json.loads(raw)
                if message.get('id') != body['id']:
                    raise HorizzonError('Horizzon gaf een antwoord met een onverwacht verzoeknummer.')
                return self.result(message)
        except (httpx.HTTPError, OSError):
            raise HorizzonError('Horizzon is niet bereikbaar. Controleer de netwerktoegang tot rotterdam.mcp.horizzon.cloud en de authenticatie.') from None
        except (json.JSONDecodeError, UnicodeError, AttributeError, TypeError):
            raise HorizzonError('Horizzon gaf geen geldig MCP-antwoord.') from None

    @staticmethod
    def result(message):
        if 'error' in message:
            raise HorizzonError('Horizzon kon de MCP-actie niet uitvoeren. Controleer de gekozen leesfunctie en parameters.')
        result = message.get('result')
        if not isinstance(result, dict):
            raise HorizzonError('Horizzon gaf geen geldig MCP-resultaat.')
        return result

    def tools(self):
        tools, cursor, seen = [], None, set()
        for _ in range(20):
            result = self.rpc('tools/list', {'cursor': cursor} if cursor else {})
            page = result.get('tools')
            if not isinstance(page, list) or any(not isinstance(t, dict) or not isinstance(t.get('name'), str) for t in page):
                raise HorizzonError('Horizzon gaf geen geldige lijst met functies.')
            tools.extend(page)
            cursor = result.get('nextCursor')
            if not cursor:
                return tools
            if not isinstance(cursor, str) or cursor in seen:
                break
            seen.add(cursor)
        raise HorizzonError('De Horizzon-functielijst is onvolledig. Probeer een kleinere selectie of neem contact op met de beheerder.')


def discover(environment=None):
    with Client(environment) as client:
        tools = client.tools()
    # Never expose known write functions through this source connector.
    return {'url': MCP_URL, 'tools': [t for t in tools if t.get('annotations', {}).get('readOnlyHint') is not False]}


def read_source(tool_name, arguments, confirmed_read_only=False, environment=None):
    if not isinstance(arguments, dict):
        raise HorizzonError('Vul de leesparameters in als JSON-object.')
    with Client(environment) as client:
        tool = next((t for t in client.tools() if t['name'] == tool_name), None)
        if tool is None:
            raise HorizzonError('Kies een beschikbare Horizzon-leesfunctie.')
        hint = tool.get('annotations', {}).get('readOnlyHint')
        if hint is False or (hint is not True and confirmed_read_only is not True):
            raise HorizzonError('Alleen leesacties zijn toegestaan. Bevestig bij een ongemarkeerde functie eerst dat dit een leesactie is.')
        from jsonschema import validate, ValidationError, SchemaError
        try:
            validate(arguments, tool.get('inputSchema', {'type': 'object'}))
        except (ValidationError, SchemaError):
            raise HorizzonError('De leesparameters voldoen niet aan het schema van de Horizzon-functie.') from None
        result = client.rpc('tools/call', {'name': tool_name, 'arguments': arguments})
    if result.get('isError'):
        raise HorizzonError('De Horizzon-leesactie is mislukt; er is geen bron toegevoegd.')
    texts = []
    for item in result.get('content', []):
        if item.get('type') == 'text' and isinstance(item.get('text'), str):
            texts.append(item['text'])
        elif item.get('type') == 'resource' and isinstance(item.get('resource', {}).get('text'), str):
            texts.append(item['resource']['text'])
    if result.get('structuredContent') is not None:
        texts.append(json.dumps(result['structuredContent'], ensure_ascii=False, indent=2))
    content = '\n\n'.join(texts).strip()
    if not content:
        raise HorizzonError('Horizzon leverde geen leesbare tekst. Kies een andere leesfunctie of haal de gevonden objecten inhoudelijk op.')
    if len(content) > 900_000:
        raise HorizzonError('De Horizzon-bron is te groot. Verklein de selectie; er wordt niets afgekapt.')
    stamp = datetime.now(timezone.utc).isoformat()
    digest = hashlib.sha256(content.encode()).hexdigest()
    metadata = {'url': MCP_URL, 'tool': tool_name, 'arguments': arguments, 'retrieved_at': stamp, 'sha256': digest}
    text = ('# Interne architectuurrepository Rotterdam — Horizzon\n\n'
            'Bronregistratie: ' + json.dumps(metadata, ensure_ascii=False) + '\n\n'
            'Dit is het resultaat van de gekozen leesactie, geen volledige kopie van de repository. '
            'Controleer de dekking, objectidentificaties en eventuele vervolgpagina’s. '
            'Een zoekresultaat bewijst niet dat de volledige objectinhoud is opgehaald.\n\n' + content)
    return {**metadata, 'name': 'Interne-architectuur-Rotterdam-Horizzon.md', 'text': text}
