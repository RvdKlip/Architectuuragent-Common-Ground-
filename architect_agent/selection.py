"""Bronkeuze voor een projectarchitectuur; broninhoud wordt nooit ingevuld."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class SourceOption:
    key: str
    title: str
    description: str
    purpose: str


SOURCE_OPTIONS = (
    SourceOption('enterprise', 'Enterprise architectuur Platform Dienstverlening',
                 'Het overkoepelende architectuurkader voor het platform.',
                 'Kaders, doelarchitectuur en samenhang met het platform.'),

)


@dataclass(frozen=True)
class SelectedDocument:
    category: str
    name: str
    content: bytes


def missing_sources(selected: list[str], documents: list[SelectedDocument]) -> list[str]:
    present = {document.category for document in documents if document.content}
    return [option.title for option in SOURCE_OPTIONS
            if option.key in selected and option.key not in present]


def write_documents(documents: list[SelectedDocument], root: Path) -> list[Path]:
    """Bewaar originele bestandsnamen voor bronverwijzingen, ook bij gelijke namen."""
    paths = []
    for index, document in enumerate(documents):
        if not document.content:
            raise ValueError(f'Bronbestand is leeg: {document.name}')
        # Bestandsnamen van uploads mogen niet buiten de tijdelijke map schrijven.
        name = Path(document.name.replace('\\', '/')).name
        if name in ('', '.', '..'):
            raise ValueError('Een bronbestand heeft geen geldige naam.')
        path = root/'sources'/f'{index:03d}'/name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(document.content)
        paths.append(path)
    return paths
