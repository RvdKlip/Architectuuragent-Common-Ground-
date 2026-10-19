"""Lokale brug van het losse index-scherm naar Notion en Confluence.

Platformtokens blijven op de server. Stel PSA_SERVICE_TOKEN (minimaal 24 tekens)
veilig in en start met python publication_service.py. Geen tokens in index.html.
"""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import hashlib
import hmac
import json
import os
import threading

from architect_agent.sources import Source, SOURCE_LIMIT
from architect_agent.schemas import validate
from architect_agent.output import house_style
from architect_agent.notion import publish_plan as notion_publish
from architect_agent.confluence import publish_plan as confluence_publish
from architect_agent.ai import generate_plan
from architect_agent.epics import list_epics, get_epic, resolve_epic_link


def generate(payload, environment):
    if payload.get('allow_ai') is not True:
        raise ValueError('Bevestig dat de geselecteerde bronnen naar de AI-dienst mogen.')
    if not environment.get('OPENAI_API_KEY'):
        raise ValueError('De AI-koppeling is niet ingesteld op de lokale service.')
    house_style(payload['brand'])
    sources = [Source(str(item['key']), str(item['filename']), str(item['text']), int(item['pages']), 'tekst')
               for item in payload['sources']]
    if not sources or len(sources)>99 or [s.key for s in sources] != [f'B{i:02d}' for i in range(len(sources))]:
        raise ValueError('Ongeldige bronselectie of bronvolgorde.')
    if sum(len(source.text) for source in sources)>SOURCE_LIMIT:
        raise ValueError('De AI-bronset overschrijdt 900.000 tekens. Verklein aanvullende projectbronnen; de enterprise architectuur wordt niet afgekapt.')
    if not str(payload['project']).strip() or not str(payload['goals']).strip():
        raise ValueError('Vul projectnaam en afbakening in.')
    plan = generate_plan(sources, payload['project'], payload['goals'], environment.get('OPENAI_MODEL'), project_start=True)
    return {'plan':plan, 'method':'AI-synthese van de geselecteerde bronnen'}


def publish(payload, environment, completed):
    if payload.get('reviewed') is not True:
        raise ValueError('Beoordeel de PA en bevestig de publicatie eerst.')
    brand = payload['brand']; house_style(brand)
    plan = payload['plan']
    sources = [Source(str(item['key']), str(item['filename']), '', int(item['pages']), 'tekst')
               for item in payload['sources']]
    errors = validate(plan, sources)
    if errors:
        raise ValueError('; '.join(errors))
    targets = payload['destinations']
    if not targets or any(target not in ('Notion', 'Confluence') for target in targets):
        raise ValueError('Kies Notion en/of Confluence als publicatiebestemming.')
    fingerprint = hashlib.sha256(json.dumps({'plan':plan, 'sources':payload['sources'], 'brand':brand}, sort_keys=True).encode()).hexdigest()
    results = {}
    for target in dict.fromkeys(targets):
        key = (fingerprint, target)
        if key in completed:
            results[target] = {'status':'published', **completed[key], 'already_published':True}
            continue
        try:
            if target == 'Notion':
                if not environment.get('NOTION_TOKEN') or not environment.get('NOTION_PARENT_PAGE_ID'):
                    raise ValueError('Notion-koppeling ontbreekt op de publicatieservice.')
                result = notion_publish(plan, sources, environment['NOTION_PARENT_PAGE_ID'], environment['NOTION_TOKEN'], brand=brand)
            else:
                required = ('CONFLUENCE_BASE_URL','CONFLUENCE_EMAIL','CONFLUENCE_TOKEN','CONFLUENCE_SPACE_ID')
                if any(not environment.get(name) for name in required):
                    raise ValueError('Confluence-koppeling ontbreekt op de publicatieservice.')
                result = confluence_publish(plan, sources, brand, *(environment[name] for name in required),
                                            environment.get('CONFLUENCE_PARENT_ID',''))
            completed[key] = result
            results[target] = {'status':'published', **result}
        except Exception as error:
            results[target] = {'status':'not_published', 'message':str(error)}
    return results


def make_handler(environment):
    completed = {}
    lock = threading.Lock()
    token = environment.get('PSA_SERVICE_TOKEN','')
    if len(token) < 24 or not token.isascii() or '\n' in token or '\r' in token:
        raise ValueError('Stel PSA_SERVICE_TOKEN veilig in met minimaal 24 tekens.')
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass  # Geen tokens of documentinhoud in requestlogs.

        def origin_allowed(self):
            origin = self.headers.get('Origin')
            return origin in (None, 'null', 'http://127.0.0.1:8501', 'http://localhost:8501', 'https://rvdklip.github.io')

        def answer(self, status, data):
            self.send_response(status)
            if self.origin_allowed() and self.headers.get('Origin'):
                self.send_header('Access-Control-Allow-Origin', self.headers['Origin'])
            self.send_header('Vary','Origin')
            self.send_header('Access-Control-Allow-Headers','Authorization, Content-Type')
            self.send_header('Access-Control-Allow-Methods','POST, OPTIONS')
            self.send_header('Access-Control-Allow-Private-Network','true')
            self.send_header('Content-Type','application/json')
            self.end_headers()
            self.wfile.write(json.dumps(data).encode())

        def do_OPTIONS(self):
            self.answer(200 if self.origin_allowed() else 403, {})

        def do_POST(self):
            authorization = self.headers.get('Authorization','')
            if not self.origin_allowed() or not hmac.compare_digest(authorization, 'Bearer '+token):
                return self.answer(403, {'error':'Geen toegang tot de publicatieservice.'})
            if self.path not in ('/publish','/generate','/epics/list','/epics/get'):
                return self.answer(404, {'error':'Onbekend endpoint.'})
            try:
                length = int(self.headers.get('Content-Length','0'))
                if not 0 < length <= 8000000:
                    raise ValueError('Ongeldige of te grote publicatieaanvraag.')
                payload = json.loads(self.rfile.read(length))
                if self.path.startswith('/epics/'):
                    try:
                        if self.path == '/epics/list':
                            result = list_epics(payload.get('provider'), environment, payload.get('cursor'))
                        else:
                            result = resolve_epic_link(payload['url'], environment) if 'url' in payload else get_epic(payload.get('provider'), payload.get('id'), environment)
                        return self.answer(200, result)
                    except ValueError as error:
                        return self.answer(400, {'error':str(error)})
                    except Exception:
                        return self.answer(502, {'error':'Epic ophalen is niet gelukt. Controleer de epicbron en integratierechten.'})
                if self.path == '/generate':
                    try:
                        result = generate(payload, environment)
                    except ValueError as error:
                        return self.answer(400, {'error':str(error)})
                    except Exception:
                        return self.answer(502, {'error':'AI-generatie niet bevestigd. Controleer de AI-koppeling; de aanvraag kan wel verwerkt zijn.'})
                    self.answer(200, result)
                else:
                    with lock:
                        result = publish(payload, environment, completed)
                    self.answer(200, {'results':result})
            except (ValueError, TypeError, KeyError, AttributeError):
                self.answer(400, {'error':'Ongeldige PA, huisstijl of publicatiekeuze.'})
    return Handler


if __name__ == '__main__':
    server = ThreadingHTTPServer(('127.0.0.1',8765), make_handler(os.environ))
    print('Lokale publicatieservice actief op poort 8765. Platformtokens worden niet gedeeld met de browser.')
    server.serve_forever()
