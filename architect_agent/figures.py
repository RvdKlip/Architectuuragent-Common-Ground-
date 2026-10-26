"""Onderwerpgerichte platen met expliciete bronstatus, zonder verzonnen relaties."""
from __future__ import annotations
from html import escape
import json
from pathlib import Path
import re
import textwrap
import cairosvg

REFERENCE=json.loads((Path(__file__).resolve().parents[1]/'assets/diagram_reference.json').read_text())
STYLES=json.loads((Path(__file__).resolve().parents[1]/'assets/housestyles.json').read_text())


def models(plan):
    result=[]
    for kind,layout in REFERENCE['layouts'].items():
        supplied=[d for d in plan.get('diagrams',[]) if d['kind']==kind]
        if supplied:
            result.extend({**d,'chapter':layout['chapter']} for d in supplied)
        else:
            result.append({'kind':kind,'chapter':layout['chapter'],'title':layout['title'],'nodes':[
                {'id':f'pending-{i}','label':'Nog te bepalen uit de projectbronnen','group':group,'status':'unknown','evidence':[]}
                for i,group in enumerate(layout['groups'])], 'edges':[]})
    result.append({'kind':'layers','chapter':5,'title':'Oplossing in vijf lagen','nodes':[
        {'id':f"layer-{layer['number']}-{i}",'label':label,'group':f"L{layer['number']} — {layer['name']}",'status':'unknown','evidence':[]}
        for layer in sorted(plan['layers'],key=lambda x:x['number'],reverse=True)
        for i,label in enumerate(layer['components'] or ['Nog te bepalen uit de projectbronnen'])], 'edges':[]})
    steps=plan['flow_steps']
    result.append({'kind':'flows','chapter':7,'title':'Proces- en gegevensstromen','nodes':[
        {'id':f'step-{i}','label':label,'group':f'Stap {i+1}','status':'unknown','evidence':[]} for i,label in enumerate(steps)],
        'edges':[{'from':f'step-{i}','to':f'step-{i+1}','label':'','evidence':[]} for i in range(len(steps)-1)]})
    return sorted(result,key=lambda d:d['chapter'])


def clean(value):
    return ''.join(c for c in str(value) if ord(c) in (9,10,13) or 32<=ord(c)<=0xD7FF or 0xE000<=ord(c)<=0xFFFD or 0x10000<=ord(c)<=0x10FFFF)


def wrapped(value,limit):
    return [line for p in clean(value).splitlines() or [''] for line in textwrap.wrap(p,limit,break_long_words=True,break_on_hyphens=False) or ['']]


def render(model,plan,brand,index=0):
    style=STYLES[brand];primary=style['primary'];ink=style['ink'];width=1440;margin=32;gap=20
    title_lines=wrapped(model['title'],85);project_lines=wrapped(plan['title'],110)
    rows=[];cards=[];positions={};y=45+len(title_lines)*34+len(project_lines)*23+50;header_y=y
    groups=list(dict.fromkeys(n['group'] for n in model['nodes']))
    def card(node,x,cy,w):
        lines=wrapped(node['label'],max(12,int((w-32)/11)))
        refs=wrapped(' · '.join(node.get('evidence',[])),max(12,int((w-32)/8)))
        h=52+len(lines)*24+(len(refs)*18 if node.get('evidence') else 0)
        c={'node':node,'x':x,'y':cy,'w':w,'h':h,'lines':lines,'refs':refs};cards.append(c);positions[node['id']]=c
        return h
    if model['kind']=='layers':
        for group in groups:
            start=y;row_y=y+20;max_h=0;w=(width-2*margin-250-2*gap)/3
            for i,node in enumerate(n for n in model['nodes'] if n['group']==group):
                if i and i%3==0:row_y+=max_h+14;max_h=0
                max_h=max(max_h,card(node,margin+240+(i%3)*(w+gap),row_y,w))
            h=row_y-start+max_h+20
            rows.append({'x':margin,'y':start,'w':width-2*margin,'h':h,'label':group,'side':True});y+=h+gap
    else:
        for offset in range(0,len(groups),4):
            batch=groups[offset:offset+4];w=(width-2*margin-gap*(len(batch)-1))/len(batch);max_h=0
            for i,group in enumerate(batch):
                x=margin+i*(w+gap);cy=y+28+len(wrapped(group,max(12,int((w-32)/11))))*25
                for node in (n for n in model['nodes'] if n['group']==group):cy+=card(node,x+12,cy,w-24)+14
                h=max(170,cy-y+4);max_h=max(max_h,h)
                rows.append({'x':x,'y':y,'w':w,'h':h,'label':group,'side':False})
            y+=max_h+gap
    height=max(y+112+len(model['edges'])*28,380)
    def text(x,ty,value,size=20,bold=False,color=ink):
        return f'<text x="{x}" y="{ty}" font-family="Arial,DejaVu Sans,sans-serif" font-size="{size}" font-weight="{700 if bold else 400}" fill="{color}">{escape(clean(value))}</text>'
    def box(x,by,w,h,fill,stroke,extra=''):
        return f'<rect x="{x}" y="{by}" width="{w}" height="{h}" rx="14" fill="{fill}" stroke="{stroke}" stroke-width="1.7" {extra}/>'
    svg=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
         f'<defs><linearGradient id="bg{index}" x2="0" y2="1"><stop stop-color="#F7FBFD"/><stop offset="1" stop-color="#EEF5F0"/></linearGradient><marker id="arrow{index}" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto"><path d="M0,0 L0,6 L9,3 z" fill="{primary}"/></marker></defs>',
         f'<rect width="100%" height="100%" fill="url(#bg{index})"/>']
    svg += [text(margin,44+i*34,line,29,True,primary) for i,line in enumerate(title_lines)]
    svg += [text(margin,44+len(title_lines)*34+i*23,line,21,True) for i,line in enumerate(project_lines)]
    svg.append(text(margin,header_y-25,'CONCEPT · Bestaand, voorstel en open punten blijven afzonderlijk herkenbaar.',17))
    for row in rows:
        svg.append(box(row['x'],row['y'],row['w'],row['h'],'#E5F1DE','#88B46B'))
        if row['side']:
            number=re.match(r'L(\d)',row['label'])
            svg += [f'<circle cx="{row["x"]+35}" cy="{row["y"]+42}" r="23" fill="{primary}"/>',text(row['x']+28,row['y']+50,number[1] if number else '',23,True,'#FFFFFF')]
        label=re.sub(r'^L\d+\s*—\s*','',row['label']) if row['side'] else row['label']
        svg.extend(text(row['x']+(72 if row['side'] else 16),row['y']+32+i*25,line,21,True,primary) for i,line in enumerate(wrapped(label,13 if row['side'] else max(12,int((row['w']-32)/11)))))
    for edge_index,edge in enumerate(model['edges']):
        a=positions[edge['from']];b=positions[edge['to']]
        if abs(a['x']-b['x'])<2:
            x=a['x']-8;path=f'M{a["x"]},{a["y"]+a["h"]/2} H{x} V{b["y"]+b["h"]/2} H{b["x"]}'
            lx,ly=a['x']+8,y+edge_index*28
        else:
            route_y=y+edge_index*28;x1=a['x']+a['w']/2;x2=b['x']+b['w']/2
            path=f'M{x1},{a["y"]+a["h"]} V{route_y} H{x2} V{b["y"]+b["h"]}'
            lx,ly=(x1+x2)/2,route_y-5
        svg.append(f'<path d="{path}" fill="none" stroke="{primary}" stroke-width="2" marker-end="url(#arrow{index})"/>')
        if edge['label']:svg.append(text(lx,ly,edge['label'],14))
    for c in cards:
        status=REFERENCE['statuses'][c['node']['status']]
        svg.append(box(c['x'],c['y'],c['w'],c['h'],status['fill'],status['color'],'stroke-dasharray="6 4"' if c['node']['status']=='unknown' else ''))
        svg.extend(text(c['x']+16,c['y']+29+i*24,line,20,True) for i,line in enumerate(c['lines']))
        ty=c['y']+35+len(c['lines'])*24;svg.append(text(c['x']+16,ty,status['label'],14,False,status['color']))
        if c['node'].get('evidence'):svg.extend(text(c['x']+16,ty+19+i*18,line,13) for i,line in enumerate(c['refs']))
    for i,status in enumerate(REFERENCE['statuses'].values()):
        x=margin+i*275;svg += [box(x,height-85,12,12,status['fill'],status['color']),text(x+20,height-74,status['label'],13)]
    svg.append(text(margin,height-31,'Pijlen volgen het uitgewerkte model; controleer bronverwijzingen en besluitstatus.' if model['edges'] else 'Geen relaties vastgesteld: verbindingslijnen zijn niet ingevuld op basis van aannames.',16))
    svg.append('</svg>');svg='\n'.join(svg)
    refs=list(dict.fromkeys([cite for node in model['nodes'] for cite in node.get('evidence',[])]+[cite for edge in model['edges'] for cite in edge.get('evidence',[])]))
    caption='Concept — '+model['title']+'. '+('Bronnen: '+'; '.join(refs) if refs else 'Beschikbaarheid, toepasbaarheid en open punten toetsen aan de projectbronnen.')
    png=cairosvg.svg2png(bytestring=svg.encode(),output_width=1440)
    return {'kind':model['kind'],'chapter':model['chapter'],'title':model['title'],'caption':caption,'svg':svg,'png':png,'width':width,'height':height}


def report_figures(plan,brand):
    return [render(model,plan,brand,i) for i,model in enumerate(models(plan))]
