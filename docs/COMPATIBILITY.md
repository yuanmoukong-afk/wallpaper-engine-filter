# Compatibility and recovery / 兼容性与恢复

Tested on Windows with Wallpaper Engine 2.8.42. This is an unofficial UI patch, not a supported plugin API.
Updates may remove the loader or change internal interfaces. Structure checks cannot guarantee compatibility.
Run `python tools/install.py repair` after an update, then reopen the wallpaper browser through Wallpaper Engine itself.
If the UI is incompatible, uninstall the loader and report the app version; keep your separate data directory.

Hidden IDs and restoration records are backed up outside the application directory.
`python tools/backup.py path` prints the location. `restore FILE` merges a saved list; `replace FILE` replaces it after backing up the previous list.
Do not edit the recovery journal. Editing a file alone does not import it. Do not share credentials or the entire data folder.
A backup process can exit or be disabled; hover Show hidden to check backup status and use `python tools/backup.py start` if needed.

已在 Windows、Wallpaper Engine 2.8.42 上验证。这是非官方界面补丁，不使用官方插件接口。
更新可能覆盖入口或改变内部接口，结构检查不能保证新版兼容。
更新后可运行 `python tools/install.py repair`，再通过 Wallpaper Engine 本身重新打开界面。
不兼容时先卸载加载入口并报告版本，保留独立数据目录。

`python tools/backup.py path` 显示备份位置；`restore 文件` 追加恢复；`replace 文件` 先备份再替换名单。
不要直接编辑恢复日志，仅修改文件不会自动导入。不要公开密钥或整个数据目录。
备份程序可能退出或被禁用，可悬停“显示已隐藏”检查状态，通过 `python tools/backup.py start` 启动。

Progressive mode is Workshop-only, bounded to 20 original pages per navigation, and may end with a partial page.
Changing filters exits the mode; exiting restores normal pagination. Earlier original pages remain accessible.
Online Workshop ordering may change during a session; deduplication does not make the remote results a fixed snapshot.

递进仅支持创意工坊，一次翻页最多检查 20 个原始页，可能不足一页。改变筛选会退出；退出后恢复普通分页，可查看前面的原始页。
创意工坊在线排序可能变化；去重不代表冻结了服务器结果。

## 4.2.1: loading stalls / 加载卡顿修复

Count queries use a separate native callback and no longer block the progressive page queue.
Page requests time out after 15 seconds; late responses with an older token are ignored.
Hidden-ID lookups are built once per fetched page. Installed cards do not enrich backup metadata;
missing discovery titles are saved together without recursively repainting the page.
Unchanged backup responses no longer rewrite browser storage. Existing hidden lists and recovery logs remain compatible.

数量查询不再堵塞递进翻页队列；单个页面请求等待超过 15 秒会报错，过期编号的迟到响应会被忽略。
隐藏名单按页建立查找表，已下载页面不再补写备份标题；搜索页缺失的标题合并保存，避免递归刷新。
备份内容未变化时不再重写浏览器存储。现有隐藏名单和恢复日志继续兼容，无需清空记录。
