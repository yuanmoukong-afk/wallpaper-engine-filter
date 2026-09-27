# 屏蔽名单导入 / Hidden-list imports

文件自动导入已停用，原有的自动备份继续工作。直接修改日志不会立即改变应用。
撤回会从当前名单中删除壁纸，但内部保留撤回记录，避免旧缓存把它重新隐藏。
不提供同步按钮。需要改写时，在应用外通过恢复工具明确执行。
精简分享格式可以只含 schemaVersion 和 hiddenIds，不需要标题、时间、路径或账号。
不要分享密钥文件、内部状态、操作日志或整个工作目录。

Automatic file imports are disabled; the existing automatic local backup remains enabled.
Editing the journal does not immediately change the running app. Restoration records are retained internally to prevent stale caches from hiding restored items again.
No sync button is provided. Use the external recovery tool to explicitly apply an edited list.
Compact shared lists need only schemaVersion and hiddenIds, not titles, timestamps, paths, or account details.
Do not share credentials, internal state, journals, or the entire workspace.

The development CLI supports merging an original backup or compact list using:
`python tools/backup.py restore list.json`
Existing hidden entries are retained. The example format is:
`{"schemaVersion":1,"hiddenIds":["123456789"]}`
The ID is a placeholder. IDs still reveal filtering preferences.

替换完整名单 / Replace the full list: `python tools/backup.py replace edited-list.json`. A pre-restore backup is saved automatically.
