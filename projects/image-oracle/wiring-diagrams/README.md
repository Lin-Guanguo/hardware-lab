# Image Oracle 接线图册

本目录保存交互式 HTML 接线图；点击表中页面或使用 macOS `open` 命令打开。`sources/` 保留可编辑的对话图源，目录下同名 HTML 是可独立打开的导出页面。

## 已归档的图

| 图 | 内容 | 适用范围与验证状态 |
| --- | --- | --- |
| [屏幕引脚位置](display-pin-locations.html) | 主板外形、完整丝印、屏幕八针 ①～⑧，可逐根高亮 | ESP32-S3-CAM N16R8；对应当前 ST7789 接线，用户已确认基本显示 |
| [中心按键引脚位置](button-pin-locations.html) | 按键八针顺序、① COM 与 ⑥ MID 的主板位置 | 用户已确认接线，中心键计数、持续连按及第三个程序的定格操作均已实测 |
| [三路共地](shared-ground-wiring.html) | 主板 GND、屏幕 GND、按键 COM 接同组 a5／b5／c5 | 用户报告已按方案接好；孔号用于示例，未收到接线近照 |
| [面包板内部连接](breadboard-connections.html) | 选择孔位，显示内部相通的五个孔 | 典型 a～j 面包板接线区；不包含两侧电源轨 |

主板位置图固定为“金属盖朝前、天线上、USB 下”，按实物照片排列引脚；圈号表示模块端针序，主板圆点旁仍是 GPIO 丝印。按键图中的灰色主板针脚不代表空闲 GPIO。

接线依据与实测详情：[屏幕接线表](../hardware/display-wiring.md)、[按键接线表](../hardware/button-wiring.md)、[屏幕启动记录](../docs/display-bringup.md)。接线前断电，不能只依据图中的空间位置省略丝印核对。

## 打开与维护

从仓库根目录打开：

```sh
open projects/image-oracle/wiring-diagrams/display-pin-locations.html
open projects/image-oracle/wiring-diagrams/button-pin-locations.html
```

制作规范及重新导出命令见[仓库统一方法](../../../docs/wiring-diagrams.md)。以 `sources/` 为修改入口，重新生成同名独立页面；不要保存额外的 `*-preview.html`。

2026-09-19：归档了对话中的四张原图，使用 Codex `visualize` 1.0.38 导出独立页面。源文件一致性、导出内容和脚本语法已检查；主板图此前已通过 320／360／736 px 下的脚本运行与选择状态检查。本次未新增浏览器目视检查或硬件测试。
