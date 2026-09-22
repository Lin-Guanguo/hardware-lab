// EasyEDA-side payload that dumps the live PCB pin->net map for the E16 sheet,
// so check-netlist-consistency.py can diff it against the schematic netlist.
//
//   node scripts/eda-exec-wait.mjs scripts/eda-export-pcb-pins.js 60000 > /tmp/pcb-pins.json
const E16_PAGE_UUID = "2fe84861daa4cba5";

await eda.dmt_EditorControl.openDocument(E16_PAGE_UUID);
await new Promise((r) => setTimeout(r, 2000));

const out = [];
for (const comp of await eda.pcb_PrimitiveComponent.getAll()) {
  if (!comp.designator) continue;
  const pins = await eda.pcb_PrimitiveComponent.getAllPinsByPrimitiveId(comp.primitiveId);
  out.push({
    ref: comp.designator,
    pins: (pins || []).map((p) => ({ number: p.padNumber, net: p.net || "" })),
  });
}
out.sort((a, b) => a.ref.localeCompare(b.ref, undefined, { numeric: true }));
return out;
