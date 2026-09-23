# easyeda-bridge

本仓库自己维护的 EasyEDA（嘉立创EDA）Run API Gateway 桥接服务，用来替代"临时 nohup 进程 + 指向上游脚本"的用法。

## 为什么有这份副本

上游 Skill（`upstreams/easyeda-api-skill`，只读）里的 `scripts/bridge-server.mjs` 有一个会让**整个进程退出**的缺陷：`/execute` 先发出 200 响应头，再对结果做 `JSON.stringify`；只要结果里含循环引用、BigInt 或函数，stringify 抛错后 catch 又写一次响应头，触发 `ERR_HTTP_HEADERS_SENT`，进程直接崩溃。崩溃时所有 EDA 连接一起掉，客户端表现就是"未找到 bridge 服务器"。

`bridge-server.mjs` 是上游脚本的补丁副本，只改了两处：

1. 15 处响应序列化改用 `safeJson()`——循环引用标 `[circular]`、BigInt 转字符串、函数忽略，永不抛错；
2. 增加 `uncaughtException` / `unhandledRejection` 兜底日志，避免单次异常带走进程。

上游子模块保持原样；依赖 `ws` 通过 `node_modules` 符号链接复用上游安装，或在本目录执行 `npm install --omit=dev`。

## 用法

**默认按需启动**：安装只把作业登记到 launchd（`RunAtLoad=false`、不带 `KeepAlive`），开机/登录都不会自动跑；要做 EDA 时手动开，用完可关。

```sh
tools/easyeda-bridge/install-agent.sh          # 安装/刷新 LaunchAgent（幂等，按需模式）
tools/easyeda-bridge/bridge-start.sh           # 现在启动（必要时先加载作业），并打印自检
tools/easyeda-bridge/bridge-stop.sh            # 现在停止（作业保留，随时再 start）
tools/easyeda-bridge/bridge-status.sh          # 健康自检：进程、/health、窗口数、崩溃与重连计数
tools/easyeda-bridge/install-agent.sh --login-start   # 改成开机自启 + 崩溃自动拉起
tools/easyeda-bridge/install-agent.sh --quiet         # 额外写入 EDA_BRIDGE_QUIET=1
tools/easyeda-bridge/install-agent.sh --uninstall
```

安装脚本会把 `com.hardwarelab.easyeda-bridge.plist.template` 渲染到 `~/Library/LaunchAgents/`，然后 `bootout → bootstrap`，并把日志指到仓库的 `logs/`（已在 .gitignore 中，超过 5 MB 自动轮转一份 `.1`）。旧 plist 自动备份成 `.bak-<时间戳>`，只保留最近 2 份。

按需模式下 `bridge-status.sh` 在服务没启动时会直接说 `bridge down`；这属于预期状态，用 `bridge-start.sh` 开即可。

## 日志与降噪

默认每次扩展重连都会写一行，`logs/easyeda-bridge.out` 会缓慢增长。两种做法（细节见[环境与常驻服务](../../docs/environment.md)）：

- **静音**：在 plist 里加 `EnvironmentVariables` → `EDA_BRIDGE_QUIET=1`，然后重新 `install-agent.sh`；
- **轮转**：直接 `: > logs/easyeda-bridge.out` 截断即可，服务继续追加。

## 已知残留

扩展自身仍会每隔数秒重连一次（`New eda connection → registered → disconnected (1005)`），这是扩展/窗口可见性的行为，不是桥接崩溃。调用侧请配合 `projects/nfc-business-card/scripts/eda-exec-wait.mjs`（先选在线窗口、失败重试）使用。
