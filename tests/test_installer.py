from pathlib import Path
from tempfile import TemporaryDirectory
import importlib.util
import sys
from unittest.mock import patch

root=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('installer',root/'tools/install.py')
installer=importlib.util.module_from_spec(spec);spec.loader.exec_module(installer)
import backup_control

with TemporaryDirectory() as temp:
    base=Path(temp);app=base/'app';dist=app/'ui/dist';(dist/'scripts').mkdir(parents=True)
    index=dist/'index.html';original=b'<html><head></head><body>Other customization</body></html>'
    index.write_bytes(original)
    (dist/'scripts/scripts.js').write_text('browseWallpaperImage wallpaperThumbnail workshopid wtTag')
    installer.DATA=base/'data'
    def invoke(action,*extra):
        with patch.object(sys,'argv',['install.py',action,'--wallpaper-dir',str(app),*extra]):installer.main()
    with patch.object(backup_control,'ensure') as ensure, patch.object(backup_control,'stop') as stop:
        invoke('install','--dry-run')
        ensure.assert_not_called();assert not installer.DATA.exists()
        # Stub token creation to keep all test writes within the temporary directory.
        with patch.object(installer,'config',return_value={'port':18766,'token':'fixture'}):
            invoke('install');invoke('repair')
        assert index.read_bytes().count(installer.LOADER)==1
        assert (dist/'scripts/we-cover-hide.js').exists()
        assert len(list((installer.DATA/'install-backups').iterdir()))==2
        invoke('uninstall');assert index.read_bytes()==original
        assert (installer.DATA/'installation.json').exists()
        stop.assert_called_once()
        (dist/'scripts/scripts.js').write_text('Unsupported future application')
        try:invoke('install')
        except ValueError:pass
        else:raise AssertionError('Unsupported UI accepted')
        assert index.read_bytes()==original
print('PASS: dry run, idempotent repair, backups, uninstall preserves unrelated content, unsupported version refusal')
