"""No live Horizzon, paid APIs or publications; test actual MCP wire messages."""
from io import BytesIO
import json
from pathlib import Path
from unittest.mock import patch

import httpx
import pytest
from streamlit.testing.v1 import AppTest

from architect_agent import horizzon_mcp as mcp
from architect_agent.selection import SelectedDocument, missing_sources, write_documents
from architect_agent.sources import collect
from architect_agent.workflow import prepare
from publication_service import make_handler

TOOL = {'name': 'read_architecture', 'description': 'Lees architectuur',
        'annotations': {'readOnlyHint': True},
        'inputSchema': {'type': 'object', 'properties': {'query': {'type': 'string'}},
                        'required': ['query'], 'additionalProperties': False}}


@pytest.fixture
def server():
    state = {'requests': [], 'tools': [TOOL], 'status': 200, 'sse': False,
             'result': {'content': [{'type': 'text', 'text': 'Object R-17: bestaande zaakregistratie, relatie naar bedrijfsservice S-2.'}]}}
    def handle(request):
        payload = json.loads(request.content)
        state['requests'].append((payload, dict(request.headers)))
        assert str(request.url) == mcp.MCP_URL
        if state['status'] != 200:
            return httpx.Response(state['status'])
        method = payload['method']
        if method == 'initialize':
            result = {'protocolVersion': '2025-03-26', 'capabilities': {'tools': {}}, 'serverInfo': {'name': 'mock', 'version': '1'}}
        elif method == 'notifications/initialized':
            return httpx.Response(202)
        elif method == 'tools/list':
            result = {'tools': state['tools']}
        elif method == 'tools/call':
            result = state['result']
        else:
            raise AssertionError(method)
        message = {'jsonrpc': '2.0', 'id': payload['id'], 'result': result}
        if state['sse']:
            return httpx.Response(200, headers={'Content-Type': 'text/event-stream', 'Mcp-Session-Id': 'session-1'},
                                 text='event: message\r\ndata: '+json.dumps(message)+'\r\n\r\n')
        return httpx.Response(200, json=message, headers={'Mcp-Session-Id': 'session-1'})
    original = mcp.Client
    with patch.object(mcp, 'Client', side_effect=lambda environment=None: original(environment, httpx.MockTransport(handle))):
        yield state


@pytest.mark.parametrize('sse', [False, True])
def test_mcp_session_and_provenance(server, sse):
    server['sse'] = sse
    snapshot = mcp.read_source(TOOL['name'], {'query': 'Zaakgericht werken'}, environment={'HORIZZON_MCP_TOKEN': 'mock-token'})
    assert 'R-17' in snapshot['text'] and 'S-2' in snapshot['text']
    assert snapshot['url'] == mcp.MCP_URL
    assert len(snapshot['sha256']) == 64
    assert snapshot['retrieved_at'] in snapshot['text']
    assert 'mock-token' not in json.dumps(snapshot)
    messages = server['requests']
    assert [p['method'] for p, _ in messages] == ['initialize', 'notifications/initialized', 'tools/list', 'tools/call']
    assert all(h['authorization'] == 'Bearer mock-token' for _, h in messages)
    assert messages[-1][1]['mcp-session-id'] == 'session-1'
    assert messages[-1][1]['mcp-protocol-version'] == '2025-03-26'
    assert messages[-1][0]['params']['arguments'] == {'query': 'Zaakgericht werken'}


@pytest.mark.parametrize('status', [401, 403, 500, 302])
def test_failed_connection_is_not_a_source(server, status):
    server['status'] = status
    with pytest.raises(mcp.HorizzonError):
        mcp.read_source(TOOL['name'], {'query': 'x'}, environment={})
    assert not any(p['method'] == 'tools/call' for p, _ in server['requests'])


def test_schema_checked_before_call(server):
    with pytest.raises(mcp.HorizzonError, match='schema'):
        mcp.read_source(TOOL['name'], {'typo': 'x'}, environment={})
    assert not any(p['method'] == 'tools/call' for p, _ in server['requests'])


def test_write_tools_blocked_even_if_confirmed(server):
    server['tools'] = [{**TOOL, 'annotations': {'readOnlyHint': False}}]
    assert mcp.discover({})['tools'] == []
    with pytest.raises(mcp.HorizzonError, match='leesacties'):
        mcp.read_source(TOOL['name'], {'query': 'x'}, True, {})
    assert not any(p['method'] == 'tools/call' for p, _ in server['requests'])


def test_unmarked_tool_needs_explicit_read_confirmation(server):
    server['tools'] = [{**TOOL, 'annotations': {}}]
    with pytest.raises(mcp.HorizzonError, match='leesacties'):
        mcp.read_source(TOOL['name'], {'query': 'x'}, environment={})
    assert mcp.read_source(TOOL['name'], {'query': 'x'}, True, {})['text']


@pytest.mark.parametrize('result', [{'content': []}, {'isError': True, 'content': [{'type': 'text', 'text': 'error'}]}])
def test_no_source_from_empty_or_error_result(server, result):
    server['result'] = result
    with pytest.raises(mcp.HorizzonError):
        mcp.read_source(TOOL['name'], {'query': 'x'}, environment={})


def test_no_token_forwarded_to_arbitrary_url():
    with pytest.raises(mcp.HorizzonError, match='HORIZZON_MCP_URL'):
        mcp.Client({'HORIZZON_MCP_URL': 'https://example.org', 'HORIZZON_MCP_TOKEN': 'mock-token'})


def test_both_foundations_reach_generation_with_source_codes(server, tmp_path):
    snapshot = mcp.read_source(TOOL['name'], {'query': 'zaken'}, environment={})
    docs = [SelectedDocument('enterprise', 'EA.md', b'Platformkader: gegevens bij de bron.'),
            SelectedDocument('horizzon', snapshot['name'], snapshot['text'].encode())]
    assert not missing_sources(['enterprise', 'horizzon'], docs)
    assert missing_sources(['enterprise', 'horizzon'], docs[:1])
    paths = write_documents(docs, tmp_path)
    with patch('architect_agent.workflow.generate_plan', return_value={}) as generate:
        prepare(None, paths, 'Zaakgericht werken', 'Toets beide architecturen', project_start=True)
    sources = generate.call_args.args[0]
    assert [s.key for s in sources] == ['B00', 'B01']
    assert 'gegevens bij de bron' in sources[0].text
    assert 'R-17' in sources[1].text and mcp.MCP_URL in sources[1].text


def test_service_route_authentication_and_source_return(server):
    handler_class = make_handler({'PSA_SERVICE_TOKEN': 'local-test-only-service-key'})
    def request(token):
        handler = object.__new__(handler_class)
        data = json.dumps({'tool': TOOL['name'], 'arguments': {'query': 'zaken'}}).encode()
        handler.headers = {'Authorization': 'Bearer '+token, 'Content-Length': str(len(data)), 'Origin': 'null'}
        handler.path = '/horizzon/read'
        handler.rfile = BytesIO(data)
        answers = []
        handler.answer = lambda status, data: answers.append((status, data))
        handler.do_POST()
        return answers[0]
    assert request('wrong')[0] == 403
    assert not server['requests']
    status, data = request('local-test-only-service-key')
    assert status == 200 and 'R-17' in data['text']


def test_streamlit_requires_horizzon_and_includes_snapshot(server, tmp_path):
    snapshot = mcp.read_source(TOOL['name'], {'query': 'zaken'}, environment={})
    enterprise = {'text': '# Enterprise Architectuur\nPlatformkader: gegevens bij de bron.',
                  'url': 'https://example.org/ea', 'sha256': 'a'*64, 'retrieved_at': snapshot['retrieved_at']}
    cache = tmp_path/'cache'; cache.touch()
    with patch('architect_agent.selection_ui.CACHE', cache), patch('architect_agent.selection_ui.load_enterprise', return_value=enterprise):
        at = AppTest.from_file(str(Path(__file__).parents[1]/'app.py')).run(timeout=30)
        at.text_input(key='project_name').set_value('Zaken')
        at.text_area(key='project_goals').set_value('Gegevens bij de bron').run()
        assert at.checkbox(key='use_horizzon').value
        assert next(b for b in at.button if b.label == 'Genereer de architectuur').disabled
        at.session_state['horizzon_snapshots'] = [snapshot]
        at.run()
        assert not at.exception
        assert not next(b for b in at.button if b.label == 'Genereer de architectuur').disabled
        names = at.dataframe[0].value['Bron'].tolist()
        assert snapshot['name'] in names and 'Enterprise-architectuur-volledig.md' in names
        at.checkbox(key='use_horizzon').uncheck().run()
        assert snapshot['name'] not in at.dataframe[0].value['Bron'].tolist()
