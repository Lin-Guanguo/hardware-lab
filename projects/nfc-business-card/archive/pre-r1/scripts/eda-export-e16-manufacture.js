// EasyEDA-side payload that re-exports the whole E16 manufacturing set
// (Gerber zip, BOM, pick-and-place, assembly PDF) from the current design.
// Every saveFile() call drops one file into ~/Downloads under a hidden
// ".cn.lceda.pro.*" name; wait a few seconds and copy the newest files out
// before running check-e16-manufacture.py.
const E16_PAGE_UUID = "2fe84861daa4cba5";
const REV = "v5";

await eda.dmt_EditorControl.openDocument(E16_PAGE_UUID);
await new Promise((r) => setTimeout(r, 2000));

const out = {};
for (const [key, produce] of [
  ["gerber", () => eda.pcb_ManufactureData.getGerberFile(`NFC-E16-gerber-${REV}`)],
  ["bom", () => eda.pcb_ManufactureData.getBomFile(`NFC-E16-bom-${REV}`, "xlsx")],
  ["cpl", () => eda.pcb_ManufactureData.getPickAndPlaceFile(`NFC-E16-cpl-${REV}`, "xlsx")],
  ["pdf", () => eda.pcb_ManufactureData.getPdfFile(`NFC-E16-board-pdf-${REV}`)],
]) {
  try {
    const file = await produce();
    out[key] = file ? { name: file.name, bytes: file.size } : null;
    if (file) await eda.sys_FileSystem.saveFile(file);
  } catch (e) {
    out[key] = { error: String(e).slice(0, 120) };
  }
}
return out;
