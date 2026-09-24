const project=await eda.dmt_Project.getCurrentProjectInfo(); if(project.uuid!=="70e4734137fc61bb6eab88e382fc9a6084e6f570f3396f1502e4f4e9dc906821")throw new Error("Wrong project");
// Export the current R1 PCB into the independent review snapshot.
// Native PCB coordinates remain in mil; poured paths use 10-mil units.
const R1_PAGE_UUID = "8033127c48771f3b";

await eda.dmt_EditorControl.openDocument(R1_PAGE_UUID);
await new Promise((r) => setTimeout(r, 2000));

const comps = await eda.pcb_PrimitiveComponent.getAll();
const pads = await eda.pcb_PrimitivePad.getAll();
const polylines = await eda.pcb_PrimitivePolyline.getAll();
const regions = await eda.pcb_PrimitiveRegion.getAll();
const strings = await eda.pcb_PrimitiveString.getAll();
const lines = await eda.pcb_PrimitiveLine.getAll();
const vias = await eda.pcb_PrimitiveVia.getAll();
const pours = await eda.pcb_PrimitivePour.getAll();
const poured = await eda.pcb_PrimitivePoured.getAll();
const round = (v) => Math.round(v * 10000) / 10000;

// A copper border or region exposes its outline as an IPCB_Polygon object, not
// as a plain array: the source data comes from getSource(). The first version of
// this exporter read `r.polygon`, which does not exist on a region, so the keep-
// out outlines were dropped from the committed snapshot without any error.
const polySource = (value) => {
  if (value === undefined || value === null) return null;
  if (typeof value.getSource === "function") {
    try {
      return value.getSource();
    } catch (err) {
      return null;
    }
  }
  return value;
};

// A poured object carries no net or layer of its own, so the filled regions are
// joined back to their copper border through pourPrimitiveId.
const pourById = new Map((pours || []).map((p) => [p.primitiveId, p]));

return {
  document: { uuid: R1_PAGE_UUID, name: "NFC Card R1" },
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
    ruleType: r.ruleType,
    regionName: r.regionName,
    lineWidth: r.lineWidth,
    complexPolygon: polySource(r.complexPolygon),
  })),
  // Copper borders: the outline a pour was drawn from. Kept separately from the
  // filled result so a checker can tell "declared" from "actually filled".
  pours: (pours || []).map((p) => ({
    id: p.primitiveId,
    net: p.net,
    layer: p.layer,
    pourName: p.pourName,
    pourFillMethod: p.pourFillMethod,
    preserveSilos: p.preserveSilos,
    pourPriority: p.pourPriority,
    lineWidth: p.lineWidth,
    complexPolygon: polySource(p.complexPolygon),
  })),
  // Filled copper: the geometry that actually ends up on the board, including
  // clearances and thermal relief. The EMC ground-plane and return-path checks
  // need this, not the border.
  //
  // Field names verified by scripts/eda-probe-copper.js against the live client:
  // a poured object exposes `pourFills` (plural), each fill carries its outline
  // under `path.complexPolygon`, and the object itself has no net or layer, only
  // `pourPrimitiveId`, which joins back to the copper border.
  poured: (poured || []).map((p) => {
    const border = pourById.get(p.pourPrimitiveId);
    return {
      id: p.primitiveId,
      pourPrimitiveId: p.pourPrimitiveId,
      net: border ? border.net : null,
      layer: border ? border.layer : null,
      pourName: border ? border.pourName : null,
      fills: (Array.isArray(p.pourFills) ? p.pourFills : []).map((f) => ({
        id: f.id,
        fill: f.fill,
        lineWidth: f.lineWidth,
        path: polySource(f.path && f.path.complexPolygon ? f.path.complexPolygon : f.path),
      })),
    };
  }),
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
