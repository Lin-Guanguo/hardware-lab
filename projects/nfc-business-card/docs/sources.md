---
description: NFC 名片技术调研的原始来源、版本与证据边界
last_updated: 2026-09-21
---

# 来源与核对记录

早期条目访问于 **2026-09-17**；新增连接器图纸及 PCBA 供货快照访问于 **2026-09-20**，具体日期见下载清单与[候选 BOM](../hardware/candidate-bom.md)。选型结论是结合用户需求的工程判断，不是厂商对整机的保证。动态网页的库存、版本、工艺能力在采购/安装前重核。

2026-09-21 新增 [FH12A 上接触插座原厂图纸](https://www.hirose.com/en/product/document?clcode=CL0586-0555-2-55&documentid=0000906835&documenttype=2DDrawing&lang=en&productname=FH12A-24S-0.5SH%2855%29&series=FH12)，归档 `downloads/fh12a-24s-drawing.pdf` 并核 SHA-256；两页均渲染检查，重点核本体、公差、开盖高度、插入段及推荐焊盘。与屏幕触点、库锚脚的差异见[84 × 52 排布记录](../hardware/pcb-84x52.md)。另核对 [TI TPD2EUSB30 数据手册](https://www.ti.com/lit/ds/symlink/tpd2eusb30.pdf)选择数据 ESD 空间候选，未完成电路连接或生产选型。

## 芯片与协议

- [Nordic nRF52832 NFCT](https://docs.nordicsemi.com/r/bundle/ps_nrf52832/page/nfc.html)：NFC-A listen、106 kbps、场检测与天线连接。
- [Nordic NFC 文档](https://nrfconnectdocs.nordicsemi.com/ncs/latest/nrf/protocols/nfc/index.html)：Type 2/Type 4、NDEF 协议栈。
- [System OFF 官方样例文档](https://nrfconnectdocs.nordicsemi.com/ncs/latest/nrf/samples/nfc/system_off/README.html)：场唤醒与重新初始化；latest 是开发文档，不用作版本锁。
- [v3.4.0 system_off 源码](https://github.com/nrfconnect/sdk-nrf/tree/v3.4.0/samples/nfc/system_off)、[record_text](https://github.com/nrfconnect/sdk-nrf/tree/v3.4.0/samples/nfc/record_text)：固定版本的开发起点；本轮核对了目录、tag 和 sample.yaml，没有导入或构建代码。
- [Nordic 天线调谐 NWP-026](https://docs.nordicsemi.com/r/bundle/nwp_026/page/wp/nwp_026/nwp_026_intro.html)：最终线圈需根据装配实测调谐。
- [Apple 背景读卡](https://developer.apple.com/documentation/corenfc/adding-support-for-background-tag-reading)：支持的 URI、机型/系统条件和通知交互。
- [NXP NTAG I²C Plus 数据手册](https://www.nxp.com/docs/en/data-sheet/NT3H2111_2211.pdf)、[勘误](https://www.nxp.com/docs/en/errata/ES_NT3H2111_2211.pdf)：无电可读备选；实际采用时一并审查勘误。
- [ST 动态 NFC 标签](https://www.st.com/en/nfc/st25-dynamic-nfc-tags.html)：Type 5 备选路线。

## 已下载的原厂文档

本地文件均相对本项目根目录。大小为十进制 MB。完整 URL、最终 URL、字节数和 SHA-256 见 [机器可读清单](download_manifest.json)。PDF 原始字节未修改，文本和页面渲染是本地缓存。

| 文件 | 文档 | 本轮重点核对 |
| --- | --- | --- |
| `downloads/raytac_mdbt42v_rev_l.pdf` | Raytac Rev L，2023-07-12，约 3.87 MB | 第 7 页尺寸与公差、第 13 页 NFC 引脚；尺寸图已目视核对 |
| `downloads/raytac_mdbt50q_rev_l.pdf` | Raytac Rev L，2023-05-24，约 5.64 MB | 第 8 页 PCB 天线版尺寸图已目视核对 |
| `downloads/gdey0154d67.pdf` | Good Display 原厂资料，由 M5Stack CDN 镜像，约 9.68 MB | 第 7 页玻璃/FPC 图已目视核对；镜像不替代采购批次交付图 |
| `downloads/js1300.pdf` | E-Switch JS1300 单页资料，约 0.15 MB | 高度、触点拓扑和安装外形已目视核对 |
| `downloads/bq25186.pdf` | TI SLUSF69A，Rev A，约 2.09 MB | 电源路径、电流配置、复位值、封装尺寸 |
| `downloads/tps7a02.pdf` | TI TPS7A02，约 3.41 MB | 输入输出范围、静态电流、DBV 最大高度 |
| `downloads/usb4500-drawing.pdf` | GCT USB4500，A1，约 0.16 MB；LCSC 原厂图纸镜像 | 第 1 页主体高度、推荐板厚及数据触点，已目视核对 |
| `downloads/fh12-24s-drawing.pdf` | Hirose FH12，约 1.05 MB；原厂下载 | 第 1 页底接触与高度公差，已目视核对 |
| `downloads/gdeh0154e01.pdf` | Good Display v1.0 / 2026-03-20，约 3.76 MB | 第 5–7、9–10 页尺寸、引脚、BUSY 与 TBD 功耗，已目视核对 |
| `downloads/despi-e01-guide.pdf` | DESPI-E01 v1.0 / 2026-05-27，约 0.81 MB | BUSY 极性及上接触/双面接触插座说明，已目视核对 |
| `downloads/despi-e01-schematic.pdf` | DESPI-E01 官方单页电路图，约 0.47 MB | 升压外围、FPC 与屏幕规格差异，已目视核对，未完成逐网络审核 |
| `downloads/e6-design-notice-cn.pdf` | 官方 E6 通用设计须知，约 2.82 MB | 第 3 页连续翻页间隔建议，已目视核对，不当作单次刷新耗时 |

另下载 `downloads/gdeh0154e01-esp32.zip`（约 37.61 MB），通过 ZIP CRC 检查，静态读取 Arduino/ESP-IDF 驱动和说明；未执行、构建或烧录。文件校验值固定本轮读取的版本，详细发现见[六色屏评估](gdeh0154e01-evaluation.md)。

本轮另复核 Raytac Rev L 第 14–17、35、40 页接口和供电、Good Display 旧图第 7/33 页机械及外围、BQ25186 默认寄存器。屏幕官网当前版下载未成功，旧图标签差异作为阻塞项保留，见[系统设计](../hardware/system-design.md)。

仅用于本地研究，厂商保留原文版权；缓存目录被 Git 忽略。未来导入固件源码另记录上游许可证和具体 revision。

## 屏幕、按键、电池与电源

- [GDEY0154D67](https://www.good-display.com/product/388.html)、[GDEY0213B74](https://www.good-display.com/product/391.html)：屏幕产品规格；部分产品页访问不稳定，以缓存原厂图纸交叉核对。
- [GDEW0102T4](https://www.good-display.com/product/207.html)、[GDEW0102I4FC](https://www.good-display.com/product/341.html)：停产小屏与柔性小屏的排除/备选原因。
- [ALPS SKQG 系列](https://tech.alpsalpine.com/c/products/category/tact-switch/sub/02/series/skqg/)：当前目录中的 1.5 mm 型号与供货状态分类；并未确认零售现货。
- [PowerStream 薄电池目录](https://www.powerstream.com/thin-lithium-ion.htm)：容量与目录尺寸、工程样品线索。只是供应商目录，不是完整包体交付图。
- [EEMB 尺寸编码说明](https://www.eemb.com/faq-6)：型号数字不等于包含保护板和引线的最大包络。
- [BQ25186](https://www.ti.com/product/BQ25186)、[TPS7A02](https://www.ti.com/product/TPS7A02)、[MCP73831](https://www.microchip.com/en-us/product/mcp73831)：电源候选与功能差异。

## 制造、外壳与粘接

- [JLCPCB PCB 能力](https://jlcpcb.com/capabilities/Capab)：板厚范围和薄板公差。
- [JLCPCB PCBA 能力](https://jlcpcb.com/capabilities/pcb-assembly-capabilities)：经济型板厚与标准型加工限制；不代表实际设计已通过 DFM。
- [JLC3DP 8001 树脂](https://jlc3dp.com/help/article/photosensitive-8001-resin)：建议壁厚 >0.8 mm、尺寸公差、透明/半透明后处理。
- [3M 低表面能塑料粘接](https://www.3m.com/3M/en_US/bonding-and-assembly-us/applications/material-bonding/lse-plastics/)、[300LSE 薄胶带说明](https://www.3m.com/3M/en_US/bonding-and-assembly-us/double-sided-tape/thin-bonding-tape/)：PP 粘接不能假定普通胶通用。
- [Henkel TECHNOMELT AS 5303](https://next.henkel-adhesives.com/uk/en/products/industrial-adhesives/central-pdp.html/technomelt-as-5303/BP000000073809.html)：存在针对 PP/聚烯烃的专用热熔胶；未针对用户卡套试验。
- 用户提供的卡套截图：2026-09-17，选项标注“容量 97 × 66 × 3 mm”。没有链接/正式尺寸图，材质和尺寸定义未独立确认；未把截图商品的宣传值当作机械设计值。

## 现成设备与软件

- [XIAO NFC 官方指南](https://wiki.seeedstudio.com/XIAO-BLE-Sense-NFC-Usage/)、[XIAO 入门与充电](https://wiki.seeedstudio.com/XIAO_BLE/)、[EN04 USB 下载](https://wiki.seeedstudio.com/EN04_opendisplay/)：USB 需求追加后核对现成板编程流程、NFC 例程与 Plus 引脚配置；没有执行其中的烧录或配置修改。
- [nRF52840 原厂特性](https://www.nordicsemi.com/Products/nRF52840/Modules)、[nRF52840 DK](https://www.nordicsemi.com/Products/Development-hardware/nRF52840-DK)：USB 与 NFC 主路线。
- [Adafruit nRF52 Bootloader](https://github.com/adafruit/Adafruit_nRF52_Bootloader)、[NCS v3.4.0 USB CDC 恢复](https://github.com/nrfconnect/sdk-nrf/blob/v3.4.0/doc/nrf/app_dev/bootloaders_dfu/mcuboot_serial_recovery.rst)：可复用下载实现，未导入代码。
- [GCT USB 2.0 Type-C](https://gct.co/news/16pin-usb-type-c)、[沉板选型](https://gct.co/usb-connector/list?mountposition=Mid+mount&style=%2CType+C&version=%2C2.0)：数据型 USB 座候选，不代表已冻结具体料号或高度。
- [EN04](https://wiki.seeedstudio.com/epaper_EN04/)、[T-Echo](https://github.com/Xinyuan-LilyGO/T-Echo)、[T-Echo Card](https://lilygo.cc/products/t-echo-card)、[Pixl.js](https://www.espruino.com/Pixl.js)、[L-ink Card](https://github.com/peng-zhihui/L-ink_Card)：参考设备/开源设计，没有一项在本轮完成目标整机验证。
- [KiCad macOS](https://www.kicad.org/download/macos/)：页面列稳定版 10.0.6。
- [FreeCAD 1.1.3 发布](https://github.com/FreeCAD/FreeCAD/releases/tag/1.1.3)：官方 macOS arm64 包。
- [Nordic 安装说明](https://nrfconnectdocs.nordicsemi.com/ncs/latest/nrf/installation/install_ncs.html)、[v3.4.0 发布](https://github.com/nrfconnect/sdk-nrf/releases/tag/v3.4.0)：SDK Manager 流程与固定版本候选。

## 证据边界

本轮已核对网页、数据手册和若干官方源码元数据；未使用商品购买、正式询价或供应商沟通工具。封装资料仍需在冻结设计时与实际订货后缀和版本一致。所有“推荐”“目标”“预算”“预留”“假定”均为本项目设计判断，不等同于实测规格。
