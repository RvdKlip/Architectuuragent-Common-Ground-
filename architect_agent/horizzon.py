"""Bouwstenen uit een expliciet aangeleverde CSV/JSON-export, zonder classificaties te verzinnen."""
import csv
import io
import json
import re


def parse_export(content: bytes, filename: str) -> tuple[list[dict], int]:
    if len(content) > 5_000_000:
        raise ValueError('De export mag maximaal 5 MB zijn.')
    text = content.decode('utf-8-sig')
    if filename.lower().endswith('.json'):
        data = json.loads(text)
        rows = data if isinstance(data, list) else data.get('building_blocks', data.get('objects'))
    else:
        first = text.splitlines()[0] if text else ''
        rows = list(csv.DictReader(io.StringIO(text), delimiter=';' if first.count(';') > first.count(',') else ','))
    if not isinstance(rows, list) or len(rows) > 10000:
        raise ValueError('Gebruik een CSV of JSON-lijst met maximaal 10.000 bouwstenen.')
    norm = lambda value: re.sub(r'[\s_-]', '', str(value).strip().lower())
    blocks, ids, skipped = [], set(), 0
    for raw in rows:
        if not isinstance(raw, dict):
            skipped += 1
            continue
        row = {norm(k): v for k, v in raw.items()}
        def get(*keys):
            return next((str(row[key]).strip() for key in keys if row.get(key) is not None and str(row[key]).strip()), '')
        kind = norm(get('buildingblocktype', 'bouwsteentype', 'classification', 'classificatie', 'type'))
        kind = 'ABB' if kind in ('abb', 'architecturebuildingblock', 'architecturebuildingblocks') else 'SBB' if kind in ('sbb', 'solutionbuildingblock', 'solutionbuildingblocks') else None
        identifier, name = get('id', 'objectid', 'identifier'), get('name', 'naam')
        if not kind or not identifier or not name:
            skipped += 1
            continue
        if identifier in ids:
            raise ValueError('Dubbel object-ID in de export: ' + identifier)
        ids.add(identifier)
        blocks.append({'id': identifier, 'name': name, 'type': kind,
                       'description': get('description', 'beschrijving', 'documentation', 'documentatie'),
                       'layer': get('layer', 'laag')})
    if not blocks:
        raise ValueError('Geen ABB’s/SBB’s gevonden. Gebruik id, name en type (ABB of SBB).')
    return blocks, skipped
