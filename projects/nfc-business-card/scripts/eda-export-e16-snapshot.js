// EasyEDA-side payload that exports the live E16 sheet into the review snapshot
// consumed by generate-e16-right-mid-svg.py and the enclosure scripts.
//
// Run through the local bridge, then unwrap "result" into
// hardware/e16-right-mid-snapshot.json:
//   node scripts/eda-exec-wait.mjs scripts/eda-export-e16-snapshot.js 60000 > /tmp/snap.json
//
// Coordinates stay in mil, matching the committed snapshot.
const E16_PAGE_UUID = "2fe84861daa4cba5";

await eda.dmt_EditorControl.openDocument(E16_PAGE_UUID);
await new Promise((r) => setTimeout(r, 2000));

const comps = await eda.pcb_PrimitiveComponent.getAll();
const pads = await eda.pcb_PrimitivePad.getAll();
const polylines = await eda.pcb_PrimitivePolyline.getAll();
const regions = await eda.pcb_PrimitiveRegion.getAll();
const strings = await eda.pcb_PrimitiveString.getAll();
const lines = await eda.pcb_PrimitiveLine.getAll();
const vias = await eda.pcb_PrimitiveVia.getAll();
const round = (v) => Math.round(v * 10000) / 10000;

return {
  document: { uuid: E16_PAGE_UUID, name: "E16 Right-Mid USB Study" },
  components: comps.map((c) => ({
    id: c.primitiveId,
    ref: c.designator,
    x: round(c.x),
    y: round(c.y),
    rotation: c.rotation,
    footprint: c.footprint && c.footprint.name,
  })),
  pads: pads.map((p) => ({
    id: p.primitiveId,
    number: p.padNumber,
    x: round(p.x),
    y: round(p.y),
    net: p.net,
    layer: p.layer,
    pad: p.pad,
    // Pad extents are stored in the footprint's local frame, so consumers need
    // the rotation to draw or measure the copper a pad actually covers.
    rotation: p.rotation,
    hole: p.hole,
  })),
  polylines: polylines.map((p) => ({
    id: p.primitiveId,
    layer: p.layer,
    polygon: p.polygon,
    widthMil: p.lineWidth,
  })),
  regions: regions.map((r) => ({
    id: r.primitiveId,
    layer: r.layer,
    rule: r.rule,
    polygon: r.polygon,
  })),
  strings: strings.map((s) => ({
    id: s.primitiveId,
    layer: s.layer,
    x: round(s.x),
    y: round(s.y),
    text: s.text,
    fontSize: s.fontSize,
  })),
  lines: lines.map((l) => ({
    net: l.net,
    layer: l.layer,
    x1: round(l.startX),
    y1: round(l.startY),
    x2: round(l.endX),
    y2: round(l.endY),
    widthMil: round(l.lineWidth),
  })),
  vias: vias.map((v) => ({
    net: v.net,
    x: round(v.x),
    y: round(v.y),
    diameterMil: round(v.diameter),
    holeMil: round(v.holeDiameter),
  })),
};
