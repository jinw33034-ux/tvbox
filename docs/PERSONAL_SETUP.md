# TVBox 多设备个人配置

本版是可扩展的空配置基线：`sites`、`lives`、`parses` 均为空，导入后没有影视站点或直播，这是预期行为。尚无用户确认授权的接口；不能将静态校验成功理解为已有视频可播放。

## 托管和订阅

上游 https://github.com/qist/tvbox ，实际默认分支 `master`。个人仓库 https://github.com/jinw33034-ux/tvbox 。功能分支 `feature/personal-tvbox-config`，不修改个人仓库的 `master`，不向上游提 PR。

功能分支提交并验证后可使用：

```text
https://raw.githubusercontent.com/jinw33034-ux/tvbox/feature/personal-tvbox-config/personal.json
```

该地址始终跟随功能分支，保留该分支即可长期使用。PR 合并、`master/personal.json` 实际可访问后，可统一将设备迁移为：

```text
https://raw.githubusercontent.com/jinw33034-ux/tvbox/master/personal.json
```

后一地址在合并前不可用。其他仓库的通式为 `https://raw.githubusercontent.com/<owner>/<repo>/<实际分支>/personal.json`。部署状态以交付报告为准。私有仓库的普通 Raw 地址不能保证匿名读取；不要把 GitHub Token 嵌入地址。

## Android TV / 电视盒子

1. 从 https://github.com/FongMi/Release 及 https://github.com/FongMi/TV 核对维护者提供的实际 APK。电视通常选 `leanback`，依据设备 CPU 和实际文件名选架构，不凭设备外观猜测。
2. 已通过 GitHub Release API 核实 [5.8.2 发布页](https://github.com/FongMi/Release/releases/tag/5.8.2)，包含 `leanback-arm64_v8a.apk`、`leanback-armeabi_v7a.apk`、`mobile-arm64_v8a.apk`、`mobile-armeabi_v7a.apk`。这是本次核对版本，不自动追随未来版本。默认分支仅含 `.gitignore`，安装包在 Releases 中，不在代码目录。未下载、安装或执行 APK。
3. 安装后按功能需要授予最低权限，找到设置中的配置/点播配置入口（名称依版本不同），输入上面的功能分支地址。
4. 重新加载。当前应无站点；接入授权来源后逐项测试站点、搜索、点播、直播。可记录“设备型号、Android 版本、CPU、客户端版本、源 key、报错和时间”，不要附带凭证。

## Android 手机 / 平板

1. 同一官方入口，若提供适用的 `mobile` 包，按实际架构安装。
2. 在应用配置入口填入与电视相同的订阅 URL 并重新加载。
3. 用相同内容测试；如存在差异，记录客户端和设备版本后再决定是否拆分配置。Windows、iOS/iPadOS、macOS 以及非 Android 电视兼容性未验证。

多设备共享的是配置，播放历史、进度、账号状态不会由本项目自动同步。无需 NAS、VPS、Docker 或常开电脑。

## 添加授权来源

先在 `SOURCE_AUDIT.md` 记录服务提供者、原始 URL、授权依据及适用地区/设备，再添加一个源。仅有网站可访问或购买会员不能证明存在可在 TVBox 中使用的授权接口。

本校验器支持常见的扁平 `sites`、`lives` 和 `parses` 配置：站点要求 `key/name/type/api`，直播和解析要求 `name/type/url`。高级分组直播等格式需先扩展校验器并核对客户端结构；不要直接绕过报错。

本地文件使用 `./` 开头且大小写完全一致。`ext` 支持嵌套对象引用。`csp_` 类站点需要独立审查的 spider；当前不启用任何 JAR、JS、Python、解析或代理。依赖的二次导入需人工审查，静态校验器不会执行或解析任意插件源码。

```powershell
python scripts/validate_personal.py
python -m unittest discover -s scripts -p 'test_*.py' -v
python scripts/validate_personal.py --network --max-urls 10 --timeout 8
```

Python 3.10+，无需 pip 依赖。默认只检查 `personal.json` 及其直接文件引用；不会扫描或执行上游插件。`--network` 是主动外连，仅在静态检查通过后，最多探测 10 个 URL（上限 25），每次超时默认 8 秒，仅读取前 1024 字节；模板 URL 跳过，失败返回非零。HTTP 可达不代表授权、安全或可播放。远程 JAR MD5 不自动下载校验，建议先取得来源并本地审查后固定版本。

## 更新、上游与回滚

日常：编辑 `personal.json` → 审核来源 → 运行校验和测试 → 在功能分支提交 → 设备重新加载。GitHub Raw 有缓存，必要时等待并重启客户端；不要随意更换代理服务。

上游：记录当前个人提交后，拉取 `qist/tvbox`，比较差异，仅按需同步文件。`README.md`、`jsm.json` 和原目录均保留；不要用上游综合配置覆盖个人配置。上游已有定时抓取和改写资源的 workflow；Fork 中保持其禁用，不点击“启用所有工作流”。本次仅新增个人校验工作流，读权限、不运行第三方源。若 Fork 默认禁用 Actions，本地命令仍可完成全部校验。

回滚：记录已验证提交 SHA；使用 `git revert <有问题的个人提交>` 并重新校验，在功能分支推送回滚。或在 GitHub PR 文件页面恢复某个已验证版本。不要强制推送覆盖历史。需要不可变订阅时使用 `https://raw.githubusercontent.com/<owner>/<repo>/<完整提交SHA>/personal.json`，更新时需逐设备更换。

Windows 检出存在上游大小写冲突：`cat/js/AppYsV2.js` 与 `cat/js/appysv2.js`、`js/LIBVIO.js` 与 `js/libvio.js`。GitHub/Linux 区分它们；普通 Windows 文件系统无法同时完整呈现。不要 `git add .` 提交这些意外差异；只暂存个人新增文件，或在 WSL/Linux 大小写敏感目录维护完整仓库。

## 故障定位

| 现象 | 检查 |
|---|---|
| 配置下载失败 | 仓库是否公开、分支是否存在、文件已提交、设备是否可直连 GitHub Raw |
| 没有站点 | 本基线预期为空；接入后检查 JSON、客户端兼容和日志 |
| 有站点但打不开 | 接口状态、授权、插件版本、设备编解码和网络 |
| 本地依赖丢失 | 是否完整保留原相对目录、文件名大小写、JAR MD5 |
| 更新没生效 | 分支地址、客户端重新加载、Raw 缓存 |
| 手机/电视表现不同 | 客户端版本、架构、协议、IPv4/IPv6 和插件支持 |

## 本地交付包

`tvbox-personal-overlay.zip` 只包含个人新增文件，不包含完整上游依赖，也不等同完整 Fork。解压覆盖到上游根目录后运行校验。`personal-config.patch` 是相对已记录上游提交的新增补丁，用 `git apply --check` 审查后再 `git apply`。原有文件不要删除。
