# Common Ground Architectuuragent

## Publiceren in Notion

Na review kun je het resultaat rechtstreeks als **nieuwe Notion-subpagina** publiceren. Word-export is optioneel. De pagina bevat bewerkbare koppen, samenvatting, wijzigingen met bronverwijzingen, vijf architectuurlagen, gegevensstroom, concept-ADR, architectuurregels, open besluiten, aannames en bronoverzicht. De inhoud blijft CONCEPT; publicatie maakt een voorstel niet tot vastgesteld besluit.

Eenmalig instellen:

1. Maak in Notion een interne integratie via **Settings → Connections → Develop or manage integrations** (of https://www.notion.so/profile/integrations). Geef deze leesrechten en het recht om inhoud toe te voegen (*Read content* en *Insert content*).
2. Open de pagina waaronder de resultaten moeten komen en geef de integratie toegang via **… → Connections**. De naam van deze optie kan per Notion-versie verschillen.
3. Start de app. Vul in de zijbalk de **Notion-integratiesleutel** en de link van de **bovenliggende Notion-pagina** in. Je kunt deze ook veilig instellen als `NOTION_TOKEN` en `NOTION_PARENT_PAGE_ID`. Zet echte sleutels nooit in Git of in chat. `.env` wordt niet automatisch geladen.
4. Analyseer de bronnen, of laad een bestaande `concept_review.json` met de oorspronkelijke bronbestanden in dezelfde volgorde. Alleen bij nieuwe AI-analyse is het bestaande Word-document verplicht. Bij hergebruik moet de oorspronkelijke bronnummering behouden blijven: was het Word-document B00, upload het dan ook bij hergebruik.
5. Controleer de JSON, vink de review/publicatiebevestiging aan en klik **Publiceer concept in Notion**. De app toont de link zodra Notion de publicatie bevestigt.

Er is geen Word-export nodig voor deze publicatiestap en geen OpenAI-aanroep bij het laden van een bestaand concept. Alleen de gereviewde resultaattekst en bronverwijzingen gaan naar Notion, inclusief de daarin voorkomende bestandsnamen. Volledige bronbestanden worden niet meegestuurd.

Deze eerste versie plaatst architectuurlagen en gegevensstroom als tekst/lijsten; SVG/PNG-afbeeldingen worden nog niet geüpload. Publicatie wijzigt geen bestaande pagina's en past geen openbare deelinstellingen aan. Wie het resultaat kan zien, wordt bepaald door de rechten van de bovenliggende Notion-pagina. Een database als bestemming of een bestaande pagina bijwerken wordt nog niet ondersteund.

Publiceer dezelfde inhoud niet opnieuw na een onduidelijke verbindingsfout zonder eerst de doelpagina te controleren: Notion kan de pagina al hebben aangemaakt. Bij een fout tijdens een lange publicatie geeft de app de link naar de gedeeltelijk gevulde pagina. Er zijn geen automatische retries van schrijfverzoeken. Binnen dezelfde appsessie blokkeert de app herhaling van een bevestigde publicatie van hetzelfde concept naar dezelfde bestemming; na een herstart is dit geheugen leeg.

Gecontroleerd met lokale tests en gemockte Notion-verzoeken; echte publicatie vereist jouw integratie en gedeelde doelpagina. De betaalde OpenAI-aanroep is niet meegenomen in deze controles.

**Prototype 0.1 · Codex-klaar · lokaal draaiende webapp + commandoregel**

Met deze app herhaal je de workflow waarmee een bestaande solutionarchitectuur is aangevuld met nieuwe bronstukken, een vijf-lagenarchitectuurplaat, een gegevensstroom en een ADR in de vorm **Context – Besluit – Principe – Implicatie – Eventuele zorgen – Implementatie**. Doelgroepen: architecten, analisten en productteams van Platform Dienstverlening / Common Ground.

## Wat werkt

- Meerdere PDF-, DOCX-, TXT- en Markdown-bronnen analyseren, inclusief paginaverwijzingen bij PDF's.
- Genereren van gestructureerd **concept-JSON** voor beoordeling (OpenAI API; betaald gebruik kan van toepassing zijn).
- Controleren van alle vijf architectuurlagen, ADR-conceptstatus en gebruikte broncodes.
- Twee architectuurdiagrammen maken in vaste G4-stijl: **SVG** (bewerkbaar) en **PNG** (voor Word).
- Bestaande Word-solutionarchitectuur behouden en **een gemarkeerde conceptupdate toevoegen of vervangen**.
- Concept-ADR's, architectuurregels, open besluiten en bronoverzicht in Word opnemen.
- Zichtbare beoordeling van JSON vóór Word-export; geen autonome besluitvorming.
- Offline hergeneratie vanuit een eerder gecontroleerde `concept_review.json`.

**Begrenzing:** de app past de bestaande hoofdstukken niet zelf inhoudelijk aan. Hij voegt een integraal onderdeel achteraan toe; bij een volgende run wordt alleen de eerder door de agent geschreven aanvulling vervangen. De oorspronkelijke inhoud blijft ongemoeid. Het is dus een bruikbare reviewversie, geen volledig autonoom gereviseerde publicatie. Foto's als stijlvoorbeeld worden alleen getoond; de architectuurdiagrammen volgen een ingebouwd vijf-lagensjabloon. PDF's moeten selecteerbare tekst bevatten (er vindt geen OCR plaats). Ingesloten tekeningen en figuren in PDF-bronnen worden niet visueel geïnterpreteerd; ontbrekende tekstpagina’s met afbeeldingen worden gesignaleerd.

## Installatie

Je hebt Python 3.11 of hoger nodig.

Voor Windows kun je ook `start_windows.bat` dubbelklikken (eerste keer installeert die de afhankelijkheden).

### Windows PowerShell

```powershell
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:OPENAI_API_KEY="<jouw-API-sleutel>"
$env:OPENAI_MODEL="gpt-4.1"
streamlit run app.py
```

Voor macOS/Linux is er `./start_mac_linux.sh`.

### macOS/Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export OPENAI_API_KEY="<jouw-API-sleutel>"
export OPENAI_MODEL="gpt-4.1"
streamlit run app.py
```

Daarna opent Streamlit doorgaans op **http://localhost:8501**.

> **Let op:** Codex zelf is een programmeerassistent. Deze runtime-app gebruikt standaard de **OpenAI API** om broninhoud te analyseren. Een ChatGPT-abonnement is niet automatisch een API-tegoed. Als je geen externe API mag gebruiken, kan je wel de offline hergeneratie gebruiken, of later een door je organisatie goedgekeurd modelkoppelvlak inbouwen.

## Gebruik (webapp)

1. Kies je **bestaande solutionarchitectuur in Word** (bijvoorbeeld de v0.3 die je al hebt).
2. Upload nieuwe bronstukken, zoals **Notion-export Signaalmanagement.pdf** en **Architectural decision (ADR).pdf**. Gebruik alleen materialen die naar de gekozen AI-dienst mogen worden verzonden.
3. Geef het onderwerp en de wijzigingswens op.
4. Klik **Analyseer bronnen en maak concept**.
5. **Review en bewerk** de JSON: met name broncodes, nieuwe aannames, architectuurregels, scope en ADR-status.
6. Klik **Maak bijgewerkte Word en diagrammen** en download Word of de ZIP met SVG/PNG/JSON.
7. Laat het resultaat door architecten beoordelen en besluitvorming via de afgesproken governance verlopen.

## Commandoregel (geschikt voor Codex en automatisering)

```bash
python cli.py \
  --base "Solutionarchitectuur_v0.3.docx" \
  --sources "Signaalmanagement.pdf" "Architectural_decision_ADR.pdf" \
  --scope "Signaalmanagement" \
  --goals "Verwerk de besluiten van 12 oktober; maak ADR en architectuurplaat" \
  --out resultaat
```

### Zonder AI opnieuw genereren

```bash
python cli.py \
  --base "Solutionarchitectuur_v0.3.docx" \
  --sources "Signaalmanagement.pdf" "Architectural_decision_ADR.pdf" \
  --scope "Signaalmanagement" \
  --reviewed-plan "resultaat/concept_review.json" \
  --out resultaat_review
```

Voor offline runs moeten de oorspronkelijke bestanden in dezelfde volgorde worden aangeleverd, omdat `B00`, `B01`, ... op de bronvolgorde gebaseerd zijn. De Word-bijlage krijgt herkenbare verborgen begin- en eindmarkeringen; die maken herhaling zonder duplicatie mogelijk.

## Output

- `Solutionarchitectuur_bijgewerkt_concept.docx`
- `architectuur_vijflagen.svg` en `.png`
- `gegevensstroom.svg` en `.png`
- `concept_review.json` (bewerkbaar tussen AI-stap en output)
- `manifest.json` (bronlijst en outputmetadata)

## Kwaliteit en beveiliging

- **Privacy:** brontekst wordt aan OpenAI verzonden zodra je op *Analyseer* klikt. Niet geschikt voor vertrouwelijke of persoonsgevoelige documentatie zonder interne goedkeuring. Gebruik een goedgekeurd model en verwerk waar nodig vooraf afscherming/maskering.
- **Geen ingelogde Notion/GitHub-connector:** exporteer de pagina of het document eerst naar PDF/Word.
- **Bronkwaliteit:** bij scans zonder tekst stopt extractie met een foutmelding; niets wordt stilzwijgend genegeerd.
- **Herleidbaarheid:** bronverwijzingen zijn op syntaxis en paginabereik gecontroleerd, niet op de semantische juistheid van elke zin. Menselijke toets vereist.
- **Geen automatische wijzigingen in bronregistraties of GitHub.** Notion-publicatie gebeurt alleen met de expliciete publicatieknop na review.
- **Conceptstatus:** alle nieuw gegenereerde ADR-teksten worden als concept aangeduid, ook wanneer de bronnen bestaande besluitvorming noemen.

## Codex-workflow

Open deze map als repository in Codex. De `AGENTS.md` legt ontwerpregels, scope en testverwachtingen vast. Bijvoorbeeld:

> Voeg een reviewstap toe waarmee de architect direct in de webapp een voorstel aanpast en het vervolgens met bronverwijzingen in een bestaande paragraaf laat vervangen; behoud tabellen en bestaande ADR-status.

Codex kan dan bestaande modules uitbreiden zonder de generator opnieuw te schrijven.

## Testen

```bash
python -m pytest -q
```

De testset draait lokaal met synthetische documenten en zonder API-verkeer.

## Roadmap

1. Documentwijzigingen per paragraaf voorstellen (review en patch met behoud van bestaande inhoud), niet alleen aanvullen.
2. Live bronconnectors (Notion/GitHub) mits toegang en privacy-goedkeuring.
3. Direct gebruik van intern beheerde AI-modellen, zonder externe modelverwerking.
4. Architectuurregels exporteren als machineleesbare policy-checklist en ADR-registry.
5. Werken met vaste sjablonen per productteam, versiehistorie en Word-comments.
