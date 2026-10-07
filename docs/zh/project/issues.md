---
status: active
owner: engineering
last_verified: 2026-10-07
source_of_truth: true
---

# 问题与风险

## 当前问题

| 问题 | 影响 | 处理方向 |
|------|------|----------|
| Streamlit 遗留代码仍在仓库 | 误改、依赖负担、CI 仍导入 `nblane.kanban_ui` | 确认无引用后整体删除 |
| 车间未上生产 | 手机进不了生产环境的终端 | 部署 8504 WS 代理、改 Caddy、撤 basic_auth |
| `/starmap` 不含技能进阶进度 | 首页看不到「可进阶」提示 | 后端把 eligible 折进 `/starmap` 后再评 |
| 新用户初始化只适配工程类技能树 | 非工程领域用户无法起步 | 领域 schema 模板 + AI 定制草案 + 预览确认 |
| 部分翼 / 房 / 箕 / 轸 / 轩辕 / 虚星官无真形数据 | 星图与技能树页这几个域用模板形状 | 补 `asterisms.json` 后在 `SECTOR_ASTERISM` 接上 |

## 风险

- 文件格式膨胀：新增字段必须保持旧 profile 可读，未知字段不破坏 parser。
- kanban 元数据契约脆弱：任何新写路径必须走 `core/kanban_io.py`。
- Agent 写入越权：新写端点未在 `core/agent_policy.py` 登记时默认 T2（需确认）；新增直写操作必须显式登记并有撤销快照。服务端无法证明确认来自人，这是助手侧技能的契约。
- MCP 无登录无权限：`nblane-mcp` 只能在本机用，不能暴露给远端或助手。
- 确认码存在进程内存：Web API 重启后待确认操作失效，助手需要重新发起。
- 公开层泄露私有信息：公开站只读取公开层文件，研究资料默认私有。
- 聚合视图误当事实源：`/starmap`、`/projects-board` 是只读投影，可重建，不手动编辑。
- 模型供应商变化：AI Gateway 保持 OpenAI-compatible 抽象，不把业务逻辑写死到某个 provider。
- 北极星全文会随助手提示词进入云端 LLM：已知并接受。

## 待观察

- 是否需要 SQLite 作为索引缓存。
- 阅读器何时从 8502 iframe 改为 SPA 原生实现。
- Claim 层在输出层重建时的形状。
