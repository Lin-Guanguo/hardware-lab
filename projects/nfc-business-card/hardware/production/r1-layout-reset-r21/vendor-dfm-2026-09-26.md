# R21：嘉立创线上 DFM 状态

## 当前确定方案

R21 的 [Gerber](NFC-Card-R1-Layout-Reset-R21-USB-CC2-gerber.zip)、[BOM](NFC-Card-R1-Layout-Reset-R21-USB-CC2-bom.csv)、[CPL](NFC-Card-R1-Layout-Reset-R21-USB-CC2-cpl.csv)已从同一保存、重开工程导出并通过[本地制造核对](../../records/r1-layout-reset-r21-manufacturing.json)。2026-09-26 在登录的 `www.jlc-dfm.com` 上传 R21 Gerber；网站显示“解析完成”，“我的文件”出现同名 ZIP，时间 **02:11:41**。点击“进入 DFM 分析界面”及文件行“打开”均未进入 R21 结果页；**没有可核对的 R21 PCB／SMT 危险明细或报价**。BOM/CPL 尚未在 R21 任务中上传。没有下单或付款。

[R20](../r1-layout-reset-r20/vendor-dfm-2026-09-26.md)也已上传 Gerber 却未能打开结果页；[R18B](../r1-layout-reset-r18b/vendor-dfm-2026-09-26.md)仍是最近可读取的线上 PCB／SMT 对照，不能代替 R21 检查。再次操作时从“我的文件”中的 R21 ZIP 进入对应分析任务，核对 0.8 mm 板厚、危险明细，再上传 BOM/CPL 检查匹配和 J1/U1 装配。页面默认表面处理与颜色不是本板工艺选择。
