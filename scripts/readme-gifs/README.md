# README 动图

`README.md` 里的动图用虚构的 `demo` 档案录制，格式是动态 WebP，放在
`docs/assets/readme/`。界面改了之后按下面步骤重录。

## 准备

1. 起隔离环境：`scripts/dev-web.sh --isolated`（18504，数据在 `.dev-data/`）。
2. 准备 `demo` 档案：`.dev-data/profiles/demo/`，论文资产在
   `.dev-assets/research/profiles/demo/`。没有的话从 `dev` 复制一份，然后
   清掉测试残留（`e2e-*`、`验收`、`walk-*`、`smoke` 等），确认
   `NBLANE_ROOT=$PWD/.dev-data nblane validate demo` 通过。
   e2e 现在会在跑完后还原 `dev`，不会再往里堆残留（见 `tests/e2e/README.md`）。
3. 需要 `ffmpeg`（带 `libwebp_anim`）和 Playwright 的 chromium（`npm install`）。

## 录制

```bash
node scripts/readme-gifs/record.mjs dist/readme-gifs        # 全部场景
node scripts/readme-gifs/record.mjs dist/readme-gifs home   # 单个场景
scripts/readme-gifs/to-webp.sh                              # 输出到 docs/assets/readme/
```

场景：`home`（星图）、`loop`（项目 → 证据 → 技能树）、`research`（研究台 →
阅读器）、`content`（内容工作台 → 公开站点）。

## 为什么星图是逐帧截的

服务器没有 GPU，chromium 用软件渲染 WebGL。边录视频边渲染时，星图只有约
9 fps，录出来一卡一卡的。所以 `home` 场景冻结页面时钟，每推进 1/15 秒截一张图，
得到均匀的 15 fps。录 10 秒大约要 2.5 分钟。其他页面没有 WebGL，直接录视频，
滚动用小步滚轮模拟，不会整页跳动。

## 裁剪和体积

录制脚本会在 `<场景>.cuts.json` 里记录加载空白的时间段（点击到内容出现之间的
等待）。`to-webp.sh` 用 ffmpeg `select` 滤镜把这些段落剪掉，让输出直接从点击
跳到渲染完的画面。场景节奏变了就重新录制——录制脚本等的是内容可见，不是固定
延迟。

默认 800 px 宽、质量 55，四段合计约 3 MB（home 670 KB、loop 530 KB、research
1.5 MB、content 400 KB）。可用 `DEMO_WIDTH`、`DEMO_QUALITY` 调整。不用 GIF 是
因为 GIF 只有 256 色，同样帧率下体积是 WebP 的两倍多。

环境变量：`NBLANE_DEMO_BASE_URL`、`NBLANE_DEMO_USER`、`NBLANE_DEMO_PASSWORD`、
`PLAYWRIGHT_CHROMIUM_EXECUTABLE`。
