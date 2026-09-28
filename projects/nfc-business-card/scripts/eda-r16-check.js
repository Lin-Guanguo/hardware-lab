const project = await eda.dmt_Project.getCurrentProjectInfo();
const document = await eda.dmt_SelectControl.getCurrentDocumentInfo();
if (project?.friendlyName !== 'NFC-Card-R1-Layout-Reset-R16' || document?.uuid !== '8033127c48771f3b') {
  throw new Error('R16 PCB is not active');
}

const pours = await eda.pcb_PrimitivePour.getAll();
for (const pour of pours) await pour.rebuildCopperRegion();
const errors = await eda.pcb_Drc.check(false, false, true);
const saved = await eda.pcb_Document.save();
if (!saved) throw new Error('R16 PCB save failed');
return { pours: pours.length, drcCount: errors.length, errors };
