---
status: active
owner: engineering
last_verified: 2026-10-26
source_of_truth: true
---

# 安卓 PWA 与 TWA

nblane 的安卓入口共享同一个 SPA，不包含另一套移动业务页面，也不包含服务器监控页。PWA 和 TWA 都从 `https://www.nblane.cloud/` 打开现有首页，登录、项目、论文、车间和 OpenClaw 继续使用现有功能。

## 两种使用方式

- **PWA**：用安卓 Chrome 打开上述地址，在菜单中选择「添加到主屏幕」。图标来自 `manifest.webmanifest`，页面以 standalone 模式打开。
- **TWA**：安装构建出的 APK。应用与域名通过 `/.well-known/assetlinks.json` 建立信任后，以全屏 TWA 打开；无法验证时使用 Chrome Custom Tab，不改成自研 WebView。

只缓存应用静态壳。账号、论文、API 响应、Reader handoff、车间和 OpenClaw 不通过 service worker 做业务离线缓存；普通网页更新不需要重新安装 APK。

## 当前进展与后续范围

截至 2026-10-26，已交付：

- PWA 基础版已部署到正式域名，包含安装 manifest、静态离线提示页、受控缓存和更新提示。
- TWA 内测包已实际构建并签名，版本 `0.1.0`（`appVersionCode: 1`）；产物为 `dist/android/nblane-0.1.0-twa.apk` 和对应 `.aab`，均附 SHA-256 校验文件。`scripts/package-android.sh` 已跑通 lint、单元测试、构建、签名和 APK 检查。
- 正式域名关联文件已配置，公开指纹与内测 APK 签名一致。网页功能更新继续走 SPA 部署，不需要重新生成 APK。

验证边界：**尚未完成真实安卓设备安装与交互验收，不能仅凭构建成功或移动设备仿真宣称 TWA 已完成。** 当前服务器没有可用于验收的已连接设备；设备型号、Android 与 Chrome 版本尚未记录。Google PageSpeed API 请求失败，没有取得评分，不能记为通过。

下次开发按以下顺序接续：

1. 用本地下载、手机文件传输或 ADB 安装 APK，完成下文的真机验收清单，并记录设备型号、Android 与 Chrome 版本及问题截图。PWA 也需在真机确认安装、独立窗口和更新提示。
2. 实现文章、论文与业务数据的离线能力；需先明确登录数据隔离、缓存失效和私密内容清除规则，不能直接把所有 API 响应交给 service worker 缓存。
3. 实现推送与后台提醒；推送通道和设备覆盖尚需确认。
4. 实现设备授权与桌面小组件。
5. 实现受限远程维护，保留鉴权、操作范围和审计边界。
6. 完善发布自动化与应用商店发布；商店账号、发布签名和发布凭据另行确认，不写入仓库。
7. 推进 Kotlin 原生重写；当前交付仍是共享 SPA 的 PWA/TWA，不是原生业务应用。

已确认的范围：**PWA 和 TWA 都需要，不做服务器监控页。** 上述离线、推送、设备授权、小组件、远程维护、商店发布和原生重写均尚未交付。后续仍需保留同一账号、同一正式域名与同一套网页业务功能。

## 固定应用身份

| 配置 | 值 |
|------|----|
| 正式 origin | `https://www.nblane.cloud` |
| applicationId | `cloud.nblane.app` |
| 启动路径 | `/` |
| TWA 配置 | `packaging/android/twa/twa-manifest.json` |
| 域名关联 | `src/nblane/web_ui/frontend/public/.well-known/assetlinks.json` |

不要混用其他域名作为 App 启动地址，否则 Cookie、TWA 信任和 assetlinks 都需要重新核对。`spa.nblane.cloud` 与 `www.nblane.cloud` 不是同一个 Cookie 主机。

## 构建环境

需要：

- Node.js ≥ 18、npm。
- JDK 17；Bubblewrap 不以系统较新的 JDK 替代这一要求。
- Android SDK、platform-tools、对应 platform 与 build-tools。
- 使用 `@bubblewrap/cli@1.27.0`，不要求全局安装。

本机开发工具位于 `.dev-data/android-sdk` 和 `.dev-data/android-home`，均已 gitignore。其他机器可设置 `JAVA_HOME`、`ANDROID_HOME`，或在 `$HOME/.bubblewrap/config.json` 中写入 `jdkPath` 和 `androidSdkPath`。`NBLANE_ANDROID_BUILD_HOME` 可指定独立的 Gradle/Bubblewrap home，`NBLANE_GRADLE_USER_HOME` 可单独覆盖 Gradle 缓存目录，默认使用构建 home 下的 `.gradle`。

修改 `twa-manifest.json` 后，用 Bubblewrap 重新生成工程：

```bash
HOME="$PWD/.dev-data/android-home" npx --yes @bubblewrap/cli@1.27.0 update \
  --directory="$PWD/packaging/android/twa" \
  --manifest="$PWD/packaging/android/twa/twa-manifest.json" \
  --skipVersionUpgrade
```

`update` 会重建生成的 Android 文件；不要在未检查自定义改动时盲目覆盖。版本升级必须提高 `appVersionCode`，普通 Web 更新不需要执行它。

## 签名与密钥

内测签名放在 `.dev-data/android-signing/`，不进入 Git：

- `nblane-upload.p12`：签名 keystore，权限 `0600`。
- `signing.env`：构建所需密码和路径，权限 `0600`。
- 默认 alias：`nblane`。

应备份整个签名目录。丢失后不能用同一应用身份覆盖升级；商店上传 key、Play App Signing 和本地内测证书是不同概念，最终商店指纹需要加入 assetlinks。私钥、密码和签名材料不能提交到仓库或打印到日志。

`assetlinks.json` 只包含 applicationId 和证书的公开 SHA-256 指纹，可以公开访问。更换证书时必须同步更新指纹并重新部署，然后验证 TWA 信任。

## 一键检查与构建

在仓库根目录执行：

```bash
scripts/package-android.sh
```

脚本先运行 `lintDebug`、`testDebugUnitTest`、`assembleDebug`，再调用 Bubblewrap 构建、签名并检查 APK，输出到 `dist/android/`：

```text
nblane-<壳版本>-twa.apk
nblane-<壳版本>-twa.apk.sha256
nblane-<壳版本>-twa.aab
nblane-<壳版本>-twa.aab.sha256
BUILDINFO
```

默认自动读取本机 `.dev-data/android-signing/signing.env`；也可用 `NBLANE_ANDROID_KEYSTORE`、`NBLANE_ANDROID_KEY_ALIAS`、`BUBBLEWRAP_KEYSTORE_PASSWORD`、`BUBBLEWRAP_KEY_PASSWORD` 从环境提供，不把密码写进命令参数。

默认要求 Git 工作树干净。开发构建可用 `NBLANE_ANDROID_ALLOW_DIRTY=1`；`NBLANE_ANDROID_SKIP_PWA_VALIDATION=1` 只用于明确跳过远程质量检查的调试，不代替正式验收。`NBLANE_ANDROID_OUT` 可改输出目录。

## 安装与验收

校验 APK：

```bash
cd dist/android
sha256sum -c nblane-<壳版本>-twa.apk.sha256
```

把 APK 传到测试手机，按系统提示允许本次安装来源。首版是内部测试包，不表示已经上架应用商店。

真机至少检查：

1. 图标、冷启动、全屏、正式域名信任和无地址栏。
2. 登录保持、会话过期后重新登录、所有现有页面与返回键。
3. 后台恢复、车间键盘/快捷输入/回车及 WebSocket 重连。
4. 论文库 handoff、阅读器翻页、PDF 和外链。
5. 后台数据更新后，网页变化无需重装 APK。
6. PWA 添加到主屏幕、断网提示、恢复网络，以及更新时未保存编辑不被强制刷新。

Playwright 移动仿真不能替代这些真机检查。调试签名、release 签名和商店签名的指纹必须分别验证，不能只看构建成功。

## 静态部署

PWA 静态文件由 Vite 构建到 `src/nblane/web_ui/static/` 并提交。生产仍通过 Git 快进和现有 `nblane-web-api` 服务提供，不新增端口，也不把文件放到 Reader 或公开个人站点。

`/.well-known/assetlinks.json` 必须无需登录直接返回 JSON，不是 SPA 的 HTML fallback。manifest、图标和 SW 使用静态根 `no-cache`，内容哈希 `/assets/*` 继续 immutable；`pyproject.toml` package-data 和 Ubuntu 离线包必须包含这些文件。

同步修改后，检查：

```bash
curl -fsS https://www.nblane.cloud/manifest.webmanifest
curl -fsS https://www.nblane.cloud/.well-known/assetlinks.json
packaging/android/twa/gradlew -p packaging/android/twa \
  lintDebug testDebugUnitTest assembleDebug
```

生产仍按[腾讯云部署](deployment-tencent-cloud.md)更新。安装包生成见 [Ubuntu 离线安装包](ubuntu-package.md)。
