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


def test_streamlit_teams_link_is_a_selected_source_and_can_be_removed():
    at = AppTest.from_file(str(Path(__file__).parents[1]/'app.py')).run(timeout=30)
    at.selectbox(key='epic_provider').set_value('teams').run()
    at.text_input(key='epic_link_teams').set_value('https://teams.microsoft.com/l/message/test/123')
    at.text_input(key='epic_title_teams').set_value('Testepic uit Teams')
    at.text_area(key='epic_description_teams').set_value('Een synthetische epicbeschrijving voor een broncontrole.').run()
    next(button for button in at.button if button.label=='Gebruik deze epic').click().run()
    assert not at.exception
    assert at.session_state['selected_epic']['provider'] == 'teams'
    assert any('Geselecteerde-epic.md' in frame.value['Bron'].tolist() for frame in at.dataframe)
    next(button for button in at.button if button.label=='Epic verwijderen').click().run()
    assert not at.exception
    assert not any('Geselecteerde-epic.md' in frame.value['Bron'].tolist() for frame in at.dataframe)
