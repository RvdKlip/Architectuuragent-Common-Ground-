"""Werk de adviescatalogus bij vanuit de expliciete mapping in de enterprise architectuur."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from architect_agent.catalogue import load_enterprise
from architect_agent.building_blocks import catalogue_from_snapshot


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--refresh', action='store_true', help='Haal de actuele openbare enterprise architectuur op.')
    args = parser.parse_args()
    catalogue = catalogue_from_snapshot(load_enterprise(refresh=args.refresh))
    if not catalogue['abbs'] or not catalogue['sbbs']:
        raise SystemExit('Geen ABB/SBB-mapping gevonden; de bestaande catalogus is niet gewijzigd.')
    (ROOT/'assets/building-blocks.json').write_text(json.dumps(catalogue, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(len(catalogue['abbs']), 'ABB’s en', len(catalogue['sbbs']), 'SBB-labels opgeslagen. Bouw index.html opnieuw met scripts/build_index.py.')
