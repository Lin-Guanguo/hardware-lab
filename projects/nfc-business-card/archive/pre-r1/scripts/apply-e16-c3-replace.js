// Fix the three real DRC violations that the first C3 move introduced.
//
// Native DRC reported, through its verbose overload:
//   Clearance Error  CHG_SDA track vs C3_1 pad      4.3 mil, need 6
//   Clearance Error  BAT_PACK_TBD track vs C3_2 pad 4.0 mil, need 6
//   Connection Error C3_2 pad has no connection
//   Physical Error   two GND vias with a 7.8 mil hole, minimum is 7.9
//
// The first move used a home-made clearance test that treated a rectangular pad
// as a circle of radius max(half_w, half_h). On the 45-degree CHG_SDA trace that
// overestimates by about 6 mil, which is exactly the size of the error DRC
// found. The placement below was produced by plan-e16-c3-move.py, which calls
// check-proposed-route.check - now calibrated against those DRC numbers.
//
// C3 goes to (48.60, 22.75) rotation 180: its pads overlap the BP and BN battery
// landing pads by 0.40 mm and 0.25 mm, so each pad is solidly connected rather
// than hoping for pour thermal spokes, which is what failed last time. Worst
// clearance is 8.47 mil against a 6 mil rule. It is also where E15 had the cap.
//
// Run: node scripts/eda-exec-wait.mjs scripts/apply-e16-c3-replace.js 300000

const E16_PAGE_UUID = "2fe84861daa4cba5";
const C3_ID = "aeb09fd14540bf14";
const NEW_POS = { x: 1913.3858, y: 895.6693, rotation: 180 };

// The tie trace the previous attempt added; its pad end moves away with C3, so
// leaving it would strand a stub.
const STALE_TIE = { net: "BAT_PACK_TBD", layer: 1, a: [1925.1969, 850.3937], b: [1974.4094, 899.6063] };

// Holes must be at least 7.9 mil; 8.0/12.0 matches the 48 other GND vias. The
// targets are selected by the defect itself - GND vias whose hole is under
// 7.9 mil - rather than by hand-copied coordinates.
const MIN_HOLE_MIL = 7.9;
const VIA_FIX = { holeDiameter: 8.0, diameter: 12.0 };

await eda.dmt_EditorControl.openDocument(E16_PAGE_UUID);
await new Promise((r) => setTimeout(r, 2500));

const out = { steps: [], errors: [] };
const step = async (name, fn) => {
  try { out.steps.push({ name, ok: true, value: await fn() }); }
  catch (err) { out.steps.push({ name, ok: false, error: String(err && err.message ? err.message : err) }); }
};

await step("delete stale tie", async () => {
  const lines = await eda.pcb_PrimitiveLine.getAll();
  const round = (v) => Math.round(v * 1000) / 1000;
  const wanted = [STALE_TIE.a, STALE_TIE.b];
  const keys = new Set([
    [round(wanted[0][0]), round(wanted[0][1]), round(wanted[1][0]), round(wanted[1][1]), STALE_TIE.layer].join("|"),
    [round(wanted[1][0]), round(wanted[1][1]), round(wanted[0][0]), round(wanted[0][1]), STALE_TIE.layer].join("|"),
  ]);
  const hit = [];
  for (const line of lines) {
    if ((line.net || "") !== STALE_TIE.net) continue;
    const f = [round(line.startX), round(line.startY), round(line.endX), round(line.endY), line.layer].join("|");
    if (keys.has(f)) hit.push(line.primitiveId);
  }
  if (hit.length !== 1) out.errors.push(`expected 1 stale tie, matched ${hit.length}`);
  return { matched: hit.length, deleted: hit.length ? await eda.pcb_PrimitiveLine.delete(hit) : false };
});

await step("move C3", async () => {
  await eda.pcb_PrimitiveComponent.modify(C3_ID, NEW_POS);
  return "modified";
});

await step("fix via holes", async () => {
  const vias = await eda.pcb_PrimitiveVia.getAll();
  const done = [];
  for (const via of vias || []) {
    if ((via.net || "") !== "GND" || via.holeDiameter >= MIN_HOLE_MIL) continue;
    await eda.pcb_PrimitiveVia.modify(via.primitiveId, VIA_FIX);
    done.push({ x_mm: +(via.x * 0.0254).toFixed(2), y_mm: +(via.y * 0.0254).toFixed(2),
                was: `${via.holeDiameter}/${via.diameter}` });
  }
  return done;
});

await step("refill ground pours", async () => {
  const pours = await eda.pcb_PrimitivePour.getAll();
  const done = [];
  for (const pour of pours || []) {
    if ((pour.net || "") !== "GND") continue;
    done.push({ pour: pour.pourName, ok: !!(await pour.rebuildCopperRegion()) });
  }
  return done;
});

await step("save", () => eda.pcb_Document.save());

await step("read back", async () => {
  const comps = await eda.pcb_PrimitiveComponent.getAll();
  const c3 = (comps || []).find((c) => c.primitiveId === C3_ID);
  const vias = await eda.pcb_PrimitiveVia.getAll();
  const small = (vias || []).filter((v) => (v.net || "") === "GND" && v.holeDiameter < 7.9)
    .map((v) => ({ x: v.x, y: v.y, hole: v.holeDiameter }));
  return {
    c3: c3 ? { x_mm: +(c3.x * 0.0254).toFixed(3), y_mm: +(c3.y * 0.0254).toFixed(3), rotation: c3.rotation } : "not found",
    lines: (await eda.pcb_PrimitiveLine.getAll()).length,
    vias: (vias || []).length,
    gnd_vias_below_7_9_mil: small,
  };
});

return out;
