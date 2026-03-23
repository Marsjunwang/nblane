# 看板归档（kanban-archive.md）

## 真源与路径

- 每个档案在 `profiles/<名称>/` 下可有 **`kanban-archive.md`**，与 **`kanban.md`** 并列。
- **`kanban.md`** 仍是主看板；归档文件只承接从主看板 **「已完成」列** 移出的历史任务。

## 写入方式

- 在 Streamlit **看板**页展开 **「已完成」列整理**，多选任务后点 **「归档所选」**。
- 每次归档会在 `kanban-archive.md` 末尾追加一节：`## Archived · YYYY-MM-DD`，其下任务行格式与 `kanban.md` 中 **Done** 列一致（含 checkbox、元信息行、子任务等）。

## 与摄入的关系

- **已完成 → 证据（AI）** 写入的是 `evidence-pool.yaml` / `skill-tree.yaml`，不替代本文件。
- 可选勾选 **「应用后将来源「已完成」任务标为已结晶」**：在主看板 Done 列将对应任务打上 **已结晶** 标记（写入 `crystallized: true` 元信息），便于区分「仍待回顾」与「已处理」。

## CLI / MCP

- `nblane ingest-kanban` 与 MCP `profile://kanban` 仍只消费 **`kanban.md` 原文**；归档文件供人读与备份，不参与默认上下文拼接。
