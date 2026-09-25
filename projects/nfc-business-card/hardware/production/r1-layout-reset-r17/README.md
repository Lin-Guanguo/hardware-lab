# R17：USB4500 焊盘基准诊断

## 当前确定方案

[R17 独立原生工程](../../../../../eda/NFC-Card-R1-Layout-Reset-R17.eprj2)用于核对 J1 封装焊盘、板框和贴片模型的共同基准，**不可下单**。它继承 R16 的 9.20 mm USB 缺口，仅将自制 `USB4500 E20` 封装中 12 个 SMT 焊盘的局部中心纵坐标从 **113.2 mil 改为 101.4 mil**（约 0.30 mm）；四个 0.60 mm 镀铜槽、器件参考点、走线、过孔与其他器件未移动。101.4 mil 来自同一导出项目内另一份 USB4500 库封装，仍需与 [GCT 原厂图纸](https://gct.co/connector/usb4500)按相同机械基准完成逐尺寸对照，不能仅以网页焊脚重叠比例认定正确。

R17 由修改后的 `.epro2` 导入嘉立创 EDA、保存为新的 `.eprj2` 并关闭重开；重开后 12 个焊盘的新坐标仍在。此步骤解决了 R15 临时位移无法持久保存的问题，但带来 **12 条 J1 焊盘到 USB 缺口边缘的原生 DRC 错误**。网页 PCB DFM 同样报 12 条焊盘距外型线危险。GCT 推荐图中的焊盘与缺口边界关系可能属于中置连接器的特殊结构；仅凭图示尚不能把该异常判作可接受。需要原厂尺寸叠图及供应商针对实际板边加工的确认，或改用符合常规板边间距的连接器／机械方案。

## 同版文件与检查

- [Gerber ZIP](NFC-Card-R1-Layout-Reset-R17-gerber.zip)、[BOM](NFC-Card-R1-Layout-Reset-R17-bom.csv)、[CPL](NFC-Card-R1-Layout-Reset-R17-cpl.csv)从重开后的同一工程导出。BOM 29 组、CPL 66 个位号；R17 J1 的 CPL 参考点仍为 X=78.829 mm，元件包络中点从 R16 的 X=78.679 mm 变为 X=78.829 mm，需单独核对贴片模型坐标。
- [原生 DRC](../../records/r1-layout-reset-r17-native-drc.json)：12 条，全部为 J1 的 `Board Outline to SMD Pad`。不是可交付 DRC 0 状态。
- [独立铜箔连通](../../records/r1-layout-reset-r17-copper-check.json)通过；[异网铜间距／同网孔到焊盘](../../records/r1-layout-reset-r17-clearance-audit.json)中离散异网铜对象 <0.15 mm 为 0，同网过孔孔边到焊盘 <0.10 mm 有 3 颗不同过孔；[板框／槽](../../records/r1-layout-reset-r17-profile-check.json)几何通过。167 个过孔的导出钻孔约 0.30 mm、最小径向孔环 0.1016 mm。以上检查不能代替焊盘到锣边加工检查。
- [嘉立创线上 PCB／SMT DFM](vendor-dfm-2026-09-25.md)是同版上传结果，不构成供应商接单或可制造确认。

## 下一步

先完成 J1 原厂焊盘、开槽、缺口和 CPL 模型按共同基准的对照。若原厂推荐结构确需焊盘紧邻铣边，应将板边铜加工与贴装作为**一个明确的供应商例外**核实，而非继续移动焊盘凑网页分数；若普通工艺不接受，应先评估更易制造的 USB-C 连接器及外壳配合。USB 扇出局部重布应在连接器封装和机械基准确定后进行，保留 ESD 顺序和去耦关系。
