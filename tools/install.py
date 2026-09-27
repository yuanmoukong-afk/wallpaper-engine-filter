"""Reversible UI loader installation; never distributes Wallpaper Engine files."""
from pathlib import Path
import argparse
import datetime
import hashlib
import json
import os
import re
import shutil
import sys

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / 'src/companion'))
from backup_service import ROOT as DATA, config, atomic_json

LOADER = b'<script src="scripts/we-cover-hide.js" data-we-cover-hide="1"></script>'

def detect_wallpaper_directory(explicit=None):
    if explicit:
        root = Path(explicit).expanduser().resolve()
        if not (root/'ui/dist/index.html').is_file():
            raise ValueError('Choose the wallpaper_engine directory containing ui/dist/index.html.')
        return root
    candidates = []
    state = DATA/'installation.json'
    if state.exists():
        candidates.append(Path(json.loads(state.read_text(encoding='utf-8'))['wallpaper_directory']))
    if os.name == 'nt':
        import winreg
        for hive, key, value in [(winreg.HKEY_CURRENT_USER, r'Software\Valve\Steam', 'SteamPath'),
                                  (winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\WOW6432Node\Valve\Steam', 'InstallPath')]:
            try:
                with winreg.OpenKey(hive, key) as handle:
                    steam = Path(winreg.QueryValueEx(handle, value)[0])
                libraries = [steam]
                vdf = steam/'steamapps/libraryfolders.vdf'
                if vdf.exists():
                    libraries += [Path(p.replace('\\\\','\\')) for p in re.findall(r'"path"\s+"([^"]+)"', vdf.read_text(encoding='utf-8'))]
                candidates += [p/'steamapps/common/wallpaper_engine' for p in libraries]
            except OSError:
                continue
    for root in candidates:
        if (root/'ui/dist/index.html').is_file(): return root.resolve()
    raise ValueError('Wallpaper Engine was not found. Pass --wallpaper-dir "D:\\SteamLibrary\\steamapps\\common\\wallpaper_engine".')

def compatible(dist):
    entry = (dist/'index.html').read_bytes()
    script = (dist/'scripts/scripts.js').read_text(encoding='utf-8')
    markers = ['browseWallpaperImage', 'wallpaperThumbnail', 'workshopid', 'wtTag']
    if b'</head>' not in entry or not all(marker in script for marker in markers):
        raise ValueError('This UI does not match the supported structure. Nothing was patched; an adapter update is needed.')
    return entry

def bundle():
    settings=json.loads((DATA/'ui-settings.json').read_text(encoding='utf-8')) if (DATA/'ui-settings.json').exists() else {'language':'zh'}
    prefix = 'window.weCoverUIConfig = '+json.dumps({'language':'en' if settings.get('language')=='en' else 'zh'})+';\n'
    prefix += 'window.weCoverBackupConfig = '+json.dumps(config(), ensure_ascii=True)+';\n'
    files = ['i18n.js','backup-client.js','batch-hide.js','cover-hide.js','progressive-pages.js','progressive-ui.js']
    return (prefix+'\n'.join((PROJECT/'src/ui'/name).read_text(encoding='utf-8') for name in files)).encode('utf-8')

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['install','repair','uninstall','status'])
    parser.add_argument('--wallpaper-dir', type=Path)
    parser.add_argument('--dry-run', action='store_true', help='Check the path/structure without writing or starting services.')
    args = parser.parse_args()
    root = detect_wallpaper_directory(args.wallpaper_dir)
    dist = root/'ui/dist'
    index = dist/'index.html'
    data = index.read_bytes()
    if args.action in ('install','repair'):
        data = compatible(dist)
        if args.dry_run:
            print('Compatible markers found:', root)
            print('Data directory:', DATA)
            return
        if os.name != 'nt': raise RuntimeError('Installation supports Windows only.')
        from backup_control import ensure
        ensure()
        backup = DATA/'install-backups'/datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')
        backup.mkdir(parents=True)
        shutil.copy2(index, backup/'index.html')
        target = dist/'scripts/we-cover-hide.js'
        if target.exists(): shutil.copy2(target, backup/'we-cover-hide.js')
        target.write_bytes(bundle())
        index.write_bytes(data if LOADER in data else data.replace(b'</head>',LOADER+b'</head>',1))
        atomic_json(DATA/'installation.json',{'wallpaper_directory':str(root),'source_directory':str(PROJECT),
            'backup':str(backup),'previous_entry_sha256':hashlib.sha256(data).hexdigest()})
        print('Installed. Close and reopen the Wallpaper Engine browser window.')
        print('Automatic backup directory:', DATA)
    elif args.action == 'uninstall':
        if args.dry_run: print('Would remove only our loader and disable our backup companion.'); return
        from backup_control import stop
        index.write_bytes(data.replace(LOADER,b''))
        stop()
        print('Loader and login startup removed. Hidden-list files preserved:', DATA)
        print('Close and reopen the Wallpaper Engine browser window.')
    else:
        print(json.dumps({'wallpaper_directory':str(root),'data_directory':str(DATA),
                          'loader_installed':LOADER in data,'script_present':(dist/'scripts/we-cover-hide.js').exists()},indent=2))

if __name__ == '__main__':
    try: main()
    except (OSError, ValueError, RuntimeError) as error:
        print('Error:', error, file=sys.stderr)
        sys.exit(1)
