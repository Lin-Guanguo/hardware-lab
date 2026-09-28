const project = await eda.dmt_Project.getCurrentProjectInfo();
const document = await eda.dmt_SelectControl.getCurrentDocumentInfo();
if (project?.friendlyName !== 'NFC-Card-R1-Layout-Reset-R16' || document?.uuid !== '8033127c48771f3b') {
  throw new Error('R16 PCB is not active');
}

const prefix = 'NFC-Card-R1-Layout-Reset-R16';
const layers = [1, 2, 3, 4, 5, 6, 7, 8, 11].map(layerId => ({ layerId, isMirror: false }));
const objects = [
  'Pad', 'Via', 'Track', 'Text', 'Image', 'Dimension', 'BoardOutline',
  'BoardCutout', 'CopperFilled', 'SolidRegion', 'FPCStiffener', 'Line',
  'PlaneZone', 'ComponentProperty', 'ComponentSilkscreen', 'TearDrop',
];
const other = {
  metallicDrillingInformation: true,
  nonMetallicDrillingInformation: true,
  drillTable: false,
  flyingProbeTestingFile: true,
};
const gerber = await eda.pcb_ManufactureData.getGerberFile(
  `${prefix}-gerber`, false, 'mm', { integerNumber: 2, decimalNumber: 6 }, other, layers, objects);
const bom = await eda.pcb_ManufactureData.getBomFile(`${prefix}-bom`, 'csv');
const cpl = await eda.pcb_ManufactureData.getPickAndPlaceFile(`${prefix}-cpl`, 'csv');
if (!gerber || !bom || !cpl) throw new Error('R16 manufacturing export failed');
await eda.sys_FileSystem.saveFile(gerber, `${prefix}-gerber.zip`);
await eda.sys_FileSystem.saveFile(bom, `${prefix}-bom.csv`);
await eda.sys_FileSystem.saveFile(cpl, `${prefix}-cpl.csv`);
return [gerber, bom, cpl].map(file => ({ name: file.name, size: file.size }));
