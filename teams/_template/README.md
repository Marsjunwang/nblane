# Team 目录模板

复制本目录为 `teams/<your-team-id>/`，填写 `team.yaml` 与 `product-pool.yaml`。

- **team.yaml**：团队元数据、成员 profile 名（对应 `profiles/{name}/`）、协作规则。
- **product-pool.yaml**：共享产品池（问题、项目、证据、方法、决策）。

设计说明见 [设计手册（中文）](../../docs/zh/design.md) §7 与 [产品设计](../../docs/zh/product.md) 中 Team OS 章节。

查看汇总：

```bash
python nblane.py team <your-team-id>
```
