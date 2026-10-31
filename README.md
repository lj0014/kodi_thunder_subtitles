# Kodi 迅雷字幕（Thunder）

根据正在播放的视频文件的 CID，从迅雷字幕库匹配并下载字幕。面向 Kodi 19 及以上的 Python 3 插件接口；0.2.0 已通过自动测试，仍需在真实 Kodi 中验证。

## 安装和使用

1. 下载插件 ZIP（`service.subtitles.thunder-0.2.0.zip`），不要直接安装 GitHub 的源码 ZIP。
2. Kodi → 设置 → 插件 → 从 ZIP 文件安装，选择插件 ZIP。若提示，先允许未知来源。依赖 `script.module.requests` 和 `script.module.chardet` 由 Kodi 安装。
3. 播放视频，打开字幕菜单，选择下载字幕，再选择 **Thunder**。
4. 选择搜索结果。ZIP 中包含多个字幕时，会提示选择其中一个。
5. 插件设置中可开启“文本字幕保存为 UTF-8”，再选择简体或繁体转换；默认保留原编码。

## 0.2.0 改进

- 替换 Kodi 20 已移除的 `xbmc.translatePath`，使用 `xbmcvfs.translatePath`。
- 修复带有 `&`、`=`、`+` 等字符的字幕下载链接被截断的问题。
- 真正下载并保存字幕到插件数据目录，然后进行编码和简繁转换。
- 请求设置连接和读取超时；搜索最多尝试 3 次，区分服务错误和无匹配结果。
- 校验文件读取和定位结果，处理空文件、无法定位的流和读取不足。
- 支持 ZIP 内字幕选择，限制下载及解压总大小为 20 MiB，避免使用压缩包提供的目录路径。
- 搜索不再删除已下载字幕；失败时显示提示，并完成 Kodi 目录回调。
- 中英文、繁体中文错误提示；日志不记录媒体凭据或字幕签名链接。

## 支持范围和限制

- 这是**文件哈希匹配**，迅雷此接口不支持片名搜索。手动搜索会提示后继续匹配当前视频。
- 本地视频及可随机定位的 Kodi VFS 文件可参与匹配（例如 SMB/NFS，取决于 Kodi 的访问权限）。实时流、无法读取大小或无法定位的 HTTP 流无法计算 CID。
- 支持直接字幕及 ZIP；暂不支持 RAR、7z。文本扩展名包括 SRT、ASS、SSA、SMI、VTT、SUB、TXT。二进制 VobSub 不转换编码，配套 IDX 文件下载尚不支持。
- 仍使用原项目的第三方接口 `http://sub.xmp.sandai.net:8000/subxl/{CID}.json`。2026-10-31 实测 HTTP 200：全零测试 CID 返回 10 条有效记录，随机 CID 返回空列表；返回列表中《指环王》的中文字幕可下载，且可转换为 UTF-8。全零 CID 不是实际电影指纹，此检查证明接口及下载链路可用，尚未验证真实视频的匹配准确度。其可用性、字幕覆盖率和返回准确性由迅雷决定；HTTP 不提供传输加密。
- 本地自动测试使用模拟网络和 Kodi 接口，不能替代真实 Kodi 中的播放测试。
- 下载的字幕保留在 Kodi 插件数据目录 `addon_data/service.subtitles.thunder/`，可在停止播放后手动清理。

## 开发、测试和打包

```sh
python -m pip install -r requirements-dev.txt
python -m unittest discover -s tests -v
python tools/build.py
```

安装包位于 `dist/`，顶层目录是 `service.subtitles.thunder/`，只包含运行文件和资源。GitHub Actions 在 Python 3.8、3.11、3.13 下运行测试，并提供安装包构建产物；不会自动发布 Release。

建议真机检查：本地视频匹配、SMB 视频匹配、含签名参数的下载链接、ZIP 多字幕选择和取消、UTF-8/简繁转换、断网提示、重新搜索后已加载字幕是否仍可使用。

## 来源

基于 [Shooter 字幕插件](https://github.com/taxigps/service.subtitles.shooter) 改造；迅雷 CID 算法和查询思路来自 [weaming/thunder-subtitle](https://github.com/weaming/thunder-subtitle) 及其引用的 xunlei-lixian 项目。保留原有简繁转换库和资源。插件元数据沿用原有 GPL v2 声明。

