---
status: active
owner: engineering
last_verified: 2026-11-15
source_of_truth: true
---

# macOS 桌面贴纸

桌面贴纸是独立的 Electron 客户端，连接已有 nblane 服务并显示 `/p/<档案>/mini`。关闭普通浏览器或打开它的网页，不影响贴纸继续运行。它不内置 Python 服务，也不复制档案文件；任务、清单与日课仍使用服务端的原有接口。交付与验收状态见 [当前状态](../project/status.md)。

## 自用安装（无需开发工具）

使用已打包的应用不需要安装 Node.js、Python，不需要自己编译，也不要求购买 Apple 开发者账号。下面的源码和打包命令只面向维护者。

1. 打开网页「设置 → 桌面贴纸」，点击「下载 Mac 版 · Apple 芯片」或「下载 Mac 版 · Intel」。可在苹果菜单的“关于本机”查看芯片类型；下载按钮只显示已发布的包。
2. 双击解压，将 `nblane Sticker.app` 拖入“应用程序”，再打开它。需要 macOS 13 或更新版本。
3. 填写已有档案名，保留默认网站地址，并用原有 nblane 账号登录。

如果首次出现“无法验证开发者”或“Apple 无法检查是否包含恶意软件”的提示，在确认下载来源可信后，可前往“系统设置 → 隐私与安全 → 仍要打开”，按系统提示确认。此流程仅适用于未验证开发者或未公证的提示；“应用已损坏”等其他错误不能假定用同一步骤解决。不要关闭 Gatekeeper。参见 [Apple 的说明](https://support.apple.com/en-us/102445)。

名称带 `-unsigned` 的交叉构建包仅用于检查内容，不提供完整应用签名，不应作为安装包交付。`-candidate` 包补全了递归 ad-hoc 签名，但仍需在 Mac 上验签和启动；不能把结构检查通过当作 macOS 放行。可用版本与验收结果见 [当前状态](../project/status.md)。

## 使用

1. 首次填写服务地址（默认 `https://www.nblane.cloud`）和已有档案名称。
2. 在贴纸内使用原有 nblane 账号登录。桌面客户端使用自己的持久会话，不读取浏览器的 Cookie；首次需要单独登录。
3. 使用顶部空白区域拖动、窗口边缘调整尺寸。顶部「已置顶 / 置顶」、贴纸设置里的「始终置顶」和菜单栏开关同步，立即生效并在重开后保持选择。默认开启，切换普通应用时贴纸仍在其窗口上方；系统界面、全屏空间的显示受 macOS 管理。
4. 在顶部调整不透明度：100% 完全不透明，40% 最透明。该设置作用于整个窗口，文字也会一起变淡；这不是只透明背景的毛玻璃效果。

顶部采用细高光、柔和局部阴影和短促按压 / 切换动效，窗口使用系统原生阴影。启用系统「减少动态效果」后关闭这些动画。透明度仍作用于整窗，不是背景独立模糊的 Liquid Glass 材质。

菜单栏中的 nblane 图标可以显示或隐藏贴纸、恢复 100% 不透明、切换置顶、设置开机启动和退出。关闭贴纸窗口会隐藏到菜单栏；选择“退出 nblane 贴纸”或按 `⌘Q` 才结束进程。开机启动默认关闭，仅打包后的 macOS 应用提供该选项。

窗口位置、尺寸、服务地址、档案、不透明度和置顶选择会保存在客户端自己的应用数据目录。显示器布局改变后，窗口恢复到可见范围。登录页和任务页在文档就绪后显示，网页内部切换页面不会重新盖上连接遮罩。连接等待超过 20 秒会显示超时；连接中或失败时都可以重试或修改服务地址，失败提示保留简短的网络错误原因。

服务需要 HTTPS；本机开发允许 `http://localhost:<端口>`、`http://127.0.0.1:<端口>` 和 IPv6 回环地址。只填写服务根地址，不填写账号、令牌或页面路径。

## 维护者：从源码运行

需要 Node.js 24 和 npm。在 macOS 上执行：

```bash
npm ci --prefix desktop
npm start --prefix desktop
```

首次启动会下载锁定版本的 Electron。客户端代码在 `desktop/`；工具栏颜色由 SPA 的 `theme.ts` 生成，执行 `npm run prepare:theme --prefix desktop` 更新。

## 维护者：打包

在 macOS 上构建对应架构：

```bash
npm ci --prefix desktop
npm test --prefix desktop
npm run package:mac --prefix desktop -- --arch=arm64
# Intel:
npm run package:mac --prefix desktop -- --arch=x64
```

输出位于 `dist/desktop/`，包含 `.app`、ZIP 和 SHA256。打包脚本在 macOS 上做本地 ad-hoc 签名并校验；该签名不等于 Apple Developer ID 签名或公证。对外正式分发前需要在 macOS 上接入开发者签名、公证并完成真机验收，不要关闭系统的 Gatekeeper。

仓库的 `macOS Sticker` GitHub Actions 工作流使用对应架构的 Mac runner。打包后会重新解压 ZIP，对解压出的 `.app` 严格验签并执行冒烟测试，全部通过后才上传产物，保留 14 天。它不自动发布到网站或 GitHub Release。直接启动可执行文件的测试并不等于 Gatekeeper 已接受互联网下载的应用；顺畅对外分发仍需 Developer ID 签名、公证与分发验收。

Linux 上可加 `--unsigned` 生成仅供检查的包，存放在 `dist/desktop/inspection/`。该模式未进行应用级签名，不等于产物内部所有可执行文件都没有上游自带的签名。

维护者也可使用官方 [Apple Codesign](https://gregoryszorc.com/docs/apple-codesign/0.29.0/) 的 `rcodesign 0.29.0` 生成候选包：

```bash
NBLANE_STICKER_RCODESIGN=/absolute/path/to/rcodesign \
  npm run package:mac --prefix desktop -- --arch=arm64 --candidate
```

候选包存放在 `dist/desktop/candidates/`，文件名带 `-candidate`。签名器递归签署嵌套代码，并将 `Info.plist` 和资源清单绑定到完整应用签名。它不使用开发者证书、不公证，也不能代替 macOS 原生验签、启动及下载后的系统验收。

## 维护者：发布到网页下载入口

「设置 → 桌面贴纸」读取 `https://www.nblane.cloud/downloads/sticker/latest.json`。设置页向所有登录用户开放；本地窗口偏好仍只在贴纸内修改，不把网页脚本连接到桌面控制接口。

1. 在当前提交运行 `macOS Sticker` 工作流，确认对应架构的打包、最终 ZIP 验签和启动检查通过。
2. 下载成功工作流的原始 ZIP 与 `.sha256` 到独立目录，保留版本化文件名；不要发布 `-unsigned` 或 `-candidate` 包。
3. 校验并生成下载清单：

   ```bash
   node desktop/scripts/release-manifest.mjs --dir=/path/to/artifacts --version=0.1.3 --out=/path/to/latest.json
   ```

   此命令检查文件名和摘要，不代替原生验签或证明产物来源。必须先核实成功的工作流及其提交。

4. 将 ZIP 与摘要放入 `/srv/nblane-downloads/sticker/<版本>/`，再原子替换根目录的 `latest.json`。已发布版本保持不变；回滚时切回旧清单。
5. Caddy 将 `/downloads/sticker/*` 映射到该独立目录，关闭目录列表，ZIP 返回 `Content-Disposition: attachment`。清单返回 `Cache-Control: no-cache`、`Access-Control-Allow-Origin: *`；版本化 ZIP 可长期缓存。不要把私有数据目录作为下载根目录。
6. 验证公开域名的清单、ZIP 下载响应与 SHA256，再更新网页代码。

ZIP 和清单不进源码 Git；正式下载在服务器长期保留，不依赖 Actions 14 天过期的 artifact 链接。网页会在清单不可用或验证失败时显示重试，不提供猜测的下载地址。当前 ad-hoc 签名包仍需用户首次在 macOS 确认打开，签名类型在界面明确说明。

## 验证与边界

```bash
npm test --prefix desktop
```

自动检查覆盖服务地址与窗口消息校验、配置恢复、窗口可见范围和不透明度边界。安装根目录的开发依赖后，还可以运行真实 Electron 冒烟测试：

```bash
npm ci
npm run test:smoke --prefix desktop
# macOS：测试从最终 ZIP 解压的应用
npm run test:smoke --prefix desktop -- "--app=/absolute/path/to/nblane Sticker.app"
```

冒烟测试使用临时应用目录和只监听本机的假服务，验证页面连接、SPA 登录跳转、未完成图片不挡住页面、被阻止的重定向、20 秒超时及恢复，以及远程隔离、透明度状态、设置草稿、退出重开和断线恢复，不读取个人档案或登录凭据。`NBLANE_STICKER_USER_DATA` 可为手工开发实例指定独立设置目录。

真实 Mac 还需验收：首次登录、关闭浏览器后独立运行、40%–100% 透明度视觉效果、拖动缩放、多显示器、隐藏后从菜单栏恢复、退出、重开后的设置保持，以及开机启动。

浏览器版小窗继续保留，其画中画限制不变。桌面端的登录状态与普通浏览器隔离，因此两个独立应用之间依靠服务端数据和已有定时刷新同步，不能把浏览器内部的即时跨窗广播当作跨应用同步。

远程任务页面没有 Node.js 或桌面控制接口。本地工具栏通过限定的消息接口修改窗口设置；远程导航限定在用户配置的服务来源，完整项目页在系统浏览器打开。
