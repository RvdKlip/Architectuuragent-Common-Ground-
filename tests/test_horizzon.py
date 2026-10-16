import json
import shutil
import subprocess
from pathlib import Path
import pytest
from architect_agent.horizzon import parse_export
from architect_agent.sources import collect
from architect_agent.workflow import prepare
from unittest.mock import patch

ROOT = Path(__file__).parents[1]


@pytest.mark.parametrize('name,text', [
    ('export.csv', '\ufeffObject ID;Naam;Bouwsteentype;Beschrijving\n1;Aanvraag;ABB;"Regel een aanvraag; bronbeschrijving"\n2;Oplossing;SBB;"Een ""geteste"" oplossing"\n3;Overig;ApplicationComponent;Geen ABB of SBB\n'),
    ('export.json', json.dumps({'objects': [{'id': '1', 'name': 'Aanvraag', 'type': 'Architecture Building Block', 'description': 'Regel een aanvraag; bronbeschrijving'}, {'id': '2', 'name': 'Oplossing', 'type': 'SBB', 'description': 'Een "geteste" oplossing'}, {'id': '3', 'name': 'Overig', 'type': 'ApplicationComponent'}]})),
])
def test_export_classification_and_js_parity(name, text):
    blocks, skipped = parse_export(text.encode(), name)
    assert [b['type'] for b in blocks] == ['ABB', 'SBB'] and skipped == 1
    assert blocks[0]['description'] == 'Regel een aanvraag; bronbeschrijving'
    if shutil.which('node'):
        result = subprocess.check_output(['node', '-e', 'const p=require("./web/horizzon.js");process.stdout.write(JSON.stringify(p.parse(process.argv[1],process.argv[2])))', text, name], cwd=ROOT, text=True)
        assert json.loads(result) == {'blocks': blocks, 'skipped': skipped}


def test_invalid_exports_do_not_invent_classification():
    with pytest.raises(ValueError, match='Geen ABB'):
        parse_export(b'id,name,type\n1,Component,ApplicationComponent', 'export.csv')
    with pytest.raises(ValueError, match='Dubbel'):
        parse_export(b'id,name,type\n1,Een,ABB\n1,Twee,SBB', 'export.csv')


def test_complete_enterprise_exceeding_old_budget_reaches_generation(tmp_path):
    text = '# Enterprise Architectuur\n' + 'Volledige broninhoud zonder hoofdstukselectie.\n' * 9000 + '# Laatste hoofdstuk\nOok dit slot moet volledig meegaan.'
    path = tmp_path/'enterprise-volledig.md'
    path.write_text(text)
    with patch('architect_agent.workflow.generate_plan', return_value={}) as generate:
        prepare(None, [path], 'Project', 'Doel', project_start=True)
    source = generate.call_args.args[0][0]
    assert len(source.text) > 155000
    assert text in source.text and source.text.endswith('Ook dit slot moet volledig meegaan.')
