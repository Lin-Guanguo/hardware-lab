#!/usr/bin/env python3
"""Prepare a local Specctra comparison with explicit, non-relaxed dimensions."""
import argparse
import json
from pathlib import Path
from kicad_sexpr import parse, dumps, child, children, Quoted

ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('input',type=Path);ap.add_argument('output',type=Path);a=ap.parse_args()
b=parse(a.input.read_text().replace('(string_quote ")',''))
structure=child(b,'structure')
# Copper pours are refilled in KiCad, never accepted from the route solver.
structure[:]=[x for x in structure if not(isinstance(x,list) and x[0]=='plane')]
child(structure,'via')[:]=['via',Quoted('Via[0-1]_600:300_um')]
rule=child(structure,'rule');rule[:]=['rule',['width','150'],['clearance','205'],['clearance','250',['type','smd_via']],['clearance','205',['type','smd_smd']]]
networks=child(b,'network');old=child(networks,'class');nets=[x for x in old[2:] if not isinstance(x,list)];networks.remove(old)
groups={'Ground':['GND'],'Power':['USB_VBUS','SYS','BAT_PACK_TBD'],'LogicPower':['VDD_3V3'],'DisplayPower':['EPD_VDD','EPD_SW','EPD_VPH','EPD_PUMP','EPD_VGL','EPD_GDR','EPD_RESE']}
assigned={x for v in groups.values() for x in v};groups['Signal']=[x for x in nets if x not in assigned]
widths={'Ground':250,'Power':350,'LogicPower':300,'DisplayPower':200,'Signal':150}
for name,members in groups.items():networks.append(['class',name,*members,['circuit',['use_via',Quoted('Via[0-1]_600:300_um')]],['rule',['width',str(widths[name])],['clearance','205']]])
text=dumps(b).replace('(parser','(parser\n    (string_quote ")',1)
a.output.write_text(text+'\n')
print(json.dumps({'file':str(a.output),'trace_width_um':widths,'new_via_um':[600,300],'copper_clearance_um':205,'smd_to_via_copper_um':250,'note':'0.25 mm pad-to-via copper implies 0.40 mm pad-to-0.30 mm drill. Native checks remain authoritative.'}))
