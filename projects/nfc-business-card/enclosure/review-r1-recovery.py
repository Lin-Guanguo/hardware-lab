"""Evaluate recovery-interface envelopes without modifying the source CAD or PCB."""
import hashlib
import json
import os
from pathlib import Path

import FreeCAD as App
import Part

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / 'r1-rounded-rear-soft/rear-cover-study.FCStd'
OUT = Path(os.environ['NFC_RECOVERY_REVIEW_OUT']).resolve()
if OUT.exists():
    raise RuntimeError('Output directory must be new.')
OUT.mkdir(parents=True)
source_hash = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
doc = App.openDocument(str(SOURCE))
V = App.Vector
upper = doc.getObject('RoundedUpperShell').Shape
rear = doc.getObject('InsetRearCover').Shape
pcb = doc.getObject('PCB').Shape
z = pcb.BoundBox.ZMax

# Validate boolean volume and direction with asymmetric known solids.
assert abs(Part.makeBox(2, 3, 4).common(Part.makeBox(2, 3, 4, V(1, 0, 0))).Volume - 12) < 1e-8

# The catalogue's plan datum is 2.1 mm behind the actuator face.
datum_x, center_y, actuator_x = 80.3, 8.6, 82.4
axis_z = z + .7
# Include catalogue dimensional tolerances plus an assumed 0.10 mm mounting allowance.
envelope = Part.makeBox(3.85, 5.05, 1.5, V(78.7, 6.075, z))
bosses = [Part.makeCylinder(.35, .6, V(x, center_y, z-.6))
          for x in (datum_x-.9, datum_x+.9)]
body_sweep = Part.makeBox(3.85, 5.05, z+1.5+10, V(78.7, 6.075, -10))
tool_hole = Part.makeCylinder(1, 2, V(83.2, center_y, axis_z), V(1, 0, 0))
opened_upper = upper.cut(tool_hole)
# Proposed 0.6 mm tool travels inward 0.2 mm after initial actuator contact.
tool_path = Part.makeCylinder(.3, 3, V(actuator_x-.2, center_y, axis_z), V(1, 0, 0))
objects = [o for o in doc.Objects if hasattr(o, 'Shape') and not o.Shape.isNull()
           and o.Name not in ('RoundedUpperShell', 'InsetRearCover', 'PCB')]
collisions = {o.Name: envelope.common(o.Shape).Volume for o in objects}
tool_collisions = {o.Name: tool_path.common(o.Shape).Volume for o in objects}
land_support = Part.makeBox(3.85, 5.05, .01, V(78.7, 6.075, z-.01))
report = {
    'status': 'CONDITIONAL_MECHANICAL_CANDIDATE_NOT_RELEASED',
    'source_sha256': source_hash,
    'reset': {
        'part': 'SKSCLBE010',
        'drawing': 'https://tech.alpsalpine.com/cms.media/product_detail_fig_sksc_d_31_en_b3efc7326a.gif',
        'datum_xy_mm': [datum_x, center_y],
        'actuator_face_xy_mm': [actuator_x, center_y],
        'push_direction': '-X; actuator faces +X',
        'pcb_top_z_mm': z,
        'push_axis_z_mm': axis_z,
        'nominal_top_z_mm': z+1.25,
        'evaluated_top_z_mm': z+1.5,
        'boss_candidate_centers_xy_mm': [[datum_x-.9, center_y], [datum_x+.9, center_y]],
        'boss_max_projection_mm': .6,
        'boss_min_z_mm': z-.6,
        'boss_to_pcb_bottom_margin_mm': z-.6-pcb.BoundBox.ZMin,
        'boss_inside_pcb': [abs(b.common(pcb).Volume-b.Volume)<1e-8 for b in bosses],
        'footprint_projection_supported': abs(land_support.common(pcb).Volume-land_support.Volume)<1e-8,
        'envelope_to_upper_mm': envelope.distToShape(upper)[0],
        'envelope_to_rear_mm': envelope.distToShape(rear)[0],
        'envelope_collisions_mm3': {k:v for k,v in collisions.items() if v>1e-8},
        'insertion_upper_overlap_mm3': body_sweep.common(upper).Volume,
        'tool_hole_diameter_mm': 2,
        'tool_diameter_mm': .6,
        'tool_contact_depth_from_outer_wall_mm': 84.6-actuator_x,
        'tool_pressed_depth_from_outer_wall_mm': 84.6-actuator_x+.2,
        'tool_existing_component_collisions_mm3': {k:v for k,v in tool_collisions.items() if v>1e-8},
        'tool_pcb_overlap_mm3': tool_path.common(pcb).Volume,
        'tool_opened_upper_overlap_mm3': tool_path.common(opened_upper).Volume,
        'opened_upper_valid': opened_upper.isValid(),
        'opened_upper_solids': len(opened_upper.Solids),
    },
    'swd': {
        'proposed_pitch_mm': 2.54,
        'proposed_x_mm': [65.9206, 68.4606, 71.0006, 73.5406, 76.0806],
        'proposed_y_mm': 48.4988,
        'pad_depth_from_rear_exterior_mm': pcb.BoundBox.ZMin,
        'axis_distance_from_case_y_edge_mm': 52.6-48.4988,
        'axis_distance_from_pcb_y_edge_mm': pcb.BoundBox.YMax-48.4988,
        'hole_comparisons': [{'diameter_mm': d, 'straight_web_mm': 2.54-d,
                              'mouth_web_with_existing_r008_mm': 2.54-d-.16}
                             for d in (2.0, 1.8, 1.6)],
        'nominal_d06_tip_center_error_limit_on_d12_pad_mm': (1.2-.6)/2,
    },
    'limits': ['Conservative switch envelope, not an official STEP model or final footprint.',
               'Mounting allowance and 0.6 mm tool are study assumptions.',
               'No routing, PCB drilling, force, solder-joint strength, fixture or print qualification.',
               'SWD clip dimensions remain unavailable; candidate coordinates are not approved.',
               'Frozen physical bodies do not include updated battery wiring or actual flex.'],
}
study = App.newDocument('RecoveryMechanicalCandidate')
for name, shape in [('UpperWithCandidateToolHole', opened_upper), ('PCBReference', pcb),
                    ('ResetEnvelopeOnly', envelope), ('ResetToolSweep', tool_path)]:
    obj = study.addObject('PartDesign::Feature', name)
    obj.Shape = shape
study.recompute()
study.saveAs(str(OUT/'recovery-candidate.FCStd'))
App.closeDocument(study.Name)
App.closeDocument(doc.Name)
report['source_unchanged'] = hashlib.sha256(SOURCE.read_bytes()).hexdigest() == source_hash
assert report['source_unchanged']
assert not report['reset']['envelope_collisions_mm3']
assert not report['reset']['tool_existing_component_collisions_mm3']
assert report['reset']['insertion_upper_overlap_mm3'] < 1e-8
assert report['reset']['tool_pcb_overlap_mm3'] < 1e-8
assert report['reset']['tool_opened_upper_overlap_mm3'] < 1e-8
assert report['reset']['opened_upper_valid'] and report['reset']['opened_upper_solids'] == 1
(OUT/'report.json').write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps({'status':report['status'], 'report':str(OUT/'report.json')}))
