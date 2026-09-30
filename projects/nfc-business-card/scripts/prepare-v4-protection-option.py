#!/usr/bin/env python3
"""Create a separate, unselected eFuse footprint and dimensioned placement option."""
import hashlib
import itertools
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Rectangle
from shapely.geometry import box
from shapely.ops import unary_union


def main():
    root = Path(__file__).resolve().parents[1]
    out = root / 'hardware/kicad/v4-protection-option'
    out.mkdir(exist_ok=True)
    library = out / 'V4_Protection.pretty'
    library.mkdir(exist_ok=True)
    shapes = {}
    for pin, x, y, h in [(1,-.9,-.7,.3),(2,-.9,-.225,.25),(3,-.9,.225,.25),(4,-.9,.7,.3),(10,.9,-.7,.3),(9,.9,-.225,.25),(8,.9,.225,.25),(7,.9,.7,.3)]:
        shape = box(x-.3,y-h/2,x+.3,y+h/2)
        if pin in (1,4,7,10):
            cx, cy = (-.725 if x<0 else .725), (-.875 if y<0 else .875)
            shape = unary_union([shape,box(cx-.125,cy-.325,cx+.125,cy+.325)])
        shapes[pin] = shape.buffer(-.05,join_style=1).buffer(.05,quad_segs=8)
    for pin,x in [(5,-.25),(6,.25)]:
        shapes[pin] = box(x-.15,-1.2,x+.15,1.2).buffer(-.05).buffer(.05,quad_segs=8)
    lines = ['(footprint "TI_RPW0010A_option" (version 20241229) (generator "hardware-lab")',
             '(layer "F.Cu") (attr smd)',
             '(descr "UNSELECTED OPTION: TI TPS25947 Rev C RPW0010A, drawing 4225183/A; verify stencil/assembly before release")',
             '(property "Reference" "U?" (at 0 -2) (layer "F.SilkS") (effects (font (size 1 1) (thickness .15))))',
             '(property "Value" "TPS259470LRPWR" (at 0 2) (layer "F.Fab") (effects (font (size 1 1) (thickness .15))))',
             '(fp_rect (start -1 -1) (end 1 1) (stroke (width .1) (type default)) (fill none) (layer "F.Fab"))',
             '(fp_rect (start -1.45 -1.45) (end 1.45 1.45) (stroke (width .05) (type default)) (fill none) (layer "F.CrtYd"))']
    for pin,g in sorted(shapes.items()):
        # The custom polygon retains the compound corner lead; no invented EP.
        anchor = g.representative_point()
        pts=' '.join(f'(xy {x-anchor.x:.6f} {y-anchor.y:.6f})' for x,y in list(g.exterior.coords)[:-1])
        lines.append(f'(pad "{pin}" smd custom (at {anchor.x:.6f} {anchor.y:.6f}) (size .05 .05) (layers "F.Cu" "F.Paste" "F.Mask") (solder_mask_margin .05) (options (clearance outline) (anchor rect)) (primitives (gr_poly (pts {pts}) (width 0) (fill yes))))')
    lines.append(')')
    fp=library/'TI_RPW0010A_option.kicad_mod'
    fp.write_text('\n'.join(lines)+'\n')
    windows={}
    for name,upper in [('OVLO',34500),('UVLO',23700)]:
        vals=[v*(1+rt/rb)+leak*rt for v,rt,rb,leak in itertools.product([1.183,1.223],[upper*.999,upper*1.001],[9990,10010],[-1e-7,1e-7])]
        windows[name]={'minimum_V':min(vals),'maximum_V':max(vals),'resistors_ohm':[upper,10000],'resistor_tolerance':.001,'pin_leakage_A':1e-7}
    parts=[('U7',178,86,2.9,2.9,'TPS259470LRPWR'),('C26',176,83.5,3.1,1.85,'1uF 50V'),('C27',179.5,83.5,2.5,1.55,'4.7uF 16V'),('R24',171,84,2.5,1.55,'23.7k 0.1%'),('R25',173.6,84,2.5,1.55,'10k 0.1%'),('R26',171,86,2.5,1.55,'34.5k 0.1%'),('R27',173.6,86,2.5,1.55,'10k 0.1%'),('R28',181.8,86,2.5,1.55,'6.65k'),('C28',184.5,86,2.5,1.55,'3.3nF')]
    fig,(a,b)=plt.subplots(1,2,figsize=(13,5),gridspec_kw={'width_ratios':[1,2.5]},constrained_layout=True)
    for pin,g in shapes.items():
        a.add_patch(Polygon(list(g.exterior.coords),facecolor='#d8ac3e',edgecolor='black',linewidth=.4))
        c=g.representative_point();a.text(c.x,c.y,str(pin),ha='center',va='center',fontsize=8)
    a.add_patch(Rectangle((-1,-1),2,2,fill=False,ls='--'))
    a.set(xlim=(-1.7,1.7),ylim=(1.7,-1.7),aspect='equal',title='TI RPW0010A / 10 pads / no EP',xlabel='mm',ylabel='mm')
    for ref,x,y,w,h,value in parts:
        b.add_patch(Rectangle((x-w/2,y-h/2),w,h,facecolor='#e7f0e9',edgecolor='#448566'))
        b.text(x,y,ref+'\n'+value,ha='center',va='center',fontsize=7)
    b.axhline(81.5,color='#888',ls='--');b.text(169.5,81.4,'Existing debug-contact row',fontsize=8)
    b.axhline(88.8,color='#888',ls='--');b.text(169.5,89.1,'Existing display power group below',fontsize=8)
    b.set(xlim=(169,186),ylim=(90,80.5),aspect='equal',xlabel='KiCad X (mm)',ylabel='KiCad Y (mm)',title='Unselected occupancy option / routing NOT proved')
    fig.suptitle('VBUS protection option — NOT PRODUCT BOM / NOT FOR FABRICATION')
    fig.savefig(out/'placement-option.png',dpi=160);plt.close(fig)
    report={'status':'Unselected geometry/threshold comparison; not a manufacturing project','source':'https://www.ti.com/lit/ds/symlink/tps25947.pdf','drawing':'4225183/A RPW0010A, 08/2019, PDF page 73','footprint_sha256':hashlib.sha256(fp.read_bytes()).hexdigest(),'pad_count':len(shapes),'minimum_interpad_gap_mm':min(g.distance(h) for p,g in shapes.items() for q,h in shapes.items() if p!=q),'static_windows':windows,'parts':[dict(zip(['ref','x_mm','y_mm','courtyard_width_mm','courtyard_height_mm','value'],p)) for p in parts],'limitations':['OVLO response has a typical value only; transient overshoot is unbounded here','Divider tolerances exclude temperature drift; choose qualified MPNs before use','Passive courtyards are conservative occupancy envelopes, not new selected footprints','Mask 0.05 and full pad paste are candidate settings; stencil DFM not validated','No routing or USB inrush compliance claim']}
    (out/'option.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'output':str(out),'thresholds':windows,'minimum_interpad_gap_mm':report['minimum_interpad_gap_mm']},indent=2))


if __name__=='__main__':main()
