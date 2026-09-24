#!/usr/bin/env python3
"""Export the open R1 project using the native EasyEDA bridge APIs."""
import argparse
import json
import urllib.request
from pathlib import Path

ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--output',type=Path,required=True)
a=ap.parse_args();out=a.output.resolve();out.mkdir(parents=True,exist_ok=True)
guard='const d=await eda.dmt_SelectControl.getCurrentDocumentInfo();if(d?.uuid!=="8033127c48771f3b"||d?.parentProjectUuid!=="70e4734137fc61bb6eab88e382fc9a6084e6f570f3396f1502e4f4e9dc906821")throw new Error("Wrong R1 document");'
jobs={
 'NFC-Card-R1-gerber.zip':'eda.pcb_ManufactureData.getGerberFile("NFC-Card-R1-gerber",false,"mm",undefined,{metallicDrillingInformation:true,nonMetallicDrillingInformation:true,drillTable:false,flyingProbeTestingFile:true},[1,2,3,4,5,6,7,8,11].map(layerId=>({layerId,isMirror:false})))',
 'NFC-Card-R1-bom.csv':'eda.pcb_ManufactureData.getBomFile("NFC-Card-R1-bom","csv")',
 'NFC-Card-R1-cpl.csv':'eda.pcb_ManufactureData.getPickAndPlaceFile("NFC-Card-R1-cpl","csv","mm")',
 'NFC-Card-R1-assembly.pdf':'eda.pcb_ManufactureData.getPdfFile("NFC-Card-R1-assembly")',
 'NFC-Card-R1-pcba.step':'eda.pcb_ManufactureData.get3DFile("NFC-Card-R1-pcba","step",["Component Model"],"Outfit",false)',
 'NFC-Card-R1-project.epro2':'eda.sys_FileManager.getProjectFile("NFC-Card-R1-project",undefined,"epro2")',
}
for name,expression in jobs.items():
    path=out/name
    if path.exists():raise SystemExit(f'Refusing to overwrite existing export: {path}')
    code=guard+'const f=await '+expression+';if(!f)throw new Error("Export failed");return await eda.sys_FileSystem.saveFileToFileSystem('+json.dumps(str(path))+',f,undefined,true);'
    req=urllib.request.Request('http://127.0.0.1:49620/execute',data=json.dumps({'code':code}).encode(),headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(req,timeout=180) as response:result=json.load(response)
    if not result.get('success') or not path.exists() or path.stat().st_size==0:raise RuntimeError(result)
    print(name,path.stat().st_size,flush=True)
