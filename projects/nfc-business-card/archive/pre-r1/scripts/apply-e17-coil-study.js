// Apply the verified E17 NFC coil study to Board1_3 only.
// The schematic short flag deliberately merges NFC1_TBD and NFC2_TBD.
// RF tuning and reader performance still require physical measurement.
const PCB = "fe6ced9e6b52b846";
const PLAN = {"name": "E17 board coil candidate", "note": "Candidate with native schematic short flag. RF tuning and reader performance remain unverified.", "keepouts": [{"name": "NFC reserve", "x0": 60.0, "y0": 24.0, "x1": 82.0, "y1": 50.0}, {"name": "U1 antenna", "x0": 59.7, "y0": 0.2, "x1": 70.3, "y1": 2.5}], "ignore_nets": [], "tracks": [{"net": "NFC1_TBD", "layer": 2, "width_mm": 0.25, "points": [[68.0, 27.6], [60.6, 27.6], [60.6, 48.9], [71.0, 48.9], [71.0, 28.0], [61.0, 28.0], [61.0, 48.5], [70.6, 48.5], [70.6, 28.4], [61.4, 28.4], [61.4, 48.1], [70.2, 48.1], [70.2, 28.8], [61.8, 28.8], [61.8, 47.7], [69.8, 47.7], [69.8, 29.2], [62.2, 29.2], [62.2, 47.3], [69.4, 47.3], [69.4, 29.6], [62.6, 29.6], [62.6, 46.9], [69.0, 46.9], [69.0, 30.0]]}, {"net": "NFC1_TBD", "layer": 2, "width_mm": 0.25, "points": [[68.0, 23.0], [68.0, 27.6]]}, {"net": "NFC1_TBD", "layer": 1, "width_mm": 0.25, "points": [[69.0, 30.0], [69.0, 25.6], [70.2, 24.4], [71.4, 24.4]]}, {"net": "NFC1_TBD", "layer": 2, "width_mm": 0.25, "points": [[71.4, 24.4], [71.4, 23.0]]}], "vias": [{"net": "NFC1_TBD", "x": 69.0, "y": 30.0, "diameter_mm": 0.3, "hole_mm": 0.2}, {"net": "NFC1_TBD", "x": 71.4, "y": 24.4, "diameter_mm": 0.3, "hole_mm": 0.2}], "turns": 6};
const MM_PER_MIL = 0.0254;
await eda.dmt_EditorControl.openDocument(PCB);
const document = await eda.dmt_SelectControl.getCurrentDocumentInfo();
if (document?.uuid !== PCB || document.documentType !== 3) throw new Error("Wrong PCB document");
const before = {lines:(await eda.pcb_PrimitiveLine.getAll()).length,
                vias:(await eda.pcb_PrimitiveVia.getAll()).length};
if (before.lines !== 791 || before.vias !== 168) throw new Error(`Unexpected base counts: ${JSON.stringify(before)}`);
const made = {lines:[],vias:[],errors:[]};
for (const v of PLAN.vias) {
  try {
    const via = await eda.pcb_PrimitiveVia.create(v.net, v.x/MM_PER_MIL, v.y/MM_PER_MIL, 8, 12);
    if (!via?.primitiveId) throw new Error("Via create returned no primitive ID");
    made.vias.push(via.primitiveId);
  } catch (error) {made.errors.push(`via ${v.x},${v.y}: ${String(error)}`);}
}
for (const track of PLAN.tracks) {
  for (let i=1;i<track.points.length;i++) {
    const a=track.points[i-1],b=track.points[i];
    try {
      const line=await eda.pcb_PrimitiveLine.create(track.net,track.layer,
        a[0]/MM_PER_MIL,a[1]/MM_PER_MIL,b[0]/MM_PER_MIL,b[1]/MM_PER_MIL,track.width_mm/MM_PER_MIL);
      if (!line?.primitiveId) throw new Error("Line create returned no primitive ID");
      made.lines.push(line.primitiveId);
    } catch(error) {made.errors.push(`line ${i}: ${String(error)}`);}
  }
}
const after={lines:(await eda.pcb_PrimitiveLine.getAll()).length,
             vias:(await eda.pcb_PrimitiveVia.getAll()).length};
if (!made.errors.length) made.saved=await eda.pcb_Document.save();
return {before,after,made};
