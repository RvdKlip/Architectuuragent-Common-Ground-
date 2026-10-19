# Common Ground Architectuuragent

## Download als Word

Na generatie staat **Download als Word** naast de bestaande knoppen voor huisstijl, PDF en opgemaakte HTML. De knop maakt een echt `.docx`-bestand met de twaalf hoofdstukken, de volledige getoonde resultaattekst, bronverwijzingen en de gekozen huisstijl. Dit werkt lokaal in de browser, zonder service of installatie, ook vanuit de ZIP. Gewijzigde projectgegevens of bronnen vereisen eerst een nieuw concept.

## Vaste indeling van de gegenereerde architectuur

Totdat de gebruiker een andere indeling vraagt, gebruiken de browserapp, AI-generatie en HTML-, PDF-, Word-, Notion- en Confluence-uitvoer dezelfde twaalf onderdelen:

1. Managementsamenvatting
2. Opdracht, scope en bronnen
3. Klantroutes en dienstverlening
4. Bestaande en benodigde bedrijfsservices
5. Oplossing in vijf lagen
6. Uitwerking van nieuwe of gewijzigde bedrijfsservices
7. Proces- en gegevensstromen
8. Informatie en registers
9. Architectuurbesluiten en beslisregels
10. Privacy, beveiliging en kwaliteit
11. Realisatie, deployment en beheer
12. Acceptatie en open besluiten

De inhoudseisen staan in `assets/architecture_structure.json`. AI-generatie vult per onderdeel bronverwijzingen en inhoud in; ontbrekende informatie wordt als open vraag gemarkeerd. Zonder AI ontstaat een eerste concept met bronfragmenten en expliciete nog uit te werken onderdelen. Een vaste indeling garandeert geen inhoudelijk volledig ontwerp. Bestaande concept-JSON zonder hoofdstukinhoud blijft bruikbaar; ontbrekende onderdelen worden zichtbaar gemaakt. Word-updates behouden de oorspronkelijke documentinhoud en voegen de twaalf hoofdstukken toe binnen de bestaande update-markers.

## Projectdocumenten en overige bronnen

Onder de projectnaam en afbakening kun je één of meerdere PDF-, DOCX-, TXT- of Markdown-bestanden toevoegen. Vink per bestand aan of het mee moet in de architectuur. De zelfstandige HTML-app leest bestanden lokaal in de browser; hiervoor zijn geen Notion-koppeling, service-sleutel of installatie nodig. Exporteer een Notion-pagina desgewenst eerst als PDF of Markdown en voeg dat bestand toe. Scans zonder leesbare tekst vereisen een tekstversie.

De sectie **Start vanuit een epic** en de bijbehorende link- en service-instellingen zijn verwijderd. AI-generatie en publicatie blijven afzonderlijke, optionele functies.

### Een index voor collega’s

- `index.html` in de repository en ZIP is de zelfstandige app.
- `downloads/index.html` is een klein startbestand dat naar de actuele GitHub Pages-site verwijst. In de ZIP heet dit `Open-Architectuuragent-online.html`.
- Voor direct openen vanuit Teams kun je na activatie de website-link delen: `https://rvdklip.github.io/Architectuuragent-Common-Ground-/`.

**GitHub Pages moet eenmalig worden ingeschakeld**: open de [repository-instellingen voor Pages](https://github.com/RvdKlip/Architectuuragent-Common-Ground-/settings/pages), kies **Deploy from a branch**, **main**, **/ (root)** en **Save**. De repository heeft `.nojekyll`; er is geen serverinstallatie nodig voor het appscherm. Het activeren kon vanuit deze omgeving niet worden uitgevoerd: de GitHub API wees de beschikbare toegang af. De website-URL is daarom een voorbereid adres, geen bevestigde live publicatie. Een raw GitHub-HTML-link is geen website. Teams kan een HTML-bijlage alleen als voorvertoning tonen of blokkeren; download/open in een browser of deel de Pages-link nadat de site beschikbaar is.

Bouw beide bestanden en de ZIP met `.venv/bin/python scripts/package_app.py`. De ZIP bevat geen lokale uploads, privé-epics of serviceconfiguratie. De browserproef gebruikt lokale synthetische projectbestanden; er worden geen AI-aanroepen gedaan of platformpagina’s gepubliceerd.

## Projectarchitectuur: vernieuwd appscherm

Open `index.html` door erop te dubbelklikken na het uitpakken van de ZIP. Het bestand bevat alle afbeeldingen, stijlen, de PDF-lezer en PDF-generator; er is geen installatie nodig. De werkruimte heet **Architectuuragent**, toont het gemeentelogo van Rotterdam en gebruikt Rotterdam-groen `#00811F`. Het originele logo en de bijbehorende rechtenverklaring staan in `assets/rotterdam/`.

### Bronselectie

- **Enterprise architectuur Platform Dienstverlening**: wordt bij het openen van de zelfstandige app automatisch geladen. De knop vernieuwt de bron handmatig; bij een verbindingsfout kun je opnieuw proberen of een eigen versie uploaden. Ophalen van de opgegeven openbare [GitHub-bron](https://github.com/ivorstenbosch-maker/EnterpriseArchitectuurCG/blob/main/Enterprisearchitectuur-GPT.md) of een eigen versie uploaden. **Alle hoofdstukken gaan volledig mee**, zonder hoofdstukkeuze of stilzwijgende inkorting. URL, ophaaldatum en SHA-256 blijven in de bronselectie vastgelegd.
- **Projectdocumenten en overige bronnen**: PDF, DOCX, TXT of Markdown lokaal uitlezen, met keuze per bestand. Niet-leesbare bronnen blokkeren generatie totdat ze zijn vervangen of uitgevinkt.

De module Bouwstenen Rotterdam en de downloadknop voor de bronselectie zijn verwijderd uit de zelfstandige app en Streamlit. De afzonderlijke secties voor bouwblokkenadvies, bestaande ADR’s en privacy-/beveiligingskaders zijn verwijderd. De oudere adviesmodule en tests van de parsing blijven beschikbaar in de code, maar worden niet gebruikt in dit scherm en leveren geen vervangende Rotterdamse catalogus.

### Generatie, huisstijl en publicatie

**Genereer de architectuur** opent de keuze **Rotterdam / Common Ground** en **PDF / Confluence / Notion** (meerdere mogelijk). Het losse bestand maakt standaard lokaal een eerste brongebaseerd concept: herkenbare bronfragmenten, concept-ADR en open besluiten. Dit is geen semantische AI-synthese of vastgesteld ontwerp. PDF en HTML gebruiken de gekozen kleuren en typografie. Notion ondersteunt alleen platformkleuren, Confluence behoudt het thema van de doelruimte. De uitvoerprofielen zijn geen gecertificeerde officiële documenttemplates.

Optioneel: open AI-synthese in het generatievenster. Stel `OPENAI_API_KEY` veilig in op de lokale service, `OPENAI_MODEL` is optioneel. Vink expliciet aan dat de geselecteerde bronnen gedeeld mogen worden. Alleen na een klik op genereren gaan volledige geselecteerde bronteksten naar de bestaande AI-workflow. De gedeelde index bevat geen sleutels. De bronlimiet is verhoogd tot **900.000 tekens** om de volledige enterprise architectuur (circa 388.000 tekens) en aanvullende bronnen te ondersteunen. Grotere sets geven een fout; niets wordt automatisch afgekapt. Gebruik een model met voldoende contextcapaciteit; de service garandeert geen capaciteit van een zelf ingesteld ander model.

Een vinkje bij Notion of Confluence publiceert nog niets. Review eerst het concept en gebruik de aparte publicatieknop. Gewijzigde bronnen maken een eerder concept verouderd en blokkeren publicatie totdat opnieuw is gegenereerd.

### Lokale AI- en publicatieservice

1. Stel `PSA_SERVICE_TOKEN` in op een eigen ASCII-sleutel van minimaal 24 tekens (bestaande configuratienaam behouden). Bewaar sleutels buiten Git en gedeelde bestanden.
2. Optioneel AI: `OPENAI_API_KEY` en `OPENAI_MODEL`.
3. Optioneel Notion: `NOTION_TOKEN` en `NOTION_PARENT_PAGE_ID`.
4. Optioneel Confluence Cloud: `CONFLUENCE_BASE_URL`, `CONFLUENCE_EMAIL`, `CONFLUENCE_TOKEN`, `CONFLUENCE_SPACE_ID`; optioneel `CONFLUENCE_PARENT_ID`.
5. Start `.venv/bin/python publication_service.py` en vul `http://127.0.0.1:8765` met de service-sleutel in het appscherm in.

De service luistert alleen lokaal, controleert toegang en review, verstuurt geen bronbestanden naar publicatieplatforms en bewaart binnen de servicerun bevestigde publicaties om dubbele pagina’s te beperken. Na time-outs of herstarts: controleer de doelpagina voor opnieuw publiceren. Er zijn geen automatische retries van schrijfverzoeken. De Streamlit-app (`.venv/bin/streamlit run app.py`) ondersteunt dezelfde bronkeuze en publicatieplatforms.

### Zelf bouwen en controleren

Voer `.venv/bin/python scripts/build_index.py` uit na wijzigingen in `web/`. Test met `.venv/bin/python -m pytest -q`. Volledige enterprise-inhoud, bronuitsluiting, PDF en mobiele weergave worden gecontroleerd. AI-aanroepen en publicaties worden uitsluitend gemockt; geen betaalde API-aanroep of echte publicatie voor deze wijziging.

## Publiceren in Notion

Na review kun je het resultaat rechtstreeks als **nieuwe Notion-subpagina** publiceren. Word-export is optioneel. De pagina bevat bewerkbare koppen, samenvatting, wijzigingen met bronverwijzingen, vijf architectuurlagen, gegevensstroom, concept-ADR, architectuurregels, open besluiten, aannames en bronoverzicht. De inhoud blijft CONCEPT; publicatie maakt een voorstel niet tot vastgesteld besluit.

Eenmalig instellen:

1. Maak in Notion een interne integratie via **Settings → Connections → Develop or manage integrations** (of https://www.notion.so/profile/integrations). Geef deze leesrechten en het recht om inhoud toe te voegen (*Read content* en *Insert content*).
2. Open de pagina waaronder de resultaten moeten komen en geef de integratie toegang via **… → Connections**. De naam van deze optie kan per Notion-versie verschillen.
3. Start de app. Vul in de zijbalk de **Notion-integratiesleutel** en de link van de **bovenliggende Notion-pagina** in. Je kunt deze ook veilig instellen als `NOTION_TOKEN` en `NOTION_PARENT_PAGE_ID`. Zet echte sleutels nooit in Git of in chat. `.env` wordt niet automatisch geladen.
4. Analyseer de bronnen, of laad een bestaande `concept_review.json` met de oorspronkelijke bronbestanden in dezelfde volgorde. Een bestaand Word-document is alleen verplicht bij de workflow Bestaande architectuur bijwerken. Bij hergebruik moet de oorspronkelijke bronnummering behouden blijven: was het Word-document B00, upload het dan ook bij hergebruik.
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
