#!/usr/bin/env python3
"""Compare R1 thickness and battery landings without editing active PCB/CAD."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import runpy

ROOT = Path(__file__).resolve().parents[1]
CAD = ROOT / 'enclosure/r1-clear-5.8/e20-clear-assembly.FCStd'
SNAPSHOT = ROOT / 'hardware/records/r1-routed-snapshot.json'
OUTPUT = ROOT / 'hardware/records/r1-packaging-study.json'
CONFIG = json.loads((ROOT / 'hardware/r1-design.json').read_text())

if os.environ.get('NFC_R1_PACKAGING_CAD') == '1':
    import FreeCAD as App
    import Part
    doc = App.openDocument(str(CAD))
    bounds = {}
    for obj in doc.Objects:
        if hasattr(obj, 'Shape') and obj.Name.startswith('Component_'):
            b = obj.Shape.BoundBox
            bounds[obj.Name[10:]] = [b.XMin, b.YMin, b.ZMin, b.XMax, b.YMax, b.ZMax]
    pcb_top = doc.getObject('PCB').Shape.BoundBox.ZMax
    trials = []
    for height, flange in [(5.8, 1.0), (5.6, .8), (5.5, .8), (5.4, .8), (5.2, .8), (5.4, 1.0)]:
        row = {'overall_mm': height, 'flange_mm': flange, 'keys': []}
        for (x, y), ref in zip(CONFIG['keys_xy_mm'], ['SW1', 'SW3', 'SW2']):
            switch = doc.getObject('Component_' + ref).Shape
            fixed = switch.cut(Part.makeCylinder(1.4, 3, App.Vector(x, y, pcb_top - .2)))
            flange_bottom = height - .8 - .05 - flange
            head = Part.makeCylinder(3.4, flange, App.Vector(x, y, flange_bottom))
            head = head.fuse(Part.makeCylinder(2, height - .03 - flange_bottom, App.Vector(x, y, flange_bottom)))
            # This retains the active cap's nominal tip datum. Travel is a clearance
            # envelope from the ALPS specification, not an imposed stop distance.
            rest_gap = 1.92 + 1.6 - switch.BoundBox.ZMax
            translation = rest_gap + .45
            head.translate(App.Vector(0, 0, -translation))
            row['keys'].append({'ref': ref, 'contact_gap_mm': rest_gap,
                'maximum_translation_mm': translation,
                'shaft_height_mm': flange_bottom - (1.92 + 1.6),
                'pressed_head_to_fixed_switch_mm': head.distToShape(fixed)[0],
                'pressed_intersection_mm3': head.common(fixed).Volume,
                'signed_vertical_clearance_mm': flange_bottom - translation - fixed.BoundBox.ZMax})
        trials.append(row)
    Path(os.environ['NFC_R1_PACKAGING_CAD_OUT']).write_text(json.dumps({'bounds_mm': bounds, 'pcb_top_mm': pcb_top, 'key_trials': trials}, indent=2) + '\n')
    App.closeDocument(doc.Name)
else:
    work = ROOT / 'artifacts/r1-packaging-study'
    work.mkdir(parents=True, exist_ok=True)
    geometry_file = work / 'cad-measurements.json'
    env = dict(os.environ, PYTHONHOME='/Applications/FreeCAD.app/Contents/Resources',
               PYTHONPATH='/Applications/FreeCAD.app/Contents/Resources/lib',
               NFC_R1_PACKAGING_CAD='1', NFC_R1_PACKAGING_CAD_OUT=str(geometry_file))
    with (work / 'freecad.log').open('w') as log:
        subprocess.run(['/Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd', str(Path(__file__).resolve())], env=env, stdout=log, stderr=log, check=True)
    cad = json.loads(geometry_file.read_text())
    from shapely.geometry import Polygon, box, LineString, Point
    from shapely.ops import unary_union
    from pour_geometry import parse_path
    pad_shape = runpy.run_path(str(Path(__file__).with_name('check-r1-copper.py')))['pad_shape']
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon as Patch, Rectangle, Circle

    snap = json.loads(SNAPSHOT.read_text())
    outline = parse_path(next(p for p in snap['polylines'] if p['layer'] == 11)['polygon']['polygon'], .0254)
    board = Polygon(outline)
    coil = unary_union([LineString([(t['x1'] * .0254, t['y1'] * .0254), (t['x2'] * .0254, t['y2'] * .0254)]).buffer(t['widthMil'] * .0254 / 2)
                        for t in snap['lines'] if t['net'] == 'NFC1_TBD'])
    options = {'A_cutout_side': [(37.9, 8.3), (37.9, 10.6)],
               'B_screen_lower_edge': [(31, 18.7), (34, 18.7)]}
    pad_options = {}
    for name, centers in options.items():
        pads = []
        for label, (x, y) in zip(['B+', 'B-'], centers):
            pad = box(x - .9, y - .75, x + .9, y + .75)
            nearby = []
            for ref, (x0, y0, z0, x1, y1, z1) in cad['bounds_mm'].items():
                distance = pad.distance(box(x0, y0, x1, y1))
                if distance < 2:
                    nearby.append({'ref': ref, 'xy_bbox_clearance_mm': distance})
            traces = []
            for t in snap['lines']:
                if t['layer'] != 1:
                    continue
                line = LineString([(t['x1'] * .0254, t['y1'] * .0254), (t['x2'] * .0254, t['y2'] * .0254)]).buffer(t['widthMil'] * .0254 / 2)
                if pad.distance(line) < .2:
                    traces.append(t['net'])
            pads.append({'label': label, 'center_mm': [x, y], 'size_mm': [1.8, 1.5],
                'inside_board': board.covers(pad), 'copper_edge_to_outline_mm': pad.distance(board.boundary),
                'projected_nfc_copper_clearance_mm': pad.distance(coil),
                'nearest_key_flange_xy_gap_mm': min(pad.distance(Point(*xy).buffer(3.4)) for xy in CONFIG['keys_xy_mm']),
                'nearby_components': nearby, 'top_trace_nets_within_0p2_mm': sorted(set(traces)),
                'existing_top_pads_within_0p2_mm': [p['id'] for p in snap['pads'] if p['layer'] in (1,12) and pad.distance(pad_shape(p)) < .2],
                'existing_vias_within_0p2_mm': [v['id'] for v in snap['vias'] if pad.distance(Point(v['x']*.0254,v['y']*.0254).buffer(v['diameterMil']*.0254/2)) < .2]})
        pad_options[name] = pads
    rows = []
    for height in [5.8, 5.6, 5.5, 5.4, 5.2]:
        lid = height - .8
        rows.append({'overall_mm': height, 'cavity_mm': height - 1.6,
            'battery_gap_mm': lid - (.8 + .1 + 3.4),
            'usb_gap_mm': lid - cad['bounds_mm']['J1'][5],
            'mcu_maximum_gap_mm': lid - (1.92 + 2.2),
            'fpc_connector_gap_mm': lid - cad['bounds_mm']['J2'][5],
            'screen_maximum_to_pcb_mm': lid - .06 - 1 - cad['pcb_top_mm'],
            'screen_to_ferrite_mm': lid - .06 - 1 - (cad['pcb_top_mm'] + .1 + .25)})
    report = {'status': 'DISCUSSION_STUDY_NOT_APPLIED_TO_ACTIVE_DESIGN',
        'source_sha256': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in [CAD, SNAPSHOT]},
        'agreed_inputs_mm': {'battery_maximum': 3.4, 'ferrite_including_adhesive_assumption': .25, 'floor': .8, 'lid': .8},
        'study_assumptions': {'support_mm': .32, 'pcb_mm': .8, 'battery_psa_mm': .1,
            'ferrite_lower_spacing_mm': .1, 'key_travel_upper_mm': .45,
            'key_travel_source': 'https://tech.alpsalpine.com/cms.media/SKQGAB_KQG_719_EN_cc4e10226e.pdf#page=3',
            'wire_and_solder_above_pcb_envelope_mm': 1.0,
            'wire_exit_reference_mm': [34, 8.5], 'wire_exit_is_unmeasured': True},
        'height_options': rows, 'key_trials': cad['key_trials'], 'pad_options': pad_options,
        'component_model_bounds_mm': cad['bounds_mm'],
        'limits': ['CAD library models are nominal, not guaranteed component maxima.',
            'Key fixed-body clearance excludes the moving actuator; 0.45 mm is the specification test travel upper bound, not a commanded operating stroke.',
            'No native routing, DRC or enclosure release is produced by this study.',
            'Pad results include outline, NFC projection and component bounds; copper pours must be rebuilt and both-layer connectivity checked after routing.',
            'The 0.25 mm ferrite assumption includes its adhesive; add any separate insulation or tape.',
            'Battery swelling allowance, resin panel deflection and accumulated assembly tolerances remain unspecified.']}
    OUTPUT.write_text(json.dumps(report, indent=2) + '\n')

    plt.rcParams.update({'font.size': 11, 'font.family': 'DejaVu Sans'})
    fig, axes = plt.subplots(1, 2, figsize=(14, 6.5))
    for ax, (name, centers), title in zip(axes, options.items(), ['A | Beside battery cutout (preferred)', 'B | Under screen lower edge']):
        ax.add_patch(Patch(outline, facecolor='#e8eff0', edgecolor='#617681', linewidth=1))
        for t in snap['lines']:
            if t['net'] != 'NFC1_TBD':
                continue
            ax.plot([t['x1']*.0254,t['x2']*.0254],[t['y1']*.0254,t['y2']*.0254],color='#b98540',lw=1)
        ax.add_patch(Rectangle((1.5,1.5),32.5,14,facecolor='#ead8a6',edgecolor='#b6a26b'))
        ax.text(17.7,8.5,'Battery envelope\n32.5 x 14 mm',ha='center',va='center',fontsize=10)
        for ref in ['SW1','SW3']:
            x0,y0,z0,x1,y1,z1=cad['bounds_mm'][ref]
            ax.add_patch(Rectangle((x0,y0),x1-x0,y1-y0,facecolor='#a4b6c6',edgecolor='#607487'))
            ax.text((x0+x1)/2,(y0+y1)/2,ref,ha='center',va='center',fontsize=8)
            ax.add_patch(Circle(((x0+x1)/2,(y0+y1)/2),3.4,fill=False,ls=':',edgecolor='#607487'))
        ax.plot([2,39.32,39.32,2,2],[18.3,18.3,50.1,50.1,18.3],color='#8097a3',ls='--',lw=1)
        for label, (x,y) in zip(['B+','B-'],centers):
            ax.add_patch(Rectangle((x-.9,y-.75),1.8,1.5,facecolor='#d86851',edgecolor='#993d2a',zorder=5))
            if name.startswith('A'):
                ax.text(x+1.25,y,label,va='center',fontsize=10,weight='bold',color='#993d2a')
            else:
                ax.text(x,y-1.15,label,ha='center',va='top',fontsize=10,weight='bold',color='#993d2a')
        for label in ['BP','BN']:
            p=next(p for p in snap['pads'] if p['number']==label)
            ax.add_patch(Circle((p['x']*.0254,p['y']*.0254),.75,facecolor='none',edgecolor='#73828b',ls='--'))
        ax.text(45.5,24.8,'Current pads',ha='center',fontsize=9,color='#73828b')
        ax.set_xlim(-1,51);ax.set_ylim(-1,29);ax.set_aspect('equal');ax.set_title(title,loc='left',weight='bold',fontsize=13)
        ax.set_xlabel('PCB X / mm');ax.set_ylabel('PCB Y / mm')
        ax.spines[['top','right']].set_visible(False)
        minimum=min(p['projected_nfc_copper_clearance_mm'] for p in pad_options[name])
        ax.text(.02,-.30,f'Pads 1.8 x 1.5 mm | NFC projection gap: {minimum:.2f} mm\n'+('Keeps the full screen copper exclusion.' if name.startswith('A') else 'Requires an explicit exception to the NFC exclusion.'),transform=ax.transAxes,fontsize=10)
    fig.suptitle('R1 battery landing options | Geometry study, not routed',x=.055,ha='left',fontsize=18,weight='bold')
    fig.text(.055,.035,'Only the relevant component bounds and NFC copper are shown. Dashed circles: current key flanges.\nPad-to-coil distances are XY measurements, not an RF pass criterion. No active PCB changes.',fontsize=10,color='#526772')
    fig.subplots_adjust(top=.88,bottom=.29,wspace=.14)
    renders=ROOT/'enclosure/renders'
    fig.savefig(renders/'r1-battery-pad-options.png',dpi=180,bbox_inches='tight');plt.close(fig)

    fig,ax=plt.subplots(figsize=(11,4.4));ax.axis('off')
    columns=['Overall / cavity','Battery gap','USB gap','MCU max gap','Screen / ferrite gap']
    values=[[f"{r['overall_mm']:.1f} / {r['cavity_mm']:.1f}",*[f"{r[k]:.2f}" for k in ['battery_gap_mm','usb_gap_mm','mcu_maximum_gap_mm','screen_to_ferrite_mm']]] for r in rows]
    table=ax.table(cellText=values,colLabels=columns,loc='center',cellLoc='center',colWidths=[.22,.17,.17,.19,.25])
    table.auto_set_font_size(False);table.set_fontsize(11);table.scale(1,2)
    for (r,c),cell in table.get_celld().items():
        cell.set_edgecolor('white');cell.set_facecolor('#284c60' if r==0 else '#e2f0ec' if r==2 else '#edf1f4')
        if r==0:cell.set_text_props(color='white',weight='bold')
    fig.suptitle('R1 thickness comparison | All dimensions in mm',x=.045,ha='left',fontsize=18,weight='bold')
    fig.text(.045,.88,'0.80 floor + cavity + 0.80 lid | battery 3.40 | ferrite + adhesive 0.25',fontsize=11)
    fig.text(.045,.075,'5.6 mm: study target with a revised key flange. 5.4 mm: tighter fitting experiment.\nNominal clearances only; printing tolerance, battery growth and panel deflection are not deducted.',fontsize=10,color='#526772')
    fig.subplots_adjust(left=.045,right=.975,top=.84,bottom=.20)
    fig.savefig(renders/'r1-thickness-options.png',dpi=180);plt.close(fig)
    print(json.dumps({'output':str(OUTPUT),'heights':rows,'pad_minimum_nfc_projection_mm':{k:min(p['projected_nfc_copper_clearance_mm'] for p in v)for k,v in pad_options.items()}},indent=2))
