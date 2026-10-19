"""Bouw de app en een deelbare ZIP zonder configuratie, sleutels of bronuploads."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from build_index import build

ROOT = Path(__file__).resolve().parents[1]


def package():
    build()
    instructions = '''ARCHITECTUURAGENT — PROJECTARCHITECTUUR

1. Kies Alles uitpakken voor deze ZIP.
2. Dubbelklik op index.html voor de zelfstandige app (zonder installatie).
3. Open-Architectuuragent-online.html opent de actuele app via GitHub Pages.
   Dit werkt nadat de repository-eigenaar GitHub Pages heeft ingeschakeld.

Gebruik Genereer de architectuur om een brongebaseerd concept te maken.
Alle hoofdstukken van de enterprise architectuur gaan mee.

Epics: kies Notion of Microsoft Teams in stap 1.
- Notion: haal epics op via de ingestelde lokale service, of voeg een eigen epiclink toe.
- Teams: plak een willekeurige Teams-link, geef de epic een naam en voeg de beschrijving toe.
Een link alleen geeft geen leesrechten: zonder beschrijving wordt alleen de verwijzing gebruikt.
De geselecteerde epic wordt als bron opgenomen en kan weer worden verwijderd.

Voor Notion-lezen, AI en publicatie is een lokaal ingestelde koppeling nodig.
Er zitten geen sleutels of privé-epics in dit bestand. Zie de repository-README:
https://github.com/RvdKlip/Architectuuragent-Common-Ground-

GitHub Pages eenmalig inschakelen:
Settings > Pages > Source: Deploy from a branch > Branch: main > / (root) > Save.
De verwachte website is https://rvdklip.github.io/Architectuuragent-Common-Ground-/
De site is pas beschikbaar nadat GitHub de publicatie heeft afgerond.
Deel daarna bij voorkeur de website-link in Teams; die opent direct zonder HTML-download.

Het gemeentelogo en de componentlicenties behouden hun eigen rechten.
Zie de meegeleverde logo-bestanden en Open-source componenten onderaan het appscherm.
'''
    target = ROOT/'downloads/architectuuragent-projectarchitectuur.zip'
    with ZipFile(target, 'w', ZIP_DEFLATED) as archive:
        archive.write(ROOT/'index.html', 'index.html')
        archive.write(ROOT/'downloads/index.html', 'Open-Architectuuragent-online.html')
        archive.write(ROOT/'downloads/index.html', 'start/index.html')
        archive.writestr('LEES-MIJ.txt', instructions)
        archive.write(ROOT/'assets/rotterdam/LICENSE.md', 'logo-LICENSE.md')
        archive.write(ROOT/'assets/rotterdam/README.md', 'logo-HERKOMST.md')
    with ZipFile(target) as archive:
        assert archive.testzip() is None
        assert archive.read('index.html') == (ROOT/'index.html').read_bytes()
    with ZipFile(ROOT/'downloads/startbestand-teams.zip', 'w', ZIP_DEFLATED) as archive:
        archive.write(ROOT/'downloads/index.html', 'index.html')
        archive.writestr('LEES-MIJ.txt', 'Pak uit en deel index.html via Teams. Open dit bestand in een browser. De GitHub Pages-site moet eerst actief zijn. Instellen: https://github.com/RvdKlip/Architectuuragent-Common-Ground-/settings/pages > Deploy from a branch > main > / (root) > Save. De site is pas beschikbaar nadat GitHub de publicatie heeft afgerond. In Teams kun je daarna ook direct de website-link delen: https://rvdklip.github.io/Architectuuragent-Common-Ground-/')
    print('ZIP gecontroleerd:', target.name, target.stat().st_size, 'bytes')


if __name__ == '__main__':
    package()
