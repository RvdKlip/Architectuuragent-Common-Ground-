"""Scherpe, deterministische SVG/PNG-architectuurplaten in G4-vijflagenstijl."""
from __future__ import annotations
from pathlib import Path
from html import escape
import textwrap
import cairosvg

TEAL = '#0D4F67'
GREEN = '#EAF6E7'
GREEN_BORDER = '#79BC70'
PALE = '#F2F7FA'
INK = '#143347'
BLUE_BORDER = '#BDD8E8'


def rect(x,y,w,h,fill='#ffffff',stroke=TEAL,rx=13,sw=1.5):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" />'


def txt(x,y,value,size=21,weight=400,fill=INK,anchor='start'):
    return f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" fill="{fill}" text-anchor="{anchor}" font-family="Arial,DejaVu Sans,sans-serif">{escape(str(value))}</text>'


def wrap(value:str, limit:int) -> list[str]:
    lines=[]
    for segment in value.split('\n'):
        lines.extend(textwrap.wrap(segment, limit, break_long_words=False, break_on_hyphens=False) or [''])
    return lines


def save_svg_png(content:str, basename:Path):
    svg=Path(str(basename)+'.svg')
    png=Path(str(basename)+'.png')
    svg.write_text(content,encoding='utf-8')
    cairosvg.svg2png(bytestring=content.encode('utf-8'),write_to=str(png),output_width=1900)
    return svg,png


def render_layers(plan:dict, out:Path):
    layers={int(l['number']):l for l in plan['layers']}
    width=1600
    name_override={
       5:'Interactie',4:'Procesinrichting',3:'Connectiviteit',2:'Diensten',1:'Registers en data'
    }
    rows=[]
    for n in range(5,0,-1):
        layer=layers[n]
        comp=layer['components']
        maxlines=sum(len(wrap(s,83)) for s in comp)
        height=max(118, 36+maxlines*26)
        rows.append((n,layer,height))
    total=140+sum(h+12 for _,_,h in rows)+100
    body=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{total}" viewBox="0 0 {width} {total}">',
          rect(0,0,width,total,'#FFFFFF','#FFFFFF',0,0),
          txt(54,54,'Architectuurpositie in vijf lagen',34,700,TEAL),
          txt(54,91,plan['title'],19,400,INK)]
    y=127
    for n,layer,h in rows:
        body.append(f'<circle cx="64" cy="{y+45}" r="30" fill="{TEAL}"/>')
        body.append(txt(64,y+55,str(n),27,700,'white','middle'))
        body.append(rect(111,y,282,h,PALE,BLUE_BORDER,14,1.7))
        body.append(txt(133,y+38,name_override[n],23,700,TEAL))
        extra=wrap(layer.get('name',name_override[n]),26)
        for k,s in enumerate(extra[:2]):
            body.append(txt(133,y+65+k*24,s,16,400,INK))
        body.append(rect(411,y,1118,h,GREEN,GREEN_BORDER,14,1.9))
        cy=y+34
        for comp in layer['components']:
            for line in wrap(comp,89):
                body.append(f'<circle cx="445" cy="{cy-7}" r="4.5" fill="{GREEN_BORDER}" />')
                body.append(txt(462,cy,line,19,500,INK))
                cy+=26
        y+=h+12
    body.append(rect(52,y+5,1476,60,PALE,BLUE_BORDER,9,1.2))
    body.append(txt(73,y+43,'Architectuurconcept • bronsystemen blijven verantwoordelijk voor hun eigen gegevens en processen',17,500,TEAL))
    body.append('</svg>')
    return save_svg_png('\n'.join(body),out)


def render_flow(plan:dict, out:Path):
    steps=plan['flow_steps']
    if not (3 <= len(steps) <= 9):
        raise ValueError('Voor het gegevensstroomdiagram zijn 3 tot 9 stappen nodig.')
    width=1675
    height=330
    left=44
    gap=26
    box_width=(width-2*left-gap*(len(steps)-1))/len(steps)
    if box_width<105:
        raise ValueError('Te veel stappen voor leesbare plaat')
    outsvg=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<defs><marker id="arrow" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto"><path d="M0,0 L0,6 L9,3 z" fill="#0D4F67"/></marker></defs>',
        rect(0,0,width,height,'white','white',0,0),
        txt(45,50,'Gegevensstroom en verwerkingsvolgorde',30,700,TEAL),
        txt(45,82,'Concept: privacytoets en expliciete bron- en kwaliteitsafspraken vereist',17,400,INK)]
    for i,step in enumerate(steps):
        x=left+i*(box_width+gap)
        outsvg.append(rect(round(x,1),123,round(box_width,1),145,GREEN if i%2 else PALE,GREEN_BORDER if i%2 else BLUE_BORDER,10,2))
        outsvg.append(f'<circle cx="{x+22}" cy="{145}" r="12" fill="{TEAL}"/>')
        outsvg.append(txt(x+22,150,str(i+1),14,700,'white','middle'))
        lines=wrap(step, max(13,int(box_width/11)))
        if len(lines)>4:
            lines=wrap(step,max(16,int(box_width/9)))
        for j,line in enumerate(lines):
            outsvg.append(txt(round(x+box_width/2,1),177+j*23,line,17,500,INK,'middle'))
        if i<len(steps)-1:
            outsvg.append(f'<line x1="{x+box_width+4}" y1="195" x2="{x+box_width+gap-4}" y2="195" stroke="{TEAL}" stroke-width="2.3" marker-end="url(#arrow)"/>')
    outsvg.append('</svg>')
    return save_svg_png('\n'.join(outsvg),out)
