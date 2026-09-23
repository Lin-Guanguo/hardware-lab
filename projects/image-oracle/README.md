# Image Oracle：图像答案之书

用摄像头拍摄图像，通过固定算法从本地答案库中选取并显示答案。默认拍摄熔岩灯，也可以拍摄其他对象。

## 当前确定方案

继续开发的入口是 [oracle_live](firmware/oracle_live/README.md)（[主程序](firmware/oracle_live/oracle_live.ino)）：ESP32-S3-CAM N16R8 + OV3660 + ST7789 + MID 中心键，USB 供电，沿用已验证的[接线图册](wiring-diagrams/README.md)。`camera_serial` 与 `display_serial` 保留作单项测试和恢复基线。

**2026-09-19：相机、屏幕与按键的桌面拼接原型完成，用户实物验收通过。** 当前运行第三个程序 `oracle_live`：左侧实时预览、MID 定格到右侧、下方生成 TRUE/FALSE。可用基线、已完成工作和后续路线见[阶段收尾记录](docs/prototype-milestone.md)。

后续有两条路线：继续拼接传感器探索玩法；或进入焊接、定制 PCB 与 3D 打印，让装置更紧凑。当前仍使用开发板、现成模块和杜邦线，尚未进行定制电路板或外壳制作。

## 实验进展记录

下列条目保留各实验阶段当时的结论；最新状态以上方阶段总结为准。

- 2026-09-16，用户确认此前购买的鹿小班硬件已经全部到货，计划当晚开始实验。具体型号、数量和完好情况仍待验货。
- 2026-09-16，已整理[商家资料与首次实验说明](docs/vendor_resources.md)，下载相机测试源码、套装教程、小智固件及屏幕资料。发现商家部分图纸混用版本，需先对照实物；本地原始下载不入 Git。
- 2026-09-18，已根据用户提供的实物总览与装箱单照片补充[到货清单](../../docs/inventory.md)。纸质清单标注主板为 ESP32-S3-N16R8 CAM、摄像头为 OV3660，额外温湿度模块为 SHT30；实物完整丝印、板卡版本和功能仍待核对。
- 2026-09-18，主板近照可辨认模组标记 ESP32-S3-N16R8；Mac 已识别 USB 串口，并在 115200、8N1 下收到预装程序循环输出的 `50%R`、`50%G`、`50%B`。已验证 USB 识别与串口接收，详见[首次连接记录](docs/first-connection.md)。
- 2026-09-18，用户报告已断电安装摄像头并重新上电；已通过串口确认预装程序为 MicroPython v1.19.1 的 `RGB Demo`，`import camera` 报模块不存在。查询后已软重启恢复灯测试，摄像头安装方向和取帧仍待验证；后续操作同时提供可复现命令。
- 2026-09-19，完整 16 MiB 原固件备份及设备摘要比对通过；[串口相机工程](firmware/camera_serial/README.md)已构建、烧录并通过写入校验，程序约 378 KB。实测识别 OV3660，初始化 8 MB PSRAM，并经原生 USB 取得 320×240 JPEG；修正 Mac 串口控制线引发复位的问题后，正式脚本连续两次拍照成功，已解码查看画面。屏幕、按键和更高分辨率未测试，详见[摄像头启动记录](docs/camera-bringup.md)。
- 2026-09-19，新增[面包板入门与屏幕、按钮准备](docs/breadboard-start.md)。下一步目标为按钮控制屏幕计数；屏幕背面版本和按钮公共端仍待实物确认，尚未分配新 GPIO 或烧录外设测试程序。
- 2026-09-19，用户确认屏幕八针标注，已制定[母对母杜邦线接线表](hardware/display-wiring.md)：SCK40、MOSI41、RST21、DC47、CS42、BL38，保留摄像头和原生 USB 引脚。待核对实际接线与背面版本、添加屏幕测试固件；尚未烧录或验证显示。
- 2026-09-19，用户报告按表接好屏幕；[屏幕测试工程](firmware/display_serial/README.md)构建、原生 USB 自动烧录及写入校验通过，自动重启后收到 `display_serial` 状态回复，待目视确认画面。相机基线保留；两个 Mac 客户端共用避免复位的原生 USB 连接类，提取后相机取帧复测通过。详见[屏幕启动记录](docs/display-bringup.md)。
- 2026-09-19，用户目视确认屏幕测试画面已显示，基本显示验证通过。下一步确认五向按键模块的公共端和针脚，再实现按键控制屏幕计数。
- 2026-09-19，按键近照已确认 `COM UP DWN LFT RHT MID SET RST` 丝印；制定 [COM 共地、MID 接 GPIO14 的方案](hardware/button-wiring.md)。屏幕程序已加入中心键计数和消抖，构建通过，尚未烧录；等待用户完成共地接线。原显示测试程序已另存本地基线。
- 2026-09-19，已将屏幕、中心按键和面包板的四张 HTML 图归档到[接线图册](wiring-diagrams/README.md)，同时保留可编辑源文件。后续沿用主板外形、完整丝印与数字序号的画法；按键实测仍待完成。
- 2026-09-19，用户确认 COM 共地、MID 接 GPIO14 并重新连接 USB；计数版本重新构建、烧录及四段写入校验通过，状态确认 `revision=button-counter`、初始 `count=0`。已发起短按和长按验证，等待用户反馈，详见[按键启动记录](docs/button-bringup.md)。
- 2026-09-19，用户实际按压后报告快速连按漏计数、整屏扫刷。确认旧版绘图阻塞采样约 152 ms，已烧录独立采样、10 ms 消抖及数字局部重绘版本。实测数字绘图约 9.6 ms、采样最大间隔约 1.4 ms；模拟按键测试通过，实物快速连按和长按复测待回报，详见[性能修正记录](docs/button-bringup.md#快速连按漏计数与刷新修正)。
- 2026-09-19，用户确认计数不再丢失，但持续按压后画面延迟。补测复现 USB 日志在无读取端时等待约 2 秒；已烧录不等待 USB 发送的版本，同一压力测试下输出峰值降至 0.212 ms，数字绘图仍约 9.6 ms。构建、烧录校验与无读取端回归测试通过；用户持续连按、停顿后再按，确认“始终跟手，问题解决”。此版本作为按键与屏幕交互基线，详见[USB 阻塞修正](docs/button-bringup.md#连续按压后变慢usb-日志阻塞)。
- 2026-09-19，第三个独立工程 [oracle_live](firmware/oracle_live/README.md)已构建、烧录并正常启动：左侧约 20 FPS 预览，MID 定格到右侧，下方根据照片像素生成 `TRUE`／`FALSE`。固定图像算法、实机预览／定格和 USB 无读取端回归通过；右图已导出 PNG，Mac 重算哈希和答案一致。用户实测确认预览、定格、答案、画面方向和颜色“都正常，效果符合预期”，第三个程序作为后续开发的可用基线。此前按键显示基线已备份，详见[第三个程序整合记录](docs/oracle-bringup.md)。

## 已确定的设计原则

- 图像是答案选择中唯一变化的输入；算法、处理规则和答案库相同时，同一份图像应得到同一个答案。
- 不额外加入随机种子、时间戳或计数器来改变结果。重新抽取意味着重新拍摄，允许答案重复。
- 计划中的核心硬件是摄像头、屏幕和五向按键模块；其他已购模块用于实验，不作为必需功能。
- 先用 USB 供电和面包板验证，功能原型跑通并测量尺寸后，再确定正式接线和外壳。
- 熔岩灯保留原装市电供电并独立放置；本项目仅开发弱电电子部分。
- AI Passport 当前公开配置没有摄像头，作为独立项目探索。

## 目录用途

- `firmware/`：完整固件工程和可复现的构建配置。
- `hardware/`：已核对的 BOM、引脚分配、接线和未来可能设计的 PCB。
- `tests/`：Mac 消抖、图像算法测试，以及实机预览、定格和 USB 无读取端回归测试。
- `wiring-diagrams/`：[交互式接线图册](wiring-diagrams/README.md)，包含独立 HTML 和 `sources/` 图源。
- `docs/`：器件资料、实验、测量结果和设计决策。
- `downloads/`：本地商家原始资料、预编译固件和解压副本，被 Git 忽略；下载来源和校验值保存在 `docs/vendor_downloads.json`。

## 后续两条路线

| 路线 | 目标 | 启动时先做什么 |
| --- | --- | --- |
| 更多传感器实验 | 尝试温湿度、光照、触摸、编码器等输入与屏幕交互 | 选一个已购模块，确认型号、电压及引脚，再做独立读取实验 |
| 紧凑装置与产品化探索 | 用焊接、定制 PCB 和 3D 打印减少杜邦线、固定模块 | 明确保留功能，测量实物尺寸与接口位置，再设计布局和连接方式 |

两条路线可以交替推进，具体步骤与尚未验证的范围见[阶段收尾记录](docs/prototype-milestone.md)。三个固件工程和可恢复基线继续保留；后续实验按实际内容创建目录，不预建 PCB 或外壳占位工程。

## 常用命令

以下安装和构建命令已在 macOS ARM64 验证；烧录与实物测试进展见[摄像头启动记录](docs/camera-bringup.md)。

```sh
bash projects/image-oracle/scripts/setup.sh
bash projects/image-oracle/scripts/build.sh
```

第三个程序使用以下命令构建、查询和定格：

```sh
bash projects/image-oracle/scripts/build-oracle.sh
uv run --offline projects/image-oracle/scripts/oracle.py --port /dev/cu.usbmodem1101 STATUS
uv run --offline projects/image-oracle/scripts/oracle.py --port /dev/cu.usbmodem1101 SNAP
uv run --offline projects/image-oracle/scripts/oracle.py --port /dev/cu.usbmodem1101 EXPORT \
  --output projects/image-oracle/artifacts/photos/oracle-frozen.png
```

`SNAP` 等同于按 MID；`EXPORT` 保存已经定格的右图并重新校验哈希和答案。构建不会自动烧录，烧录、恢复和代码阅读入口见[第三个程序说明](firmware/oracle_live/README.md)。

切回第二个屏幕／按键程序后，使用以下命令控制显示：

```sh
bash projects/image-oracle/scripts/build-display.sh
uv run projects/image-oracle/scripts/display.py --port /dev/cu.usbmodem1101 STATUS
uv run projects/image-oracle/scripts/display.py --port /dev/cu.usbmodem1101 COUNTER
uv run projects/image-oracle/scripts/display.py --port /dev/cu.usbmodem1101 RED
uv run projects/image-oracle/scripts/display.py --port /dev/cu.usbmodem1101 TEST
```

完整步骤及 `COUNTER`、`GREEN`、`BLUE`、`LIGHT_OFF` 等命令见[屏幕工程说明](firmware/display_serial/README.md)。

切回相机固件后，保持原生 USB 连接，不按 BOOT，从仓库根目录拍照：

```sh
uv run projects/image-oracle/scripts/capture.py \
  --port /dev/cu.usbmodem1101 \
  --output projects/image-oracle/artifacts/photos/my-photo.jpg
```

重新插入后用 `ls /dev/cu.*` 核对端口；每次拍照换一个新文件名。照片和原固件备份均不入 Git。

串口连接、MicroPython REPL 与 `screen` 操作见[首次连接记录](docs/first-connection.md)。

## 参考资料

- [拼接原型阶段收尾与后续路线](docs/prototype-milestone.md)
- [第三个程序：相机、屏幕与按键整合实测](docs/oracle-bringup.md)
- [知识笔记：任务、局部重绘与非阻塞日志](docs/responsive-input-display.md)
- [知识笔记：两个 USB-C 接口、UART 与固件通信](docs/usb-uart-notes.md)
- [商家资料、下载位置与首次实验说明](docs/vendor_resources.md)
- [下载来源及 SHA-256 清单](docs/vendor_downloads.json)
- [原始讨论、采购记录与启动计划](../../../CyberMnema/timeline/2026/09/W38/熔岩灯交互装置.20260914.md)
- [共享器件清单](../../docs/inventory.md)
