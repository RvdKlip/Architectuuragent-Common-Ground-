"""Vast gegevenscontract tussen taalmodel, review en Office-generator."""
from __future__ import annotations
import re
import json
from pathlib import Path

ARCHITECTURE_STRUCTURE = json.loads((Path(__file__).resolve().parents[1]/'assets/architecture_structure.json').read_text(encoding='utf-8'))


def object_schema(properties: dict) -> dict:
    return {"type": "object", "properties": properties, "required": list(properties), "additionalProperties": False}


def array(schema: dict) -> dict:
    return {"type": "array", "items": schema}


STR = {"type": "string"}
STR_LIST = array(STR)
UPDATE_SCHEMA = object_schema({
    "chapter_content": object_schema({chapter["key"]: {**array(object_schema({"text": STR, "evidence": STR_LIST})), "minItems": 1} for chapter in ARCHITECTURE_STRUCTURE}),
    "title": STR,
    "scope": STR,
    "management_summary": STR,
    "changes": array(object_schema({"section": STR, "change": STR, "rationale": STR, "evidence": STR_LIST})),
    "layers": array(object_schema({"number": {"type":"integer"}, "name": STR, "components": STR_LIST})),
    "flow_steps": STR_LIST,
    "adr": object_schema({
        "title": STR, "status": STR, "context": STR, "decision": STR,
        "principles": STR_LIST, "implications": STR_LIST, "concerns": STR_LIST,
        "implementation": STR_LIST, "relation_existing_adrs": STR,
    }),
    "decision_rules": array(object_schema({"id": STR, "rule": STR, "evidence": STR_LIST, "status": STR})),
    "open_decisions": STR_LIST,
    "assumptions": STR_LIST,
})


def validate(plan: dict, sources: list | None = None) -> list[str]:
    """Valideert niet alleen structuur, maar ook bronverwijzingen en conceptstatus."""
    errors = []
    required = UPDATE_SCHEMA['required']
    for key in required:
        if key != 'chapter_content' and key not in plan:
            errors.append(f"Ontbrekend hoofdveld: {key}")
    if errors:
        return errors
    if not isinstance(plan['layers'], list):
        errors.append('layers is geen lijst')
    else:
        nums = [lay.get('number') for lay in plan['layers'] if isinstance(lay, dict)]
        if sorted(nums) != [1, 2, 3, 4, 5]:
            errors.append('Precies vijf architectuurlagen (1 t/m 5) zijn verplicht')
    adr = plan.get('adr', {})
    for field in UPDATE_SCHEMA['properties']['adr']['required']:
        if field not in adr:
            errors.append(f"ADR mist veld: {field}")
    if 'concept' not in adr.get('status', '').lower():
        errors.append('ADR moet expliciet de status CONCEPT hebben; dit is geen formeel besluit')
    evidence = []
    for change in plan.get('changes', []):
        evidence.extend(change.get('evidence', []))
    for rule in plan.get('decision_rules', []):
        evidence.extend(rule.get('evidence', []))
    if 'chapter_content' in plan:
        content = plan['chapter_content']
        expected = {chapter['key'] for chapter in ARCHITECTURE_STRUCTURE}
        if not isinstance(content, dict) or set(content) != expected:
            errors.append('chapter_content moet exact de twaalf standaardonderdelen bevatten')
        else:
            for key, entries in content.items():
                if not isinstance(entries, list) or not entries:
                    errors.append(f'Hoofdstuk {key} mist inhoud of een expliciete open vraag')
                    continue
                for entry in entries:
                    if not isinstance(entry, dict) or not isinstance(entry.get('text'), str) or not entry['text'].strip() or not isinstance(entry.get('evidence'), list) or not all(isinstance(c, str) for c in entry['evidence']):
                        errors.append(f'Ongeldige hoofdstukinhoud: {key}')
                    else:
                        evidence.extend(entry['evidence'])
    known = {s.key: s.pages for s in sources or []}
    for cite in evidence:
        match = re.search(r'\b(B\d\d)(?:\s+p\.?\s*(\d+)|\s+doc|\s+tekst)?\b', cite, flags=re.I)
        if not match:
            errors.append(f"Ongeldig bronkenmerk: {cite}")
        elif sources:
            key = match.group(1).upper()
            if key not in known:
                errors.append(f"Bron ontbreekt: {cite}")
            elif match.group(2) and int(match.group(2)) > known[key]:
                errors.append(f"Paginanummer bestaat niet: {cite}")
    return errors
