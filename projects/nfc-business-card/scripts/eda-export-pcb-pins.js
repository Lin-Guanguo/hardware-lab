const project=await eda.dmt_Project.getCurrentProjectInfo();
if(project.uuid!=="70e4734137fc61bb6eab88e382fc9a6084e6f570f3396f1502e4f4e9dc906821")throw new Error("Wrong R1 project");
await eda.dmt_EditorControl.openDocument("8033127c48771f3b");
await new Promise(r=>setTimeout(r,1500));
const out = [];
for (const comp of await eda.pcb_PrimitiveComponent.getAll()) {
  if (!comp.designator) continue;
  const pins = await eda.pcb_PrimitiveComponent.getAllPinsByPrimitiveId(comp.primitiveId);
  out.push({
    ref: comp.designator,
    pins: (pins || []).map((p) => ({ number: p.padNumber, net: p.net || "", x:p.x, y:p.y, layer:p.layer })),
  });
}
out.sort((a, b) => a.ref.localeCompare(b.ref, undefined, { numeric: true }));
return out;
