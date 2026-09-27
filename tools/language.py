"""Configure patch language outside the Wallpaper Engine interface."""
from pathlib import Path
import argparse
import json
import re
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src/companion'))
from backup_service import ROOT, atomic_json


def set_language(root, language):
    if language not in ('zh', 'en'):
        raise ValueError('Choose zh or en')
    root.mkdir(parents=True, exist_ok=True)
    atomic_json(root / 'ui-settings.json', {'language': language})
    state = root / 'installation.json'
    if not state.exists():
        return False
    info = json.loads(state.read_text(encoding='utf-8'))
    dist = Path(info['directory']) if 'directory' in info else Path(info['wallpaper_directory']) / 'ui/dist'
    bundle = dist / 'scripts/we-cover-hide.js'
    if not bundle.exists():
        return False
    text = bundle.read_text(encoding='utf-8')
    line = 'window.weCoverUIConfig = ' + json.dumps({'language': language}) + ';\n'
    text = re.sub(r'^window\.weCoverUIConfig\s*=\s*[^\n]*\n', '', text, count=1)
    temporary = bundle.with_suffix('.js.tmp')
    temporary.write_text(line + text, encoding='utf-8')
    temporary.replace(bundle)
    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('language', choices=['zh', 'en'], nargs='?')
    parser.add_argument('--data-dir', type=Path, default=ROOT)
    args = parser.parse_args()
    language = args.language
    if language is None:
        print('1. 中文\n2. English')
        answer = input('选择插件语言 / Choose patch language [1/2]: ').strip()
        if answer not in ('1', '2'):
            raise SystemExit('未修改 / No change')
        language = 'zh' if answer == '1' else 'en'
    installed = set_language(args.data_dir, language)
    print('已保存。关闭并重新打开壁纸界面后生效。' if language == 'zh' else 'Saved. Close and reopen the wallpaper browser to apply.')
    if not installed:
        print('安装或修复补丁时生效 / Applies on the next installation or repair.')


if __name__ == '__main__':
    main()
