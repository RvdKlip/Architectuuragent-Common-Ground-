import json
from pathlib import Path
from unittest.mock import patch

import fitz
import pytest

from architect_agent.output import report_pdf, report_html, house_style
from architect_agent.sources import Source
from architect_agent.confluence import publish_plan as confluence_publish
from architect_agent.notion import publish_plan as notion_publish
from publication_service import publish, make_handler, generate


@pytest.fixture
def plan():
    return json.loads((Path(__file__).parents[1]/'examples/example_plan.json').read_text())


@pytest.fixture
def sources():
    return [Source(f'B{i:02d}', f'bron{i}.pdf', 'Deze volledige brontekst mag niet worden gepubliceerd.', 30, 'pdf') for i in range(3)]


@pytest.mark.parametrize('brand,color', [('Rotterdam','#00811F'),('Common Ground','#0D4F67')])
def test_pdf_contains_psa_and_chosen_brand(plan, sources, brand, color):
    pdf = report_pdf(plan, sources, brand)
    assert pdf.startswith(b'%PDF')
    with fitz.open(stream=pdf, filetype='pdf') as doc:
        text = '\n'.join(page.get_text() for page in doc)
        assert brand in text
        assert 'Managementsamenvatting' in text
        assert 'Openstaande' in text or 'Open besluiten' in text
        assert 'Signaalmanagement' in text
        assert sources[0].text not in text
        rgb = tuple(int(color[index:index+2],16)/255 for index in (1,3,5))
        assert any(shape['fill'] and all(abs(a-b)<.01 for a,b in zip(shape['fill'],rgb)) for shape in doc[0].get_drawings())


def test_html_housestyle_escapes_source_content(plan, sources):
    plan['title'] = '<script>alert(1)</script>'
    html = report_html(plan,sources,'Rotterdam')
    assert '#00811F' in html and 'Huisstijl: Rotterdam' in html
    assert '<script>' not in html and '&lt;script&gt;' in html
    with pytest.raises(ValueError):house_style('Onbekende huisstijl')


def test_confluence_posts_selected_style_and_only_psa(plan, sources):
    with patch('architect_agent.confluence.urlopen') as send:
        send.return_value.__enter__.return_value.read.return_value = b'{"id":"123"}'
        result = confluence_publish(plan,sources,'Rotterdam','https://voorbeeld.atlassian.net','user@example.test','test-only','456','789')
    request = send.call_args.args[0]
    payload = json.loads(request.data)
    assert request.full_url == 'https://voorbeeld.atlassian.net/wiki/api/v2/pages'
    assert payload['parentId'] == '789' and payload['spaceId'] == '456'
    assert '#00811F' in payload['body']['value']
    assert 'Huisstijl: Rotterdam' in payload['body']['value']
    assert sources[0].text not in payload['body']['value']
    assert result['id'] == '123'


def test_confluence_does_not_send_token_to_untrusted_host(plan,sources):
    with patch('architect_agent.confluence.urlopen') as send:
        with pytest.raises(ValueError):confluence_publish(plan,sources,'Rotterdam','https://evil.example','user','test-only','456')
        send.assert_not_called()


def test_notion_style_uses_supported_platform_color(plan,sources):
    with patch('architect_agent.notion._request',return_value={'id':'123','url':'https://www.notion.so/123'}) as send:
        notion_publish(plan,sources,'0123456789abcdef0123456789abcdef','test-only',brand='Rotterdam')
    blocks=[block for call in send.call_args_list for block in call.args[3]['children']]
    assert blocks[0]['paragraph']['color']=='green'
    assert 'Rotterdam' in blocks[0]['paragraph']['rich_text'][0]['text']['content']
    assert all(block[block['type']]['color']=='green' for block in blocks if block['type'].startswith('heading_'))


def payload(plan):
    return {'plan':plan,'sources':[{'key':f'B{i:02d}','filename':f'bron{i}.pdf','pages':30} for i in range(3)],
            'brand':'Rotterdam','reviewed':True,'destinations':['Notion','Confluence']}


def test_publication_service_requires_review_and_platform_setup(plan):
    data=payload(plan)
    with patch('publication_service.notion_publish') as notion,patch('publication_service.confluence_publish') as confluence:
        data['reviewed']=False
        with pytest.raises(ValueError):publish(data,{}, {})
        data['reviewed']=True
        result=publish(data,{}, {})
        assert all(item['status']=='not_published' for item in result.values())
        notion.assert_not_called();confluence.assert_not_called()
    with pytest.raises(ValueError):make_handler({})


def test_confirmed_publication_is_not_duplicated(plan):
    environment={'NOTION_TOKEN':'test-only','NOTION_PARENT_PAGE_ID':'123',
                 'CONFLUENCE_BASE_URL':'https://example.atlassian.net','CONFLUENCE_EMAIL':'example@example.test',
                 'CONFLUENCE_TOKEN':'test-only','CONFLUENCE_SPACE_ID':'456'}
    done={}
    with patch('publication_service.notion_publish',return_value={'id':'1','url':'https://notion.so/1'}) as notion,patch('publication_service.confluence_publish',return_value={'id':'2','url':'https://example.atlassian.net/2'}) as confluence:
        first=publish(payload(plan),environment,done)
        second=publish(payload(plan),environment,done)
        assert all(item['status']=='published' for item in first.values())
        assert all(item['already_published'] for item in second.values())
        assert notion.call_count == confluence.call_count == 1
        assert notion.call_args.kwargs == {'brand':'Rotterdam'}


def test_ai_generation_requires_explicit_consent_and_connection(plan):
    data={'allow_ai':False,'brand':'Rotterdam','project':'Project','goals':'Doel',
          'sources':[{'key':'B00','filename':'bron.md','pages':1,'text':'Documentinhoud voor de architectuur.'}]}
    with patch('publication_service.generate_plan') as ai:
        with pytest.raises(ValueError,match='Bevestig'):generate(data,{})
        data['allow_ai']=True
        with pytest.raises(ValueError,match='niet ingesteld'):generate(data,{})
        ai.assert_not_called()


def test_ai_generation_sends_only_selected_sources(plan):
    data={'allow_ai':True,'brand':'Common Ground','project':'Project','goals':'Doel',
          'sources':[{'key':'B00','filename':'gekozen.md','pages':1,'text':'Alleen de geselecteerde broninhoud.'}]}
    with patch('publication_service.generate_plan',return_value=plan) as ai:
        result=generate(data,{'OPENAI_API_KEY':'test-only','OPENAI_MODEL':'test-model'})
    assert result['plan']==plan
    assert len(ai.call_args.args[0])==1
    assert ai.call_args.args[0][0].filename=='gekozen.md'
    assert ai.call_args.args[3]=='test-model'
    assert ai.call_args.kwargs=={'project_start':True}


def test_ai_generation_rejects_oversized_sources_before_api():
    data={'allow_ai':True,'brand':'Rotterdam','project':'Project','goals':'Doel',
          'sources':[{'key':'B00','filename':'lang.md','pages':1,'text':'x'*900001}]}
    with patch('publication_service.generate_plan') as ai:
        with pytest.raises(ValueError,match='900.000'):generate(data,{'OPENAI_API_KEY':'test-only'})
        ai.assert_not_called()
