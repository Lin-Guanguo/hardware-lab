// EasyEDA-side payload that exports the E16 board plus its component models as
// a STEP file, which check-e16-board-fit.py compares against the printed
// shells. Run through the local bridge:
//
//   node scripts/eda-exec-wait.mjs scripts/eda-export-e16-3d.js 120000
//
// sys_FileSystem.saveFile() writes the file into ~/Downloads under a hidden
// ".cn.lceda.pro.*" name and keeps flushing for a few seconds after the call
// returns, so wait until the byte count settles before copying it out.
const E16_PAGE_UUID = "2fe84861daa4cba5";

await eda.dmt_EditorControl.openDocument(E16_PAGE_UUID);
await new Promise((r) => setTimeout(r, 2000));

const file = await eda.pcb_ManufactureData.get3DFile("NFC-E16-3D", "step", ["Component Model"], "Outfit", true);
if (!file) return { ok: false, error: "get3DFile returned null" };
await eda.sys_FileSystem.saveFile(file);
return { ok: true, name: file.name, bytes: file.size };
