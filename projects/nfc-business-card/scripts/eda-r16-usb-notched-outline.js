const project = await eda.dmt_Project.getCurrentProjectInfo();
const document = await eda.dmt_SelectControl.getCurrentDocumentInfo();
if (project?.friendlyName !== 'NFC-Card-R1-Layout-Reset-R16' || document?.uuid !== '8033127c48771f3b') {
  throw new Error('R16 PCB is not active');
}

const outline = (await eda.pcb_PrimitivePolyline.getAll()).find(
  primitive => primitive.primitiveId === 'c84e1edb0cfe96f2');
if (!outline || outline.layer !== 11) throw new Error('Expected board outline was not found');
const source = outline.getState_Polygon().getSource();
const expected = {
  35: 3263.7795, 36: 1213.4212, 37: 3043.474, 38: 1213.4212,
  39: 'ARC', 40: 90, 41: 3023.789, 42: 1193.7362, 43: 'L',
  44: 3023.789, 45: 853.4984, 46: 'ARC', 47: 90,
  48: 3043.474, 49: 833.8133, 50: 'L', 51: 3263.7795,
  52: 833.8133,
};
for (const [key, value] of Object.entries(expected)) {
  const actual = source[Number(key)];
  if (typeof value === 'number' ? Math.abs(actual - value) > 0.001 : actual !== value) {
    throw new Error(`Unexpected original USB notch vertex ${key}: ${actual}`);
  }
}

const mil = mm => mm / 0.0254;
const centerY = (802.3 + 1244.9) / 2;
// Nominal 9.20 mm fits GCT's 9.24 ±0.05 mm callout; fabrication tolerance
// and the 0.20 mm internal corner remain unqualified.
const halfNotch = mil(9.20) / 2;
const cornerRadius = mil(0.20);
const innerX = 3023.789;
const outerX = innerX + cornerRadius;
const upperY = centerY - halfNotch;
const lowerY = centerY + halfNotch;
const updated = source.slice();
updated[36] = lowerY + cornerRadius;
updated[37] = outerX;
updated[38] = lowerY + cornerRadius;
updated[42] = lowerY;
updated[45] = upperY;
updated[48] = outerX;
updated[49] = upperY - cornerRadius;
updated[52] = upperY - cornerRadius;
const polygon = eda.pcb_MathPolygon.createPolygon(updated);
if (!polygon) throw new Error('Failed to construct USB notch outline');
const pending = outline.toAsync();
pending.setState_Polygon(polygon);
await pending.done();
const saved = await eda.pcb_Document.save();
if (!saved) throw new Error('Failed to save R16 outline');
return {
  notchWidthMm: (lowerY - upperY) * 0.0254,
  radiusMm: cornerRadius * 0.0254,
  upperY, lowerY,
};
