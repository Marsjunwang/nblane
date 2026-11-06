# README 动图

`README.md` 里的 GIF 用虚构的 `demo` 档案录制，放在 `docs/assets/readme/`。
界面改了之后按下面步骤重录。

## 准备

1. 起隔离环境：`scripts/dev-web.sh --isolated`（18504，数据在 `.dev-data/`）。
2. 准备 `demo` 档案：`.dev-data/profiles/demo/`，论文资产在
   `.dev-assets/research/profiles/demo/`。没有的话从 `dev` 复制一份，然后
   清掉测试残留（`e2e-*`、`验收`、`walk-*`、`smoke` 等），确认
   `NBLANE_ROOT=$PWD/.dev-data nblane validate demo` 通过。
   e2e 现在会在跑完后还原 `dev`，不会再往里堆残留（见 `tests/e2e/README.md`）。
3. 需要 `ffmpeg` 和 Playwright 的 chromium（`npm install`）。

## 录制

```bash
node scripts/readme-gifs/record.mjs dist/readme-gifs        # 全部场景
node scripts/readme-gifs/record.mjs dist/readme-gifs home   # 单个场景
scripts/readme-gifs/to-gif.sh                               # 转 GIF 到 docs/assets/readme/
```

场景：`home`（星图）、`loop`（项目 → 证据 → 技能树）、`research`（研究台 →
阅读器）、`content`（内容工作台 → 公开站点）。

`to-gif.sh` 里的裁剪时间点用来剪掉页面加载时的空白帧。场景节奏变了就重新量：
`ffmpeg -i dist/readme-gifs/home.webm -vf "fps=2,signalstats,metadata=mode=print:key=lavfi.signalstats.YAVG:file=-" -f null -`，
亮度接近 37 的帧是空白的深色背景。

每个 GIF 控制在 2 MB 左右（800 px 宽、6 到 8 fps）。

环境变量：`NBLANE_DEMO_BASE_URL`、`NBLANE_DEMO_USER`、`NBLANE_DEMO_PASSWORD`、
`PLAYWRIGHT_CHROMIUM_EXECUTABLE`。
