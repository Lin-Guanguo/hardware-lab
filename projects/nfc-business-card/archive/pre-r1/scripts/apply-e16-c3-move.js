// Move C3 back beside U2 and reconnect it to the battery rail.
//
// C3 is the BQ25186 BAT pin capacitor (2.2 uF). The E16 USB rearrangement swept
// it in with the USB parts and left it 24.49 mm from the pin it serves, which
// DC-001 flags as critical. E15 had it about 4.7 mm away.
//
// Position chosen by search over legal placements, using the correct rule that
// each pad only has to clear copper of a different net. (49.60, 21.60) at
// rotation 0 puts the BAT pad 3.43 mm from U2's BAT pin, well under DC-001's
// 5 mm warning, keeps the GND pad inside the top pour, and needs a 1.77 mm tie
// to the battery trace. Cross-net margins are 0.261 mm at the BAT pad and
// 0.253 mm at the GND pad, and the tie traces with zero violations.
//
const E16_PAGE_UUID = "2fe84861daa4cba5";
const C3_ID = "aeb09fd14540bf14";
const NEW_POS = { x: 1952.7559, y: 850.3937, rotation: 0 };

// The twelve trace segments that detour from the battery rail out to C3's old
// place. Matched geometrically so a stale index cannot delete the wrong copper.
const DETOUR = [
 [
  2007.875,
  744.095,
  2007.875,
  712.599,
  2
 ],
 [
  2007.875,
  712.599,
  2023.623,
  696.851,
  2
 ],
 [
  2023.623,
  696.851,
  2023.623,
  653.544,
  2
 ],
 [
  2023.623,
  653.544,
  2015.749,
  645.67,
  2
 ],
 [
  2015.749,
  645.67,
  2015.749,
  586.614,
  2
 ],
 [
  2015.749,
  586.614,
  2263.781,
  338.583,
  2
 ],
 [
  2263.781,
  338.583,
  2350.395,
  251.969,
  1
 ],
 [
  2350.395,
  251.969,
  2503.938,
  251.969,
  2
 ],
 [
  2503.938,
  251.969,
  2559.057,
  307.087,
  2
 ],
 [
  2559.057,
  307.087,
  2767.718,
  515.748,
  1
 ],
 [
  2767.718,
  515.748,
  2767.718,
  775.591,
  1
 ],
 [
  2767.718,
  775.591,
  2787.403,
  795.276,
  1
 ]
];

const TIE = { net: "BAT_PACK_TBD", layer: 1, width: 5.9055,
              a: [1925.1969, 850.3937], b: [1974.4094, 899.6063] };

await eda.dmt_EditorControl.openDocument(E16_PAGE_UUID);
await new Promise((r) => setTimeout(r, 2500));

const out = { steps: [], errors: [] };
const step = async (name, fn) => {
  try { out.steps.push({ name, ok: true, value: await fn() }); }
  catch (err) { out.steps.push({ name, ok: false, error: String(err && err.message ? err.message : err) }); }
};

await step("counts before", async () => ({
  lines: (await eda.pcb_PrimitiveLine.getAll()).length,
  vias: (await eda.pcb_PrimitiveVia.getAll()).length,
}));

await step("move C3", async () => {
  const r = await eda.pcb_PrimitiveComponent.modify(C3_ID, NEW_POS);
  return r === undefined ? "modify returned undefined (check the read-back)" : "modified";
});

await step("delete detour segments", async () => {
  const lines = await eda.pcb_PrimitiveLine.getAll();
  const round = (v) => Math.round(v * 1000) / 1000;
  const wanted = new Set(DETOUR.map((d) => d.join("|")));
  const hit = [];
  for (const line of lines) {
    if ((line.net || "") !== "BAT_PACK_TBD") continue;
    const f = [round(line.startX), round(line.startY), round(line.endX), round(line.endY), line.layer].join("|");
    const r = [round(line.endX), round(line.endY), round(line.startX), round(line.startY), line.layer].join("|");
    if (wanted.has(f) || wanted.has(r)) hit.push(line.primitiveId);
  }
  if (hit.length !== DETOUR.length) {
    out.errors.push(`expected ${DETOUR.length} detour segments, matched ${hit.length}`);
  }
  const ok = await eda.pcb_PrimitiveLine.delete(hit);
  return { matched: hit.length, deleted: ok };
});

await step("add tie trace", async () => {
  const made = await eda.pcb_PrimitiveLine.create(
    TIE.net, TIE.layer, TIE.a[0], TIE.a[1], TIE.b[0], TIE.b[1], TIE.width);
  return made ? `created ${made.primitiveId}` : "create returned undefined";
});

await step("refill ground pours", async () => {
  const pours = await eda.pcb_PrimitivePour.getAll();
  const done = [];
  for (const pour of pours || []) {
    if ((pour.net || "") !== "GND") continue;
    const poured = await pour.rebuildCopperRegion();
    done.push({ pour: pour.pourName, ok: !!poured });
  }
  return done;
});

await step("save", () => eda.pcb_Document.save());

await step("counts after", async () => ({
  lines: (await eda.pcb_PrimitiveLine.getAll()).length,
  vias: (await eda.pcb_PrimitiveVia.getAll()).length,
}));

await step("read C3 back", async () => {
  const comps = await eda.pcb_PrimitiveComponent.getAll();
  const c3 = (comps || []).find((c) => c.primitiveId === C3_ID);
  return c3 ? { x_mm: (c3.x * 0.0254).toFixed(3), y_mm: (c3.y * 0.0254).toFixed(3), rotation: c3.rotation } : "not found";
});

return out;
