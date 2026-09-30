#!/usr/bin/env python3
"""Freeze V4 evidence and render a read-only whole-board layout review."""
import collections
import csv
import hashlib
import html
import json
import math
from pathlib import Path
import re
import zipfile

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as Patch, Rectangle
from shapely.geometry import LineString, Point
from shapely.ops import unary_union

from kicad_sexpr import child, children
from v4_geometry import geometry, filled_ground

ROOT = Path(__file__).resolve().parents[3]
P = ROOT / 'projects/nfc-business-card'
S = P / 'hardware/kicad/v4-phase3'
OUT = P / 'hardware/records/kicad-v4-phase3/layout-review'
OUT.mkdir(exist_ok=True)
board_path = S / 'NFC-Card-V4.kicad_pcb'
before = hashlib.sha256(board_path.read_bytes()).hexdigest()
board, pads, objects, refs = geometry(board_path)
drc = json.loads((OUT / 'native-drc.json').read_text())

groups = [
 ('MCU', 'U1 / module', ['U1'], '#3959a0'),
 ('DEC', 'C1/C6/C7 / MCU decoupling', ['C1','C6','C7'], '#267c93'),
 ('CHG', 'U2 / charge + controls', ['U2','C2','C3','C8','R5','R6','R7','R8','R9','R19','NTC'], '#c17324'),
 ('LDO', 'U3 / regulator', ['U3','C4','C5'], '#a06223'),
 ('USB', 'J1 + ESD / USB + CC', ['J1','U5','U6','R1','R2'], '#ab4471'),
 ('SER', 'R3/R4 / USB series', ['R3','R4'], '#933264'),
 ('EPD', 'Display switch + full boost/pump', ['U4','C9','C10','Q1','L1','R13','R14','R15','D1','D2','D3','C11','C12','C13','R16','R18'], '#1d8d87'),
 ('FPC', 'J2 / display interface', ['J2','R17'], '#216c74'),
 ('OUT', 'C14-C22 / panel rails', [f'C{i}' for i in range(14,23)], '#387d6e'),
 ('ADC', 'Q2/Q3 / battery sensing', ['Q2','Q3','R20','R21','R22','R23','C25'], '#8b58a1'),
 ('KEY', 'Keys + pullups', ['SW1','SW2','SW3','R10','R11','R12'], '#5b7633'),
 ('RF', 'NFC / matching + contacts', ['C23','C24','NFC1','NFC2'], '#7945a0'),
 ('BAT', 'BP/BN / fixed battery lands', ['BP','BN'], '#985131'),
 ('DBG', 'TP1-TP5 / fixed SWD lands', ['TP1','TP2','TP3','TP4','TP5'], '#436287'),
]
ref_group = {ref:g[0] for g in groups for ref in g[2]}
net_pads = collections.defaultdict(list)
for name, p in pads.items():
    if p['net'] and not p['net'].startswith('unconnected-'):
        net_pads[p['net']].append({'pin':name, 'at':list(p['at']), 'layers':p['layers'], 'group':ref_group.get(name.split('.')[0], 'OTHER')})
airwires=[]
for i,item in enumerate(drc['unconnected_items'],1):
    ends=item['items']; matches=re.findall(r'\[([^\]]+)\]', ends[0]['description'])
    net=matches[0] if matches else 'UNKNOWN'
    airwires.append({'id':f'A{i:02}', 'net':net, 'ends':ends})
with (OUT/'unconnected.csv').open('w') as f:
    w=csv.writer(f);w.writerow(['id','net','from','x1_mm','y1_mm','to','x2_mm','y2_mm'])
    for a in airwires:
        x,y=a['ends'];w.writerow([a['id'],a['net'],x['description'],x['pos']['x'],x['pos']['y'],y['description'],y['pos']['x'],y['pos']['y']])

# Keep source plans, logs, native project and library paths together in a small checkpoint.
files=[f for f in S.rglob('*') if f.is_file() and not f.name.startswith('~') and f.suffix not in ('.kicad_prl',)]
art=P/'artifacts/kicad-v4-phase3'
files += [f for f in art.iterdir() if f.is_file() and f.suffix in ('.log','.py','.json')]
files += [f for f in art.glob('layout-*.kicad_pcb')]
files += [P/'scripts'/n for n in ('route-v4-octilinear.py','resolve-v4-route-conflicts.py','v4_geometry.py','kicad_sexpr.py','prepare-v4-freerouting.py','apply-v4-ipc.py')]
manifest={str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest() for f in files}
archive=OUT/'checkpoint.zip'
if not archive.exists():
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
        for f in files:z.write(f,f.relative_to(ROOT))
    (OUT/'checkpoint-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
else:
    frozen=json.loads((OUT/'checkpoint-manifest.json').read_text())
    assert frozen[str(board_path.relative_to(ROOT))]==before, 'Frozen native PCB changed'

trials=[]
for path in sorted(S.glob('*-plan.json')):
    q=json.loads(path.read_text())
    if 'failures' not in q:continue
    trials.append({'trial':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(), 'route_pieces':len(q.get('routes',[])), 'vias':len(q.get('vias',[])), 'failure_count':len(q['failures']), 'failed_requests':[x.get('name',x.get('via',{}).get('name','via')) for x in q['failures']]})
(OUT/'trial-index.json').write_text(json.dumps(trials,indent=2)+'\n')

zones=[]
for z in children(board,'zone'):
    if not child(z,'keepout'):continue
    zones.append({'name':child(z,'name')[1], 'layers':(child(z,'layers') or child(z,'layer'))[1:], 'rules':{x[0]:x[1] for x in child(z,'keepout')[1:]}, 'polygon':[[float(c) for c in xy[1:]] for xy in child(child(z,'polygon'),'pts')[1:]]})

bottlenecks=[
 ('B1',[163,110.5,178.8,120.2],'MCU entry: screen / USB / SWD / decoupling / charger control'),
 ('B2',[157,103.5,181.5,111.5],'Crossing: charger control + SYS / VBUS / 3V3 / BAT'),
 ('B3',[165,93.5,170.1,100.0],'J2: six signals, high-voltage outputs and return'),
 ('B4',[178.5,100.5,187.5,110.5],'USB fanout + ESD ground + proposed debug passage'),
 ('B5',[163.5,118.4,171.7,125.0],'SWD / keys / fixed NFC matching'),
]
# Windows below are planning envelopes, not placed footprints or approved routes.
options={
 'A':{'title':'A / east charger, short local controls', 'windows':[
  ['CHG east',[173.8,104.7,181.8,111.9]], ['LDO west of CHG',[168,105,173.4,110.4]],
  ['Full display group',[168,85,182,103.8]], ['Key pullups west',[151,109,163,116]],
  ['ADC retained east',[180,112,190.3,124.5]]],
  'corridors':[['Screen B',[[166.4,118],[164.3,109],[164.3,98],[168.1,96]]],
   ['SWD F west',[[167,119],[153,118],[153,83],[183,81.5]]],
   ['USB B southeast',[[165,115],[170,118],[180,118],[183,104]]],
   ['Charge local F',[[177,108],[177,113.9]]],
   ['BAT + return',[[144,111.3],[155,110],[163,110],[175,107]]]]},
 'B':{'title':'B / west power island, east debug corridor', 'windows':[
  ['CHG rotate / west',[151.5,102,162.5,111.5]], ['LDO beside CHG',[162.8,105,168,110.5]],
  ['Full display group north',[168,84,180.5,101]], ['ESD against J1',[182,101,185.3,110]],
  ['ADC + key pullups east',[180,112,190.3,124.5]]],
  'corridors':[['Screen B spine',[[167,118],[165.5,110],[165.5,99],[168.1,96]]],
   ['Charge F crossing',[[160,107],[169,108],[177,113.9]]],
   ['SWD B east',[[167,119],[178.5,116],[180.5,100],[183,81.5]]],
   ['USB B southeast',[[165,115],[169,118],[179,117],[184,104]]],
   ['VBUS + return',[[186,106.4],[172,104],[161,104]]]]}}

data={'board':str(board_path.relative_to(ROOT)), 'sha256':before,'counts':{'segments':len(children(board,'segment')), 'vias':len(children(board,'via')), 'drc':len(drc['violations']), 'unconnected':len(airwires),'parity':len(drc['schematic_parity'])}, 'drc_categories':dict(collections.Counter(x['type'] for x in drc['violations'])), 'groups':[{'id':a,'title':b,'refs':c,'color':d} for a,b,c,d in groups], 'nets':dict(sorted(net_pads.items())), 'unconnected':airwires,'keepouts':zones,'bottlenecks':bottlenecks,'options':options}
(OUT/'review-data.json').write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n')

# SVG uses KiCad millimetres directly; no remapping of pad locations.
def esc(x):return html.escape(str(x),quote=True)
def shape_svg(g,attrs):
    if hasattr(g,'geoms'):return ''.join(shape_svg(x,attrs) for x in g.geoms)
    if not hasattr(g,'exterior') or g.is_empty:return ''
    rings=[g.exterior,*g.interiors]
    d=' '.join('M '+' L '.join(f'{x:.5f},{y:.5f}' for x,y in ring.coords)+' Z' for ring in rings)
    return f'<path d="{d}" fill-rule="evenodd" {attrs}/>'
svg=['<svg id="board" viewBox="107 75 89 58" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="V4 全板布局与可布性复盘">','<rect x="107" y="75" width="89" height="58" fill="#fff"/>']
for layer in ('F.Cu','B.Cu'):
    svg.append('<g class="ground '+layer[0]+'">'+shape_svg(filled_ground(board,layer),'fill="#bcdbc9" opacity=".38"')+'</g>')
for z in zones:
    poly=' '.join(','.join(map(str,p)) for p in z['polygon']);hard=z['rules'].get('tracks')=='not_allowed';col='#df7e14' if hard else '#bc97bb'
    svg.append(f'<polygon class="zones" points="{poly}" fill="{col}" fill-opacity=".10" stroke="{col}" stroke-width=".12" stroke-dasharray=".6 .4"><title>{esc(z["name"]+" "+str(z["rules"]))}</title></polygon>')
for o in objects:
    if o['kind']=='keepout':continue
    for layer in o['layers']:
        col='#276fa3' if layer=='B.Cu' else '#d65a46'
        if o['kind']=='pad':col='#535963'
        if o['net']=='GND':col='#338265'
        attrs=f'class="copper {layer[0]}" data-net="{esc(o["net"])}" fill="{col}" opacity=".8"'
        svg.append('<g>'+shape_svg(o['shape'],attrs)+f'<title>{esc(o["name"])} · {esc(o["net"])} · {layer}</title></g>')
for x in board:
    if not isinstance(x,list) or x[0] not in ('gr_line','gr_arc') or child(x,'layer')[1]!='Edge.Cuts':continue
    a,b=[list(map(float,child(x,k)[1:3])) for k in ('start','end')]
    if x[0]=='gr_arc':
        # Native arc midpoint is retained as a visible polyline for overview only.
        m=list(map(float,child(x,'mid')[1:3]));pts=[a,m,b]
    else:pts=[a,b]
    svg.append('<polyline points="'+' '.join(','.join(map(str,p)) for p in pts)+'" fill="none" stroke="#27313f" stroke-width=".16"/>')
for a in airwires:
    p,q=a['ends'];p=p['pos'];q=q['pos'];color=next((g[3] for g in groups if any(x['group']==g[0] for x in net_pads.get(a['net'],[]))),'#d02626')
    svg.append(f'<line class="airwire" data-net="{esc(a["net"])}" x1="{p["x"]}" y1="{p["y"]}" x2="{q["x"]}" y2="{q["y"]}" stroke="{color}" stroke-width=".10" stroke-dasharray=".45 .3"><title>{a["id"]} {esc(a["net"])} — DRC 未连接标记点；不是建议走线</title></line>')
for ref,(x,y,a) in refs.items():
    svg.append(f'<text class="refs" x="{x}" y="{y-.65}" font-size=".65" text-anchor="middle" fill="#27313f" paint-order="stroke" stroke="white" stroke-width=".2">{ref}</text>')
for name,p in pads.items():
    x,y=p['at'];svg.append(f'<text class="pins" data-net="{esc(p["net"])}" x="{x}" y="{y+.12}" font-size=".34" text-anchor="middle" fill="black" paint-order="stroke" stroke="white" stroke-width=".09">{esc(name)}</text>')
for ident,title,members,col in groups:
    gs=[o['shape'] for o in objects if o['kind']=='pad' and o['name'].split('.')[0] in members]
    if not gs:continue
    x0,y0,x1,y1=unary_union(gs).bounds
    # Dispersed groups use an ID near each member instead of a misleading giant box.
    if ident in ('KEY','RF'):
        for ref in members:
            if ref in refs:
                x,y,_=refs[ref];svg.append(f'<text class="groups" x="{x}" y="{y+1.0}" font-size=".62" fill="{col}" text-anchor="middle">{ident}</text>')
    else:
        svg.append(f'<rect class="groups" x="{x0-.45}" y="{y0-.45}" width="{x1-x0+.9}" height="{y1-y0+.9}" rx=".4" fill="none" stroke="{col}" stroke-width=".12" stroke-dasharray=".6 .35"/>')
        svg.append(f'<text class="groups" x="{x0}" y="{y0-.65}" font-size=".9" fill="{col}" paint-order="stroke" stroke="white" stroke-width=".22">{ident}</text>')
for name,(x0,y0,x1,y1),label in bottlenecks:
    svg.append(f'<rect class="bottlenecks" x="{x0}" y="{y0}" width="{x1-x0}" height="{y1-y0}" fill="#ff9c71" fill-opacity=".035" stroke="#a64216" stroke-width=".15" stroke-dasharray=".2 .5"><title>{name} {label}</title></rect>')
    svg.append(f'<text class="bottlenecks" x="{x1-.8}" y="{y1-.4}" font-size=".85" fill="#993e1a">{name}</text>')
# Named source/return relationships are overlays, never claimed as completed copper.
relationships=[(name,[pads[p]['at'] for p in names]) for name,names in [
    ('VBUS feed',['J1.A4B9','C8.1','U2.10']),
    ('SYS feed',['U2.1','C2.1','C4.1','U3.1']),
    ('3V3 feed',['U3.5','C5.1','C6.1','C7.1']),
    ('BAT feed',['BP.1','C3.1','U2.2']),
    ('BN return REQUIRED',['BN.1','C3.2','U2.11']),
    ('USB return REQUIRED',['U2.11','C8.2','J1.A1B12']),
    ('U3 local return',['C5.2','U3.2','C4.2']),
    ('Display local return',['C12.2','C10.2','R15.2','J2.17'])]]
for label,pts in relationships:
    svg.append('<g class="power"><polyline points="'+' '.join(','.join(map(str,p)) for p in pts)+'" fill="none" stroke="#ac5619" stroke-width=".25" stroke-dasharray=".7 .4"/>'+
        f'<text x="{pts[0][0]}" y="{pts[0][1]-1}" font-size=".8" fill="#9a4213" paint-order="stroke" stroke="white" stroke-width=".2">{label}</text></g>')
for key,opt in options.items():
    svg.append(f'<g class="option option{key}" style="display:none">')
    for label,(x0,y0,x1,y1) in opt['windows']:
        svg.append(f'<rect x="{x0}" y="{y0}" width="{x1-x0}" height="{y1-y0}" fill="#426cc0" fill-opacity=".17" stroke="#244ea2" stroke-width=".16"/><text x="{x0+.2}" y="{y0+.85}" font-size=".65" fill="#193d8b">{label}</text>')
    for label,pts in opt['corridors']:
        svg.append('<polyline points="'+' '.join(','.join(map(str,p)) for p in pts)+'" fill="none" stroke="#d94167" stroke-width=".32" stroke-dasharray=".8 .5"/>'+f'<text x="{pts[1][0]}" y="{pts[1][1]-.3}" font-size=".65" fill="#a52d4c">{label}</text>')
    svg.append('</g>')
svg.append('<text x="111" y="80" font-size="1.25" fill="#27313f">V4 · frozen layout diagnosis</text><text x="111" y="82" font-size=".85" fill="#8a4e40">61 airwires · 361 segments / 65 vias · NOT FOR FABRICATION</text><text x="114" y="96" font-size="1.0" fill="#8b5981">NFC / screen mechanical region</text><text x="114" y="98" font-size=".8" fill="#8b5981">No general-purpose placement / return plane</text></svg>')
svg=''.join(svg)
(OUT/'whole-board.svg').write_text(svg)

page=r'''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>NFC V4 全板可布性复盘</title>
<style>*{box-sizing:border-box}body{margin:0;background:#eff2f6;color:#203044;font:15px -apple-system,BlinkMacSystemFont,"PingFang SC",sans-serif}header{padding:22px 28px;background:#192d45;color:white}h1{margin:0 0 8px;font-size:24px}p{line-height:1.6;margin:8px 0}.layout{display:grid;grid-template-columns:300px 1fr;gap:16px;padding:18px}aside,main{background:white;border-radius:10px;padding:18px}aside{max-height:90vh;overflow:auto}button,select{padding:7px;border:1px solid #bdc9d9;border-radius:5px;background:#fff;color:#243f62;margin:3px 1px;cursor:pointer}button.active{background:#284c81;color:white}label{display:block;margin:7px 0}#board{width:100%;height:66vh;min-height:480px;border:1px solid #dce2eb}table{border-collapse:collapse;width:100%;font-size:12px}th,td{border-bottom:1px solid #e4e8ee;padding:6px;text-align:left;vertical-align:top}.scroll{max-height:260px;overflow:auto}.muted{color:#637287;font-size:12px}.note{background:#fff5e9;border-left:3px solid #dca257;padding:8px 12px}h2{font-size:17px;margin:20px 0 8px}.groups-list{font-size:12px;line-height:1.8}.legend{display:flex;gap:16px;font-size:12px;flex-wrap:wrap}.pins{display:none}.power{display:none}#details{white-space:pre-wrap;font:12px ui-monospace,monospace}a{color:#245d9c}@media(max-width:900px){.layout{display:block}aside{max-height:280px;margin-bottom:14px}#board{height:58vh;min-height:360px}}</style>
<header><h1>NFC V4 全板布局与可布性复盘</h1><p>冻结候选，停止试路。实铜、未连接关系与方案意图分别显示；A/B 均未实施。</p></header><div class="layout"><aside><b>显示与定位</b><div><button onclick="zoom('all')">全板</button><button onclick="zoom('critical')">关键区</button><button onclick="zoom('mcu')">MCU 出口</button><button onclick="zoom('j2')">J2</button><button onclick="zoom('usb')">USB</button></div>
<label>选择网络 <select id="net"><option value="">全部网络</option></select></label><label><input type="checkbox" checked onchange="toggle('.F',this.checked)">顶层实铜 / 焊盘</label><label><input type="checkbox" checked onchange="toggle('.B',this.checked)">底层实铜 / 焊盘</label><label><input type="checkbox" checked onchange="toggle('.ground',this.checked)">保存的实际地铜</label><label><input type="checkbox" checked onchange="toggle('.airwire',this.checked)">全部 61 个 DRC 未连接项</label><label><input type="checkbox" checked onchange="toggle('.groups',this.checked)">功能组</label><label><input type="checkbox" checked onchange="toggle('.bottlenecks',this.checked)">通道瓶颈 B1–B5</label><label><input type="checkbox" onchange="toggle('.pins',this.checked)">实际引脚名称（放大看）</label><label><input type="checkbox" onchange="toggle('.power',this.checked)">供电 / 返回关系提示</label>
<h2>布局方案覆盖层</h2><button onclick="option('')">冻结实况</button><button onclick="option('A')">方案 A</button><button onclick="option('B')">方案 B</button><p class="muted">蓝色框是待排入的器件组窗口；红虚线仅示通道意图，没有完成引脚逃逸、铺铜或 DRC。旧铜不是固定障碍。</p><h2>功能组索引</h2><div id="groups" class="groups-list"></div></aside><main>
<div class="legend"><span>红：F.Cu</span><span>蓝：B.Cu</span><span>绿：实际 GND</span><span>细虚线：未连接关系</span><span>紫/橙：禁铜/禁布区</span></div>__SVG__
<p class="note" id="status">冻结实况。未连接虚线来自原生 DRC 的对象标记点；Zone 端点不是实际最近铜边，也不是建议走线。双层透视不代表两面铜互通。</p>
<div class="scroll"><table><thead><tr><th>编号 / 网络</th><th>起点</th><th>终点</th></tr></thead><tbody id="airs"></tbody></table></div><h2>所选网络的全部实际引脚</h2><div id="details">选网络查看引脚、坐标、图层和功能组。</div><p class="muted">KiCad mm，顶视坐标；底层未镜像。板框圆弧仅在此概览中用原生起/中/终点折线显示，精确制造几何保持原文件。</p><p><a href="../../../v4-layout-routability-review.md">完整复盘报告</a> · <a href="unconnected.csv">61 项 CSV</a> · <a href="checkpoint.zip">冻结工程与失败记录</a></p></main></div>
<script>const D=__DATA__;const net=document.querySelector('#net');for(const n of Object.keys(D.nets)){const o=document.createElement('option');o.value=n;o.textContent=n+' ('+D.unconnected.filter(a=>a.net===n).length+' 未连接)';net.append(o)}
function toggle(sel,on){document.querySelectorAll(sel).forEach(e=>e.style.display=on?'inline':'none')}
function zoom(where){const v={all:'107 75 89 58',critical:'149 80 44 49',mcu:'162 109 20 17',j2:'156 87 18 18',usb:'176 98 17 15'};document.querySelector('#board').setAttribute('viewBox',v[where])}
function option(k){document.querySelectorAll('.option').forEach(e=>e.style.display='none');if(k)document.querySelector('.option'+k).style.display='block';document.querySelector('#status').textContent=k?D.options[k].title+'。仅布局/通道提案，未实施；不构成可布或回流通过。':'冻结实况。虚线是原生 DRC 未连接对象标记点；Zone 标记不是最近铜边。'}
function render(){const n=net.value;document.querySelectorAll('[data-net]').forEach(e=>e.style.opacity=!n||e.dataset.net===n?'':'.055');const t=document.querySelector('#airs');t.replaceChildren();for(const a of D.unconnected.filter(a=>!n||a.net===n)){const row=document.createElement('tr');for(const s of [a.id+' '+a.net,...a.ends.map(e=>e.description+' @ '+e.pos.x.toFixed(3)+', '+e.pos.y.toFixed(3))]){const c=document.createElement('td');c.textContent=s;row.append(c)}t.append(row)}document.querySelector('#details').textContent=n?D.nets[n].map(p=>p.pin+'  '+p.at.map(x=>x.toFixed(4)).join(', ')+' mm  '+p.layers.join('/')+'  '+p.group).join('\n'):'选网络查看引脚、坐标、图层和功能组。'}net.onchange=render;render();document.querySelector('#groups').innerHTML=D.groups.map(g=>'<div><b style="color:'+g.color+'">'+g.id+'</b> '+g.title+'</div>').join('');</script></html>'''
page=page.replace('__SVG__',svg).replace('__DATA__',json.dumps(data,ensure_ascii=False).replace('</','<\\/'))
(OUT/'index.html').write_text(page)

# Static board figure contains every native airwire; the HTML supplies readable filtering.
fig,ax=plt.subplots(figsize=(16,10),constrained_layout=True)
outline_segments=[]
for item in board:
    if not isinstance(item,list) or item[0] not in ('gr_line','gr_arc') or child(item,'layer')[1]!='Edge.Cuts':continue
    tags=('start','mid','end') if item[0]=='gr_arc' else ('start','end')
    pts=[list(map(float,child(item,k)[1:3])) for k in tags]
    outline_segments.append(pts)
    x,y=zip(*pts);ax.plot(x,y,color='#263746',lw=.8)
for layer in ('F.Cu','B.Cu'):
    ground=filled_ground(board,layer)
    for g in (list(ground.geoms) if hasattr(ground,'geoms') else [ground]):
        if g.is_empty:continue
        ax.add_patch(Patch(g.exterior.coords,facecolor='#d9e9df',edgecolor='none',alpha=.4))
        for hole in g.interiors:ax.add_patch(Patch(hole.coords,facecolor='white',edgecolor='none'))
for z in zones:
    ax.add_patch(Patch(z['polygon'],facecolor='#d4b4d1',alpha=.2,edgecolor='#9a719b',hatch='//'))
for o in objects:
    if o['kind']=='keepout':continue
    color='#555c65' if o['kind']=='pad' else ('#bf6255' if o['layers']==['F.Cu'] else '#557ba9')
    if o['net']=='GND':color='#549471'
    g=o['shape'];ax.add_patch(Patch(g.exterior.coords,facecolor=color,edgecolor='none',alpha=.8))
for a in airwires:
    p,q=a['ends'];ax.plot([p['pos']['x'],q['pos']['x']],[p['pos']['y'],q['pos']['y']],color='#b06b72',lw=.45,ls='--',alpha=.5)
for ref,(x,y,_) in refs.items():ax.text(x,y-.6,ref,fontsize=5.5,ha='center',bbox=dict(facecolor='white',alpha=.7,pad=.1,edgecolor='none'))
for name,(x0,y0,x1,y1),label in bottlenecks:
    ax.add_patch(Rectangle((x0,y0),x1-x0,y1-y0,fill=False,ec='#ad4b21',lw=1.1,ls=':'));ax.text(x1-.8,y1-.4,name,color='#ad4b21',fontsize=11)
for ident,title,members,col in groups:
    pts=[refs[r][:2] for r in members if r in refs]
    x,y=pts[0];ax.annotate(ident,(x,y),(x+1,y-2),fontsize=9,color=col,arrowprops=dict(arrowstyle='-',color=col,lw=.6),bbox=dict(facecolor='white',alpha=.8,edgecolor='none',pad=1))
ax.text(114,82,'FROZEN V4 / 61 AIRWIRES',fontsize=16,color='#294058')
ax.text(114,84,'Solid: saved copper. Dashed: connectivity only.\nA/B proposals have NOT been implemented.',fontsize=10,color='#5e6c7c')
ax.text(115,95,'NFC / screen region\nNot general-purpose placement area',fontsize=12,color='#8a668c')
ax.set(xlim=(109,194),ylim=(131,77),aspect='equal',xlabel='KiCad X / mm',ylabel='KiCad Y / mm')
ax.grid(alpha=.12);fig.savefig(OUT/'whole-board.png',dpi=180);plt.close(fig)
fig,axes=plt.subplots(1,2,figsize=(16,9),constrained_layout=True)
for ax,(key,opt) in zip(axes,options.items()):
    for pts in outline_segments:
        x,y=zip(*pts);ax.plot(x,y,color='#263746',lw=.8)
    for z in zones:
        ax.add_patch(Patch(z['polygon'],facecolor='#d4b4d1',alpha=.2,edgecolor='#9a719b',hatch='//'))
    for o in objects:
        if o['kind']!='pad':continue
        fixed=o['name'].split('.')[0] in ['U1','J1','J2','BP','BN','TP1','TP2','TP3','TP4','TP5','SW1','SW2','SW3','C23','C24']
        ax.add_patch(Patch(o['shape'].exterior.coords,facecolor='#657384' if fixed else '#dce0e6',edgecolor='none',alpha=.8 if fixed else .4))
    for label,(x0,y0,x1,y1) in opt['windows']:
        ax.add_patch(Rectangle((x0,y0),x1-x0,y1-y0,facecolor='#426cc0',alpha=.12,edgecolor='#244ea2'))
        ax.text(x0+.2,y0+.8,label,fontsize=7,color='#193d8b')
    for label,pts in opt['corridors']:
        x,y=zip(*pts);ax.plot(x,y,color='#bc3b64',lw=1.4,ls='--')
        ax.text(pts[1][0],pts[1][1]-.3,label,fontsize=7,color='#993357',bbox=dict(facecolor='white',alpha=.8,edgecolor='none',pad=.3))
    for ref in ['U1','J1','J2','BP','BN','TP1','TP5','SW1','SW2','SW3']:
        x,y,_=refs[ref];ax.text(x,y,ref,fontsize=8,color='#263746')
    ax.set(xlim=(140,194),ylim=(130,78),aspect='equal',title=opt['title']+'\nPlanning windows only / NOT PLACED OR ROUTED',xlabel='X / mm',ylabel='Y / mm');ax.grid(alpha=.12)
fig.savefig(OUT/'layout-options.png',dpi=180);plt.close(fig)
assert hashlib.sha256(board_path.read_bytes()).hexdigest()==before
print(json.dumps({'output':str(OUT),'board_unchanged':True,'counts':data['counts'],'nets':len(net_pads),'failure_plans':len(trials),'archive_bytes':archive.stat().st_size}))
