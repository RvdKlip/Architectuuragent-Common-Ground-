"""Huisstijl en inhoudelijke PSA-uitvoer, onafhankelijk van de publicatiebestemming."""
from html import escape
import json
from pathlib import Path

import fitz

from .schemas import validate, ARCHITECTURE_STRUCTURE

STYLES = json.loads((Path(__file__).resolve().parents[1]/'assets/housestyles.json').read_text())


def house_style(name):
    if name not in STYLES:
        raise ValueError('Kies Rotterdam of Common Ground als huisstijl.')
    return STYLES[name]


def report_sections(plan, sources):
    errors = validate(plan, sources)
    if errors:
        raise ValueError('; '.join(errors))
    content = plan.get('chapter_content', {})
    sections = []
    for chapter in ARCHITECTURE_STRUCTURE:
        key = chapter['key']
        lines = [entry['text'] + ('\nBron: ' + ', '.join(entry['evidence']) if entry['evidence'] else '')
                 for entry in content.get(key, [])]
        if not lines and key not in ('summary', 'scope', 'layers', 'flows', 'decisions'):
            lines.append('Nog te bepalen op basis van bronanalyse en architectuurreview: ' + chapter['requirements'])
        if key == 'summary':
            lines.insert(0, plan['management_summary'])
        elif key == 'scope':
            lines.insert(0, 'Opdracht en afbakening: ' + plan['scope'])
            for change in plan['changes']:
                lines += ['Architectuurkeuze: ' + change['section'], change['change'],
                          'Onderbouwing: ' + change['rationale'], 'Bron: ' + ', '.join(change['evidence'])]
            lines += ['Bronnen en herleidbaarheid:'] + [source.reference for source in sources]
        elif key == 'layers':
            for layer in sorted(plan['layers'], key=lambda item: item['number'], reverse=True):
                lines += [f"Laag {layer['number']} — {layer['name']}"] + layer['components']
        elif key == 'flows':
            lines += plan['flow_steps']
        elif key == 'decisions':
            adr = plan['adr']
            lines += ['ADR — ' + adr['title'], 'Status: ' + adr['status'], 'Context: ' + adr['context'],
                      'Besluit (voorgesteld): ' + adr['decision']]
            for title, field in [('Principe', 'principles'), ('Implicatie', 'implications'),
                                 ('Eventuele zorgen', 'concerns'), ('Implementatie', 'implementation')]:
                lines += [title + ':'] + adr[field]
            lines += ['Samenhang met bestaande ADR’s: ' + adr['relation_existing_adrs'], 'Architectuurregels:']
            lines += [f"{rule['id']}: {rule['rule']} — {rule['status']}; bron: {', '.join(rule['evidence'])}" for rule in plan['decision_rules']]
        elif key == 'acceptance':
            lines += ['Open besluiten:'] + plan['open_decisions'] + ['Aannames en controlepunten:'] + plan['assumptions']
        sections.append((chapter['title'], lines))
    return sections



def report_html(plan, sources, brand, *, confluence=False):
    style = house_style(brand)
    sections = report_sections(plan, sources)
    title = escape(plan['title'])
    content = ''.join('<h2>'+escape(title)+'</h2>'+''.join('<p>'+escape(str(line))+'</p>' for line in lines)
                      for title, lines in sections)
    banner = '<p><strong>CONCEPT — ter beoordeling</strong> · Huisstijl: '+escape(brand)+'</p>'
    if confluence:
        banner = ('<ac:structured-macro ac:name="panel"><ac:parameter ac:name="bgColor">'+style['pale']+
                  '</ac:parameter><ac:parameter ac:name="borderColor">'+style['primary']+
                  '</ac:parameter><ac:rich-text-body>'+banner+'</ac:rich-text-body></ac:structured-macro>')
        return '<h1>'+title+'</h1>'+banner+content
    css = f"body{{font-family:{style['font']};font-size:11pt;color:{style['ink']};line-height:1.5}}h1{{color:{style['primary']};font-size:27pt}}h2{{color:{style['primary']};font-size:15pt;page-break-after:avoid}}.banner{{background:{style['pale']};border-left:5px solid {style['primary']};padding:12px}}p{{white-space:pre-wrap}}"
    return '<!doctype html><html lang="nl"><head><meta charset="utf-8"><style>'+css+'</style></head><body><h1>'+title+'</h1><div class="banner">'+banner+'</div>'+content+'</body></html>'


def report_pdf(plan, sources, brand):
    style = house_style(brand)
    html = report_html(plan, sources, brand)
    document = fitz.open()
    # insert_htmlbox verzorgt tekstomloop; pagineer met Story voor lange PSA’s.
    import io
    buffer = io.BytesIO()
    writer = fitz.DocumentWriter(buffer)
    story = fitz.Story(html=html)
    page_size = fitz.paper_rect('a4')
    def rectangle(number, filled):
        return page_size, fitz.Rect(45, 48, page_size.width-45, page_size.height-48), None
    story.write(writer, rectangle)
    writer.close()
    document.close()
    document = fitz.open(stream=buffer.getvalue(), filetype='pdf')
    color = tuple(int(style['primary'][i:i+2], 16)/255 for i in (1, 3, 5))
    for number, page in enumerate(document, 1):
        page.draw_rect(fitz.Rect(0, 0, page.rect.width, 12), color=color, fill=color, overlay=True)
        page.insert_text((45, page.rect.height-24), f'{brand} | CONCEPT | {number}/{len(document)}', fontsize=8, color=color)
    result = document.tobytes()
    document.close()
    return result
