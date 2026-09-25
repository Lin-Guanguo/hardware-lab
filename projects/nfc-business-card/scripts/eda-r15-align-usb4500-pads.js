const project = await eda.dmt_Project.getCurrentProjectInfo();
const document = await eda.dmt_SelectControl.getCurrentDocumentInfo();
if (project?.friendlyName !== 'NFC-Card-R1-Layout-Reset-R15' || document?.uuid !== '8033127c48771f3b') {
  throw new Error('R15 PCB is not active');
}

const componentId = '9271c705bc7e0d5f';
const oldX = 2990.3;
const newX = 3002.1; // EasyEDA stores pad coordinates to 0.1 mil.
const padNumbers = new Set([
  'A1B12', 'A4B9', 'A5', 'A6', 'A7', 'A8',
  'B1A12', 'B4A9', 'B5', 'B6', 'B7', 'B8',
]);
const pads = (await eda.pcb_PrimitivePad.getAll()).filter(pad =>
  pad.primitiveId.startsWith(componentId) && padNumbers.has(pad.padNumber));
if (pads.length !== 12 || new Set(pads.map(pad => pad.padNumber)).size !== 12) {
  throw new Error(`Unexpected USB4500 pad count: ${pads.length}`);
}
for (const pad of pads) {
  if (pad.layer !== 1 || pad.pad?.[0] !== 'RECT' ||
      (Math.abs(pad.x - oldX) > 0.001 && Math.abs(pad.x - newX) > 0.001)) {
    throw new Error(`Unexpected USB4500 pad ${pad.padNumber}`);
  }
}

for (const pad of pads.filter(pad => Math.abs(pad.x - oldX) <= 0.001)) {
  const pending = pad.toAsync();
  pending.setState_X(newX);
  await pending.done();
}

const updated = (await eda.pcb_PrimitivePad.getAll()).filter(pad =>
  pad.primitiveId.startsWith(componentId) && padNumbers.has(pad.padNumber));
if (updated.length !== 12 || updated.some(pad => Math.abs(pad.x - newX) > 0.001)) {
  throw new Error('USB4500 pad shift did not persist in the active document');
}
return { count: updated.length, oldX, newX, shiftMm: (newX - oldX) * 0.0254 };
