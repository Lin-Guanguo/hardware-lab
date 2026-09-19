# 第三个程序：相机、屏幕与按键整合记录

日期：2026-09-19。工程与完整命令见 [oracle_live](../firmware/oracle_live/README.md)。

## 本次实现与接线

沿用已验证的 OV3660 排线、ST7789 八针接线和 MID14／COM 共地，不新增接线。固件同时运行：

- core 0：采集 160×120 JPEG，解码为 RGB565，缩到 112×84，发布最新预览帧。
- core 1 主循环：更新左侧 `LIVE`；收到 MID 或 USB `SNAP` 后，把已经显示的帧保存到右侧 `FROZEN`，计算并显示答案。
- core 1 独立按键任务：每 1 ms 采样、10 ms 消抖；绘图和 USB 不参与采样路径。

右图和答案只在定格时更新，左图继续播放。图像只保存在 RAM；断电后清空。答案采用 `RGB565-FNV1a32-MSB-v1`：对右图像素计算 FNV-1a 32 bit 哈希，以最高位决定 `TRUE`／`FALSE`。相同像素得到相同结果，不加入时间、计数或随机数。

## 构建、烧录与启动

构建通过，程序占用 408,244 字节、静态 RAM 35,784 字节。图像、驱动和任务栈另行动态分配。此前用户确认可用的按键显示程序已备份到本地 `artifacts/firmware/display-nonblocking-20260919/`，备份摘要核对通过；完整原厂备份仍保留。

本次自动进入下载模式未成功，失败发生在写入前。用户按住 BOOT 插入原生 USB 后，以下命令成功写入并通过四段摘要校验：

```sh
(
  cd projects/image-oracle/build/oracle_live
  uv tool run --offline --from esptool==5.1.0 esptool \
    --chip esp32s3 --port /dev/cu.usbmodem1101 \
    --before no-reset --after watchdog-reset write-flash @flash_args
)
```

自动重启及一次短按 EN/RST 后没有应用回复。没有重新烧录，而是先用不触发复位的只读操作确认状态：

```sh
uv tool run --offline --from esptool==5.1.0 esptool \
  --chip esp32s3 --port /dev/cu.usbmodem1101 \
  --before no-reset --after no-reset --no-stub --connect-attempts 1 read-mac
```

能够与 ROM 下载器通信，确认此时还未进入应用。用户拔 USB、等待 2 秒、不按任何按钮重新插入后，屏幕显示 `IMAGE ORACLE`，应用 `STATUS` 正常回复，识别 `sensor_pid=3660`。

这里要区分“固件写入成功”和“应用已经启动”：前者由烧录摘要校验确认，后者由应用自己的协议和实际画面确认。下载模式下不会执行屏幕程序；正常开机使用同一个原生 USB 接口即可。

## 实机结果

首次状态为 `ready=1 tasks=1 camera=1 camera_error=0`，采集与预览帧数持续增加。首轮自动测试期间出现物理按键，冻结照片发生变化，测试按预期中止；松开按键重测通过。

```sh
uv run --offline projects/image-oracle/tests/oracle_smoke.py --port /dev/cu.usbmodem1101
```

测试主动定格、等待 2 秒，确认左侧继续推进，右图的帧编号、哈希和答案保持不变。随后排队发送状态请求并关闭串口读取端，等待 5 秒再连接，确认预览继续推进、设备未重启、日志发生丢弃但没有长时间阻塞。

| 指标 | 本次实测 |
| --- | --- |
| 预览帧率 | 约 20 FPS，短窗口估算 |
| 相机错误 | 0 |
| 最近一帧解码与缩放 | 16.752 ms |
| 左图绘制峰值 | 21.073 ms |
| 右图保存、计算与答案绘制峰值 | 52.561 ms |
| 按键采样间隔峰值 | 1.490 ms |
| USB 消息发送峰值 | 0.314 ms |
| 主循环间隔峰值 | 76.009 ms |
| 无读取端压力测试期间跳过的消息 | 6 条 |

这是本次运行窗口内的结果，不是长时间运行的最坏上界。按键任务独立采样，显示仍需等待当前绘制完成；连续请求可能合并为一次定格，原始按下次数单独记录。USB 丢弃策略仅用于诊断和尽力回复；图片导出采用逐行请求与校验，失败会报错。

本地原始日志：`logs/oracle-smoke-20260919.log`，不入 Git。

## 真实照片与答案复核

```sh
uv run --offline projects/image-oracle/scripts/oracle.py --port /dev/cu.usbmodem1101 EXPORT \
  --output projects/image-oracle/artifacts/photos/oracle-frozen-20260919.png
```

成功导出右图的 112×84 像素；Mac 端重新计算得到 `232CB5A2 / FALSE`，与板上结果一致。已打开 PNG 查看，能辨认实际室内画面。照片在本地忽略目录，未加入 Git。

固定输入、重复计算、两种 Boolean 结果与最近邻缩放也已通过 `tests/oracle_image_test.cpp` 的 Mac 测试。

用户移动摄像头并多次按 MID 后，确认左侧持续预览、右侧按键换图、下方显示 TRUE/FALSE，以及画面方向和颜色“都正常，效果符合预期”。第三个程序实物体验验收通过，作为后续开发的可用基线。尚未进行长时间连续运行或专门的长按实物测试。

## 经验复用

- 固定照片应复制已经显示完成的预览帧，使按键与用户看到的画面一致。
- 摄像头的采集、解码和显示各有耗时；使用独立任务发布最新帧，避免积压旧帧。
- 图像互斥锁只保护像素复制和元数据更新，不包住相机等待、JPEG 解码或 SPI 传输。
- 沿用[按键与显示响应性笔记](responsive-input-display.md)中的独立采样、局部绘制和非阻塞日志，并重新测试相机加入后的开销。
- 导出冻结像素并在电脑重算答案，可以验证“屏幕照片 → 算法结果”是否对应；仅检查屏幕上出现 TRUE/FALSE 还不够。
