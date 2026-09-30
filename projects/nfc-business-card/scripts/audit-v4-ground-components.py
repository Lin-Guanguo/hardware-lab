#!/usr/bin/env python3
"""Map actual two-layer ground components and their attached pads for local repair."""
import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path
import importlib.util

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as Patch
from shapely.geometry import Point, box
from shapely.ops import unary_union, nearest_points
from v4_geometry import geometry, filled_ground


def inspect(path, window=None):
    board,pads,objects,refs=geometry(path)
    planes={l:filled_ground(board,l) for l in ['F.Cu','B.Cu']}
    copper={l:unary_union([planes[l],*[o['shape'] for o in objects if o['net']=='GND' and l in o['layers']]]) for l in planes}
    if window is not None: copper={l:g.intersection(box(*window)) for l,g in copper.items()}
    pieces={l:list(g.geoms) if g.geom_type=='MultiPolygon' else [g] for l,g in copper.items()}
    nodes={(l,i):g for l,gs in pieces.items() for i,g in enumerate(gs) if not g.is_empty}
    def contacts(shape,layers):
        return {k for k,g in nodes.items() if k[0] in layers and g.distance(shape)<.00001}
    graph=defaultdict(set)
    for o in objects:
        if o['net']=='GND' and len(o['layers'])==2:
            ids=contacts(o['shape'],o['layers'])
            for k in ids:graph[k].update(ids)
    groups=[];pending=set(nodes)
    while pending:
        reached=set();todo=[min(pending)]
        while todo:
            k=todo.pop()
            if k not in reached:reached.add(k);todo.extend(graph[k]-reached)
        pending-=reached;groups.append(reached)
    groups.sort(key=lambda g:(not bool(g&contacts(pads['U2.11']['shape'],['F.Cu'])),-sum(nodes[k].area for k in g)))
    memberships={k:i for i,group in enumerate(groups) for k in group}
    padgroups={n:sorted({memberships[k] for k in contacts(p['shape'],p['layers'])}) for n,p in pads.items() if p['net']=='GND'}
    return board,pads,objects,refs,planes,nodes,groups,padgroups


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('board',type=Path);ap.add_argument('output',type=Path);a=ap.parse_args();a.output.mkdir(parents=True,exist_ok=True)
    board,pads,objects,refs,planes,nodes,groups,padgroups=inspect(a.board)
    entries=[]
    for i,group in enumerate(groups):
        attached=[n for n,ids in padgroups.items() if i in ids]
        boundaries=[]
        for layer,index in sorted(group):
            g=nodes[layer,index]
            neighbours=[dict(id=o['name'],net=o['net'],kind=o['kind']) for o in objects if o['net']!='GND' and layer in o['layers'] and o['shape'].distance(g)<.301]
            boundaries.append(dict(layer=layer,area_mm2=round(g.area,6),bounds_mm=list(g.bounds),near_boundary_objects=neighbours))
        entries.append(dict(id=i,pads=attached,pieces=boundaries))
    report=dict(board=str(a.board),sha256=hashlib.sha256(a.board.read_bytes()).hexdigest(),scope='Saved native fill and explicit copper. Group 0 contains U2 EP only as a connectivity reference; no star-ground topology is implied. Boundary proximity is a candidate obstruction, not proof of causality.',components=entries,pad_groups=padgroups)
    (a.output/'components.json').write_text(json.dumps(report,indent=2)+'\n')
    colors=['#d7e5d7','#f7b570','#74b9ef','#dbaaeb','#e59b9f','#e3d85a','#75cbb8','#bbac9c','#d4b1ad','#bac6e4']
    for name,bounds in [('whole',(110,78,194,131)),('critical',(163,94,193,125))]:
        fig,axes=plt.subplots(1,2,figsize=(17,10 if name=='critical' else 6.5),constrained_layout=True)
        for ax,layer in zip(axes,planes):
            for i,group in enumerate(groups):
                for k in group:
                    if k[0]!=layer:continue
                    g=nodes[k];ax.add_patch(Patch(g.exterior.coords,facecolor=colors[i%len(colors)],linewidth=.3,edgecolor='#777777'))
                    for ring in g.interiors:ax.add_patch(Patch(ring.coords,facecolor='white',linewidth=0))
                    pt=g.representative_point()
                    if box(*bounds).contains(pt):ax.text(pt.x,pt.y,f'G{i}',fontsize=8,weight='bold',clip_on=True)
            for o in objects:
                if layer not in o['layers'] or o['net']=='GND':continue
                ax.add_patch(Patch(o['shape'].exterior.coords,facecolor='#bd554c' if layer=='F.Cu' else '#416db7',linewidth=0,alpha=.8))
            for n,ids in padgroups.items():
                x,y=pads[n]['at']
                if bounds[0]<x<bounds[2] and bounds[1]<y<bounds[3]:
                    ax.text(x,y,n+' G'+','.join(map(str,ids)),fontsize=5.2,clip_on=True,bbox=dict(facecolor='white',alpha=.8,edgecolor='none',pad=.1))
            ax.set(xlim=(bounds[0],bounds[2]),ylim=(bounds[3],bounds[1]),aspect='equal',title=layer+' ground components / top view',xlabel='KiCad X / mm',ylabel='KiCad Y / mm');ax.grid(alpha=.15)
        fig.savefig(a.output/(name+'.png'),dpi=160);plt.close(fig)
    print(json.dumps([{'id':x['id'],'pads':x['pads'],'areas':[(z['layer'],z['area_mm2']) for z in x['pieces']]} for x in entries],indent=2))


if __name__=='__main__':main()
