#!/usr/bin/env python3
"""Build a complete local R1 handoff from tracked inputs without changing them."""
import hashlib
import json
import shutil
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT/'artifacts'
PRODUCTION = ROOT/'hardware/production/r1'
CASE = ROOT/'enclosure/r1-clear-5.8'

def digest(path):
    return {'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}

ARTIFACTS.mkdir(exist_ok=True)
with tempfile.TemporaryDirectory(prefix='r1-package-',dir=ARTIFACTS) as temp:
    out=Path(temp)
    for p in PRODUCTION.iterdir():
        if p.is_file():shutil.copy2(p,out/p.name)
    shutil.copy2(ROOT.parents[1]/'eda/NFC-Card-R1.eprj2',out/'NFC-Card-R1.eprj2')
    shutil.copy2(ROOT/'enclosure/renders/r1-routed-front-rear.png',out/'NFC-Card-R1-copper-preview.png')
    shutil.copy2(ROOT/'enclosure/renders/r1-control-routing-comparison.png',out/'NFC-Card-R1-routing-comparison.png')
    for name in ['hardware/r1-usb-swd-recovery.md','enclosure/r1-recovery-study.md','enclosure/r1-recovery-study.json']:
        target=out/name
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(ROOT/name,target)
    (out/'case').mkdir();(out/'checks').mkdir()
    names={'e20-clear-assembly.FCStd':'NFC-Card-R1-case.FCStd','e20-clear-assembly.step':'NFC-Card-R1-case.step',
           'e20-clear-report.json':'geometry-report.json','e20-clear-assembled-iso.png':'assembled-preview.png',
           'e20-clear-open-iso.png':'open-preview.png'}
    for kind in ['tray','lid','keys']:
        for ext in ['step','stl']:
            if (CASE/f'e20-clear-{kind}.{ext}').exists():names[f'e20-clear-{kind}.{ext}']=f'NFC-Card-R1-{kind}.{ext}'
    for old,new in names.items():shutil.copy2(CASE/old,out/'case'/new)
    shutil.copy2(CASE/'design-inputs.json',out/'case/cad-build-inputs.json')
    shutil.copy2(ROOT/'hardware/r1-design.json',out/'case/design-inputs.json')
    for p in sorted((ROOT/'hardware/records').glob('r1-*')):
        if p.name!='r1-delivery-manifest.json':shutil.copy2(p,out/'checks'/p.name)
    (out/'README.md').write_text('''# NFC Card R1 engineering prototype\n\nUpload NFC-Card-R1-gerber.zip for bare PCB fabrication; BOM/CPL are separate assembly inputs.\nThe complete prototype ZIP is a handoff, not a Gerber upload.\n\nNFC-Card-R1.eprj2 is the native editable project; .epro2 is its portable backup.\nThe PDF is an assembly review; the PCBA STEP is a mechanical model.\ncase/ contains CAD and millimetre STL meshes for tray, lid and three keys.\nThe retained 5.8 mm CAD has old wire/ferrite service bodies; it does not validate the new B-pad wiring or 0.25 mm sheet.\nRegional height and button follow-up is recorded in the repository at enclosure/r1-height-handoff.md.\nchecks/ contains frozen geometry and verification evidence.\n\nThe C1 finding was retracted: C1 serves U1 VBUS; C8 already bypasses the charger input. Nominal minimum drill is now 0.25 mm; confirm vendor DFM, hole-processing tier and USB connector assembly. USB reference-path detours still need powered prototype tests.\nCE/SCL routing removes two vias. R3/R4 are now 0 ohm / C21189.\nRead hardware/r1-usb-swd-recovery.md and enclosure/r1-recovery-study.md before ordering.\nThe five SWD pads use 2.54 mm pitch with matching cover holes; TP1/GND is square. Generic 5P clip assumptions are accepted; trial fit remains. No hidden RESET switch or access hole is installed.\nThe user will program the initial bootloader via SWD; no factory programming is requested. UF2/USB logs and recovery remain firmware/bench work.\nRF tuning, complete battery dimensions and physical assembly remain unverified.\nRead checks/r1-validation.json and checks/r1-review.json when present for status.\nNo order has been placed.\n''')
    manifest={'revision':'R1','status':json.loads((ROOT/'hardware/records/r1-validation.json').read_text())['status'],'files':{str(p.relative_to(out)):digest(p) for p in sorted(out.rglob('*')) if p.is_file()}}
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    archive=ARTIFACTS/'archive/r1-packages';archive.mkdir(parents=True,exist_ok=True)
    current=ARTIFACTS/'NFC-Card-R1-prototype.zip'
    if current.exists():
        backup=archive/f"NFC-Card-R1-prototype-{digest(current)['sha256'][:12]}.zip"
        if not backup.exists():shutil.copy2(current,backup)
    with zipfile.ZipFile(current,'w',zipfile.ZIP_DEFLATED) as z:
        for p in sorted(out.rglob('*')):
            if p.is_file():z.write(p,p.relative_to(out))
    # Existing expanded packages are preserved before replacing the generated view.
    expanded=ARTIFACTS/'r1-delivery'
    if expanded.exists():
        old_hash=hashlib.sha256((expanded/'manifest.json').read_bytes()).hexdigest()[:12]
        backup=archive/f'expanded-{old_hash}'
        if backup.exists():backup=Path(tempfile.mkdtemp(prefix=f'expanded-{old_hash}-',dir=archive))/'contents'
        shutil.move(expanded,backup)
    shutil.copytree(out,expanded)
    with zipfile.ZipFile(current) as z:
        assert z.testzip() is None
        for name,meta in manifest['files'].items():assert hashlib.sha256(z.read(name)).hexdigest()==meta['sha256']
    (ROOT/'hardware/records/r1-delivery-manifest.json').write_text(json.dumps({**manifest,'bundle':digest(current)},indent=2)+'\n')
    print(json.dumps({'file':str(current),**digest(current),'members':len(manifest['files'])+1}))
