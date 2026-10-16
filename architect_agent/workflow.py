"""Genereer voorstel en bestanden; AI-stap optioneel te omzeilen met beoordeeld JSON."""
from __future__ import annotations
from pathlib import Path
import json
from .sources import collect
from .schemas import validate
from .ai import generate_plan
from .diagram import render_layers, render_flow
from .word import make_document


def prepare(base_doc:Path, sources:list[Path], scope:str, goals:str, model:str|None=None, approved_json:Path|None=None):
    parsed=collect(sources,base_doc=base_doc)
    if approved_json:
        plan=json.loads(Path(approved_json).read_text(encoding='utf-8'))
        # Handmatig gereviewde concepten: kenmerkcontrole wél uitvoeren, geen AI-aanroep.
        errors=validate(plan,parsed)
        if errors:
            raise ValueError('Concept-JSON bevat fouten: '+'; '.join(errors))
    else:
        plan=generate_plan(parsed,scope,goals,model)
    return parsed,plan


def build(base_doc:Path, parsed:list, plan:dict, outdir:Path):
    outdir=Path(outdir);outdir.mkdir(parents=True,exist_ok=True)
    layers_svg,layers_png=render_layers(plan,outdir/'architectuur_vijflagen')
    flow_svg,flow_png=render_flow(plan,outdir/'gegevensstroom')
    document=make_document(base_doc,plan,parsed,{'layers':layers_png,'flow':flow_png},outdir/'Solutionarchitectuur_bijgewerkt_concept.docx')
    (outdir/'concept_review.json').write_text(json.dumps(plan,indent=2,ensure_ascii=False),encoding='utf-8')
    manifest={
       'document':document.name, 'figures':[layers_svg.name,layers_png.name,flow_svg.name,flow_png.name],
       'review_file':'concept_review.json', 'sources':[s.reference for s in parsed],
       'disclaimer':'CONCEPT: eerst broncheck en formele ADR-besluitvorming. Geen vervanging bestaande hoofdstukken.'
    }
    (outdir/'manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False),encoding='utf-8')
    return manifest
