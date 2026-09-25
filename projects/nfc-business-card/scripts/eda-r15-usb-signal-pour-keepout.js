const project = await eda.dmt_Project.getCurrentProjectInfo();
const document = await eda.dmt_SelectControl.getCurrentDocumentInfo();
if (project?.friendlyName !== 'NFC-Card-R1-Layout-Reset-R15' || document?.uuid !== '8033127c48771f3b') {
  throw new Error('R15 PCB is not active');
}

const name = 'J1_SIGNAL_POUR_CLEARANCE';
const regions = await eda.pcb_PrimitiveRegion.getAll();
const existing = regions.find(region => region.primitiveId === '1c2979245a7f5d36');

const mmToMil = value => Math.round(value / 0.0254 * 10) / 10;
const x1 = mmToMil(75.05);
const x2 = mmToMil(82.9);
const y1 = mmToMil(22.9);
const y2 = mmToMil(29.0);
const polygon = eda.pcb_MathPolygon.createPolygon([x1, y1, 'L', x2, y1, x2, y2, x1, y2, x1, y1]);
if (!polygon) throw new Error('Failed to create J1 pour keepout polygon');
// Layer 1 is Top Layer; rule 7 is NO_POURS in EPCB_PrimitiveRegionRuleType.
let region;
if (existing) {
  const pending = existing.toAsync();
  pending.setState_ComplexPolygon(polygon);
  region = await pending.done();
} else {
  region = await eda.pcb_PrimitiveRegion.create(1, polygon, [7], name, 0.2, false);
}
if (!region) throw new Error('Failed to create J1 pour keepout');
return { id: region.primitiveId, name, x1, x2, y1, y2 };
