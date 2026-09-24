---
description: 使用 ESP32 与 PN532 或 nRF52840 开发板，先验证按键切换 NFC 名片的手机体验
last_updated: 2026-09-25
status: serial_url_switch_verified
---

# NFC 最小桌面实验

用户希望复用此前 ESP32 面包板经验，先确认 NFC 能否达到预期效果，再投入定制生产。这项实验补充现有 PCB/PCBA 主线，不将最终主控改为 ESP32；PN532 已接入 ESP32，SPI 探测、手机读取固定 NDEF 网址和串口临时切换 URI 均通过，实体按键切换待测。

## 已选实验模块

2026-09-20 用户选择淘宝「深圳市优信电子科技有限公司」商品中的 **PN532_NFC模块_蓝板**，并确认该选项排针已焊好。2026-09-23 用户确认到货并提供正反面照片：可见 PCB 天线、已焊双排针、SET0/SET1 开关，以及另一排印有接口名称的未焊孔位。其外观接近 ITEAD PN532 NFC Module，但实物版本和双排针针序尚未独立确认。商品图标称约 79 × 49 mm；不把桌面模块的尺寸计为最终名片设计。

商家提供的说明标注 SPI 为 3.3 V 逻辑，I2C/UART 为 5 V TTL，因此实验优先核对 SPI 接口；它与所引用例程默认 HSU 接口不同，实现时需要调整驱动配置。ITEAD 同外观模块的[原厂规格书](https://www.openimpulse.com/blog/wp-content/uploads/wpsc/downloadables/PN532-NFC-Module-Datasheet.pdf)列出 SPI 模式为 SET0=L、SET1=H；已按所列六线接法完成 SPI 通信验证。照片中带 SCK 等丝印的一排是未焊孔位，不能直接按其位置推断已焊双排针的针序。手机已实测读取固定 NDEF 网址。

桌面测试复用 [Image Oracle 的 ESP32-S3-CAM N16R8](../../image-oracle/README.md)。其现有 `oracle_live` 固件、相机、TFT 和按键已验证；先在 USB 断电后拆下 TFT 的八根连接线并保留相机排线，不需要为拆屏而擦除固件。测试 PN532 与墨水屏转接板时逐个接入、分别构建和烧录测试程序；新程序烧录后原程序不再运行，恢复文件已归档于 Image Oracle 项目。墨水屏裸屏不能直接接 GPIO，必须先确认随附转接板型号、FPC 插入方向和接口丝印。

## PN532 双排针与接线实测

可逐根查看的[PN532 与 ESP32 实物排针接线图](../wiring-diagrams/pn532-esp32-spi.html)已归档。2026-09-24 按该接线表、SET0=L、SET1=H，通过 ESP32-S3-CAM 读取 PN532 版本。

照片左侧的已焊 **2×13 双排针**是 Raspberry Pi 26 针接口；照片左右镜像，不能直接按屏幕上的左右方向数针。[ITEAD 原厂规格书](https://www.openimpulse.com/blog/wp-content/uploads/wpsc/downloadables/PN532-NFC-Module-Datasheet.pdf)第 2 页的板卡图与实物布局相符，[原厂连接示例](https://itead.cc/nextion/raspberry-pi-drives-itead-pn532-nfc-module-with-libnfc/)用 26 芯排线连接 Raspberry Pi。板边标 `SCK / MI / MO/SDA/TX / NSS/SCL/RX / IRQ / RST# / GND / 5V` 的八孔是另一个接口，用户这块尚未焊排针。不要把八孔丝印逐行套到双排针上。

以下按该双排针遵循标准 Raspberry Pi 26 针排布**推导**；六线功能已在用户实物上通过 SPI 探测，但尚未逐针量通断。将板正面 `NFC` 字样摆正、天线置左、双排针置右；原厂图中双排针靠上、靠天线一侧的**方形焊盘为 1 号脚**，相邻靠板外缘的是 2 号脚，往下逐排递增。从背面看会左右反转，因此以双排针自身的方形焊盘定位，不以照片左右定位；顶部另一组单排孔也有方形焊盘，不能拿来当双排针 1 号。若实物看不清方形焊盘或方向不符，先暂停接线。Raspberry Pi 物理针序与 SPI 信号取自[官方 GPIO 文档](https://www.raspberrypi.com/documentation/computers/raspberry-pi.html#spi)。ESP32 的 40/41/42 是拆除 TFT 后释放的原已验证引脚；39 在这块 ESP32 板的排针上，已随 PN532 SPI 探测通过。

| PN532 双排针物理脚 | 预期信号 | ESP32-S3-CAM 丝印 | 状态 |
| --- | --- | --- | --- |
| 2 | 5 V 供电 | `5V` | SPI 探测通过 |
| 6 | GND | `GND` | SPI 探测通过 |
| 19 | MOSI | `41` | SPI 探测通过 |
| 21 | MISO | `39` | SPI 探测通过 |
| 23 | SCK | `40` | SPI 探测通过 |
| 24 | CE0 / NSS | `42` | SPI 探测通过 |

按**双排针从方形焊盘所在的第一排开始**，13 排逐排数如下；`—` 表示本次不接，列位置随正反面观察会互换：

| 从方形焊盘开始的排数 | 方形焊盘所在列：奇数脚 | 相邻列：偶数脚 |
| --- | --- | --- |
| 1 | 1 — | **2 → ESP32 `5V`** |
| 2 | 3 — | 4 — |
| 3 | 5 — | **6 → ESP32 `GND`** |
| 4 | 7 — | 8 — |
| 5 | 9 — | 10 — |
| 6 | 11 — | 12 — |
| 7 | 13 — | 14 — |
| 8 | 15 — | 16 — |
| 9 | 17 — | 18 — |
| 10 | **19 → ESP32 `41`** | 20 — |
| 11 | **21 → ESP32 `39`** | 22 — |
| 12 | **23 → ESP32 `40`** | **24 → ESP32 `42`** |
| 13 | 25 — | 26 — |

只需六根母对母杜邦线；IRQ、RST# 和其余双排针暂不接。SET0 拨到板上 `L`、SET1 拨到 `H`，对应 SPI。先断 USB、拆 TFT；准备并烧录专用 PN532 测试固件后再次断 USB，逐根核对供电与信号再接模块，最后重新上电。不要把 5 V 接到任何 ESP32 GPIO，也不要在通电时改线。若不想使用双排针，也可给板边八孔焊一排单列排针后按丝印连接；未焊孔不能靠松插导线作可靠测试。

## 实验目标与术语

目标：程序选择名片 A/B，设备呈现对应的 NDEF HTTPS URI；手机靠近后读到当前链接，移开、切换、再次靠近后读到新链接。先用 USB 供电和串口显示状态，之后增加一个按键；墨水屏、电池与薄壳不参与第一轮。

要找的是卡模拟/标签仿真（Card Emulation / NFC Tag Emulation），不能只搜「主动 NFC」。主动产生射频场的读卡器功能不等于本项目需要的被读取标签功能。NDEF URI 是本次验证载荷，不涉及门禁凭据或任意 UID 模拟。

## 两条可买现成硬件的路线

| 路线 | 所需硬件 | 能验证什么 | 与最终定制板的差异 |
| --- | --- | --- | --- |
| **复用 ESP32** | 空闲 ESP32 + 带天线的 PN532 开发模块 + 导线，按键可后加 | 卡模拟、程序更换 NDEF、手机提示及打开链接体验 | Seeed 例程使用 Type 4 标签模拟，最终计划是 nRF52840 Type 2；驱动、功耗和天线距离不直接迁移 |
| 同主控验证 | 普通版 XIAO nRF52840 + 已验证配套 NFC 天线，或带天线的 nRF52840 DK | 更接近最终主控的 Type 2 标签行为、内容切换及恢复 | 板级天线/布局仍不同，最终装壳要重测；XIAO 天线通常需要焊接 |

希望沿用手头 ESP32 时，PN532 是合理的交互实验选择。若准备专门买主控且希望直接验证最终架构，优先比较 nRF52840 开发板。不要同时采购两套完整设备作为默认要求。

## PN532 购买与软件依据

- 候选类别：带板载天线、可选择 HSU/UART、SPI 或 I2C 的 PN532 模块；优先有明确板卡版本、原理图和卡模拟例程的型号。若只做桌面实验，可选焊好排针的版本。
- [Seeed PN532 库](https://github.com/Seeed-Studio/PN532) 明确列出 NFC Type 4 卡模拟，README 也有 ESP32 硬件串口支持说明。
- [emulate_tag_ndef 例程](https://github.com/Seeed-Studio/PN532/blob/arduino/examples/emulate_tag_ndef/emulate_tag_ndef.ino) 使用 URI 记录、NDEF 缓冲区和 `EmulateTag`；当前源码默认启用 HSU。默认 `emulate()` 会阻塞，提供超时形式；加入按钮时需设计返回/会话边界，不能简单把按钮读取放在无限阻塞调用后。
- 「读卡 UID」例程不能作为本项目通过证据。需要运行标签模拟程序，使手机读取模块自己呈现的内容。
- [Elechouse PN532 V3 手册](https://www.elechouse.com/elechouse/images/product/PN532_module_V3/PN532_%20Manual_V3.pdf) 可作为支持虚拟卡模式的硬件参考；它是较早版本资料，不能直接用于所有淘宝同名兼容板。采购前确认实际电源和所选接口的逻辑电平，ESP32 GPIO 不因模块支持 5 V 供电就变成 5 V 容忍。

已将 Seeed PN532 与 don/NDEF 作为仓库子模块锁定，复用其 NFC Type 4 模拟与 NDEF 编码实现，见[固定网址测试固件](../firmware/pn532_ndef_test/README.md)。子模块源码与许可证保持上游原样。

## nRF52840 购买与软件依据

[Seeed NFC 指南](https://wiki.seeedstudio.com/XIAO-BLE-Sense-NFC-Usage/) 提供原生 Type 2 标签及网址例程，记录验证的 Seeed nRF52 Boards 1.1.13。普通 XIAO nRF52840/Sense 与 Plus 的 NFC 引脚默认配置可能不同；初次验证可优先普通版，减少 Plus 配置恢复的步骤。Sense 的传感器不是本实验必需。

指南列出 MOLEX 1462360051、TAOGLAS FXR.07.A.DG 天线的测试经验，但当前供应情况和最终距离未确认。天线是线圈及匹配问题，不能购买一张普通 NFC 标签贴纸当作裸天线直接连接。最终卡片的匹配仍按实际装配验证。

## 验收顺序

1. 固定一个普通 HTTPS 链接，先使用 NFC 读取工具确认收到有效 NDEF。
2. 不打开读取工具，检查手机系统是否提示以及点击后的页面；分别记录手机型号、系统版本、屏幕亮灭/锁定状态。URI、文本和 vCard 的系统处理不等价，不预设碰一下就自动保存联系人。
3. 从串口选择 A/B 两个可区分的 URI：手机移开 → 切换 → 再靠近，每次读到当前值；再把选择动作改成面包板按键。
4. 连续做至少 10 轮切换与读取，记录漏读、旧内容、耗时；手机一直贴着时切换单独记录，不假定手机会自动重新读取。
5. 用实际将使用的 iPhone/Android 分别验证。若目标还包括桌面读卡器，明确型号及读取软件后另测。

通过后可以确认交互方向，再在最终 nRF52840 固件和 PCBA 上重复核心测试。PN532 实验成功不能证明定制板的功耗、读距或 Type 2 兼容性；PN532 特定驱动失败也不能直接判定最终 nRF52840 路线不可行。

2026-09-23 已在 `/dev/cu.usbmodem1101` 用原 `oracle_live STATUS` 确认当前板卡；Image Oracle 恢复包八个文件的 SHA-256 校验均通过。新建 [PN532 SPI 探测固件](../firmware/pn532_probe/README.md)，使用 Adafruit PN532 1.3.4 与现有 ESP32 工具链构建通过，实机写入四段摘要校验通过；芯片识别为 ESP32-S3 v0.2，MAC 为 `68:ee:8f:4c:ff:b0`。烧录后串口 `STATUS` 返回 `PN532_PROBE_READY pins_idle=1`，证明原 `oracle_live` 已停止。新固件只在收到 `PROBE` 时初始化 SPI。

2026-09-24 用户接好六线后，PN532 的 PWR 指示灯亮；第一次两个开关均为 H，`PROBE` 返回 `PROBE_FAIL no_pn532_response`。断 USB 后改为 SET0=L、SET1=H，再次上电，串口返回 `PN532_PROBE_READY pins_idle=1`、`PROBE_START`、`PROBE_OK chip=0x32 firmware=1.6`。这证明当前接线和 SPI 通信可用；双排针尚未逐针量通断。

随后烧录[固定网址 NDEF 测试固件](../firmware/pn532_ndef_test/README.md)，串口 `STATUS` 返回 `NDEF_READY url=https://example.com chip=0x32 firmware=1.6 sam_response=0`。手机靠近后串口记录 `NDEF_SESSION`；用户报告手机弹出“是否打开链接”，打开后确认网址正确。该结果验证了这块 PN532 与当前手机之间的固定 NDEF 网址交互；手机型号及系统版本未记录，A/B 切换和不同手机的体验尚未验证。

当前缺口：实体按键切换、墨水屏转接板实物型号和接口。桌面测试成功不能证明最终 nRF52840 Type 2 实现及整机读距。

## 个人主页与微信入口实测（2026-09-25）

为逐一比较手机体验，[PN532 NDEF 测试固件](../firmware/pn532_ndef_test/README.md)新增串口 `URL <地址>`，可在保持 USB 供电时临时替换只读 NDEF URI。重新构建、烧录及写入摘要校验通过；ESP32-S3 的 MAC 与先前记录一致，PN532 `STATUS` 持续返回 `chip=0x32 firmware=1.6`。下列每个地址切换后均获得 `NDEF_URL_SET` 和 `NDEF_READY`；手机结果由用户在同一部手机上报告，手机型号与系统版本仍未记录。

| NDEF URI | 手机实际结果 | 判断 |
| --- | --- | --- |
| 用户从小红书复制的 `https://xhslink.cn/o/...` 主页链接 | 先出现网址提示，点击后进入浏览器，再到正确的小红书主页 | 能到达目标，仍有浏览器中转 |
| 用户微信个人二维码解出的 `https://u.wechat.com/...` | 点击网址后浏览器显示微信下载页 | 未到达个人加好友页；二维码中的完整地址不入库 |
| `weixin://addfriend/<本人微信号>` | 手机出现应用选择卡片，选择微信后没有进一步页面 | 系统能交给微信，指定好友跳转未成功 |
| `weixin://addfriend/<另一人微信号>` | 用户再次确认未到达指定人的加好友页 | 排除仅因“不能加自己”造成的失败；另一人账号不入库 |

用户已提供真实微信号与二维码用于本轮实验，但固件上电仍默认 `https://example.com`，所有个人地址只通过串口临时切换。实验结束后已将当前运行状态切回上述可用的小红书链接；ESP32 重启后仍会恢复默认地址。

搜索到的[墨水屏 NFC 卡实物体验](https://www.einkcn.com/html/product_6a5c413ec5d491752.html)把微信二维码作为屏幕图片，NFC 则打开预设名片网页；[官微名片产品](https://ltd.com/article_detail/5601786242260997?is_header=card)声称 NFC 可打开其自有小程序名片页，属于不同于个人微信加好友的入口。这些实例只作为交互方向参考，不算本项目实测。[Apple 后台 NFC 说明](https://developer.apple.com/documentation/corenfc/adding-support-for-background-tag-reading)明确指出不支持自定义 URL scheme，因此 `weixin://` 即便在这部手机能唤起应用选择，也不能作为跨平台方案。

下一步先单独验证随屏转接板与墨水屏，确认尺寸、驱动和清晰度后试着显示**未经美化的原始微信个人二维码**，用另一部手机的微信“扫一扫”验证能否到达加好友页；NFC 侧继续用 HTTPS 分享小红书或个人名片网页。墨水屏扫码能力、个人名片网页与最终定制板均未验证。

## NFC 与 App 唤起的边界

本轮实验说明：NDEF URI 能被手机读取，不等于每个 App 都提供通用、稳定的指定页面入口。手机系统可按[Android App Links](https://developer.android.com/training/app-links/about)或[Apple Universal Links／后台 NFC](https://developer.apple.com/documentation/corenfc/adding-support-for-background-tag-reading)把受支持的 HTTPS 地址交给对应 App；目标 App 仍需自己声明可处理的域名和页面，未匹配时可能落到浏览器。Apple 后台 NFC 不支持任意自定义 URL scheme。这里不能据小红书和微信两项实验推断“国内 App 普遍支持很少”的数量结论，应逐个平台、链接类型和手机实测。

支付宝“碰一下支付”是另一项专门接入的支付服务。[支付宝活动规则](https://render.alipay.com/p/c/180020570000128061/index.html?caprMode=sync)将其描述为基于**支付宝付款码和 NFC 通讯技术**，由已解锁且启用 NFC 的手机触碰**商家碰一下收银设备**完成支付。这说明 NFC 只是近距离交互环节，支付宝的账号、支付流程与商家设备也共同参与；不能据此认为任意 NDEF 名片链接都能唤起支付宝支付或其他 App 的内部操作。就本项目而言，优先使用目标平台正式提供的 HTTPS 分享链接；个人微信加好友继续以屏幕二维码作为待验证方案。
