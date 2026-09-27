# Wallpaper Engine Filter · 壁纸筛选助手

隐藏看过或不喜欢的壁纸，减少重复筛选。

[English](README.md)

- **单张隐藏**：隐藏整张卡片，不占位置。
- **批量隐藏**：勾选要保留的，一键隐藏本页其余壁纸。
- **显示与恢复**：找回已隐藏的壁纸，随时撤回。
- **递进浏览**：选择起始页，翻页时跳过隐藏项并补位；隐藏单张时不补位。
- **订阅区独立**：搜索里隐藏，不影响已订阅列表。
- **备份与恢复**：自动保存名单，支持通过应用外工具恢复或改写。
- **中英文设置**：在插件文件夹设置语言，重开壁纸界面生效。

<details>
<summary>安装、操作与恢复详情</summary>

**留下喜欢的壁纸，不再反复筛选已经看过、不想要的作品。**

简体中文 · [English](README.md) · [兼容性与恢复](docs/COMPATIBILITY.md) · [参与贡献](CONTRIBUTING.md)

在 Wallpaper Engine 里找壁纸时，你可能点开一张作品、确认不喜欢，下一次搜索或翻页时却又遇到它。分类筛选无法记住这些针对单张壁纸的决定。这个项目为 **Wallpaper Engine 软件内部的创意工坊和发现页面**增加个人隐藏名单，让你把时间花在新选择上。

面对一整页结果，还可以先勾选想保留的壁纸，再一键隐藏其余作品。

## 这是插件，还是 Skill？

准确地说，这是 **Windows 上的非官方界面补丁／扩展**，附带一个本地备份程序。它不是 AI Skill，也不是 Chrome 扩展或壁纸播放器，更不是 Wallpaper Engine 官方提供接口的插件。

它通过本地界面入口加载我们编写的脚本，不使用官方插件 API。目前在 **Wallpaper Engine 2.8.42** 上验证过，不能保证其他版本可用。仓库不包含 Wallpaper Engine 的源文件、壁纸作品或程序本体。

## 新增的按钮与用法

| 控件 | 功能 |
| --- | --- |
| **隐藏壁纸／恢复壁纸** | 位于单张搜索结果卡片上，按创意工坊编号记录。隐藏后整张卡片消失，不占位置，后面的壁纸向前补位。 |
| **显示已隐藏／收起已隐藏** | 临时显示当前页被隐藏的壁纸。仍可点击查看详情，或恢复正常显示。括号里的数字是全部隐藏记录数。 |
| **批量隐藏本页** | 进入选择模式，先勾选要保留的壁纸，再点击“隐藏其余 N 张”。勾选的含义是 **保留**。 |
| **递进浏览** | 选择原始起始页，启用后点击“递进下一页”，跳过隐藏项补足一页；隐藏当前卡片时不会立即补位。 |

批量操作分三步：

1. 点击 **批量隐藏本页**。
2. 勾选想保留的壁纸，卡片会出现绿色边框和“已保留”。
3. 核对数量，点击 **隐藏其余 N 张**。

一张都不勾选，就隐藏本页全部尚未隐藏的壁纸；全部勾选时确认按钮不可用。点击“取消”不会改动记录。翻页、切换页面、修改搜索或筛选条件、结果变化时自动退出选择模式；提交时还会再次核对当前页。

**已安装／已订阅列表不受影响。** 已订阅的壁纸仍可在搜索结果里隐藏，回到自己的壁纸库则照常显示。隐藏不会取消订阅、删除文件或更改壁纸内容。

普通模式仅过滤当前页。可选的递进模式使用自己的上一页／下一页，并显示读取的原始页范围。起始页之前的页面不重排，退出递进即可通过普通分页查看。搜索条件改变会退出递进；一次最多检查 20 个原始页，未补满时可继续下一页。最后一页可能不足一页。

**语言设置放在插件文件夹里。** 双击“设置插件语言.cmd”，选择中文或 English，然后重新打开壁纸浏览界面。应用内没有语言下拉框或同步按钮。

## 安装

需要 Windows、通过 Steam 安装的 Wallpaper Engine，以及 **Python 3.10 或更新版本**（包含 `pythonw.exe`，终端能运行 `python`）。运行时只使用 Python 标准库；Node 和 Playwright 仅用于开发测试。

1. 下载仓库 ZIP，解压到一个准备长期保留的文件夹，不要直接在压缩包中运行。
2. 关闭 Wallpaper Engine 的壁纸浏览窗口。
3. 双击 **`install.cmd`**，或者运行：

   ```powershell
   python tools/install.py install
   ```

4. 重新打开壁纸浏览窗口，新增控件会出现在创意工坊标签旁和搜索结果卡片上。

安装器会查找 Steam 游戏库。找不到时，可以指定 Wallpaper Engine 目录：

```powershell
python tools/install.py install --wallpaper-dir "D:\SteamLibrary\steamapps\common\wallpaper_engine"
```

只检查路径与界面结构、不写入文件：

```powershell
python tools/install.py install --dry-run --wallpaper-dir "D:\SteamLibrary\steamapps\common\wallpaper_engine"
```

安装器会备份界面入口、加入一个带标记的加载项，并设置本地备份程序随当前 Windows 用户登录启动。它是后台登录启动程序，不是 Windows 系统服务。请保留解压文件夹；移动后需要重新运行安装或修复，以更新启动路径。同一备份端口只应由一套安装占用。

## 更新可能导致失效，为什么仍能找回记录？

**软件更新或 Steam 验证文件完整性，可能覆盖加载入口；应用内部界面结构的改变也可能让补丁失效。** 重新安装入口不能自动修复不兼容的界面代码。

因此，我们还会把隐藏编号和操作日志保存在 **应用安装目录之外**。将来可能需要先适配新版界面，但不必重新逐张筛选所有壁纸。

在资源管理器地址栏输入：

```text
%LOCALAPPDATA%\WallpaperEngineWorkshopHide
```

| 文件 | 用途 |
| --- | --- |
| `隐藏名单.json` | 可用记事本查看的当前名单：编号、已知标题、创意工坊链接。单独保留它也可以恢复。 |
| `隐藏记录.jsonl` | 隐藏、恢复和批量操作的追加日志。 |
| `backup-state.json` | 同步状态，也记住恢复操作，防止旧缓存再次隐藏已经恢复的壁纸。 |
| `backup-config.json` | 本地连接配置与认证令牌，请勿公开。 |
| `install-backups/` | 每次安装／修复前的本地界面入口备份。 |

之前只有编号的记录可以从旧版界面存储自动迁移。以后遇到对应卡片时补齐标题；缺少标题不影响按编号恢复。备份不会保存壁纸图片本身。

通常每次操作会先保存在应用里，再同步到独立文件。鼠标停在“显示已隐藏”上可以查看备份状态。备份程序暂时不可用时，记录仍保存在应用内，浏览窗口打开期间每 10 秒重试。**登录启动不等于永远运行：程序可能被禁用或退出，界面目前不会自动重启它。** 待同步记录完成备份前，不要清理应用存储。

手动启动备份、更新后修复入口，或者恢复一份保存的名单：

```powershell
python tools/backup.py start
python tools/install.py repair
python tools/backup.py restore "E:\MyBackups\隐藏名单.json"
```

修复后重开浏览窗口。兼容的补丁重新运行后，可以从备份重建被清空的界面记录。手动恢复会合并名单，不清除其他已隐藏记录。若要用编辑后的完整名单替换，请运行 `python tools/backup.py replace "名单副本.json"`；这会先备份现有名单，再恢复新名单中没有列出的旧隐藏项。仅编辑文件不会触发导入；不要直接修改内部操作日志。重要名单也建议复制到另一处：同一硬盘上的文件无法抵御硬盘损坏。

## 隐私与卸载

备份程序仅监听本机 `127.0.0.1`，默认端口 `18765`，使用随机令牌验证写入。它不上传名单、不下载壁纸内容。标题与编号可能透露个人偏好，请不要把数据文件夹放进公开 Issue。

双击 **`uninstall.cmd`**，或运行：

```powershell
python tools/install.py uninstall
```

然后重开壁纸浏览窗口。卸载会移除我们的加载入口、停止备份程序并删除其登录启动项；隐藏名单和日志继续保留，其他应用内容不会被还原覆盖。

## 开发与测试

```powershell
python -m pip install -r requirements-dev.txt
python -m playwright install chromium
python tests/run.py
```

测试使用虚构卡片和临时数据，覆盖保留选择、翻页退出、壁纸库隔离、双语界面、批量日志、断开后的同步与恢复。安装器测试使用假的应用目录，不修改真实 Wallpaper Engine 安装。

源码按 `src/ui/`、`src/companion/`、`tools/`、`tests/`、`docs/` 和 `examples/` 分开。详见 [贡献说明](CONTRIBUTING.md) 和 [兼容性说明](docs/COMPATIBILITY.md)。

## 许可与致谢

采用 [MIT 许可证](LICENSE)。本项目独立开发，与 Wallpaper Engine、Valve 无隶属关系；使用者需自行获得 Wallpaper Engine。

说明结构参考了 [GitHub README 指引](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-readmes)、[SponsorBlock](https://github.com/ajayyy/SponsorBlock) 和 [WEave](https://github.com/psyattack/WEave) 的公开项目组织方式，没有复制它们的代码。项目使用 AI 辅助开发，欢迎提交兼容性反馈与贡献。


</details>
