// Build HL_NFC_COIL_E16: the on-board NFC spiral as footprint copper, with the
// two terminals as pads. Per Altium's knowledge base this is the net tie shape -
// "planar inductor, coil, spiral antenna pattern ... its two ends are terminated
// by pads to be registered as a Net Tie Component" - so the spiral lives inside
// the footprint and only the pads carry nets.
//
// Local origin is the NFC1 landing pad, so placing this footprint at
// (68.00, 23.00) puts pad 1 on NFC1 and pad 2 on NFC2. The pads are on layer 2
// because that is where the landing pads and the NFC feed sit.
//
// Units: the footprint document declares "mm" on its CANVAS, but the API and the
// stored geometry are mil like the board's. Measured, not assumed - building it in
// millimetres put pad 2 at 3.4 mil from pad 1 instead of 3.4 mm, which is a factor
// of 39.37. Every number below is therefore mil.
const E16 = "2fe84861daa4cba5";
const LIB = "hardware-lab";
const FP = "628b3d578f8845afa16440ca44024c80";

const WIDTH = 9.8425;
const PAD_SIZE = 59.1;   // 1.5 mm, matching the NFC landing pads
const PAD2 = [133.8583, 0.0];
const SEGMENTS = [
 {
  "layer": 2,
  "a": [
   0.0,
   181.1024
  ],
  "b": [
   -291.3386,
   181.1024
  ]
 },
 {
  "layer": 2,
  "a": [
   -291.3386,
   181.1024
  ],
  "b": [
   -291.3386,
   1019.685
  ]
 },
 {
  "layer": 2,
  "a": [
   -291.3386,
   1019.685
  ],
  "b": [
   118.1102,
   1019.685
  ]
 },
 {
  "layer": 2,
  "a": [
   118.1102,
   1019.685
  ],
  "b": [
   118.1102,
   196.8504
  ]
 },
 {
  "layer": 2,
  "a": [
   118.1102,
   196.8504
  ],
  "b": [
   -275.5906,
   196.8504
  ]
 },
 {
  "layer": 2,
  "a": [
   -275.5906,
   196.8504
  ],
  "b": [
   -275.5906,
   1003.937
  ]
 },
 {
  "layer": 2,
  "a": [
   -275.5906,
   1003.937
  ],
  "b": [
   102.3622,
   1003.937
  ]
 },
 {
  "layer": 2,
  "a": [
   102.3622,
   1003.937
  ],
  "b": [
   102.3622,
   212.5984
  ]
 },
 {
  "layer": 2,
  "a": [
   102.3622,
   212.5984
  ],
  "b": [
   -259.8425,
   212.5984
  ]
 },
 {
  "layer": 2,
  "a": [
   -259.8425,
   212.5984
  ],
  "b": [
   -259.8425,
   988.189
  ]
 },
 {
  "layer": 2,
  "a": [
   -259.8425,
   988.189
  ],
  "b": [
   86.6142,
   988.189
  ]
 },
 {
  "layer": 2,
  "a": [
   86.6142,
   988.189
  ],
  "b": [
   86.6142,
   228.3465
  ]
 },
 {
  "layer": 2,
  "a": [
   86.6142,
   228.3465
  ],
  "b": [
   -244.0945,
   228.3465
  ]
 },
 {
  "layer": 2,
  "a": [
   -244.0945,
   228.3465
  ],
  "b": [
   -244.0945,
   972.4409
  ]
 },
 {
  "layer": 2,
  "a": [
   -244.0945,
   972.4409
  ],
  "b": [
   70.8661,
   972.4409
  ]
 },
 {
  "layer": 2,
  "a": [
   70.8661,
   972.4409
  ],
  "b": [
   70.8661,
   244.0945
  ]
 },
 {
  "layer": 2,
  "a": [
   70.8661,
   244.0945
  ],
  "b": [
   -228.3465,
   244.0945
  ]
 },
 {
  "layer": 2,
  "a": [
   -228.3465,
   244.0945
  ],
  "b": [
   -228.3465,
   956.6929
  ]
 },
 {
  "layer": 2,
  "a": [
   -228.3465,
   956.6929
  ],
  "b": [
   55.1181,
   956.6929
  ]
 },
 {
  "layer": 2,
  "a": [
   55.1181,
   956.6929
  ],
  "b": [
   55.1181,
   259.8425
  ]
 },
 {
  "layer": 2,
  "a": [
   55.1181,
   259.8425
  ],
  "b": [
   -212.5984,
   259.8425
  ]
 },
 {
  "layer": 2,
  "a": [
   -212.5984,
   259.8425
  ],
  "b": [
   -212.5984,
   940.9449
  ]
 },
 {
  "layer": 2,
  "a": [
   -212.5984,
   940.9449
  ],
  "b": [
   39.3701,
   940.9449
  ]
 },
 {
  "layer": 2,
  "a": [
   39.3701,
   940.9449
  ],
  "b": [
   39.3701,
   275.5906
  ]
 },
 {
  "layer": 2,
  "a": [
   0.0,
   0.0
  ],
  "b": [
   0.0,
   181.1024
  ]
 },
 {
  "layer": 1,
  "a": [
   39.3701,
   275.5906
  ],
  "b": [
   39.3701,
   102.3622
  ]
 },
 {
  "layer": 1,
  "a": [
   39.3701,
   102.3622
  ],
  "b": [
   86.6142,
   55.1181
  ]
 },
 {
  "layer": 1,
  "a": [
   86.6142,
   55.1181
  ],
  "b": [
   133.8583,
   55.1181
  ]
 },
 {
  "layer": 2,
  "a": [
   133.8583,
   55.1181
  ],
  "b": [
   133.8583,
   0.0
  ]
 }
];
const VIAS = [
 {
  "x": 39.3701,
  "y": 275.5906
 },
 {
  "x": 133.8583,
  "y": 55.1181
 }
];
const VIA_DIAMETER = 12;      // mil, the board's standard via
const VIA_HOLE = 8;           // mil; the floor is 7.9

const out = { steps: [], errors: [] };
const step = async (name, fn) => {
  try { out.steps.push({ name, ok: true, value: await fn() }); }
  catch (err) { out.steps.push({ name, ok: false, error: String(err && err.message ? err.message : err) }); }
};

await step("open footprint", async () => {
  await eda.lib_Footprint.openInEditor(FP, LIB);
  await new Promise((r) => setTimeout(r, 3000));
  const i = await eda.dmt_SelectControl.getCurrentDocumentInfo();
  return i ? `${i.uuid}/${i.documentType}` : "null";
});

await step("clear any existing copper", async () => {
  const lines = (await eda.pcb_PrimitiveLine.getAll()) || [];
  const vias = (await eda.pcb_PrimitiveVia.getAll()) || [];
  const pads = (await eda.pcb_PrimitivePad.getAll()) || [];
  if (lines.length) await eda.pcb_PrimitiveLine.delete(lines.map((l) => l.primitiveId));
  if (vias.length) await eda.pcb_PrimitiveVia.delete(vias.map((v) => v.primitiveId));
  if (pads.length) await eda.pcb_PrimitivePad.delete(pads.map((p) => p.primitiveId));
  return { lines: lines.length, vias: vias.length, pads: pads.length };
});

await step("create the two terminal pads", async () => {
  const p1 = await eda.pcb_PrimitivePad.create(2, "1", 0, 0, 0, ["RECT", PAD_SIZE, PAD_SIZE, 0], "");
  const p2 = await eda.pcb_PrimitivePad.create(2, "2", PAD2[0], PAD2[1], 0, ["RECT", PAD_SIZE, PAD_SIZE, 0], "");
  if (!p1 || !p2) out.errors.push("a pad came back undefined");
  return { pad1: !!p1, pad2: !!p2 };
});

await step("create the spiral", async () => {
  let made = 0;
  for (const s of SEGMENTS) {
    const l = await eda.pcb_PrimitiveLine.create("", s.layer, s.a[0], s.a[1], s.b[0], s.b[1], WIDTH);
    if (l) made += 1;
  }
  if (made !== SEGMENTS.length) out.errors.push(`created ${made} of ${SEGMENTS.length} segments`);
  return `${made}/${SEGMENTS.length}`;
});

await step("create the two crossover vias", async () => {
  let made = 0;
  for (const v of VIAS) {
    const r = await eda.pcb_PrimitiveVia.create("", v.x, v.y, VIA_HOLE, VIA_DIAMETER);
    if (r) made += 1;
  }
  return `${made}/${VIAS.length}`;
});

await step("save", () => eda.pcb_Document.save());

await step("read back", async () => {
  const lines = (await eda.pcb_PrimitiveLine.getAll()) || [];
  const vias = (await eda.pcb_PrimitiveVia.getAll()) || [];
  const pads = (await eda.pcb_PrimitivePad.getAll()) || [];
  return { lines: lines.length, vias: vias.length, pads: pads.length,
           padSample: pads[0] ? { num: pads[0].padNumber, x: pads[0].x, y: pads[0].y, shape: pads[0].pad } : null,
           lineSample: lines[0] ? { startX: lines[0].startX, endX: lines[0].endX, width: lines[0].width, layer: lines[0].layer } : null };
});

await step("restore E16", async () => {
  const i = await eda.dmt_SelectControl.getCurrentDocumentInfo();
  if (i && i.tabId && i.uuid !== E16) await eda.dmt_EditorControl.closeDocument(i.tabId);
  await eda.dmt_EditorControl.openDocument(E16);
  return "restored";
});
return out;
