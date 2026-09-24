#!/usr/bin/env python3
"""Verify the R1 USB/SWD net and BOM contract without claiming hardware operation."""
import csv
import hashlib
import json
from pathlib import Path

P = Path(__file__).resolve().parents[1]
R = P/'hardware/records'
schematic = json.loads((R/'r1-schematic.enet').read_text())
parts = {c['props']['Designator']:c for c in schematic['components'].values()}
pins = {c['ref']:{str(p['number']):p['net'] for p in c['pins']} for c in json.loads((R/'r1-pcb-pins.json').read_text())}
expected = {
    'J1': {'A6':'USB_DP_CONN','B6':'USB_DP_CONN','A7':'USB_DM_CONN','B7':'USB_DM_CONN',
           'A5':'USB_CC1','B5':'USB_CC2','A4B9':'USB_VBUS','B4A9':'USB_VBUS'},
    'R1': {'1':'USB_CC1','2':'GND'}, 'R2': {'1':'USB_CC2','2':'GND'},
    'R3': {'1':'USB_DP_CONN','2':'USB_DP_MCU'}, 'R4': {'1':'USB_DM_CONN','2':'USB_DM_MCU'},
    'U5': {'1':'USB_DP_CONN','2':'USB_DM_CONN','3':'GND'},
    'U6': {'1':'USB_CC1','2':'USB_CC2','3':'GND'},
    'U1': {'28':'VDD_3V3','30':'VDD_3V3','31':'','32':'USB_VBUS','34':'USB_DM_MCU',
           '35':'USB_DP_MCU','40':'NRESET','51':'SWDIO','53':'SWDCLK','4':'KEY_NEXT_N'},
    'U2': {'1':'SYS','2':'BAT_PACK_TBD','4':'CHG_CE_N','10':'USB_VBUS'},
    'U3': {'1':'SYS','2':'GND','3':'SYS','5':'VDD_3V3'},
    'C1': {'1':'USB_VBUS','2':'GND'}, 'C8': {'1':'USB_VBUS','2':'GND'},
    'R7': {'1':'VDD_3V3','2':'CHG_CE_N'},
    'SW2': {'1':'KEY_NEXT_N','2':'KEY_NEXT_N','3':'GND','4':'GND'},
}
for ref, mapping in expected.items():
    for number, net in mapping.items():
        assert parts[ref]['pinInfoMap'][number]['net']==pins[ref][number]==net,(ref,number,net)
for ref in ('R1','R2'): assert parts[ref]['props']['Supplier Part']=='C23186', ref
for ref in ('R3','R4'):
    p = parts[ref]['props']
    assert p['Value']=='0Ω' and p['Supplier Part']=='C21189' and p['Manufacturer Part']=='0603WAF0000T5E',ref
bom=list(csv.DictReader((P/'hardware/production/r1/NFC-Card-R1-bom.csv').open(encoding='utf-8-sig')))
for ref in ('R3','R4'):
    row=next(r for r in bom if ref in r['Designator'].split(','))
    assert row['Value']=='0Ω' and row['Supplier Part']=='C21189',ref
s=json.loads((R/'r1-routed-snapshot.json').read_text())
pads=[]
for ref,net in zip(['TP1','TP2','TP3','TP4','TP5'],['GND','VDD_3V3','SWDCLK','SWDIO','NRESET']):
    pad=next(p for p in s['pads'] if p['number']==ref)
    assert pad['net']==net and pad['layer']==2
    assert pad['pad'][0]==('RECT' if ref=='TP1' else 'ELLIPSE')
    pads.append({'land':ref,'net':net,'x_mm':round(pad['x']*.0254,5),'y_mm':round(pad['y']*.0254,5),'diameter_mm':round(pad['pad'][1]*.0254,5)})
assert all(abs(b['x_mm']-a['x_mm']-2.54)<.001 for a,b in zip(pads,pads[1:]))
assert all(abs(p['y_mm']-48.49876)<.001 for p in pads)
report={'status':'HARDWARE_NET_AND_BOM_CHECK_PASS','snapshot_sha256':hashlib.sha256((R/'r1-routed-snapshot.json').read_bytes()).hexdigest(),
        'verified_pin_assignments':sum(len(v) for v in expected.values()),'usb_series_resistors':'R3/R4 = 0 ohm / C21189',
        'physical_swd_pads_front_coordinate_system':pads,'current_swd_pitch_mm':round(pads[1]['x_mm']-pads[0]['x_mm'],5),
        'swd_clip_compatibility':'2.54 mm implemented for user-selected generic Lushen 1x5 clip; physical fit untested',
        'pin1_identification':'TP1 GND is square; TP2-TP5 are circular; all five rear signal labels follow the lands',
        'hidden_reset':'Not selected for R1; user accepts SWD programmer recovery','factory_programming':False,
        'usb_updates_logs_hardware_tested':False,'swd_breakpoint_debug_hardware_tested':False,
        'remaining':['Final framework and bootloader port','VBUS transients/current/backfeed/suspend tests','Physical clip contact and cover trial fit','SWD/NRESET recovery with an invalid application and battery connected'],
        'scope':'Pin assignments and 0-ohm procurement consistency; no electrical waveform, USB compliance or fixture validation.'}
(R/'r1-usb-swd-check.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
