# easyeda-bridge

本仓库自己维护的 EasyEDA（嘉立创EDA）Run API Gateway 桥接服务，用来替代"临时 nohup 进程 + 指向上游脚本"的用法。

## 为什么有这份副本

上游 Skill（`upstreams/easyeda-api-skill`，只读）里的 `scripts/bridge-server.mjs` 有一个会让**整个进程退出**的缺陷：`/execute` 先发出 200 响应头，再对结果做 `JSON.stringify`；只要结果里含循环引用、BigInt 或函数，stringify 抛错后 catch 又写一次响应头，触发 `ERR_HTTP_HEADERS_SENT`，进程直接崩溃。崩溃时所有 EDA 连接一起掉，客户端表现就是"未找到 bridge 服务器"。

`bridge-server.mjs` 是上游脚本的补丁副本，只改了两处：

1. 15 处响应序列化改用 `safeJson()`——循环引用标 `[circular]`、BigInt 转字符串、函数忽略，永不抛错；
2. 增加 `uncaughtException` / `unhandledRejection` 兜底日志，避免单次异常带走进程。

上游子模块保持原样；依赖 `ws` 通过 `node_modules` 符号链接复用上游安装，或在本目录执行 `npm install --omit=dev`。

## 用法

```sh
tools/easyeda-bridge/install-agent.sh          # 安装/刷新 LaunchAgent（幂等）
tools/easyeda-bridge/bridge-status.sh          # 健康自检：进程、/health、窗口数、崩溃与重连计数
tools/easyeda-bridge/install-agent.sh --uninstall
```

安装脚本会把 `com.hardwarelab.easyeda-bridge.plist.template` 渲染到 `~/Library/LaunchAgents/`，然后 `bootout → bootstrap → kickstart`，并把日志指到仓库的 `logs/`（已在 .gitignore 中）。旧 plist 会自动备份成 `.bak-<时间戳>`。

## 已知残留

扩展自身仍会每隔数秒重连一次（`New eda connection → registered → disconnected (1005)`），这是扩展/窗口可见性的行为，不是桥接崩溃。调用侧请配合 `projects/nfc-business-card/scripts/eda-exec-wait.mjs`（先选在线窗口、失败重试）使用。
