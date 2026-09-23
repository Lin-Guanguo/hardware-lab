// Open the E16 holder project and prove its identity from board content.
//
// software.md: after openProject() the window title and prjPath may still point
// at the previous project, and the API-reported project name must not be used to
// decide which file is being edited. So identity is established by fingerprint:
// the committed snapshot is 56 components / 244 pads / 798 copper segments /
// 168 vias, and a mismatch means stop, do not write.
//
// Read-only. Nothing is saved.
//
// Run: node scripts/eda-exec-wait.mjs scripts/eda-open-e16.js 120000

const PROJECT_UUID = "a68e904fd0949ac3"; // NFC-Business-Card-84x52-E14-Battery-Layout
const E16_PAGE_UUID = "2fe84861daa4cba5";
const EXPECT = { components: 56, pads: 244, lines: 798, vias: 168 };

const out = { steps: [] };
const step = async (name, fn) => {
  try {
    const value = await fn();
    out.steps.push({ name, ok: true, value });
    return value;
  } catch (err) {
    out.steps.push({ name, ok: false, error: String(err && err.message ? err.message : err) });
    return undefined;
  }
};

// Resolve the full uuid: the DMT list returns complete hashes.
let fullUuid = PROJECT_UUID;
await step("resolve uuid", async () => {
  const list = (await eda.dmt_Project.getAllProjectsUuid(
    "/Users/linguanguo/dev/hardware-lab/eda", "", "Personal")) || [];
  const match = list.find((u) => String(typeof u === "string" ? u : u.uuid).startsWith(PROJECT_UUID));
  if (match) fullUuid = typeof match === "string" ? match : match.uuid;
  return fullUuid.slice(0, 24);
});

await step("openProject", async () => {
  await eda.dmt_Project.openProject(fullUuid);
  return "requested";
});

// The project has to finish loading before any primitive call is meaningful.
await step("wait for load", async () => {
  for (let i = 0; i < 20; i += 1) {
    await new Promise((r) => setTimeout(r, 1500));
    const proj = await eda.dmt_Project.getCurrentProjectInfo();
    const pcbs = await eda.dmt_Pcb.getAllPcbsInfo();
    if (proj && Array.isArray(pcbs) && pcbs.length) {
      return { waitedMs: (i + 1) * 1500, project: proj.friendlyName || proj.name, pcbs: pcbs.length };
    }
  }
  return "timed out waiting for project/pcbs";
});

await step("open E16 page", async () => {
  await eda.dmt_EditorControl.openDocument(E16_PAGE_UUID);
  await new Promise((r) => setTimeout(r, 2500));
  return "opened";
});

await step("fingerprint", async () => {
  const [comps, pads, lines, vias] = await Promise.all([
    eda.pcb_PrimitiveComponent.getAll(),
    eda.pcb_PrimitivePad.getAll(),
    eda.pcb_PrimitiveLine.getAll(),
    eda.pcb_PrimitiveVia.getAll(),
  ]);
  const actual = {
    components: Array.isArray(comps) ? comps.length : null,
    pads: Array.isArray(pads) ? pads.length : null,
    lines: Array.isArray(lines) ? lines.length : null,
    vias: Array.isArray(vias) ? vias.length : null,
  };
  const match = Object.keys(EXPECT).every((k) => actual[k] === EXPECT[k]);
  out.actual = actual;
  out.expected = EXPECT;
  out.identityConfirmed = match;
  return match ? "MATCH" : `MISMATCH: expected ${JSON.stringify(EXPECT)}`;
});

return out;
