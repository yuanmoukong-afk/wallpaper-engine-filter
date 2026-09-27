# Contributing / 参与贡献

Use Windows and Python 3.10+ with Node.js for tests. Install `requirements-dev.txt`, run `python -m playwright install chromium`, then `python tests/run.py`.
Tests use temporary directories and synthetic cards. Never commit user lists, credentials, local launch arguments, crash dumps, or Wallpaper Engine files.
Describe the app version, expected behavior, reproduction steps, and relevant test results in issues and pull requests. Redact private data.
Keep language settings outside the application toolbar and preserve the separation between Workshop hiding and the installed library.

开发测试使用 Windows、Python 3.10+ 和 Node.js。安装开发依赖与 Playwright Chromium 后运行 `python tests/run.py`。
测试只使用临时目录和模拟卡片。不要提交个人名单、密钥、启动参数、崩溃转储或 Wallpaper Engine 原文件。
报告问题或提交修改时请说明应用版本、预期行为、复现步骤与验证结果，并移除私人信息。
语言设置应保留在应用外，创意工坊隐藏与已安装列表必须保持独立。
