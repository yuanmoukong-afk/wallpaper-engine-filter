# Wallpaper Engine Filter · 壁纸筛选助手

Hide wallpapers you have reviewed or do not want to see again.

[简体中文](README.zh-CN.md)

- **Hide one**: Remove a wallpaper card without leaving a gap.
- **Hide a page**: Select what to keep, then hide the rest.
- **Reveal and restore**: Find hidden wallpapers and undo your choices.
- **Progressive browsing**: Choose a starting page and fill results when advancing, never immediately after hiding a card.
- **Separate library**: Hiding search results does not affect your subscribed library.
- **Backup and recovery**: Save the list automatically; restore or edit it with an external tool.
- **Chinese / English**: Set the language from the patch folder, then reopen the wallpaper browser.

<details>
<summary>Installation, usage, and recovery details</summary>

**Keep the wallpapers you like. Stop reviewing the same ones again.**

[简体中文](README.zh-CN.md) · English · [Compatibility & recovery](docs/COMPATIBILITY.md) · [Contributing](CONTRIBUTING.md)

When browsing Wallpaper Engine, you may open a wallpaper, decide it is not for you, and encounter it again on your next search. Category filters cannot remember those individual decisions. This project adds a personal hide list to Wallpaper Engine's **in-app Workshop and discovery browser**, so you can spend your time looking at new choices.

For long result pages, select the wallpapers you want to **keep**, then hide the rest of that page in one action.

## What is this?

An **unofficial Windows UI patch / extension**, with a small local backup companion. It is not an AI Skill, a Chrome extension, a wallpaper renderer, or an official Wallpaper Engine plugin. It loads our own JavaScript through the application's local UI entry point; it does not use a supported plugin API.

Tested against Wallpaper Engine **2.8.42**. Other versions are not guaranteed. No Wallpaper Engine source files, artwork, or binaries are included in this repository.

## Controls

| Control | What it does |
| --- | --- |
| **Hide wallpaper / Restore wallpaper** | On each discovery card, hide that wallpaper by its Workshop ID. The whole card disappears and the following cards fill the gap. |
| **Show hidden / Collapse hidden** | Temporarily reveal hidden items on the current page. Click a revealed card for its normal details, or restore it. The count is the total saved hide list, not just this page. |
| **Hide this page…** | Start batch selection. Check the wallpapers to **keep**, then press **Hide remaining N**. Checked does **not** mean “delete.” |
| **Progressive browsing** | Choose an original starting page, enable the mode, then use Next filled page to skip hidden entries and fill a page. Hiding a card never refills it immediately. |

In batch mode:

1. Click **Hide this page…**.
2. Check the wallpapers you want to retain. A green border marks them as **Keeping**.
3. Review the count and click **Hide remaining N**.

Checking nothing hides all currently unhidden wallpapers on this page. Keeping everything disables the final button. **Cancel** exits without changes. Navigation, search/filter edits and changing results cancel selection; the page is checked again before the batch is saved.

**Your Installed / subscribed library is unaffected.** A subscribed wallpaper can still be hidden in discovery results, while remaining visible in your library. Hiding never unsubscribes, deletes files, or changes wallpaper content.

Normal mode filters the current page. Optional progressive mode provides its own Previous/Next controls and reports the original page range used. Earlier original pages are untouched and remain accessible after exiting the mode. Search changes exit the mode. Each navigation checks up to 20 original pages; continue with Next if it stops short. The final page may contain fewer items.

**Language settings live in the patch folder.** Open `设置插件语言.cmd`, choose 中文 or English, then reopen the wallpaper browser. There is no in-app language selector or synchronization button.

## Install

Requirements: Windows, Wallpaper Engine installed through Steam, and **Python 3.10+** with `pythonw.exe` and `python` available in your terminal. Runtime uses only Python's standard library; Node and Playwright are needed only for development/tests.

1. Download this repository as a ZIP and extract it to a folder you intend to keep. Do not run it from inside the ZIP.
2. Close Wallpaper Engine's wallpaper browser window.
3. Double-click **`install.cmd`**, or run:

   ```powershell
   python tools/install.py install
   ```

4. Reopen the wallpaper browser. The added controls appear near the Workshop tab and on discovery cards.

The installer searches your Steam libraries. If it cannot locate Wallpaper Engine, specify its directory:

```powershell
python tools/install.py install --wallpaper-dir "D:\SteamLibrary\steamapps\common\wallpaper_engine"
```

You can inspect compatibility without changing files:

```powershell
python tools/install.py install --dry-run --wallpaper-dir "D:\SteamLibrary\steamapps\common\wallpaper_engine"
```

The installer backs up the existing UI entry, adds one marked script loader, and registers the quiet backup companion to start when the current Windows user signs in. This is a login startup program, not a Windows service. Keep the extracted source folder: moving it requires running install/repair again. Only one installation should own the local backup port at a time.

## Update compatibility and recoverable records

**Wallpaper Engine updates or Steam file verification may remove the loader. Changes to internal UI structure can also break the patch.** Reinstalling the loader cannot fix an incompatible adapter automatically.

That is why hidden IDs are also written **outside the application installation directory**, along with a change journal. The UI adapter may need repair after an update, but you should not have to review all those wallpapers again.

By default, open this folder in Windows Explorer:

```text
%LOCALAPPDATA%\WallpaperEngineWorkshopHide
```

| File | Purpose |
| --- | --- |
| `隐藏名单.json` | Human-readable current hidden list: Workshop ID, title when known, and Workshop link. It can be restored on its own. |
| `隐藏记录.jsonl` | Append-only journal of hide/restore operations, including batches. |
| `backup-state.json` | Synchronization state, including restorations, to prevent stale app data from re-hiding restored wallpapers. |
| `backup-config.json` | Local connection settings and authentication token. Keep it private. |
| `install-backups/` | Local copies of the UI entry from before installation/repair. |

Existing ID-only records can be imported automatically from the previous UI storage. Titles are filled in when matching cards are encountered; a missing title does not prevent restoration. Wallpaper images are not backed up.

Normally each action is saved in the application and then synchronized to disk. Hover **Show hidden** to check the backup status. If the companion is unavailable, records remain in app storage and synchronization retries every 10 seconds while the browser window is open. **Login startup is not a guarantee of continuous operation:** the companion can be disabled or exit, and the UI does not restart it automatically. Do not clear app storage until pending changes have synced.

To restart backup, repair after an update, or import a saved list:

```powershell
python tools/backup.py start
python tools/install.py repair
python tools/backup.py restore "E:\MyBackups\隐藏名单.json"
```

Close and reopen the browser after repair. Once a compatible patch is running again, it can rebuild cleared UI storage from the companion. A manual import merges the listed IDs; it does not clear other hidden items. To replace the full hidden list with an edited copy, run `python tools/backup.py replace "edited-list.json"`. This backs up the current list first and restores previously hidden IDs absent from the new list. File edits alone never trigger imports. Do not manually edit the internal journal. For long-term backup, copy the data folder elsewhere too: a file on the same disk does not protect against disk failure.

## Privacy and uninstall

The companion listens only on `127.0.0.1` (default port `18765`), authenticates changes with a generated token, and writes local files. It does not upload your list or fetch wallpaper content. Hidden titles and IDs may reveal your preferences; do not attach your data folder to public issues.

Run **`uninstall.cmd`** or:

```powershell
python tools/install.py uninstall
```

Then reopen the wallpaper browser. This removes our loader, stops our companion, and removes its login startup entry. Your hidden-list files are retained. Other application content is preserved.

## Development

```powershell
python -m pip install -r requirements-dev.txt
python -m playwright install chromium
python tests/run.py
```

Tests use synthetic cards and temporary data. They cover selection, page-change cancellation, library isolation, bilingual UI, batch journaling, offline synchronization, and recovery. Installer tests use a fake application directory; they do not modify your Wallpaper Engine installation.

```text
src/ui/          injected UI, batch selection, language dictionary, backup client
src/companion/   loopback backup server and startup controls
tools/          reversible installer and backup command line
tests/          isolated browser and installer checks
docs/           compatibility and architecture notes
examples/       empty portable backup example (no personal data)
```

## License and acknowledgements

MIT — see [LICENSE](LICENSE). This is an independent project, not affiliated with Wallpaper Engine or Valve. You must obtain Wallpaper Engine separately.

Documentation organization was informed by [GitHub's README guidance](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-readmes) and the public project layouts of [SponsorBlock](https://github.com/ajayyy/SponsorBlock) and [WEave](https://github.com/psyattack/WEave). No code was copied from those projects. Developed with AI assistance; contributions and compatibility reports are welcome.


</details>
