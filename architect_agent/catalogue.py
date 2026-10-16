"""Lees de openbare enterprise architectuur en maak expliciete hoofdstukselectie mogelijk."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
from urllib.request import urlopen


ENTERPRISE_GITHUB = 'https://github.com/ivorstenbosch-maker/EnterpriseArchitectuurCG/blob/main/Enterprisearchitectuur-GPT.md'
ENTERPRISE_GITBOOK = 'https://dienstverleningsplatform.gitbook.io/platform-generieke-dienstverlening-public/enterprisearchitectuur'
ENTERPRISE_RAW = 'https://raw.githubusercontent.com/ivorstenbosch-maker/EnterpriseArchitectuurCG/main/Enterprisearchitectuur-GPT.md'
CACHE = Path(__file__).resolve().parents[1]/'.source-cache'/'enterprise.json'


@dataclass(frozen=True)
class Chapter:
    key: str
    title: str
    text: str


def chapters(text: str) -> list[Chapter]:
    """Splits uitsluitend op hoofdkoppen buiten fenced code; behoud alle tekst."""
    result = []
    title = 'Inleiding'
    lines = []
    fence = None
    for line in text.splitlines(keepends=True):
        marker = re.match(r'^\s{0,3}(`{3,}|~{3,})', line)
        if marker:
            current = marker.group(1)
            if fence is None:
                fence = current
            elif current[0] == fence[0] and len(current) >= len(fence):
                fence = None
        heading = re.match(r'^#\s+(.+?)\s*#*\s*$', line) if fence is None else None
        if heading:
            if lines:
                result.append(Chapter(str(len(result)), title, ''.join(lines)))
            title = heading.group(1).strip()
            lines = []
        lines.append(line)
    if lines:
        result.append(Chapter(str(len(result)), title, ''.join(lines)))
    return result


def load_enterprise(cache: Path = CACHE, *, refresh: bool = False) -> dict:
    if cache.exists() and not refresh:
        data = json.loads(cache.read_text(encoding='utf-8'))
        if hashlib.sha256(data['text'].encode()).hexdigest() != data['sha256']:
            raise ValueError('De lokale enterprise-architectuurbron is gewijzigd. Haal de bron opnieuw op.')
        return data
    with urlopen(ENTERPRISE_RAW, timeout=30) as response:
        body = response.read(3_000_001)
    if len(body) > 3_000_000:
        raise ValueError('De enterprise architectuur is groter dan de downloadlimiet van 3 MB.')
    text = body.decode('utf-8-sig')
    if not text.startswith('# ') or 'Enterprise Architectuur' not in text[:1000]:
        raise ValueError('De opgehaalde bron lijkt geen enterprise-architectuurdocument te zijn.')
    data = {'text': text, 'sha256': hashlib.sha256(text.encode()).hexdigest(),
            'retrieved_at': datetime.now(timezone.utc).isoformat(), 'url': ENTERPRISE_GITHUB}
    cache.parent.mkdir(parents=True, exist_ok=True)
    temporary = cache.with_suffix('.tmp')
    temporary.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')
    temporary.replace(cache)
    return data


def chapter_document(data: dict, selected: list[str]) -> str:
    available = chapters(data['text'])
    known = {chapter.key for chapter in available}
    if not selected or not set(selected) <= known:
        raise ValueError('Selecteer minstens één bestaand hoofdstuk uit de enterprise architectuur.')
    chosen = [chapter for chapter in available if chapter.key in selected]
    return ('# Geselecteerde hoofdstukken — Enterprise architectuur Platform Dienstverlening\n\n'
            f"Bron: {data['url']}\nOpgehaald (UTC): {data['retrieved_at']}\n"
            f"SHA-256 volledige bron: {data['sha256']}\n"
            'Geselecteerde hoofdstukken: ' + '; '.join(c.title for c in chosen) + '\n\n'
            'Dit is een expliciete selectie; de overige hoofdstukken zijn niet meegenomen.\n\n'
            + '\n\n'.join(chapter.text for chapter in chosen))


if __name__ == '__main__':
    snapshot = load_enterprise()
    print(f"Enterprise architectuur beschikbaar: {len(snapshot['text']):,} tekens; SHA-256 {snapshot['sha256']}")
