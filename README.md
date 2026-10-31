# Kodi 迅雷字幕（Thunder）

Kodi 中文字幕下载插件。播放影片时，根据视频文件的 CID 匹配迅雷字幕，下载后加载到播放器。

支持 UTF-8 编码转换、简繁转换和 ZIP 字幕包。

## 兼容性

- Kodi 19 及以上版本（Python 3）。
- 0.2.1 已在 Windows 版 Kodi 19 实测，字幕搜索、下载和加载正常。
- Android TV 尚未实测。

## 安装和使用

1. 下载插件安装包 `service.subtitles.thunder-0.2.1.zip`。
2. 在 Kodi 中打开 **设置 → 插件 → 从 ZIP 文件安装**，选择安装包。首次安装可能需要开启“未知来源”。
3. 播放影片，打开 **字幕 → 下载字幕 → Thunder**。
4. 选择字幕。ZIP 包含多个字幕时，可选择其中一个文件。

依赖 `script.module.requests` 和 `script.module.chardet`，由 Kodi 安装。

在插件设置中开启“文本字幕保存为 UTF-8”后，可选择简体或繁体转换。默认保留原编码。

## 使用说明

- 按视频文件匹配字幕，不支持片名搜索。手动搜索仍会匹配当前播放文件。
- 支持本地文件和可读取、可定位的网络文件，如 SMB、NFS。无法获取文件大小或随机定位的流媒体不能参与匹配。
- 支持 SRT、ASS、SSA、SMI、VTT、SUB、TXT 及 ZIP 包。暂不支持 RAR、7z 和需要配套 IDX 文件的 VobSub 字幕。
- 下载及 ZIP 解压总大小上限为 20 MiB。
- 字幕库不一定包含当前视频版本的字幕。部分旧字幕名称已在源站损坏，列表会清理乱码并保留可读部分。
- 下载文件保存在 Kodi 插件数据目录 `addon_data/service.subtitles.thunder/`，停止播放后可手动清理。

## 更新记录

### 0.2.1

- 修复字幕列表名称乱码，兼容旧中文编码、URL 转义名称和部分可恢复的乱码。

### 0.2.0

- 修复 Kodi 20 及以上版本的路径接口兼容问题。
- 修复含特殊字符的下载链接、字幕保存、UTF-8 编码及简繁转换。
- 增加网络超时、错误提示、ZIP 多字幕选择和下载大小限制。

## 开发

安装依赖并运行测试：

```sh
python -m pip install -r requirements-dev.txt
python -m unittest discover -s tests -v
```

构建安装包：

```sh
python tools/build.py
```

安装包输出到 `dist/`，顶层目录为 `service.subtitles.thunder/`。GitHub Actions 在 Python 3.8、3.11、3.13 下运行测试并构建安装包。

## 来源与许可

基于 [Shooter 字幕插件](https://github.com/taxigps/service.subtitles.shooter) 改造。迅雷 CID 算法和查询代码参考 [weaming/thunder-subtitle](https://github.com/weaming/thunder-subtitle) 及其引用的 xunlei-lixian 项目，沿用原有简繁转换库和资源。

许可证沿用插件元数据中的 GPL v2 声明。
