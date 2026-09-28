const project = await eda.dmt_Project.getCurrentProjectInfo();
const document = await eda.dmt_SelectControl.getCurrentDocumentInfo();
if (project?.friendlyName !== 'NFC-Card-R1-Layout-Reset-R12' || document?.uuid !== '8033127c48771f3b') {
  throw new Error('R12 PCB is not active');
}

const edits = [
  { kind: 'via', id: '6bd504afe53e18a7', oldX: 2907.6142, newX: 2900.6 },
  { kind: 'lineEnd', id: 'af3ccbfe5a36e5ec', oldX: 2907.6142, newX: 2900.6 },
  { kind: 'via', id: '8918971c99a4f7e6', oldX: 3011.811, newX: 3006.8 },
  { kind: 'lineStart', id: '892f18b92fb427fb', oldX: 3011.811, newX: 3006.8 },
  { kind: 'lineEnd', id: '77d488abe0aada47', oldX: 3011.811, newX: 3006.8 },
];

const result = [];
for (const edit of edits) {
  const primitive = edit.kind === 'via'
    ? await eda.pcb_PrimitiveVia.get(edit.id)
    : await eda.pcb_PrimitiveLine.get(edit.id);
  if (!primitive) throw new Error(`Missing ${edit.kind} ${edit.id}`);
  const property = edit.kind === 'via' ? 'x' : edit.kind === 'lineStart' ? 'startX' : 'endX';
  if (Math.abs(primitive[property] - edit.newX) <= 0.001) {
    result.push({ id: edit.id, from: edit.oldX, to: edit.newX, alreadyUpdated: true });
    continue;
  }
  if (Math.abs(primitive[property] - edit.oldX) > 0.001) {
    throw new Error(`Unexpected ${edit.id} ${property}: ${primitive[property]}`);
  }
  const pending = primitive.toAsync();
  if (edit.kind === 'via') pending.setState_X(edit.newX);
  else if (edit.kind === 'lineStart') pending.setState_StartX(edit.newX);
  else pending.setState_EndX(edit.newX);
  const updated = await pending.done();
  result.push({ id: edit.id, from: edit.oldX, to: updated[property] });
}

const batLines = (await eda.pcb_PrimitiveLine.getAll()).filter(line => line.net === 'BAT_PACK_TBD' && line.layer === 2);
const nearly = (a, b) => Math.abs(a - b) < 0.001;
const oldBranch = batLines.find(line =>
  nearly(line.startX, 2964.5669) && nearly(line.startY, 592.5197) &&
  nearly(line.endY, 592.5197) &&
  (nearly(line.endX, 3011.811) || nearly(line.endX, 3006.8)));
if (!oldBranch) throw new Error('Missing Q2 lower copper branch');
if (nearly(oldBranch.endX, 3011.811)) {
  const pending = oldBranch.toAsync();
  pending.setState_EndX(3006.8);
  await pending.done();
}
const stubs = (await eda.pcb_PrimitiveLine.getAll()).filter(line =>
  line.net === 'BAT_PACK_TBD' && line.layer === 2 &&
  nearly(line.startX, 3006.8) && nearly(line.startY, 592.5197) &&
  nearly(line.endX, 3011.811) && nearly(line.endY, 592.5197));
for (const stub of stubs) await eda.pcb_PrimitiveLine.delete(stub.primitiveId);
result.push({ lowerBranch: oldBranch.primitiveId, removedStubs: stubs.length });
return result;
