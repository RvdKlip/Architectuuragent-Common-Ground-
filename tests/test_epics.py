import json
from unittest.mock import patch
from pathlib import Path
import pytest
from streamlit.testing.v1 import AppTest
from architect_agent.epics import list_epics, get_epic, validate_epic_link, epic_document, NOTION_EPICS_ID

PAGE = '11111111-1111-4111-8111-111111111111'
CURSOR = '22222222-2222-4222-8222-222222222222'
ENV = {'NOTION_TOKEN':'test-only-not-a-real-token'}


def page(parent=NOTION_EPICS_ID):
    return {'id':PAGE,'url':'https://www.notion.so/'+PAGE.replace('-',''),
            'parent':{'database_id':parent},'properties':{
                'Naam':{'type':'title','title':[{'plain_text':'Synthetische epic'}]},
                'Doel':{'type':'rich_text','rich_text':[{'plain_text':'Maak dienstverlening toegankelijk.'}]}}}


def test_notion_list_is_scoped_and_paginated():
    with patch('architect_agent.epics._request', return_value={'results':[page()], 'has_more':True, 'next_cursor':CURSOR}) as request:
        result = list_epics('notion', ENV, CURSOR)
    assert result['next_cursor'] == CURSOR
    assert result['epics'][0]['title'] == 'Synthetische epic'
    assert request.call_args.args[2] == 'databases/'+NOTION_EPICS_ID+'/query'
    assert request.call_args.args[4]['start_cursor'] == CURSOR
    assert request.call_args.args[0:2] == ('notion','POST')
    assert 'test-only' not in json.dumps(result)


def test_notion_selected_epic_reads_full_paginated_text_and_table():
    responses = [page(),
        {'results':[{'id':PAGE,'type':'paragraph','paragraph':{'rich_text':[{'plain_text':'Eerste bronfragment'}]},'has_children':False}], 'has_more':True,'next_cursor':CURSOR},
        {'results':[{'id':CURSOR,'type':'table_row','table_row':{'cells':[[{'plain_text':'Cel A'}],[{'plain_text':'Cel B'}]]},'has_children':False}], 'has_more':False}]
    with patch('architect_agent.epics._request', side_effect=responses) as request:
        result = get_epic('notion', PAGE, ENV)
    assert 'Eerste bronfragment' in result['text'] and 'Cel A | Cel B' in result['text']
    assert request.call_count == 3
    assert 'start_cursor='+CURSOR in request.call_args.args[2]
    assert 'URL: https://www.notion.so/' in epic_document(result)


def test_notion_refuses_other_database_and_missing_connection():
    with patch('architect_agent.epics._request', return_value=page(CURSOR)) as request:
        with pytest.raises(ValueError,match='hoort niet'):get_epic('notion',PAGE,ENV)
        assert request.call_count == 1
    with patch('architect_agent.epics._request') as request:
        with pytest.raises(ValueError,match='niet ingesteld'):list_epics('notion',{})
        with pytest.raises(ValueError):list_epics('teams',ENV)
        with pytest.raises(ValueError):get_epic('notion','https://evil.example',ENV)
        request.assert_not_called()


@pytest.mark.parametrize('url,provider', [
    ('https://teams.microsoft.com/l/message/thread/123?context=test','teams'),
    ('https://teams.cloud.microsoft/l/entity/test','teams'),
    ('https://app.notion.com/p/workspace/'+PAGE,'notion'),
])
def test_links_accept_actual_platform_urls(url, provider):
    assert validate_epic_link(url, provider) == url


@pytest.mark.parametrize('url', ['javascript:alert(1)','https://teams.microsoft.com.evil.example/l/test','https://evil.example','http://teams.microsoft.com/l/test','https://user@teams.microsoft.com/l/test'])
def test_teams_link_validation(url):
    with pytest.raises(ValueError):validate_epic_link(url,'teams')


def test_streamlit_link_resolves_details_and_invalidates_on_change():
    epic = {'provider':'teams','id':'123','url':'https://teams.microsoft.com/l/message/test/123',
            'title':'Testepic', 'text':'Gelezen beschrijving', 'mode':'connector'}
    with patch('architect_agent.epics_ui.resolve_epic_link', return_value=epic) as resolve:
        at = AppTest.from_file(str(Path(__file__).parents[1]/'app.py')).run(timeout=30)
        assert not any(s.label == 'Bron van de epic' for s in at.selectbox)
        at.text_input(key='epic_link').set_value(epic['url']).run()
        next(b for b in at.button if b.label == 'Epic ophalen').click().run()
        assert not at.exception
        assert at.session_state['selected_epic']['text'] == epic['text']
        assert any(i.value == epic['title'] and i.disabled for i in at.text_input)
        resolve.assert_called_once()
        at.text_input(key='epic_link').set_value('https://teams.microsoft.com/l/message/other/456').run()
        assert not any('Geselecteerde-epic.md' in frame.value['Bron'].tolist() for frame in at.dataframe)


def test_resolve_notion_link_uses_page_id():
    from architect_agent.epics import resolve_epic_link
    with patch('architect_agent.epics.get_epic', return_value={'title':'Epic', 'text':'Beschrijving'}) as get:
        result = resolve_epic_link('https://www.notion.so/Epic-'+PAGE.replace('-', ''), ENV)
    assert get.call_args.args == ('notion', PAGE, ENV)
    assert result['text'] == 'Beschrijving'


def test_resolve_teams_message_reads_graph_and_extracts_html():
    from architect_agent.epics import resolve_epic_link
    from unittest.mock import MagicMock
    response = MagicMock()
    response.__enter__.return_value.read.return_value = json.dumps({'id':'123','subject':'Epicnaam','body':{'contentType':'html','content':'<p>Eerste alinea</p><p>Tweede &amp; derde</p>'}}).encode()
    url = 'https://teams.microsoft.com/l/message/19%3Atest%40thread.tacv2/123?groupId='+PAGE
    with patch('architect_agent.epics.urlopen', return_value=response) as request:
        epic = resolve_epic_link(url, {'MICROSOFT_GRAPH_TOKEN':'test-only'})
    assert epic['title'] == 'Epicnaam'
    assert epic['text'] == 'Eerste alinea\nTweede & derde'
    assert request.call_args.args[0].full_url.startswith('https://graph.microsoft.com/v1.0/teams/'+PAGE+'/channels/')


@pytest.mark.parametrize('url', ['https://evil.example/a','http://teams.microsoft.com/a','https://teams.microsoft.com/l/meetup-join/test'])
def test_resolver_rejects_unsupported_links_without_network(url):
    from architect_agent.epics import resolve_epic_link
    with patch('architect_agent.epics.urlopen') as request:
        with pytest.raises(ValueError):
            resolve_epic_link(url, {'MICROSOFT_GRAPH_TOKEN':'test-only'})
        request.assert_not_called()
