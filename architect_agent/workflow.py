"""Genereer voorstel en bestanden; AI-stap optioneel te omzeilen met beoordeeld JSON."""
from __future__ import annotations
from pathlib import Path
import json
from .sources import collect
from .schemas import validate
from .ai import generate_plan
from .word import make_document


def prepare(base_doc:Path|None, sources:list[Path], scope:str, goals:str, model:str|None=None, approved_json:Path|None=None, *, project_start:bool=False):
    parsed=collect(sources,base_doc=base_doc)
    if approved_json:
        plan=json.loads(Path(approved_json).read_text(encoding='utf-8'))
        # Handmatig gereviewde concepten: kenmerkcontrole wél uitvoeren, geen AI-aanroep.
        errors=validate(plan,parsed)
        if errors:
            raise ValueError('Concept-JSON bevat fouten: '+'; '.join(errors))
    else:
        if project_start:
            plan=generate_plan(parsed,scope,goals,model,project_start=True)
        else:
            plan=generate_plan(parsed,scope,goals,model)
    return parsed,plan


def build(base_doc:Path, parsed:list, plan:dict, outdir:Path):
    outdir=Path(outdir);outdir.mkdir(parents=True,exist_ok=True)
    from .figures import report_figures
    figures=report_figures(plan,'Common Ground');by_chapter={};figure_names=[];counts={}
    for figure in figures:
        kind=figure['kind'];counts[kind]=counts.get(kind,0)+1
        name={'layers':'architectuur_vijflagen','flows':'gegevensstroom'}.get(kind,kind+'_'+str(counts[kind]))
        svg=outdir/(name+'.svg');png=outdir/(name+'.png')
        svg.write_text(figure['svg'],encoding='utf-8');png.write_bytes(figure['png'])
        figure_names.extend([svg.name,png.name]);by_chapter.setdefault(figure['chapter'],[]).append({'path':png,'caption':figure['caption']})
    document=make_document(base_doc,plan,parsed,{'by_chapter':by_chapter},outdir/'Solutionarchitectuur_bijgewerkt_concept.docx')
    (outdir/'concept_review.json').write_text(json.dumps(plan,indent=2,ensure_ascii=False),encoding='utf-8')
    manifest={
       'document':document.name, 'figures':figure_names,
       'review_file':'concept_review.json', 'sources':[s.reference for s in parsed],
       'disclaimer':'CONCEPT: eerst broncheck en formele ADR-besluitvorming. Geen vervanging bestaande hoofdstukken.'
    }
    (outdir/'manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False),encoding='utf-8')
    return manifest
