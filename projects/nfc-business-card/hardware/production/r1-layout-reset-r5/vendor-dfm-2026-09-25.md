# R5：嘉立创线上 DFM 对照

## 当前确定方案

2026-09-25 上传同版 Gerber、BOM、CPL，Gerber SHA-256 为 `60f0ec3fff56541058e7eb62e5d2ae3700170869250258a4331362ab3860cc35`。[线上任务 DFMP2609240835](https://www.jlc-dfm.com/order/smt-dfm-lceda?dfmPcbTaskCode=DFMP2609240835&dfmPcbUploadFileKeyId=626068272962908162&dfmPcbTaskKeyId=626068284732887042)。板厚设为 0.8 mm；表面处理显示网站默认有铅喷锡，不代表最终选型。未下单或付款。

PCB 危险／警告：盘到线 0／4，PTH 孔到线 0／0，焊盘距焊盘 **4／6**，VIA 孔到焊盘 32／20，孔环 100／0，阻焊桥 43／4，开窗露线 3／47，四个 0.60 mm 镀铜槽仍报危险。R4 的盘到线 2 条和 PTH 孔到线 2 条危险消失；新 CC2 过孔附近一条焊盘距焊盘危险约 0.03 mm。BOM 自动匹配 29/29 组，SMT DFM 多次给出空白／禁用的 0 项结果，**不是通过证据**。R5 因 PCB 回退及遗留危险而停止，后续由 R6 承接。
