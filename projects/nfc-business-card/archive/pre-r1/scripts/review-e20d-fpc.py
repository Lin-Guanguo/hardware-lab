#!/usr/bin/env python3
"""Check drawing datums against native E20D connector and window geometry."""
import hashlib
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

ROOT=Path(__file__).resolve().parents[1]
C=json.loads((ROOT/'hardware/e20d-design.json').read_text())
pins={c['ref']:c for c in json.loads((ROOT/'hardware/records/e20d-layout-pins.json').read_text())}
bounds=json.loads((ROOT/'hardware/records/e20d-body-bounds.json').read_text())
fpc=C['screen']['fpc'];sx,sy=C['screen']['xy_mm'];sw,sh,_=C['screen']['nominal_mm']
tail_y=sy+sh-fpc['edge_offset_mm']-fpc['width_mm']/2
actual_y=pins['J2']['y']*.0254
assert abs(tail_y-actual_y)<.002
# Physical top view: +Y is up. Rotating the manufacturer's front view to
# put the tail on the right puts screen pin 1 at the smaller Y coordinate.
pin_checks=[]
for n in [1,24]:
    expected=tail_y+(n-12.5)*.5
    actual=next(p for p in pins['J2']['pins'] if p['number']==str(n))['y']*.0254
    assert abs(actual-expected)<.002
    pin_checks.append({'screen_pin':n,'connector_pin':n,'expected_y_mm':expected,'actual_y_mm':actual})
active=C['screen']['active_xywh_mm'];window=C['screen']['window_xywh_mm']
margins=[active[0]-window[0],active[1]-window[1],window[0]+window[2]-active[0]-active[2],window[1]+window[3]-active[1]-active[3]]
assert all(abs(v-.4)<1e-6 for v in margins)
flat=sw+fpc['extension_mm'];insertion=fpc['insertion_depth_nominal_mm']
mouth=bounds['J2']['min_mm'][0];tail_tip=mouth+insertion
projection=tail_tip-(sx+sw);stiff_start=tail_tip-fpc['stiffener_length_mm']
report={'status':'DRAWING_AND_PHOTO_CROSSCHECK_FINAL_BEND_UNQUALIFIED',
 'drawing':{'screen_mm':[37.32,31.8,.85],'extended_tail_mm':14.3,'flat_total_mm':flat,'worst_case_arithmetic_flat_range_mm':[flat-.4,flat+.4],
 'insertion_nominal_mm':insertion,'connector_body_depth_mm':4.9,'connector_including_leads_mm':5.4,
 'assembled_flat_to_body_rear_mm':flat-insertion+4.9,'assembled_flat_to_lead_rear_mm':flat-insertion+5.4,'stiffener_mm':6},
 'user_photos':{'unplugged_total_reading_mm':51.5,'plugged_to_connector_rear_reading_mm':54.8,'measurement_precision':'Rough hand-held endpoint measurement; caliper accuracy and exact plugged endpoint are not established.'},
 'native_candidate':{'screen_xy_mm':[sx,sy],'window_xywh_mm':window,'active_xywh_mm':active,'window_margins_mm':margins,
 'j2_origin_xy_mm':[pins['J2']['x']*.0254,actual_y],'fpc_center_y_mm':tail_y,'pin_alignment':pin_checks,
 'connector_mouth_x_mm':mouth,'seated_tip_x_mm':tail_tip,'stiffener_start_x_mm':stiff_start,'nominal_flex_length_before_stiffener_mm':14.3-6,
 'projected_span_before_stiffener_mm':stiff_start-(sx+sw),'nominal_length_less_plan_projection_mm':14.3-projection,
 'rear_lead_to_screen_far_edge_mm':bounds['J2']['max_mm'][0]-sx},
 'screen_pdf_sha256':hashlib.sha256((ROOT/'downloads/gdeh0154e01.pdf').read_bytes()).hexdigest(),
 'sources':{'screen_page':'https://www.good-display.com/companyfile/2038.html','screen_pdf':'https://v4.cecdn.yun300.cn/100001_1909185148/GDEH0154E01.pdf','connector_drawing':'https://www.lcsc.com/datasheet/C2856831.pdf'},
 'limits':['Total length agreement does not verify the final bent assembly.','The 2.1 mm insertion is read from the connector section drawing, not measured on the delivered connector.','Screen exit height, connector FPC seating height, minimum bend radius and tolerance stack remain unmeasured.','Nominal 0.4 mm window margins require controlled screen registration and print verification.','A prior verbal pin-reversal warning was a mixed-coordinate-view error. No electrical pin mapping was changed.']}
(ROOT/'hardware/records/e20d-fpc-review.json').write_text(json.dumps(report,indent=2)+'\n')
fig=plt.figure(figsize=(15,9),facecolor='#f5f7fa')
fig.text(.055,.94,'E20D | screen, flex and window registration',fontsize=22,weight='bold',color='#17334d')
fig.text(.055,.9,'The screen stays fixed to the window datum. J2 moves +3.17 mm X / +0.26 mm Y; pin mapping stays unchanged.',fontsize=11,color='#526477')
ax=fig.add_axes([.055,.27,.62,.56]);ax.set_aspect('equal');ax.set_xlim(0,66);ax.set_ylim(16,53)
ax.add_patch(Rectangle((sx,sy),sw,sh,facecolor='#cad8e3',edgecolor='#557995',lw=1.2))
ax.add_patch(Rectangle(active[:2],*active[2:],facecolor='#eef3f7',edgecolor='#7898b0'))
ax.add_patch(Rectangle(window[:2],*window[2:],fill=False,edgecolor='#428d7b',ls='--',lw=2))
ax.text(active[0]+13.5,active[1]+13.5,'27 x 27 mm\nactive display\n\n27.8 x 27.8 mm\ncase aperture',ha='center',va='center',fontsize=13,color='#496b88')
ax.add_patch(Rectangle((sx+sw,tail_y-6.25),projection,12.5,facecolor='#d5ad70',edgecolor='#af844a',alpha=.8))
ax.add_patch(Rectangle((stiff_start,tail_y-6.25),6,12.5,fill=False,hatch='//',edgecolor='#8d6a3d',lw=1))
lo=bounds['J2']['min_mm'];hi=bounds['J2']['max_mm']
ax.add_patch(Rectangle(lo[:2],hi[0]-lo[0],hi[1]-lo[1],facecolor='#57778e',edgecolor='#365b73',alpha=.9))
ax.text((lo[0]+hi[0])/2,tail_y,'J2',ha='center',va='center',color='white',fontsize=12)
ax.axhline(tail_y,color='#78908c',ls=':',lw=.9)
ax.annotate('1',xy=(tail_tip,tail_y-5.75),xytext=(59,tail_y-6.7),fontsize=10,arrowprops={'arrowstyle':'-','color':'#536d80'},color='#536d80')
ax.annotate('24',xy=(tail_tip,tail_y+5.75),xytext=(59,tail_y+6),fontsize=10,arrowprops={'arrowstyle':'-','color':'#536d80'},color='#536d80')
ax.text(42.8,tail_y,'FLEX',ha='center',va='center',fontsize=9,color='#775830',rotation=90)
ax.text(48.9,tail_y,'STIFFENER',ha='center',va='center',fontsize=8,color='#775830',rotation=90)
ax.annotate('',xy=(sx,51.5),xytext=(hi[0],51.5),arrowprops={'arrowstyle':'<->','color':'#536d80'})
ax.text((sx+hi[0])/2,52,f"Current CAD to rear lead: {hi[0]-sx:.2f} mm",ha='center',fontsize=10,color='#536d80')
ax.axis('off')
x=.70
for y,title,body in [(.79,'Unplugged photo: 51.5 mm','Drawing: 37.32 + 14.3 = 51.62 mm\nDifference: -0.12 mm'),(.64,'Plugged photo: 54.8 mm','Drawing flat assembly:\n54.42 mm to body / 54.92 mm to leads'),(.46,'Fixed optical datum','Three 2.4 mm borders; FPC side 7.92 mm\n0.4 mm nominal aperture margin per edge'),(.29,'Mechanical fit still open','6 mm reinforced tail stays straight.\nActual vertical bend and print tolerances\nrequire a sample; do not pull the screen.')]:
 fig.text(x,y,title,fontsize=12,weight='bold',color='#17334d');fig.text(x,y-.038,body,fontsize=10,color='#526477',va='top',linespacing=1.6)
fig.text(.055,.14,'Top projection only; +Y up, display facing the viewer. Hatched area is the 6 mm stiffener. FPC thickness and final bend are not shown.',fontsize=10,color='#526477')
fig.text(.055,.095,'Sources: GDEH0154E01 mechanical drawing p.5; XUNPU FPC-05FB connector section drawing; two user-supplied caliper photographs.',fontsize=9.5,color='#526477')
for ext in ['png','svg']:fig.savefig(ROOT/f'enclosure/renders/e20d-screen-fpc-registration.{ext}',dpi=150)
print(json.dumps(report['native_candidate'],indent=2))
