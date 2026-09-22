"""Generate a conservative E14 PCBA spatial study from the new battery layout."""
from pathlib import Path
import json
import FreeCAD as App
import Part

OUT = Path(__file__).resolve().parent
MODEL = OUT / 'pcba-e14-battery-layout.FCStd'
if MODEL.exists():
    raise SystemExit(f'Existing model refused: {MODEL}')

W, H, PCB_T = 84.0, 52.0, 0.8
BAT = (30.0, 12.0, 3.0)
doc = App.newDocument('NfcCardE14BatteryLayout')
doc.Label = 'NFC 名片 · E14 新电池尺寸空间布局'
doc.Comment = 'E14 块级空间验证；不是生产 PCB、外壳或打印稿。'
params = doc.addObject('App::FeaturePython', 'StudyParameters')
params.Label = 'E14 设计参数'
for name, value in [('CardWidth', W), ('CardHeight', H), ('CardThickness', 5.0), ('BackWall', 0.8), ('FrontWall', 0.8)]:
    params.addProperty('App::PropertyLength', name, 'Envelope')
    setattr(params, name, value)
for name, value in [('BoardWidth', W), ('BoardHeight', H), ('BoardThickness', PCB_T),
                    ('BatteryLength', BAT[0]), ('BatteryWidth', BAT[1]), ('BatteryThickness', BAT[2]),
                    ('NominalStackTarget', 5.0)]:
    params.addProperty('App::PropertyLength', name, 'Envelope')
    setattr(params, name, value)
params.addProperty('App::PropertyString', 'Status', 'Evidence')
params.Status = 'E14 空间验证候选；电池包体、板框、FPC、RF 和外壳仍待验证'

rows=[]
objects={}
def box(name, label, size, pos, role, color, evidence):
    obj=doc.addObject('Part::Box', name)
    obj.Label=label
    obj.Length,obj.Width,obj.Height=size
    obj.Placement.Base=App.Vector(*pos)
    obj.addProperty('App::PropertyString','Role','Evidence'); obj.Role=role
    obj.addProperty('App::PropertyString','SourceAndLimits','Evidence'); obj.SourceAndLimits=evidence
    obj.addProperty('App::PropertyColor','StudyColor','Appearance')
    obj.StudyColor=tuple(int(color[i:i+2],16)/255 for i in (1,3,5))
    if App.GuiUp:
        obj.ViewObject.ShapeColor=obj.StudyColor
        if role=='reserve': obj.ViewObject.Transparency=65
    objects[name]=obj
    rows.append({'name':name,'label':label,'size_mm':list(size),'position_mm':list(pos),'role':role,'color':color,'evidence':evidence})
    return obj

pcb=doc.addObject('Part::Feature','BoardEnvelope')
pcb.Label='PCB · 84 × 52 × 0.8 mm'
pcb.Shape=Part.makeBox(W-3.0,H-3.0,PCB_T,App.Vector(1.5,1.5,0.9)).cut(Part.makeBox(BAT[0],BAT[1],PCB_T+0.2,App.Vector(3.0,38.0,0.8)))
pcb.addProperty('App::PropertyString','Role','Evidence'); pcb.Role='reference'
pcb.addProperty('App::PropertyString','SourceAndLimits','Evidence'); pcb.SourceAndLimits='板框和 USB 槽仍需依据 E14 PCB 真实板框重新定义。'
pcb.addProperty('App::PropertyColor','StudyColor','Appearance'); pcb.StudyColor=(0.72,0.84,0.79)
objects['BoardEnvelope']=pcb
rows.append({'name':'BoardEnvelope','label':pcb.Label,'size_mm':[W-3.0,H-3.0,PCB_T],'position_mm':[1.5,1.5,0.9],'role':'reference','color':'#B8D7C9','evidence':pcb.SourceAndLimits})
screen=box('ScreenEnvelope','屏幕 · GDEH0154E01 包络',(37.4,32.0,1.1),(3.0,2.0,1.8),'component','#D9E3EE','屏幕名义包络；FPC、玻璃保护和支撑未建模。')
battery=box('BatteryEnvelope','电池 · 301230 标称 30 × 12 × 3 mm',BAT,(3.0,38.0,1.0),'component','#F0C886','301230 仅作为布局尺寸目标；完整包体、保护板、引线和鼓胀余量未确认。')
nfc=box('NfcReserve','NFC 右上净空',(24.0,25.0,0.2),(57.0,2.0,1.7),'reserve','#B8E0D7','空间净空示意；线圈铜、匹配网络、金属距离和实测读距未设计。')
usb=box('UsbBody','USB-C · J1 主体',(8.0,8.94,3.2),(76.0,27.5,1.8),'component','#C7D0DB','右边板框开口、锚脚和插拔受力需在 PCB/CAD 联动后重定义。')
fpc=box('FpcEnvelope','J2 · FPC 座目标',(16.5,6.8,2.2),(42.0,31.0,1.8),'component','#B8D4C0','16.5 × 6.8 × 2.2 mm 目标包络，实际座型、接触方向和折弯待确认。')
power=box('PowerEnvelope','USB/充电/稳压区',(19.0,11.0,1.8),(45.0,19.0,1.8),'reserve','#E6C9CE','U2/U3/U5/CC 与外围的块级空间，尚未完成焊盘和走线。')
mcu=box('McuEnvelope','U1 · MDBT50Q 主控',(8.5,6.5,2.2),(74.0,37.0,1.8),'component','#B7CFE7','右下主控方向候选；模块天线净空和完整铜布局尚未核对。')
for i,x in enumerate((38.0,45.0,52.0),1):
    box(f'Button{i}',f'SW{i} · 按键包络',(5.2,5.2,1.6),(x,38.0,1.8),'component','#ECC2A7','按键主体包络；键帽、孔位、行程和限位未建模。')

# Mark the intended front-panel reserve without claiming a shell.
front=box('FrontPlane','前盖窗口/按键/USB 待设计区',(W-1.6,H-1.6,0.2),(0.8,0.8,4.5),'reserve','#CBD5E1','仅作为 5 mm 厚度预算参考；没有窗口、卡扣、螺柱或打印公差。')
outer=box('OuterEnvelope','84 × 52 × 5 mm 目标包络',(W,H,5.0),(0,0,0),'reference','#64748B','外壳体积目标；未建窗口、卡扣、圆角、壁厚或打印公差。')

physical=[pcb,screen,battery,usb,fpc,mcu]+[objects[f'Button{i}'] for i in range(1,4)]
collisions=[]
for i,a in enumerate(physical):
    if not a.Shape.isValid():
        collisions.append({'object':a.Name,'reason':'invalid_shape'})
    for b in physical[i+1:]:
        v=a.Shape.common(b.Shape).Volume
        if v>1e-6: collisions.append({'objects':[a.Name,b.Name],'volume_mm3':round(v,6)})
report={'status':'E14_CAD_SPATIAL_STUDY_NOT_PRINTABLE_SHELL','board_mm':[W,H,PCB_T],
        'battery_nominal_mm':list(BAT),'components':rows,'collisions':collisions,
        'nfc_keepout_mm':[24.0,25.0],'mechanical_checks':{'board_connected':len(pcb.Shape.Solids)==1,'component_collisions':len(collisions)},
        'limitations':['This is a block-level spatial study, not a manufacturing shell.','PCB outline and USB edge cutout must be synchronized with E14 after routing.','Battery supplier maximum envelope, leads, protection board and swelling allowance are unknown.','FPC insertion, screen support, button travel, wall thickness and assembly tolerances are not verified.','No vendor Gerber, Excellon, BOM, CPL, printable STEP or STL is generated from this study.']}
assert not collisions, collisions
doc.recompute()
doc.saveAs(str(MODEL))
# Export only the PCBA spatial envelope as a review STEP.
step=OUT/'pcba-e14-layout-envelope.step'
Part.export([pcb,screen,battery,usb,fpc,power,mcu,nfc]+[objects[f'Button{i}'] for i in range(1,4)],str(step))
(OUT/'pcba-e14-battery-layout-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
# Minimal top-view SVG generated from the same coordinates.
scale=10; ox=40; oy=40
colors={'screen':'#D9E3EE','battery':'#F0C886','nfc':'#B8E0D7','usb':'#C7D0DB','fpc':'#B8D4C0','power':'#E6C9CE','mcu':'#B7CFE7'}
rects=[('screen','屏幕',3,2,37.4,32),('battery','301230 电池目标',3,38,30,12),('nfc','NFC 右上净空',57,2,24,25),('usb','USB-C',76,27.5,8,8.94),('fpc','FPC 座',42,31,16.5,6.8),('power','USB/充电/稳压',45,19,19,11),('mcu','U1 主控',74,37,8.5,6.5)]
svg=[f'<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="760" viewBox="0 0 1100 760">','<rect width="1100" height="760" fill="#F7F9FC"/>','<style>text{font-family:Arial,"PingFang SC",sans-serif;fill:#172B41}.small{font-size:14px}.muted{fill:#52657B}</style>','<text x="40" y="32" font-size="25" font-weight="bold">E14 新电池尺寸 · PCB/CAD 空间布局</text>','<text x="40" y="58" class="muted">84 × 52 mm · 屏幕左上 / 301230 左下 / NFC 右上 / USB 与主控右下 · 空间验证候选</text>',f'<rect x="{ox}" y="{oy}" width="{W*scale}" height="{H*scale}" rx="12" fill="#E5EAF0" stroke="#64748B" stroke-width="2"/>']
for key,label,x,y,w,h in rects:
    fill=colors[key]; dash=' stroke-dasharray="6 4" fill-opacity="0.34"' if key in ('nfc','power') else ''
    px=ox+x*scale; py=oy+y*scale
    svg.append(f'<rect x="{px:.1f}" y="{py:.1f}" width="{w*scale:.1f}" height="{h*scale:.1f}" rx="4" fill="{fill}" stroke="#61738A"{dash}/>')
    svg.append(f'<text x="{px+w*scale/2:.1f}" y="{py+h*scale/2:.1f}" text-anchor="middle" font-size="13">{label}</text>')
for i,x in enumerate((38,45,52),1):
    px=ox+x*scale; py=oy+38*scale; svg.append(f'<rect x="{px}" y="{py}" width="52" height="52" rx="4" fill="#ECC2A7" stroke="#61738A"/>'); svg.append(f'<text x="{px+26}" y="{py+31}" text-anchor="middle" font-size="13">SW{i}</text>')
svg += ['<text x="730" y="110" font-size="18" font-weight="bold">机械待验证</text>','<text x="730" y="145" class="small">PCB 板框 / USB 槽 / 工艺边</text>','<text x="730" y="172" class="small">电池完整包体 / 引线 / 鼓胀</text>','<text x="730" y="199" class="small">FPC 插合、屏幕支撑、按键孔</text>','<text x="730" y="226" class="small">NFC 铜线、匹配与实测读距</text>','<text x="40" y="630" class="muted">本图和 STEP 只用于空间评审；不包含可打印上下壳、孔位、卡扣或供应商制造层。</text>','</svg>']
(OUT/'pcba-e14-battery-layout.svg').write_text('\n'.join(svg)+'\n')
print(json.dumps({'model':str(MODEL),'step':str(step),'report':str(OUT/'pcba-e14-battery-layout-report.json'),'svg':str(OUT/'pcba-e14-battery-layout.svg'),'collisions':collisions},ensure_ascii=False))
