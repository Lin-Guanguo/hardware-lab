#!/usr/bin/env python3
"""Export the open R1 project using the native EasyEDA bridge APIs."""
import argparse
import json
import urllib.request
from pathlib import Path

ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--output',type=Path,required=True)
ap.add_argument('--project-uuid',default='70e4734137fc61bb6eab88e382fc9a6084e6f570f3396f1502e4f4e9dc906821')
ap.add_argument('--prefix',default='NFC-Card-R1')
ap.add_argument('--core-only',action='store_true',help='Export Gerber, BOM, and CPL only')
a=ap.parse_args();out=a.output.resolve();out.mkdir(parents=True,exist_ok=True)
guard='const d=await eda.dmt_SelectControl.getCurrentDocumentInfo();if(d?.uuid!=="8033127c48771f3b"||d?.parentProjectUuid!=='+json.dumps(a.project_uuid)+')throw new Error("Wrong R1 document");'
jobs={
 '-gerber.zip':'eda.pcb_ManufactureData.getGerberFile('+json.dumps(a.prefix+'-gerber')+',false,"mm",undefined,{metallicDrillingInformation:true,nonMetallicDrillingInformation:true,drillTable:false,flyingProbeTestingFile:true},[1,2,3,4,5,6,7,8,11].map(layerId=>({layerId,isMirror:false})))',
 '-bom.csv':'eda.pcb_ManufactureData.getBomFile('+json.dumps(a.prefix+'-bom')+',"csv")',
 '-cpl.csv':'eda.pcb_ManufactureData.getPickAndPlaceFile('+json.dumps(a.prefix+'-cpl')+',"csv","mm")',
}
if not a.core_only:
    jobs.update({
        '-assembly.pdf':'eda.pcb_ManufactureData.getPdfFile('+json.dumps(a.prefix+'-assembly')+')',
        '-pcba.step':'eda.pcb_ManufactureData.get3DFile('+json.dumps(a.prefix+'-pcba')+',"step",["Component Model"],"Outfit",false)',
        '-project.epro2':'eda.sys_FileManager.getProjectFile('+json.dumps(a.prefix+'-project')+',undefined,"epro2")',
    })
for suffix,expression in jobs.items():
    name=a.prefix+suffix
    path=out/name
    if path.exists():raise SystemExit(f'Refusing to overwrite existing export: {path}')
    code=guard+'const f=await '+expression+';if(!f)throw new Error("Export failed");return await eda.sys_FileSystem.saveFileToFileSystem('+json.dumps(str(path))+',f,undefined,true);'
    req=urllib.request.Request('http://127.0.0.1:49620/execute',data=json.dumps({'code':code}).encode(),headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(req,timeout=180) as response:result=json.load(response)
    if not result.get('success') or not path.exists() or path.stat().st_size==0:raise RuntimeError(result)
    print(name,path.stat().st_size,flush=True)
