# Hardware Lab

用于个人硬件实验和小装置开发的 Git 仓库。每个装置放在 `projects/` 下，独立维护固件、硬件资料、依赖和构建流程。

## 项目

| 项目 | 用途 | 最近记录的状态 |
| --- | --- | --- |
| [AI Passport](projects/ai-passport/README.md) | 探索紧凑的可编程胸牌、屏幕按键交互与 NFC 链接 | 2026-09-16 确认已下单，等待到货 |
| [Image Oracle](projects/image-oracle/README.md) | 用固定算法将摄像头图像映射为答案，默认拍摄熔岩灯 | 2026-09-16 确认鹿小班硬件全部到货，待验货和首次实验 |

## 目录结构

```text
hardware-lab/
├── README.md
├── AGENTS.md
├── .gitignore
├── docs/
│   └── inventory.md
└── projects/
    ├── ai-passport/
    │   ├── README.md
    │   ├── firmware/
    │   └── docs/
    └── image-oracle/
        ├── README.md
        ├── firmware/
        ├── hardware/
        ├── enclosure/
        └── docs/
```

- `firmware/`：完整且可独立构建的固件工程。
- `docs/`：项目专属的参考资料、测量结果和实验记录。
- `hardware/`：实际 BOM（元件清单）、接线、原理图和 PCB 源文件。
- `enclosure/`：可编辑的外壳模型和用于加工的文件。
- 根目录 `docs/`：跨项目共享的信息，目前包括器件清单。

空目录通过 `.gitkeep` 保留在 Git 中，有实际文件后删除占位文件。其他目录按需添加；目前没有共享框架或根目录构建系统。

## 开始工作

1. 阅读 [AGENTS.md](AGENTS.md) 和目标项目的 README。
2. 分配引脚和确定供电前，先核对实物及对应资料。
3. 将固件放入项目的 `firmware/`，在项目 README 记录具体工具链、依赖版本和已验证的 shell 命令。
4. 先复现已知可用的例程，再修改应用功能。
5. 记录完成了哪些构建、哪些实机测试，以及仍未确认的事项。

目前尚未建立构建、烧录或测试命令，首次提交仅搭建工作区。后续在本地 Mac 上使用编辑器、shell 工具和 AI 辅助开发。

## 仓库约定

- 按装置或用途组织项目，每个项目可使用不同的 MCU 和工具链版本。
- 详细状态和下一步放在项目 README，根目录项目表仅作简要导航。
- Git 保存源码、实用的小型素材、可编辑 CAD、依赖锁文件和可复现配置。临时固件导出、采集数据和测量输出放入被忽略的 `artifacts/` 或 `logs/` 目录。
- ESP-IDF 的有意配置保存在 `sdkconfig.defaults` 及所需变体中；生成的 `sdkconfig` 和构建产物不入库。
- 导入上游代码时保留许可证，在项目文档中记录 URL、revision 和本地修改。不要意外导入嵌套的 `.git` 目录；初始结构不使用 submodule。
- 文档默认使用中文；代码、代码注释和专有名词保持英文，具体见 [AGENTS.md](AGENTS.md) 的语言约定。

历史讨论和采购决策继续保存在 [CyberMnema](../CyberMnema/README.md)，通过链接关联。本仓库记录实际工程进展。
