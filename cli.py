"""Commandoregel voor Codex, CI of incidentele offline runs."""
from pathlib import Path
import argparse
from architect_agent.workflow import prepare,build


def main():
    p=argparse.ArgumentParser(description='Herhaalbaar architectuurdocument + ADR + diagrammen')
    p.add_argument('--base',required=True,type=Path,help='Bestaande Word-solutionarchitectuur')
    p.add_argument('--sources',nargs='+',required=True,type=Path,help='Bronnen: PDF, DOCX, TXT, MD')
    p.add_argument('--scope',required=True,help='Onderwerp / epic')
    p.add_argument('--goals',default='Maak een brongetrouwe concept-architectuurupdate.')
    p.add_argument('--model',default=None)
    p.add_argument('--reviewed-plan',type=Path,help='Gebruik gereviewd JSON in plaats van een nieuwe AI-aanroep')
    p.add_argument('--out',default=Path('output'),type=Path)
    args=p.parse_args()
    parsed,plan=prepare(args.base,args.sources,args.scope,args.goals,args.model,args.reviewed_plan)
    files=build(args.base,parsed,plan,args.out)
    print('Bestanden aangemaakt in',args.out.resolve())
    for key,v in files.items():print(f'  {key}: {v}')

if __name__=='__main__':
    main()
