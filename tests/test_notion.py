import json
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError, URLError

import pytest

from architect_agent.notion import (
    NotionPublishError, _request, blocks_for_plan, page_id, publish_plan,
)
from architect_agent.sources import Source

PARENT = '01234567-89ab-cdef-0123-456789abcdef'
PAGE = {'id': '87654321-89ab-cdef-0123-456789abcdef', 'url': 'https://www.notion.so/resultaat'}


@pytest.fixture
def plan():
    return json.loads((Path(__file__).parents[1]/'examples/example_plan.json').read_text())


@pytest.fixture
def sources():
    return [Source(f'B{i:02d}', f'bron{i}.pdf', 'Vertrouwelijke brontekst niet publiceren', 30, 'pdf')
            for i in range(3)]


def text_of(blocks):
    return '\n'.join(''.join(t['text']['content'] for t in b[b['type']]['rich_text']) for b in blocks)


def test_blocks_preserve_content_and_exclude_raw_sources(plan, sources):
    text = text_of(blocks_for_plan(plan, sources))
    assert plan['management_summary'] in text
    for change in plan['changes']:
        assert change['change'] in text
        assert change['rationale'] in text
        assert all(c in text for c in change['evidence'])
    for layer in plan['layers']:
        assert all(c in text for c in layer['components'])
    for key, value in plan['adr'].items():
        if key == 'title': assert value in text
        elif isinstance(value, list): assert all(v in text for v in value)
        else: assert value in text
    for key in ['flow_steps', 'open_decisions', 'assumptions']:
        assert all(v in text for v in plan[key])
    assert all(s.reference in text for s in sources)
    assert all(s.text not in text for s in sources)
    assert 'CONCEPT' in text


def test_large_text_is_not_truncated(plan, sources):
    plan['management_summary'] = 'ä' * 25001
    blocks = blocks_for_plan(plan, sources)
    assert text_of(blocks).count('ä') == 25001
    assert all(len(t['text']['content']) <= 2000
               for b in blocks for t in b[b['type']]['rich_text'])


@pytest.mark.parametrize('value', [PARENT, PARENT.replace('-', ''),
    'https://www.notion.so/team/Pagina-' + PARENT.replace('-', '') + '?source=copy_link'])
def test_parent_id(value):
    assert page_id(value) == PARENT


def test_publish_batches_and_never_creates_word(plan, sources):
    plan['open_decisions'] = ['Te beoordelen vraag'] * 220
    blocks = blocks_for_plan(plan, sources)
    with patch('architect_agent.notion._request', side_effect=[PAGE, {}, {}, {}]) as request:
        result = publish_plan(plan, sources, PARENT, 'test-token')
    assert result == PAGE
    first = request.call_args_list[0].args
    assert first[:3] == ('POST', 'pages', 'test-token')
    assert first[3]['parent']['page_id'] == PARENT
    assert first[3]['properties']['title']['title'][0]['text']['content'].endswith('CONCEPT')
    actual = []
    for call in request.call_args_list:
        assert len(call.args[3]['children']) <= 100
        actual.extend(call.args[3]['children'])
    assert actual == blocks
    assert all(c.args[0:2] == ('PATCH', f"blocks/{PAGE['id']}/children")
               for c in request.call_args_list[1:])


def test_invalid_concept_does_not_contact_notion(plan, sources):
    plan['adr']['status'] = 'Vastgesteld'
    with patch('architect_agent.notion._request') as request:
        with pytest.raises(ValueError, match='CONCEPT'):
            publish_plan(plan, sources, PARENT, 'test-token')
        request.assert_not_called()


@pytest.mark.parametrize('parent, token', [('niet-een-id', 'test'),
    ('https://evil.example/'+PARENT, 'test'), (PARENT, ''), (PARENT, 'bad\nheader')])
def test_invalid_destination_and_token_do_not_send(parent, token, plan, sources):
    with patch('architect_agent.notion._request') as request:
        with pytest.raises(ValueError): publish_plan(plan, sources, parent, token)
        request.assert_not_called()


def test_partial_publish_identifies_page(plan, sources):
    plan['open_decisions'] = ['Vraag'] * 150
    with patch('architect_agent.notion._request', side_effect=[PAGE, NotionPublishError('Fout')]):
        with pytest.raises(NotionPublishError, match='gedeeltelijk') as exc:
            publish_plan(plan, sources, PARENT, 'test')
    assert exc.value.page_url == PAGE['url']


@pytest.mark.parametrize('error', [HTTPError('url', 401, 'SECRET', {}, None),
                                  URLError('SECRET')])
def test_request_errors_redact_details_and_do_not_retry(error):
    with patch('architect_agent.notion.urlopen', side_effect=error) as request:
        with pytest.raises(NotionPublishError) as exc:
            _request('POST', 'pages', 'SECRET', {})
    assert 'SECRET' not in str(exc.value)
    assert request.call_count == 1


def test_request_uses_fixed_https_destination_and_auth_headers():
    with patch('architect_agent.notion.urlopen') as send:
        send.return_value.__enter__.return_value.read.return_value = json.dumps(PAGE).encode()
        assert _request('POST', 'pages', 'test-token', {'children': []}) == PAGE
    request = send.call_args.args[0]
    assert request.full_url == 'https://api.notion.com/v1/pages'
    assert request.get_header('Authorization') == 'Bearer test-token'
    assert json.loads(request.data) == {'children': []}


def test_web_review_then_publish_without_word(plan, sources, tmp_path):
    from streamlit.testing.v1 import AppTest
    at = AppTest.from_file(str(Path(__file__).parents[1]/'app.py'))
    at.session_state['agent_plan_json'] = json.dumps(plan)
    at.session_state['review_json'] = json.dumps(plan)
    at.session_state['agent_sources'] = sources
    at.session_state['agent_root'] = str(tmp_path)
    at.session_state['agent_base'] = None
    at.run(timeout=30)
    assert not at.exception
    for field in at.text_input:
        if field.label == 'Notion-integratiesleutel': field.set_value('test-token')
        if field.label.startswith('Bovenliggende Notion-pagina'): field.set_value(PARENT)
    at.run()
    publish = next(b for b in at.button if b.label == '2 · Publiceer concept in Notion')
    assert publish.disabled
    at.checkbox[0].check().run()
    with patch('architect_agent.notion.publish_plan', return_value=PAGE) as send:
        next(b for b in at.button if b.label == '2 · Publiceer concept in Notion').click().run()
        assert not at.exception
        assert send.call_count == 1
        assert send.call_args.args == (plan, sources, PARENT, 'test-token')
    assert any('gepubliceerd' in s.value for s in at.success)
    assert not list(tmp_path.iterdir())
    at.run()
    assert next(b for b in at.button if b.label == '2 · Publiceer concept in Notion').disabled
    # Een aangepast concept vereist een nieuwe review.
    changed = dict(plan, scope='Nieuwe scope')
    at.text_area[0].set_value(json.dumps(changed)).run()
    assert not at.checkbox[0].value
    assert next(b for b in at.button if b.label == '2 · Publiceer concept in Notion').disabled
