import hashlib
import json
from pathlib import Path
from unittest.mock import patch

import pytest
from streamlit.testing.v1 import AppTest

from architect_agent.catalogue import chapter_document, chapters, load_enterprise
from architect_agent.selection import SelectedDocument, missing_sources, write_documents
from architect_agent.sources import collect
from architect_agent.workflow import prepare


@pytest.fixture
def snapshot():
    text = ('# Enterprise Architectuur\nDocumentoverzicht.\n'
            '# Managementsamenvatting\nGemeentelijke dienstverlening en kaders voor dit project.\n'
            '# Visie, principes, scope\nBronnen blijven verantwoordelijk voor hun gegevens.\n'
            '# Applicatiearchitectuur\nDeze niet-geselecteerde tekst moet buiten de analyse blijven.\n')
    return {'text': text, 'sha256': hashlib.sha256(text.encode()).hexdigest(),
            'retrieved_at': '2026-10-16T12:00:00+00:00', 'url': 'https://github.com/example/architecture'}


@pytest.fixture
def plan():
    data = json.loads((Path(__file__).parents[1]/'examples/example_plan.json').read_text())
    for item in data['changes'] + data['decision_rules']:
        item['evidence'] = ['B00 tekst']
    return data


def test_chapter_selection_preserves_text_and_provenance(snapshot):
    sections = chapters(snapshot['text'])
    assert ''.join(s.text for s in sections) == snapshot['text']
    selected = chapter_document(snapshot, ['1', '2'])
    assert sections[1].text in selected and sections[2].text in selected
    assert sections[3].text not in selected
    assert snapshot['sha256'] in selected and snapshot['url'] in selected
    assert 'overige hoofdstukken zijn niet meegenomen' in selected
    with pytest.raises(ValueError): chapter_document(snapshot, [])
    with pytest.raises(ValueError): chapter_document(snapshot, ['404'])


def test_fenced_code_does_not_create_chapters():
    text = '# Eerste\n```python\n# commentaar\n```\n# Tweede\nTekst\n'
    result = chapters(text)
    assert [s.title for s in result] == ['Eerste', 'Tweede']
    assert ''.join(s.text for s in result) == text


def test_missing_sources_are_not_treated_as_available():
    docs = [SelectedDocument('enterprise', 'ea.md', b'inhoud')]
    assert not missing_sources(['enterprise'], docs)
    assert missing_sources(['enterprise', 'horizon'], docs) == ['Bouwstenen Rotterdam']
    assert missing_sources(['enterprise'], [SelectedDocument('enterprise', 'ea.md', b'')])


def test_upload_paths_preserve_names_and_cannot_escape(tmp_path):
    docs = [SelectedDocument('project', '../../bron.md', b'Unieke brontekst nummer een voor het project.'),
            SelectedDocument('project', r'C:\bron.md', b'Unieke brontekst nummer twee voor het project.')]
    paths = write_documents(docs, tmp_path)
    assert paths[0] != paths[1]
    assert all(p.name == 'bron.md' and p.is_relative_to(tmp_path) for p in paths)
    parsed = collect(paths)
    assert [s.key for s in parsed] == ['B00', 'B01']
    assert all(s.filename == 'bron.md' for s in parsed)


def test_snapshot_cache_detects_changed_content(snapshot, tmp_path):
    cache = tmp_path/'snapshot.json'
    cache.write_text(json.dumps(snapshot))
    with patch('architect_agent.catalogue.urlopen') as request:
        assert load_enterprise(cache) == snapshot
        request.assert_not_called()
    snapshot['text'] += 'wijziging'
    cache.write_text(json.dumps(snapshot))
    with pytest.raises(ValueError, match='gewijzigd'): load_enterprise(cache)


def test_new_psa_does_not_require_word_and_only_passes_selected_text(snapshot, plan, tmp_path):
    content = chapter_document(snapshot, ['1', '2'])
    paths = write_documents([SelectedDocument('enterprise', 'EA.md', content.encode())], tmp_path)
    with patch('architect_agent.workflow.generate_plan', return_value=plan) as generate:
        parsed, result = prepare(None, paths, 'Testproject', 'Projectdoel', project_start=True)
    assert result == plan
    assert len(parsed) == 1 and parsed[0].key == 'B00'
    assert 'niet-geselecteerde tekst' not in parsed[0].text
    assert generate.call_args.kwargs == {'project_start': True}


def test_psa_request_asks_for_new_architecture_with_selected_sources(snapshot, plan, tmp_path):
    from architect_agent.ai import generate_plan
    paths = write_documents([SelectedDocument('enterprise', 'EA.md',
                            chapter_document(snapshot, ['1']).encode())], tmp_path)
    sources = collect(paths)
    with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-only'}), patch('openai.OpenAI') as client:
        client.return_value.responses.create.return_value.output_text = json.dumps(plan)
        assert generate_plan(sources, 'Testproject', 'Testdoel', project_start=True) == plan
    request = client.return_value.responses.create.call_args.kwargs
    assert 'NIEUWE projectarchitectuur' in request['input']
    assert 'nieuwe concept-projectarchitectuur' in request['instructions']
    assert 'B00 tekst' in request['input']
    assert 'niet-geselecteerde tekst' not in request['input']


def test_source_limit_stops_before_api_call(tmp_path):
    path = tmp_path/'large.md'; path.write_text('Veel te lange brontekst. ' * 50000)
    with patch('architect_agent.workflow.generate_plan') as generate:
        with pytest.raises(ValueError, match='overschrijdt'):
            prepare(None, [path], 'Project', 'Doel', project_start=True)
        generate.assert_not_called()


def test_pa_screen_generates_from_all_chapters(snapshot, plan, tmp_path):
    cache = tmp_path/'cache'; cache.touch()
    with patch('architect_agent.selection_ui.CACHE', cache), \
         patch('architect_agent.selection_ui.load_enterprise', return_value=snapshot), \
         patch('architect_agent.workflow.generate_plan', return_value=plan) as generate:
        at = AppTest.from_file(str(Path(__file__).parents[1]/'app.py')).run(timeout=30)
        assert not at.exception
        assert at.title[0].value == 'Projectarchitectuur'
        assert at.checkbox(key='use_enterprise').value
        assert any('Enterprise architectuur Platform Dienstverlening' in c.label for c in at.checkbox)
        generate.assert_not_called()
        at.text_input(key='project_name').set_value('Nieuw dienstverleningsproject')
        at.text_area(key='project_goals').set_value('Maak dienstverlening toegankelijker.').run()
        button = next(b for b in at.button if b.label == 'Genereer PA')
        assert not button.disabled
        # Een geselecteerd kader zonder inhoud blokkeert generatie.
        at.checkbox(key='use_horizon').check().run()
        assert next(b for b in at.button if b.label == 'Genereer PA').disabled
        at.checkbox(key='use_horizon').uncheck().run()
        next(b for b in at.button if b.label == 'Genereer PA').click().run()
        assert not at.exception
        assert generate.call_count == 1
        assert generate.call_args.kwargs == {'project_start': True}
        assert snapshot['text'].strip() in generate.call_args.args[0][0].text
        assert not at.multiselect
        assert at.session_state['agent_selection']['enterprise_architecture']['all_chapters']
        assert at.session_state['agent_base'] is None
        assert at.session_state['agent_selection']['project'] == 'Nieuw dienstverleningsproject'


def test_enterprise_deselection_excludes_source(snapshot, tmp_path):
    cache = tmp_path/'cache'; cache.touch()
    with patch('architect_agent.selection_ui.CACHE', cache), \
         patch('architect_agent.selection_ui.load_enterprise', return_value=snapshot):
        at = AppTest.from_file(str(Path(__file__).parents[1]/'app.py')).run(timeout=30)
        at.checkbox(key='use_enterprise').uncheck().run()
        assert not at.exception
        assert at.metric[0].value == '0'
        assert not at.dataframe
        assert next(b for b in at.button if b.label == 'Genereer PA').disabled
