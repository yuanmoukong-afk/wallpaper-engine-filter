# Local verification

Run the scripts in `tests/` using the development requirements. Browser tests use an isolated Playwright browser and temporary backup directories.
Never test list replacement against a user's live files without preserving and restoring their full list.

For native verification, open the wallpaper browser through the running Wallpaper Engine application.
Do not replay a saved `wallpaperui.exe` command line. Direct launches were observed to open Chromium tabs from application arguments and subsequent launches crashed in `libcef.dll`.
In the tested installation, invoking the main `wallpaper64.exe` with no arguments while it was already running let the existing main process open the proper Wallpaper UI.
Do not kill the wallpaper rendering process to restart the browser.

Temporary diagnostics and their loopback receiver must be removed after verification. Do not publish diagnostic reports, launch arguments, application backups, or user lists.

# Native pagination feasibility

The tested build exposes a Workshop query through its internal host service. A sequential query returned 50 entries from the following original page without changing the current displayed page.
Progressive pagination is implemented as an opt-in mode. Native verification filled two consecutive 50-item pages, removed hidden items, avoided duplicate IDs, and preserved the previous page on backward navigation.

The host service uses a shared callback per method, so simultaneous Workshop requests can conflict. The implementation serializes requests and provides cancellation on search/source changes, cached composed pages, ID deduplication, a bounded scan, and explicit original-page ranges.
The requested behavior is to fill only on navigation, with an explicit start at original page N and no compaction of earlier pages. Original and composed page numbers must not be presented as interchangeable.
These are internal interfaces and require rechecking after application updates.
