# 来源和依赖审查

审查日：2026-10-25（Asia/Shanghai）。上游 `qist/tvbox`，默认分支 `master`，本地基准提交 `01091f4bd07b1d3afc8dbe5fb25d9da9f0b22a25`。这是一次快照，不代表未来状态。

## 实际结构与决策

已读取 README、`jsm.json`、Git 文件树和原有 workflow。`jsm.json` 是严格 JSON，含 152 个站点、3 个直播配置、29 个解析；顶层还包含 spider、wallpaper、danmaku、hosts、flags、doh、rules、ads。配置规模仅作结构调查，不代表已逐源审查。

实际目录包括 `jar/`（8 文件）、`js/`（含中文路径，完整清单见 Git 文件树）、`lib/`、`py/`、`json/`、`live/`（6 个地区/运营商列表）、`FTY/`、`XBPQ/`、`XYQBiu/`、`XYQHiker/`、`biliext/`、`cat/`、`tools/`、`xiaosa/`。`0821.json`、`0825.json`、`0826.json`、`0827.json`、`fty.json` 均存在，第一版无需导入。

本次新增 `personal.json` 仅含 4 个空数组。不设置 spider、壁纸、代理、DoH、广告或规则。直接本地依赖 0，启用外部 URL 0；所以不需要复制 JAR，不产生缺失插件。不删除任何上游资源；不能据“个人配置未引用”推断整个上游无人引用。

| 项目 | 用途和来源 | 授权/许可情况 | 默认启用 | 处理 |
|---|---|---|---|---|
| 个人空配置 | 本次新建 personal.json | 不包含影视内容 | 是 | 无可播放源，等待授权接口 |
| 上游综合配置 | https://github.com/qist/tvbox/blob/master/jsm.json | README 明示无法保证合法性；未找到 LICENSE | 否 | 仅保留作参考，不作为订阅 |
| spider.jar | 上游 jar/spider.jar | 未逐文件审计，许可和执行行为待确认 | 否 | 本地保留，不加载、不执行 |
| drpy2 / drpy | 上游 lib/drpy2.min.js、js/drpy.js | 脚本及所访问内容的权限需分别确认 | 否 | 不复制到个人配置 |
| Python / 其他 JAR / JS | 上游 py/、jar/、js/、lib/ | 没有完成代码和许可审计 | 否 | 不运行 |
| 上游 migu 直播项 | develop202.github.io/migu_video/interface.txt | 第三方列表，未取得内容提供方对本使用方式的授权证据 | 否 | 待用户提供明确授权接口 |
| 上游 live 直播项 | epg.pw/test_channels.m3u | 列表可访问不等同频道传播授权 | 否 | 不探测其中视频 |
| IPv6 / 本地直播列表 | tvboxtv.txt、list.txt 等上游文件 | 频道来源与授权未逐一确认 | 否 | 保留，不启用 |
| 第三方解析、壁纸、EPG、Logo、弹幕、代理 | jsm.json 对应字段 | 非必要；许可、隐私和可用性待确认 | 否 | 不引入额外网络依赖 |
| 客户端 | https://github.com/FongMi/Release/releases/tag/5.8.2 ，https://github.com/FongMi/TV | 已核实官方 5.8.2 四种电视/移动端 APK 文件名；未审计 APK | 不适用 | 未下载 APK、实机兼容性未验证 |
| 上游自动更新 | .github/workflows/run.yml | 会安装依赖并执行第三方抓取和改写 | 否 | 不启用；个人校验独立 |

README 的免责文字不是内容授权许可；仓库公开也不证明所有代码可任意再分发。用户已明确授权公开 Fork，仍需在正式接入前分别确认插件许可和服务授权。

## 凭证及执行边界

另已核对 FongMi/TV 的 `fongmi` 分支源码：`app/src/main/java/com/fongmi/android/tv/api/config/VodConfig.java` 的 `initSite`、`initParse` 对空数组有空对象回退，`initLive` 对空直播返回。说明本基线与该源码结构相符，仍不能替代已发布 APK 的实机导入测试。

不收集用户 Cookie、密码、Token、网盘密钥；不将上游配置内的认证/加密参数复制到个人配置或文档。本次凭证扫描范围是个人 JSON；没有声称整个上游已通过安全扫描。静态检测为启发式，不保证识别所有秘密。

校验器递归检查 JSON 的嵌套 `./` 引用、路径越界、文件大小写、MD5、重复 key/name、字段类型和常见秘密。不会执行 JAR/JS/Python，也不会分析插件中动态生成的 URL、依赖或网络请求。新增插件前要手工追踪全部二次依赖，记录来源和 SHA256；MD5 只提供一致性检查，不构成安全保证。

## 后续接入记录模板

每个新源单独记录：唯一 key、显示名、提供方原始地址、授权证据链接或书面范围（不含秘密）、内容范围/地区、审核日期、所需插件来源/许可/提交/SHA256、本地及二次依赖、网络检查、客户端及实机播放结果。证据和兼容性未确认前保持未启用。
