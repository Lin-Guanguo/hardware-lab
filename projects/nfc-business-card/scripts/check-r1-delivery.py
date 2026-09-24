#!/usr/bin/env python3
"""Cross-check the frozen R1 export package against native PCB evidence."""
import csv
import hashlib
import io
import json
import math
import re
import runpy
import sqlite3
import zipfile
from pathlib import Path

from pour_geometry import sample_arc, load_pours, calibrate
import pour_geometry

ROOT = Path(__file__).resolve().parents[1]
RECORDS = ROOT/'hardware/records'
DELIVERY = ROOT/'hardware/production/r1'

def read(name):
    return json.loads((RECORDS/name).read_text())

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

s = read('r1-routed-snapshot.json')
old = json.loads((ROOT/'archive/pre-r1/hardware/records/e20d-placement-snapshot.json').read_text())
fields = ('ref','x','y','rotation','footprint')
placement = lambda data: sorted(tuple(c[k] for k in fields) for c in data['components'])
assert placement(s)==placement(old), 'Component placement changed from approved E20D'
outline = lambda data: [p['polygon'] for p in data['polylines'] if p['layer']==11]
assert outline(s)==outline(old), 'Board outline changed from approved E20D'
refs = {c['ref']:c for c in s['components']}

# Preserve the native UTF-16 tab-delimited originals, then expose real UTF-8 CSV.
rows = {}
for kind in ('bom','cpl'):
    path = DELIVERY/f'NFC-Card-R1-{kind}.csv'
    raw = path.read_bytes()
    if raw.startswith((b'\xff\xfe', b'\xfe\xff')):
        (ROOT/f'artifacts/r1-routing/native-{kind}.tsv').write_bytes(raw)
        reader = csv.DictReader(io.StringIO(raw.decode('utf-16')), delimiter='\t')
        rows[kind] = list(reader)
        with path.open('w', encoding='utf-8-sig', newline='') as f:
            writer=csv.DictWriter(f,fieldnames=reader.fieldnames)
            writer.writeheader();writer.writerows(rows[kind])
    else:
        rows[kind] = list(csv.DictReader(io.StringIO(raw.decode('utf-8-sig'))))
bomrefs=[]
for row in rows['bom']:
    rr=[x.strip() for x in row['Designator'].split(',')]
    assert len(rr)==int(row['Quantity'])
    bomrefs.extend(rr)
assert len(bomrefs)==len(set(bomrefs))==58 and set(bomrefs)==set(refs)
assert len(rows['cpl'])==58 and {r['Designator'] for r in rows['cpl']}==set(refs)
max_position_error=0
midpoint_offsets={}
for row in rows['cpl']:
    c=refs[row['Designator']]
    error=math.dist([float(row[k].removesuffix('mm')) for k in ('Ref X','Ref Y')],[c['x']*.0254,c['y']*.0254])
    max_position_error=max(max_position_error,error)
    assert error<.015 and row['Layer']=='T'
    assert abs((float(row['Rotation'])-c['rotation']+180)%360-180)<.01
    offset=[float(row[m].removesuffix('mm'))-float(row[r].removesuffix('mm')) for m,r in [('Mid X','Ref X'),('Mid Y','Ref Y')]]
    if math.hypot(*offset)>.002:
        # The custom J1 signal lands shift the automatic pad-bounds midpoint.
        assert row['Designator']=='J1' and abs(offset[0]+.15)<.002 and abs(offset[1])<.002
        midpoint_offsets[row['Designator']]=offset

with zipfile.ZipFile(DELIVERY/'NFC-Card-R1-gerber.zip') as z:
    names=z.namelist()
    assert len([n for n in names if n.endswith('.GKO')])==1
    assert {n.rsplit('.',1)[-1] for n in names if n.startswith('Gerber_')}=={'GTL','GBL','GTO','GBO','GTS','GBS','GTP','GBP','GKO'}
    def drill(name):
        text=z.read(name).decode();tools={};active=None;hits=[];slots=[]
        for line in text.splitlines():
            m=re.fullmatch(r'(T\d+)C([\d.]+)',line)
            if m:tools[m[1]]=float(m[2])
            if re.fullmatch(r'T\d+',line):active=line
            m=re.fullmatch(r'X([\d.]+)Y([\d.]+)',line)
            if m:hits.append((float(m[1]),float(m[2]),tools[active]))
            if 'G85' in line:slots.append(line)
        return hits,slots
    allhits,slots=drill('Drill_PTH_Through.DRL')
    viahits,viaslots=drill('Drill_PTH_Through_Via.DRL')
    assert len(allhits)==len(viahits)==len(s['vias']) and len(slots)==4 and not viaslots
    expected=[(v['x']*.0254,v['y']*.0254,v['holeMil']*.0254) for v in s['vias']]
    for hits in (allhits,viahits):
        remaining=list(hits)
        for via in expected:
            match=[i for i,h in enumerate(remaining) if math.dist(via[:2],h[:2])<.003 and abs(via[2]-h[2])<.003]
            assert len(match)==1, ('Missing/duplicate drill',via)
            remaining.pop(match[0])
        assert not remaining

with zipfile.ZipFile(DELIVERY/'NFC-Card-R1-project.epro2') as z:
    layers=[];pcb_documents=[];active=False
    for line in z.read('NFC-Card-R1.epru').decode().splitlines():
        try:
            h,d=line.rstrip('|').split('||',1);h=json.loads(h);d=json.loads(d)
        except ValueError:continue
        if h['type']=='DOCHEAD':
            active=d.get('docType')=='PCB'
            if active:pcb_documents.append(d['uuid'])
        if active and h['type']=='LAYER_PHYS':
            layers.append({'id':json.loads(h['id'])[1],**d})
    assert pcb_documents==['8033127c48771f3b']
    thickness=sum(l['thickness'] for l in layers)*.0254
    assert abs(thickness-.8)<.002
    assert len([l for l in layers if l['id'] in (1,2)])==2
with sqlite3.connect(f"file:{ROOT.parents[1]/'eda/NFC-Card-R1.eprj2'}?mode=ro",uri=True) as c:
    assert c.execute('pragma quick_check').fetchone()[0]=='ok'

source=ROOT.parents[1]/'eda/archive/nfc-business-card/NFC-Business-Card-84x52-E14-Battery-Layout.eprj2'
assert sha(source)==read('r1-validation.json')['old_project_unchanged_sha256']
pins=runpy.run_path(str(ROOT/'scripts/check-netlist-consistency.py'))
sch=pins['schematic_map'](RECORDS/'r1-schematic.enet');pcb=pins['pcb_map'](RECORDS/'r1-pcb-pins.json')
assert sch==pcb and len(sch)==238

def leaf_errors(value):
    if isinstance(value,list):return sum(leaf_errors(v) for v in value)
    if isinstance(value,dict):return 1 if 'errorType' in value else leaf_errors(value.get('list',[]))
    return 0
assert leaf_errors(read('r1-native-drc.json'))==0
assert read('r1-copper-check.json')['ok'] and read('r1-nfc-check.json')['ok']
assert read('r1-profile-check.json')['gerber_sha256']==sha(DELIVERY/'NFC-Card-R1-gerber.zip')
mechanical=read('r1-mechanical-check.json')
assert mechanical['status']=='NOMINAL_CAD_AND_PRINT_MESH_PASS'
assert len(mechanical['debug_access'])==5
for access in mechanical['debug_access']:
    pad=next(p for p in s['pads'] if p['number']==access['pad'])
    assert math.dist(access['center_mm'],[pad['x']*.0254,pad['y']*.0254])<.002, 'Stale CAD debug holes'
for kind, evidence in mechanical['meshes'].items():
    assert evidence['sha256']==sha(ROOT/f'enclosure/r1-clear-5.8/e20-clear-{kind}.stl'), 'Stale CAD mesh evidence'

arcs=[]
for sweep in (90,-90,135,-135):
    error=math.dist(sample_arc((1.2,-2.3),(5.7,3.1),sweep)[-1],(5.7,3.1))
    assert error<1e-10
    arcs.append({'sweep_degrees':sweep,'endpoint_error_mm':error})
assert calibrate(load_pours(s))[0]
unit=pour_geometry.FILL_UNIT
pour_geometry.FILL_UNIT=unit/10
try:assert not calibrate(load_pours(s))[0]
finally:pour_geometry.FILL_UNIT=unit
calibration={'ok':True,'asymmetric_arc_cases':arcs,'tenfold_wrong_fill_scale_rejected':True}
(RECORDS/'r1-geometry-calibration.json').write_text(json.dumps(calibration,indent=2)+'\n')
report={'status':'REVIEW_REQUIRED_BEFORE_ORDER','native_drc_errors':0,'schematic_pcb_pin_count':len(sch),'pin_mismatches':0,
        'counts':{k:len(s[k]) for k in ('components','pads','lines','vias','pours')},
        'native_project_sqlite_quick_check':'ok','portable_pcb_count':1,'stackup_total_mm':thickness,
        'bom_component_count':len(bomrefs),'cpl_component_count':len(rows['cpl']),'max_cpl_reference_error_mm':max_position_error,
        'native_cpl_midpoint_minus_reference_mm':midpoint_offsets,
        'drill_vias':len(viahits),'usb_mounting_slots':len(slots),'outline_and_components_identical_to_e20d':True,
        'old_project_unchanged_sha256':sha(source),
        'screen_projection_no_foreign_copper':not read('r1-copper-check.json')['screen_foreign_copper_mm2'],
        'screen_projection_no_unexpected_copper':not read('r1-copper-check.json')['screen_unexpected_copper_mm2'],
        'screen_projection_no_poured_copper':not read('r1-copper-check.json')['screen_poured_copper_mm2'],
        'nfc_no_bypass_proved':True,
        'mechanical_status':mechanical['status'],
        'mechanical_scope':'Existing 5.8 mm shell and unchanged component geometry. New B-pad wire/ferrite service bodies are pending mechanical revision.',
        'single_layer_or_isolated_via_count':len(read('r1-copper-check.json')['single_layer_or_isolated_vias']),
        'snapshot_sha256':sha(RECORDS/'r1-routed-snapshot.json'),
        'open_review':[item['item'] for item in read('r1-review.json')['discussion_items']] + [
            'Trial-fit the user-selected 2.54 mm five-pin clip on the bare board and through the revised cover.',
            'Validate SWD/NRESET programmer recovery on the prototype; the user declined a hidden RESET switch for R1.',
            'Implement and test the board-specific bootloader and USB CDC firmware; hardware net checks do not prove operation.'],
        'limits':['RF resonance/read range with screen and case not measured.','Battery complete envelope and physical assembly not verified.','No order placed; not production-qualified.']}
(RECORDS/'r1-validation.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
