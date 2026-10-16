"""Read-only epic connectors. Tokens remain on the local service."""
import json
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlparse
from uuid import UUID

NOTION_EPICS_URL = 'https://app.notion.com/p/platformvoordienstverlening/e9375da1960249bba23c49d038d3c888?v=2b078b5f4db4808da728000c21a96e11'
NOTION_EPICS_ID = 'e9375da1-9602-49bb-a23c-49d038d3c888'


def _request(provider, method, path, token, body=None):
    base = 'https://api.notion.com/v1/'
    headers = {'Authorization': 'Bearer '+token, 'Content-Type': 'application/json'}
    if provider == 'notion':
        headers['Notion-Version'] = '2022-06-28'
    request = Request(base+path, data=json.dumps(body).encode() if body is not None else None, headers=headers, method=method)
    try:
        with urlopen(request, timeout=30) as response:
            data = response.read(5_000_001)
        if len(data) > 5_000_000:
            raise ValueError('De epicrespons is te groot. Gebruik een kleinere bronlijst.')
        return json.loads(data)
    except (HTTPError, URLError, OSError, TimeoutError):
        raise ValueError('Epics ophalen is niet gelukt. Controleer de bronconfiguratie, integratierechten en verbinding.') from None


def _notion_text(items):
    return ''.join(str(item.get('plain_text', item.get('text', {}).get('content', ''))) for item in items)


def _properties(page):
    lines = []
    title = ''
    for name, prop in page.get('properties', {}).items():
        kind = prop.get('type')
        if kind == 'title':
            title = _notion_text(prop.get('title', []))
        elif kind == 'rich_text':
            lines.append(name+': '+_notion_text(prop.get(kind, [])))
        elif kind in ('select', 'status') and prop.get(kind):
            lines.append(name+': '+str(prop[kind].get('name', '')))
    return title or 'Naamloze epic', '\n'.join(lines)


def _token(provider, env):
    if provider != 'notion':
        raise ValueError('Teams-epics worden met een eigen link en beschrijving toegevoegd.')
    token = env.get('NOTION_TOKEN', '')
    if not token:
        raise ValueError('Notion-koppeling is nog niet ingesteld op de lokale service.')
    if '\r' in token or '\n' in token:
        raise ValueError('Ongeldige integratieconfiguratie.')
    return token


def list_epics(provider, env, cursor=None):
    if provider not in ('notion', 'teams'):
        raise ValueError('Kies Notion of Microsoft Teams.')
    token = _token(provider, env)
    if provider == 'notion':
        database = str(UUID(env.get('NOTION_EPICS_DATABASE_ID') or NOTION_EPICS_ID))
        body = {'page_size': 100}
        if cursor:
            body['start_cursor'] = str(UUID(cursor))
        data = _request(provider, 'POST', 'databases/'+database+'/query', token, body)
        epics = []
        for page in data.get('results', []):
            title, text = _properties(page)
            epics.append({'id': page['id'], 'title': title, 'text': text, 'url': page.get('url', ''), 'provider': provider})
        return {'epics': epics, 'next_cursor': data.get('next_cursor') if data.get('has_more') else None}


def get_epic(provider, identifier, env):
    token = _token(provider, env)
    if provider == 'notion':
        identifier = str(UUID(identifier))
        page = _request(provider, 'GET', 'pages/'+identifier, token)
        expected = str(UUID(env.get('NOTION_EPICS_DATABASE_ID') or NOTION_EPICS_ID))
        if page.get('parent', {}).get('database_id') != expected:
            raise ValueError('De gekozen epic hoort niet bij de ingestelde Notion-database.')
        title, text = _properties(page)
        parts = [text]
        count = 0
        def read_blocks(block_id, depth=0):
            nonlocal count
            if depth > 12:
                raise ValueError('De epic is te diep genest. Gebruik een gecontroleerde export.')
            cursor = None
            while True:
                path = 'blocks/'+block_id+'/children?page_size=100'+('&start_cursor='+quote(cursor, safe='') if cursor else '')
                data = _request(provider, 'GET', path, token)
                for block in data.get('results', []):
                    count += 1
                    if count > 1000:
                        raise ValueError('De epic bevat te veel blokken. Gebruik een gecontroleerde export.')
                    kind = block['type']
                    content = block.get(kind, {})
                    if kind in ('child_database', 'child_page'):
                        parts.append('[Onderliggende pagina/database niet ingelezen: '+str(content.get('title', ''))+']')
                        continue
                    value = _notion_text(content.get('rich_text', []))
                    if kind == 'table_row':
                        value = ' | '.join(_notion_text(cell) for cell in content.get('cells', []))
                    if value:
                        parts.append(value)
                    if kind in ('image', 'file', 'pdf', 'embed', 'bookmark', 'link_preview', 'synced_block', 'unsupported'):
                        parts.append('[Niet tekstueel ingelezen blok: '+kind+']')
                    if block.get('has_children'):
                        read_blocks(block['id'], depth+1)
                if not data.get('has_more'):
                    break
                cursor = data.get('next_cursor')
                if not cursor:
                    raise ValueError('Onvolledige epicrespons van Notion.')
        read_blocks(identifier)
        text = '\n\n'.join(parts)
        url = page.get('url', '')
    else:
        raise ValueError('Kies Notion of Microsoft Teams.')
    if len(text) > 250000:
        raise ValueError('De epic is te groot; er wordt niets stilzwijgend afgekapt.')
    return {'id': identifier, 'title': title, 'text': text, 'url': url, 'provider': provider}


def epic_document(epic):
    return ('# Epic — '+epic['title']+'\n\nBron: '+epic['provider']+'\nID: '+epic['id']+'\nURL: '+epic.get('url', '')+'\nInhoud: '+('Beschrijving toegevoegd' if epic['text'].strip() else 'Alleen verwijzing; inhoud niet ingelezen')+'\n\n'+epic['text'])


def validate_epic_link(value, provider):
    uri = urlparse(value.strip())
    host = (uri.hostname or '').lower()
    if provider == 'notion':
        valid = any(host == base or host.endswith('.'+base) for base in ('app.notion.com', 'notion.so', 'notion.site'))
    elif provider == 'teams':
        valid = host in ('teams.microsoft.com', 'teams.cloud.microsoft', 'teams.live.com')
    else:
        valid = False
    if uri.scheme != 'https' or not valid or uri.username or uri.password or uri.port:
        raise ValueError('Gebruik een geldige HTTPS-link naar de gekozen epicbron.')
    return value.strip()
