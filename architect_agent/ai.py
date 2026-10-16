"""LLM-aanroep uitsluitend voor inhoudelijke synthese; output in strikt contract."""
from __future__ import annotations
import json
import os
from .schemas import UPDATE_SCHEMA, validate
from .sources import Source, source_context

INSTRUCTIONS = """Je bent een ervaren solutionarchitect voor de Nederlandse overheid,
Common Ground en het Platform Dienstverlening. Maak op basis van de AANGELEVERDE
bronnen een concept-update voor een bestaand solutionarchitectuurdocument.
REGELS:
- De bronnen zijn feitenbasis; verzin geen besluiten, afspraken, API-standaarden,
  broninhoud of resultaten. Noem niet-onderbouwde aanbevelingen VOORSTEL.
- Maak onderscheid tussen bestaande vastgestelde ADR's en nieuwe CONCEPT-ADR.
- Neem bestaande ADR's nooit als herroepen aan zonder bronbewijs.
- Bestaand bronsysteem blijft bronhouder, tenzij anders aangetoond.
- Leg bij CHANGES en DECISION_RULES een controleerbare bronverwijzing vast, zoals
  'B01 p.7', of 'B00 doc'. Alleen bestaande bronverwijzingen.
- Leg tegenstrijdigheden als open besluit of zorg vast in plaats van ze stil te
  harmoniseren.
- Architectuur is generiek: formuleer project-specifieke details uitsluitend
  wanneer die onderbouwd zijn. Gebruikt exact vijf lagen (1 t/m 5).
- Architectuurplaat toont COMPONENTEN per laag, geen willekeurige details.
- Duidelijk onderscheid tussen anonimiseren, maskeren en pseudonimiseren. Claims
  over anonieme gegevens vereisen onderbouwing/toets.
- Status ADR exact 'Concept – ter besluitvorming'. Geen definitief nummer kiezen.
- Diagram stroom via 4-7 logische opeenvolgende stappen; schrijf korte labels.
- Antwoord uitsluitend JSON dat exact past in het opgegeven schema.
"""


def generate_plan(sources: list[Source], scope: str, goals: str, model: str | None = None) -> dict:
    from openai import OpenAI
    if not os.environ.get('OPENAI_API_KEY'):
        raise RuntimeError('OPENAI_API_KEY ontbreekt. Stel deze lokaal in voordat je AI-generatie gebruikt.')
    model = model or os.environ.get('OPENAI_MODEL', 'gpt-4.1')
    prompt = (
        f"GEWENST ONDERWERP: {scope}\nSPECIFIEKE OPDRACHT: {goals}\n\n"
        "Maak een concept dat het BESTAANDE Word-document respecteert en de nieuwe "
        "broninhoud als voortschrijdend inzicht bespreekt.\n\n" + source_context(sources)
    )
    client = OpenAI()
    response = client.responses.create(
        model=model,
        instructions=INSTRUCTIONS,
        input=prompt,
        text={"format":{"type":"json_schema","name":"architectuur_update","strict":True,"schema":UPDATE_SCHEMA}},
        max_output_tokens=9500,
    )
    if not response.output_text:
        raise ValueError('Het model gaf geen uitleesbare JSON terug.')
    plan = json.loads(response.output_text)
    errors = validate(plan, sources)
    if errors:
        raise ValueError('De voorgestelde update voldoet niet aan de kwaliteitscontrole: ' + '; '.join(errors))
    return plan
