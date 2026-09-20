# Hardware Lab

用于个人硬件实验和小装置开发的 Git 仓库。每个装置放在 `projects/` 下，独立维护固件、硬件资料、依赖和构建流程。

## 项目

| 项目 | 用途 | 最近记录的状态 |
| --- | --- | --- |
| [AI Passport](projects/ai-passport/README.md) | 探索紧凑的可编程胸牌、屏幕按键交互与 NFC 链接 | 2026-09-16 确认已下单，等待到货 |
| [Image Oracle](projects/image-oracle/README.md) | 用固定算法将摄像头图像映射为答案，默认拍摄熔岩灯 | 2026-09-19 拼接原型完成并验收；后续探索更多传感器，或焊接、定制 PCB 与 3D 打印的紧凑装置 |
| [Programmable NFC Business Card](projects/nfc-business-card/README.md) | 按键切换身份的薄型 NFC 墨水屏名片 | 2026-09-20 已有 FreeCAD 包络模型；EDA 官方 AI 接口已连通，独立测试电路完成保存重开、工程导出和网表核对 |

## 目录结构

```text
hardware-lab/
├── README.md
├── AGENTS.md
├── .gitignore
├── .gitmodules
├── .agents/
│   └── skills/
│       └── easyeda-api -> ../../upstreams/easyeda-api-skill
├── upstreams/
│   └── easyeda-api-skill/
├── eda/
│   ├── README.md
│   └── AI-API-Smoke-Test.eprj2
├── docs/
│   ├── inventory.md
│   └── wiring-diagrams.md
└── projects/
    ├── ai-passport/
    │   └── README.md
    ├── image-oracle/
    │   ├── README.md
    │   ├── firmware/
    │   ├── hardware/
    │   ├── scripts/
    │   ├── wiring-diagrams/
    │   └── docs/
    └── nfc-business-card/
        ├── README.md
        ├── hardware/
        ├── enclosure/
        └── docs/
```

目录用途与命名约定见 [AGENTS.md](AGENTS.md)。所有目录均在首次有实际内容时创建；新项目可以只有 README，不使用占位文件预建目录。根目录 `docs/` 保存跨项目信息，包括器件清单和[接线图制作与归档方法](docs/wiring-diagrams.md)。

根目录 [eda/](eda/README.md) 直接保存嘉立创 EDA 的原始 `.eprj2` 工程，不使用工程文件符号链接，也不再嵌套目录。客户端只需登记一次 `hardware-lab/eda/`。正式工程纳入 Git，所属项目通过文档关联；BOM 等资料仍保存在项目的 `hardware/`，临时导出产物放在 `artifacts/`。

现有接线图见 [Image Oracle 图册](projects/image-oracle/wiring-diagrams/README.md)。后续默认使用带主板外形、完整丝印和模块排针数字序号的接线图；各项目使用相同目录名。

## 开始工作

1. 阅读 [AGENTS.md](AGENTS.md) 和目标项目的 README。
2. 分配引脚和确定供电前，先核对实物及对应资料。
3. 将固件放入项目的 `firmware/`，在项目 README 记录具体工具链、依赖版本和已验证的 shell 命令。
4. 先复现已知可用的例程，再修改应用功能。
5. 记录完成了哪些构建、哪些实机测试，以及仍未确认的事项。

各项目在自己的 README 记录已验证的构建、烧录与测试命令；在本地 Mac 上使用编辑器、shell 工具和 AI 辅助开发。

克隆后使用 `git submodule update --init --recursive` 初始化 `upstreams/` 下的外部仓库。外部 Skill 通过 `.agents/skills/` 中的相对符号链接供 Codex 发现；EDA Skill 的本地依赖与启动方式见 [软件说明](projects/nfc-business-card/docs/software.md)。

## 仓库约定

- 按装置或用途组织项目，每个项目可使用不同的 MCU 和工具链版本。
- 详细状态和下一步放在项目 README，根目录项目表仅作简要导航。
- Git 保存源码、实用的小型素材、可编辑 CAD、依赖锁文件和可复现配置。临时固件导出、采集数据和测量输出放入被忽略的 `artifacts/` 或 `logs/` 目录。
- ESP-IDF 的有意配置保存在 `sdkconfig.defaults` 及所需变体中；生成的 `sdkconfig` 和构建产物不入库。
- 外部上游仓库统一用 Git submodule 放在 `upstreams/`，固定提交并保留上游许可证，在项目文档记录 URL、revision 和使用方式。直接导入的例程仍需记录来源，避免把其嵌套 `.git` 目录复制进仓库。
- 文档默认使用中文；代码、代码注释和专有名词保持英文，具体见 [AGENTS.md](AGENTS.md) 的语言约定。

历史讨论和采购决策继续保存在 [CyberMnema](../CyberMnema/README.md)，通过链接关联。本仓库记录实际工程进展。
