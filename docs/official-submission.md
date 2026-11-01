# Kodi 官方仓库提交准备

候选版本：`service.subtitles.thunder` 0.3.1。

## 已完成

- GPL v2 完整许可证和来源说明；简繁转换代码的上游版本已记录。
- 英语、简体及繁体中文元数据，英文更新记录，项目及问题反馈链接。
- requests、chardet 声明最低版本，由 Kodi 官方仓库提供。
- 原创 512×512 不透明图标、1920×1080 背景及绘制源码；移除继承的旧素材。
- 入口拆分，移除旧 psyco 导入及未使用的 Python 2 命令行代码。
- 安装包仅含运行所需源码、语言、设置、素材、说明与许可；无 pyc、测试或开发工具。
- UTF-8 无 BOM、LF 换行，ZIP 内文件权限 0644。
- 39 项本地回归测试通过。
- kodi-addon-checker 0.0.36，目标 matrix，启用 PR 和依赖检查：0 个问题、0 个警告。

检查器从 Kodi 官方镜像 `https://ftp.fau.de/xbmc/addons/` 读取所有版本的真实仓库索引。
替换索引下载地址是为避开默认 HTTP 地址与镜像跳转问题，没有关闭依赖检查或放宽规则。
Windows 下官方检查器跳过 POSIX 可执行权限检查；ZIP 权限已另行核对，CI 在 Linux 重跑官方检查。
检查日志由 CI 保存，源码中的复现命令见 README。

## 提交前验证

0.2.1 已经在 Windows Kodi 19 实测。0.3.1 的入口拆分目前通过自动化测试，尚未做新版本的播放器实测；Android TV 也尚未实测。

安装 0.3.1 后，在 Kodi 中验证以下流程：

1. 播放视频，打开「字幕 → 下载字幕 → Thunder」，检查自动搜索及中文字幕名称。
2. 手动搜索英文片名和年份，例如 `Spider-Man.2.2004`。
3. 下载 SRT 或 ASS，确认播放器加载；再验证 ZIP 多字幕选择与取消。
4. 开启 UTF-8 和简繁转换后重复下载，检查中文显示。

## 官方提交

本分支为准备版本，尚未向 Team Kodi 提交审核，也不代表获得官方认可。

实测完成后，重新核对官方接收分支，将构建暂存目录中的 `service.subtitles.thunder/`
以一个提交放入 `xbmc/repo-scripts` 的独立分支。PR 标题使用 `[service.subtitles.thunder] 0.3.1`。
开发工具、CI、测试及本文件不放入官方仓库的插件目录。

字幕搜索访问迅雷现有 CID 与名称接口，不需要登录，不上传视频内容。它不是官方授权 SDK；
接口稳定性、字幕来源以及是否收录仍由维护者和 Team Kodi 审核。

要求参考：

- https://kodi.wiki/view/Add-on_rules
- https://kodi.wiki/view/Submitting_Add-ons
- https://github.com/xbmc/repo-scripts/blob/master/CONTRIBUTING.md
- https://github.com/xbmc/addon-check
