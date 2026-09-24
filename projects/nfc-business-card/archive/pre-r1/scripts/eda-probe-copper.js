// Discover the real shape of the keep-out, copper-border and copper-fill
// objects on the E16 sheet before the snapshot exporter is changed to read
// them.
//
// Why this exists: the first exporter assumed a region exposes `polygon` and
// `rule`, so both came back undefined and JSON.stringify silently dropped them.
// The API reference shows the real names are `complexPolygon` (an IPCB_Polygon
// object with getSource()/discretize(), not a plain array) and `ruleType`.
// Probing first, instead of guessing a third time, is the point.
//
// Run through the local bridge:
//   node scripts/eda-exec-wait.mjs scripts/eda-probe-copper.js 60000 > /tmp/probe.json

const E16_PAGE_UUID = "2fe84861daa4cba5";

await eda.dmt_EditorControl.openDocument(E16_PAGE_UUID);
await new Promise((r) => setTimeout(r, 2000));

// Describe a value without assuming anything about it.
const describe = (v, depth = 0) => {
  if (v === null) return "null";
  if (v === undefined) return "undefined";
  if (typeof v === "function") return "function";
  if (typeof v !== "object") return `${typeof v}:${String(v).slice(0, 40)}`;
  if (Array.isArray(v)) {
    return v.length === 0 ? "array[0]" : `array[${v.length}] of ${describe(v[0], depth)}`;
  }
  const keys = Object.keys(v);
  if (depth >= 2) return `object{${keys.join(",")}}`;
  const inner = keys.map((k) => `${k}=${describe(v[k], depth + 1)}`);
  return `object{${inner.join(", ")}}`;
};

// Try every documented accessor and report which one yields usable geometry.
const sourceOf = (obj) => {
  const out = { tried: [], used: null, value: null };
  if (!obj || typeof obj !== "object") return out;
  for (const name of ["getSource", "getPolygon", "getPoints"]) {
    if (typeof obj[name] === "function") {
      try {
        const r = obj[name]();
        out.tried.push(`${name}() -> ${describe(r)}`);
        if (out.value === null && r !== undefined && r !== null) {
          out.used = name;
          out.value = r;
        }
      } catch (e) {
        out.tried.push(`${name}() threw ${String(e).slice(0, 80)}`);
      }
    }
  }
  if (typeof obj.discretize === "function") {
    try {
      const r = obj.discretize();
      out.tried.push(`discretize() -> ${describe(r)}`);
    } catch (e) {
      out.tried.push(`discretize() threw ${String(e).slice(0, 80)}`);
    }
  }
  // Plain-data fallbacks, in case a future client returns a bare object.
  for (const name of ["polygon", "complexPolygon", "source", "points", "path"]) {
    if (obj[name] !== undefined) out.tried.push(`.${name} = ${describe(obj[name])}`);
  }
  return out;
};

const regions = await eda.pcb_PrimitiveRegion.getAll();
const pours = await eda.pcb_PrimitivePour.getAll();
const poured = await eda.pcb_PrimitivePoured.getAll();

return {
  counts: {
    regions: Array.isArray(regions) ? regions.length : null,
    pours: Array.isArray(pours) ? pours.length : null,
    poured: Array.isArray(poured) ? poured.length : null,
  },
  regions: (regions || []).map((r) => ({
    keys: Object.keys(r),
    shape: describe(r),
    geometry: sourceOf(r.complexPolygon),
    complexPolygonType: typeof r.complexPolygon,
    ruleType: r.ruleType,
    regionName: r.regionName,
    layer: r.layer,
    lineWidth: r.lineWidth,
  })),
  pours: (pours || []).map((p) => ({
    keys: Object.keys(p),
    shape: describe(p),
    geometry: sourceOf(p.complexPolygon),
    net: p.net,
    layer: p.layer,
    pourName: p.pourName,
    pourFillMethod: p.pourFillMethod,
    preserveSilos: p.preserveSilos,
    pourPriority: p.pourPriority,
    lineWidth: p.lineWidth,
  })),
  poured: (poured || []).map((p) => ({
    keys: Object.keys(p),
    shape: describe(p),
    net: p.net,
    layer: p.layer,
    // The filled copper is expected under pourFill[].path; report the shape so
    // the exporter can be written against what is actually returned.
    pourFillShape: describe(p.pourFill),
    pourFillSample: Array.isArray(p.pourFill) && p.pourFill.length
      ? {
          keys: Object.keys(p.pourFill[0]),
          fill: p.pourFill[0].fill,
          lineWidth: p.pourFill[0].lineWidth,
          pathShape: describe(p.pourFill[0].path),
        }
      : null,
  })),
};
