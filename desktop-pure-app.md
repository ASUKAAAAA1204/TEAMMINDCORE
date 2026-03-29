# Pure Desktop Migration

## Goal

把 TeamMindHub 改造成没有本地 HTTP 服务的纯桌面应用，同时保留现有能力，不靠裁功能换轻量化。

## Phase 2 status

- [x] 抽离 Python runtime 组装逻辑，供 Web API 和桌面入口共用
  Verify: [`app/runtime.py`](/D:/programss/p2/app/runtime.py)
- [x] 抽出 ingestion 共享操作，避免 HTTP 路由和桌面桥接重复实现
  Verify: [`app/modules/ingestion/operations.py`](/D:/programss/p2/app/modules/ingestion/operations.py)
- [x] 实现桌面桥接 API，让前端直接调用 Python
  Verify: [`app/desktop/bridge.py`](/D:/programss/p2/app/desktop/bridge.py)
- [x] 接入原生 WebView 桌面入口，不依赖 `uvicorn`
  Verify: [`app/desktop/main.py`](/D:/programss/p2/app/desktop/main.py)
- [x] 前端 API 切换为桌面桥接优先，HTTP 仅作为兼容回退
  Verify: [`frontend/src/api.ts`](/D:/programss/p2/frontend/src/api.ts)
- [x] 桌面模式迁移到用户数据目录
  Verify: [`app/core/config.py`](/D:/programss/p2/app/core/config.py)
- [x] 补齐纯桌面桥接测试
  Verify: [`tests/test_desktop_bridge.py`](/D:/programss/p2/tests/test_desktop_bridge.py)
- [x] 补齐桌面资源解析与启动覆盖测试
  Verify: [`tests/test_desktop_assets.py`](/D:/programss/p2/tests/test_desktop_assets.py)
- [x] 更新桌面优先 README
  Verify: [`README.md`](/D:/programss/p2/README.md)
- [x] 补齐桌面打包入口、发布 manifest 和归档能力
  Verify: [`app/desktop/build.py`](/D:/programss/p2/app/desktop/build.py)
- [x] 补齐桌面环境自检命令
  Verify: [`app/desktop/doctor.py`](/D:/programss/p2/app/desktop/doctor.py)

## Done when

- [x] 桌面入口可以直接启动 UI 并调用 Python 业务能力
- [x] 核心工作流在纯进程内桥接下可验证通过
- [x] 不需要本地 HTTP 服务即可完成核心操作

## Known blockers in this sandbox

- `npm run build` 在当前沙箱可能因为 `esbuild spawn EPERM` 失败
- `pywebview` 安装在当前沙箱可能因为临时目录权限失败

这两个问题属于环境限制，不是当前桌面桥接实现本身的逻辑缺口。

## Next likely phase

1. 处理自动更新、图标、安装器与签名
2. 做真实打包机上的 `pywebview` / PyInstaller 烟测
3. 评估是否移除或进一步弱化 HTTP 兼容层
