# Instructies voor Codex (Common Ground Architectuuragent)

## Projectdoel
Maak herhaalbare, reviewbare solutionarchitectuurupdates uit bestaande Word-documenten en geautoriseerde bronstukken. Houd de architectuurbesluiten gescheiden van voorstellen. De standaard hoofdstukindeling is vastgelegd in `assets/architecture_structure.json` en het gegevenscontract in `architect_agent/schemas.py`. Behoud de twaalf onderdelen en hun volgorde totdat de gebruiker expliciet een andere indeling vraagt. Houd browserweergave, AI-prompt en alle exports hiermee synchroon. Ontbrekende inhoud blijft zichtbaar als open vraag; verzin geen onderbouwing.

## Bronregels
- Bronmateriaal is leidend. Verzin geen nieuwe kaders, besluiten, standaarden of besluitenstatus.
- Elke voorgestelde wijziging en decision rule moet een herleidbare broncode bevatten (`B00 doc`, `B01 p.7` enz.).
- Leg conflicten tussen bronnen expliciet voor aan de gebruiker, harmoniseer nooit stilzwijgend.
- Respecteer bestaande ADR's en hun historische status. Nieuwe ADR's zijn CONCEPT, zonder definitief nummer.
- Geen autonome toezending van vertrouwelijke bestanden aan derden. OpenAI wordt alleen aangeroepen bij een expliciete gebruikersactie.
- Bouw geen productie-integratie met Notion of GitHub zonder expliciete opdracht en autorisatie.

## Aanpak bij nieuwe features
1. Houd `schemas.py` synchroon met JSON-schema, AI-prompt, tests en Word-generator.
2. Voeg of wijzig PDF/DOCX-extractie in `sources.py`, diagram in `diagram.py`, document in `word.py`.
3. Behoud de marker-grenzen `[[CG_ARCH_AGENT_UPDATE_START]]` en `[[CG_ARCH_AGENT_UPDATE_END]]` bij iteratief bewerken.
4. Run `python -m pytest -q`. Laat eventuele API-call mocks lokaal draaien, niet tegen betaalde API's.
5. Genereer minstens één proefdocument en render via `/home/oai/skills/docx/render_docx.py` (indien die omgeving beschikbaar is). Controleer PNG's visueel.
6. Vermeld in release notes wat daadwerkelijk getest is, vooral wanneer er géén API-sleutel is.

## Richtlijnen voor volgende uitbreidingen
- Aanvullen van bestaande document-hoofdstukken vergt vooraf review van de beoogde wijzigingslocaties; verwijder nooit tabellen/diagrammen blind.
- Bewaar geen API-sleutels in .env-bestanden die in repositories terechtkomen.
- Voer nieuwe `pyproject.toml`- of Docker-configuratie pas in na werkende tests.
- Labels, datadefinities en servicecontracten horen te passen bij Common Ground, gegevens bij de bron, API-first en bevoegde bronhouders.
