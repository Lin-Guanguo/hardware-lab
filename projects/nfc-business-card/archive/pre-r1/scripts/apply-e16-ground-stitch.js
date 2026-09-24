// Apply the E16 ground-stitching plan: tie the ESD ground pads to the ground
// pour and add vias to the bottom pour.
//
// Generated from hardware/e16-ground-stitch-plan.json, which
// plan-e16-ground-stitch.py produced and check-proposed-route.py validated with
// zero violations. Coordinates here are mil, matching the snapshot and the API;
// the plan is in mm.
//
// A pour is a computed fill, so the new vias stay isolated until the copper
// region is rebuilt. That is why the refill step is not optional.
//
// Run: node scripts/eda-exec-wait.mjs scripts/apply-e16-ground-stitch.js 300000

const E16_PAGE_UUID = "2fe84861daa4cba5";

const VIAS = [
  {
    "net": "GND",
    "x": 2862.2047,
    "y": 637.7953,
    "hole": 12.0,
    "dia": 24.0,
    "mm": "0.61/0.305"
  },
  {
    "net": "GND",
    "x": 2862.2047,
    "y": 669.2913,
    "hole": 12.0,
    "dia": 24.0,
    "mm": "0.61/0.305"
  },
  {
    "net": "GND",
    "x": 2856.2992,
    "y": 564.9606,
    "hole": 7.8,
    "dia": 11.8,
    "mm": "0.3/0.2"
  },
  {
    "net": "GND",
    "x": 2875.9843,
    "y": 576.7717,
    "hole": 7.8,
    "dia": 11.8,
    "mm": "0.3/0.2"
  }
];

const TRACKS = [
  {
    "net": "GND",
    "layer": 1,
    "width": 15.748,
    "a": [
      2877.9528,
      653.5433
    ],
    "b": [
      2864.1732,
      629.685
    ]
  },
  {
    "net": "GND",
    "layer": 1,
    "width": 11.811,
    "a": [
      2877.9528,
      653.5433
    ],
    "b": [
      2862.2047,
      637.7953
    ]
  },
  {
    "net": "GND",
    "layer": 1,
    "width": 11.811,
    "a": [
      2877.9528,
      653.5433
    ],
    "b": [
      2862.2047,
      669.2913
    ]
  },
  {
    "net": "GND",
    "layer": 1,
    "width": 9.8425,
    "a": [
      2860.2362,
      580.7087
    ],
    "b": [
      2856.2992,
      564.9606
    ]
  },
  {
    "net": "GND",
    "layer": 1,
    "width": 9.8425,
    "a": [
      2860.2362,
      580.7087
    ],
    "b": [
      2875.9843,
      576.7717
    ]
  }
];

await eda.dmt_EditorControl.openDocument(E16_PAGE_UUID);
await new Promise((r) => setTimeout(r, 2500));

const before = {
  lines: (await eda.pcb_PrimitiveLine.getAll()).length,
  vias: (await eda.pcb_PrimitiveVia.getAll()).length,
};

const created = { vias: [], tracks: [], errors: [] };

for (const v of VIAS) {
  try {
    const made = await eda.pcb_PrimitiveVia.create(v.net, v.x, v.y, v.hole, v.dia);
    if (!made) created.errors.push(`via (${v.x}, ${v.y}) returned undefined`);
    else created.vias.push({ id: made.primitiveId, x: v.x, y: v.y, size: v.mm });
  } catch (err) {
    created.errors.push(`via (${v.x}, ${v.y}): ${String(err && err.message ? err.message : err)}`);
  }
}

for (const t of TRACKS) {
  try {
    const made = await eda.pcb_PrimitiveLine.create(
      t.net, t.layer, t.a[0], t.a[1], t.b[0], t.b[1], t.width);
    if (!made) created.errors.push(`track (${t.a})-(${t.b}) returned undefined`);
    else created.tracks.push({ id: made.primitiveId, net: t.net, width: t.width });
  } catch (err) {
    created.errors.push(`track (${t.a})-(${t.b}): ${String(err && err.message ? err.message : err)}`);
  }
}

// Rebuild the copper fill of every ground pour so the new vias are connected.
const refilled = [];
try {
  const pours = await eda.pcb_PrimitivePour.getAll();
  for (const pour of pours || []) {
    if ((pour.net || "") !== "GND") continue;
    const poured = await pour.rebuildCopperRegion();
    refilled.push({
      pour: pour.pourName,
      layer: pour.layer,
      fills: poured && Array.isArray(poured.pourFills) ? poured.pourFills.length : null,
    });
  }
} catch (err) {
  created.errors.push(`refill: ${String(err && err.message ? err.message : err)}`);
}

const saved = await eda.pcb_Document.save();

const after = {
  lines: (await eda.pcb_PrimitiveLine.getAll()).length,
  vias: (await eda.pcb_PrimitiveVia.getAll()).length,
};

return {
  before,
  after,
  delta: { lines: after.lines - before.lines, vias: after.vias - before.vias },
  expected: { lines: TRACKS.length, vias: VIAS.length },
  refilled,
  saved,
  created,
};
