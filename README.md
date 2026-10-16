# Common Ground Architectuuragent

## Direct openen zonder installatie

Download `index.html` en open dit bestand met een dubbelklik in je browser. Het donkere app-scherm en de architectuurafbeelding zitten samen in dit ene bestand; hiervoor is geen Python, Streamlit of webserver nodig.

Je kunt projectgegevens invullen, bronnen selecteren, lokale documenten kiezen, de openbare enterprise architectuur ophalen en hoofdstukken selecteren, en de bronselectie inclusief bouwblokkenadvies als JSON downloaden. Voor het ophalen van de openbare bron is internet nodig; een eigen versie uploaden werkt ook zonder internet. Geselecteerde PDF-, DOCX-, TXT- en Markdown-documenten worden lokaal gelezen voor het bouwblokkenadvies. Er worden geen documentbestanden naar externe diensten verstuurd. Het JSON-bestand bevat de bronkeuze, bestandsmetadata en korte bewijsfragmenten bij het advies, geen volledige kopieën van de lokale bestanden. Dit zelfstandige scherm genereert geen volledige PSA met AI en publiceert niets in Notion; daarvoor blijft de Python-app beschikbaar.

De werkruimte heeft een donkere vormgeving met mintgroene accenten en een lokaal opgeslagen architectuurvisual. Het beeld in `assets/architecture-hero.png` is speciaal voor deze app gegenereerd: een illustratief model met vijf zwevende lagen, geen weergave van een vastgesteld ontwerp. De visual en stijlen worden zonder externe beeldservers geladen. De bronselectie, invoer en review blijven bedienbaar op desktop en telefoon. De groene knop in het beeld navigeert naar de bronselectie.

## Projectstartarchitectuur: project en bronnen kiezen

Het beginscherm laat een architect een **nieuwe projectstartarchitectuur (PSA)** samenstellen. Vul de projectnaam en het doel/de afbakening in en selecteer welke bronnen moeten worden meegenomen. Voor een nieuwe PSA is geen bestaand Word-document nodig. De bestaande workflow blijft beschikbaar via **Type architectuur → Bestaande architectuur bijwerken**.

De vaste bronoptie **Enterprise architectuur Platform Dienstverlening** verwijst naar de door de gebruiker opgegeven [GitBook](https://dienstverleningsplatform.gitbook.io/platform-generieke-dienstverlening-public/enterprisearchitectuur) en leest de [Markdown-bron op GitHub](https://github.com/ivorstenbosch-maker/EnterpriseArchitectuurCG/blob/main/Enterprisearchitectuur-GPT.md). De volledige tekst is circa 388.000 tekens, groter dan de huidige bronlimiet van 155.000 tekens. Daarom kiest de architect expliciet welke hoofdstukken mee moeten. Standaard zijn dit **Managementsamenvatting** en **Visie, principes, scope**. Andere hoofdstukken worden niet automatisch meegenomen of samengevat.

Met **Bron vernieuwen** haalt de app de actuele openbare tekst op. Een lokale momentopname wordt bewaard in de genegeerde map `.source-cache/`. De app toont ophaaldatum en bronkenmerk; het geselecteerde brondocument bevat de URL, de SHA-256 van de volledige tekst en de gekozen hoofdstukken. De momentopname is geen vastgezette officiële versie. Voor een eigen of historische versie kun je ook een PDF, DOCX, TXT of Markdown uploaden. De opgehaalde volledige bron wordt niet in deze Git-repository gepubliceerd.

Andere broncategorieën zijn **Horizon Rotterdam**, **bestaande ADR’s** en **privacy- en beveiligingskaders**. Dit zijn uploadmogelijkheden, geen vooraf ingevulde of gevalideerde documenten. Daarnaast kun je projectopdrachten, requirements en andere projectdocumenten toevoegen en per bestand aan- of uitvinken.

## Geadviseerd gebruik van ABB’s en SBB’s

Tussen de enterprise architectuur en Horizon Rotterdam staat **Toe te passen bouwblokken**. De catalogus bevat de 34 ABB’s en 30 unieke SBB-labels uit het onderdeel *Solution Building Blocks (SBB’s) en mapping op ABB’s* in de enterprise architectuur. Namen, onderlinge mapping, bronregels, ophaaldatum en de SHA-256 van de bronmomentopname zijn vastgelegd in `assets/building-blocks.json`. Samengestelde of alternatieve SBB-labels uit de bron (bijvoorbeeld `Keycloak / Autorisatieservice`) blijven als zodanig herkenbaar: dit is geen keuze voor alle alternatieven tegelijk.

Het scherm geeft **lokaal trefwoordadvies** op basis van projectnaam, afbakening en de daadwerkelijk geselecteerde documentinhoud. De adviesregels zijn heuristieken; het is geen semantische AI-analyse en er worden geen verplichte kaders bij verzonnen. De algemene enterprise-architectuurtekst wordt niet als projectvraag gebruikt, omdat deze anders ieder bouwblok relevant zou laten lijken.

Bij een match worden de ABB en de bijbehorende SBB’s automatisch aangevinkt. De architect ziet de aanleiding, het bewijsfragment en de letterlijke bronmapping. Onderwerpwijzigingen en aan- of uitvinken van documenten werken door in het advies. Handmatige afwijkingen blijven behouden; **Volg automatisch advies** wist die afwijkingen. Overige catalogusbouwblokken zijn handmatig toe te voegen. Het advies blijft **te beoordelen**, geen vastgesteld architectuurbesluit.

De HTML-versie leest PDF’s lokaal met de ingebedde PDF.js 6.4.299 en DOCX via de Word-XML. Hiervoor is een moderne browser nodig die module-workers en `DecompressionStream` ondersteunt. De PDF.js-download is gecontroleerd tegen de officiële SHA-512 uit de npm-pakketmetadata; versie, integriteit en Apache-2.0-licentie staan in `assets/vendor/pdfjs/`. De volledige licentie en beide PDF.js-modules zijn ook in het deelbare HTML-bestand opgenomen. Er is geen CDN nodig. Scans zonder tekst, wachtwoordbeveiliging, onleesbare bestanden en bestanden boven 20 MB worden duidelijk gemeld; wanneer de inhoud niet kan worden gelezen, wordt hooguit de bestandsnaam gebruikt, met een expliciete waarschuwing. PDF’s boven 300 pagina’s en tekst boven 1.000.000 tekens worden niet stilzwijgend afgekapt.

In de Python-app wordt de gekozen bouwblokkenlijst met bronmapping als `Bouwblokkenadvies.md` toegevoegd aan de bronset voor conceptgeneratie. In het losse HTML-bestand staat het advies onder `building_blocks` in de gedownloade bronselectie. Daarin staan ook handmatige afwijkingen, bronkenmerken en eventuele leesproblemen. De JSON kan bewijsfragmenten uit je documenten bevatten: deel deze alleen met bevoegde personen.

### Horizon Rotterdam

De bronkaart verwijst naar de [door de gebruiker opgegeven Horizon Rotterdam-view](https://rotterdam.horizzon.cloud/sites/8579a6d6-9680-4fee-959c-4793130eef6f/views/e059f7c1-e164-f111-bb43-025a1dd2f359). Het klikken op deze link laadt de inhoud niet automatisch in de app. Voeg een PDF-, DOCX-, TXT- of Markdown-export toe om de tekst lokaal mee te wegen. Selecteer de Horizon-kaart en de bijbehorende bestanden; uitgevinkte Horizon-bronnen tellen niet mee.

De Horizon-view kon in de ontwikkelomgeving niet worden uitgelezen: de netwerkproxy weigerde het domein met een 403. Dit bewijst niet dat de Horizon-pagina zelf een login vereist. De additionele Rotterdamse ABB/SBB-mapping en eventuele verplichtingen zijn daarom nog niet geverifieerd of aan de catalogus toegevoegd. Het huidige advies verwijst naar de enterprise-architectuurmapping; onbekende Rotterdamse oplossingen worden niet verzonnen. Domeintoegang is als conceptconfiguratie klaargezet voor beoordeling in de cloudomgevingsinstellingen.

### Het deelbare bestand opnieuw bouwen

De bewerkbare frontend staat in `web/`. Het rootbestand `index.html` wordt daaruit opgebouwd en bevat alle benodigde code en afbeeldingen:

```bash
python scripts/build_index.py
```

De broncatalogus bijwerken vanuit een bestaande bronmomentopname kan met `python scripts/update_building_catalogue.py`. Gebruik `--refresh` om eerst de actuele openbare bron op te halen. Bouw daarna `index.html` opnieuw. De trefwoordregels in `architect_agent/building_blocks.py` zijn lokale adviesregels en zijn gescheiden van de letterlijk overgenomen mapping.

Getest: Python-tests, JavaScript/Python-pariteit en browserproeven met onderwerpwijzigingen, handmatige keuzes, TXT/Markdown-, PDF- en DOCX-inhoud, scans, uitvinken en de JSON-download. API-generatie en Notion-publicatie zijn bij deze wijziging niet uitgevoerd. Node.js is alleen nodig voor de optionele pariteitscontrole, niet om de app of het index-bestand te gebruiken.

Onderaan staat de daadwerkelijke bronset met broncodes. Een geselecteerd kader zonder inhoud blokkeert generatie. **Download bronselectie** legt de keuze vast als JSON. **Maak concept-projectstartarchitectuur** gebruikt uitsluitend de gekozen bronnen, controleert lokaal de tekstlimiet en doet pas daarna een AI-aanroep. Bij een te grote bronset wordt niets stilzwijgend afgekapt. Het beoordeelbare concept is als JSON te downloaden; er wordt geen Word-document gemaakt of Notion-publicatie uitgevoerd door deze knop.

Een eerste bronmomentopname voorbereiden (leest een bestaande cache of haalt de openbare bron op):

```bash
.venv/bin/python -m architect_agent.catalogue
```

Netwerktoegang tot `raw.githubusercontent.com` is hiervoor nodig. Zonder netwerk blijft een geldige lokale momentopname bruikbaar; anders kun je een eigen versie uploaden. Tests gebruiken synthetische bronnen en gemockte API-aanroepen. De echte enterprise-architectuurbron is opgehaald en de standaard hoofdstukselectie is lokaal op extractie en omvang gecontroleerd. Er zijn geen betaalde AI-aanroepen of Notion-publicaties uitgevoerd voor deze wijziging.

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
