#!/usr/bin/env python3
"""Move component annotations to assembly layers in a closed phase3 candidate."""
import copy
import hashlib
import json
import uuid
from pathlib import Path

from kicad_sexpr import child, children, prop, read, write, Quoted, dumps, set_child


def protected(board):
    geometry=[]
    for fp in children(board,'footprint'):
        geometry.append([prop(fp,'Reference')[2],child(fp,'at'),*children(fp,'pad'),
            *[n for n in fp if isinstance(n,list) and n[0].startswith('fp_') and child(n,'layer') and child(n,'layer')[1] not in ('F.SilkS','B.SilkS','F.Fab','B.Fab')]])
    geometry.extend(n for n in board if isinstance(n,list) and n[0] in ('segment','via','zone','general','setup'))
    geometry.extend(n for n in board if isinstance(n,list) and child(n,'layer') and child(n,'layer')[1] in ('Edge.Cuts','F.Paste','B.Paste'))
    return hashlib.sha256(dumps(geometry).encode()).hexdigest()


def move_annotations(fp, diode):
    counts={'reference_fields':0,'graphics':0,'retained_polarity_bars':0}
    for ref in children(fp,'property'):
        layer=child(ref,'layer')
        if layer and layer[1] in ('F.SilkS','B.SilkS'):
            layer[1]=Quoted('F.Fab' if layer[1]=='F.SilkS' else 'B.Fab')
            counts['reference_fields']+=1
    for item in fp:
        if not isinstance(item,list) or not item[0].startswith('fp_'):continue
        layer=child(item,'layer')
        if not layer or layer[1] not in ('F.SilkS','B.SilkS'):continue
        start,end=child(item,'start'),child(item,'end')
        if diode and item[0]=='fp_line' and start and end and abs(float(start[1])+2.667)<.002 and abs(float(end[1])+2.667)<.002:
            counts['retained_polarity_bars']+=1
            continue
        layer[1]=Quoted('F.Fab' if layer[1]=='F.SilkS' else 'B.Fab')
        counts['graphics']+=1
    return counts


def main():
    project=Path(__file__).resolve().parents[1]
    target=project/'hardware/kicad/v4-phase3'
    assert not list(target.glob('~*.kicad_pcb.lck')), 'Close phase3 PCB Editor first'
    file=target/'NFC-Card-V4.kicad_pcb';board=read(file);before=protected(board)
    record={}
    for fp in children(board,'footprint'):
        ref=prop(fp,'Reference')[2]
        record[ref]=move_annotations(fp,ref in ('D1','D2','D3'))
        library=target/'NFC_V4.pretty'/(fp[1].split(':',1)[1]+'.kicad_mod')
        lib=read(library);move_annotations(lib,ref in ('D1','D2','D3'));write(library,lib)
    for text in children(board,'gr_text'):
        layer=child(text,'layer')[1]
        if layer in ('F.SilkS','B.SilkS'):
            font=child(child(text,'effects'),'font')
            set_child(font,'size','0.8','1.0');set_child(font,'thickness','0.15')
        if 'V4 PHASE 2' in text[1]:text[1]=Quoted('V4 PHASE 3 - ENGINEERING CANDIDATE - NOT FOR FABRICATION')
    if not any(t[1]=='NFC V4.3 / 0.8 mm' for t in children(board,'gr_text')):
        board.append(['gr_text',Quoted('NFC V4.3 / 0.8 mm'),['at','132','88','0'],['layer',Quoted('B.SilkS')],['uuid',Quoted(str(uuid.uuid4()))],['effects',['font',['size','1','1'],['thickness','0.15']],['justify','mirror']]])
    after=protected(board);assert before==after, 'Silkscreen cleanup changed protected geometry'
    write(file,board)
    result={'protected_geometry_sha256_before':before,'protected_geometry_sha256_after':after,'footprints':record,'preserved':'copper, mask, paste, pads, drills, courtyards, outline, rules and mechanical drawings','board_labels':'Battery polarity, GND/3V3/CLK/DIO/RST and board revision retained'}
    (project/'hardware/records/kicad-v4-phase3/silkscreen.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'footprints':len(record),'protected_geometry_unchanged':True}))


if __name__=='__main__':main()
