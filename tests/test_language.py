from pathlib import Path
from tempfile import TemporaryDirectory
import importlib.util
import json

spec=importlib.util.spec_from_file_location('language_tool',Path(__file__).resolve().parents[1]/'tools/language.py')
tool=importlib.util.module_from_spec(spec);spec.loader.exec_module(tool)
with TemporaryDirectory() as temp:
    root=Path(temp);dist=root/'app/ui/dist';(dist/'scripts').mkdir(parents=True)
    bundle=dist/'scripts/we-cover-hide.js';bundle.write_text('window.weCoverBackupConfig = {"token":"test"};\n// body\n')
    (root/'installation.json').write_text(json.dumps({'directory':str(dist)}))
    assert tool.set_language(root,'en')
    assert bundle.read_text().startswith('window.weCoverUIConfig = {"language": "en"};')
    assert tool.set_language(root,'zh')
    text=bundle.read_text();assert text.count('window.weCoverUIConfig')==1
    assert '"token":"test"' in text
    assert json.loads((root/'ui-settings.json').read_text())['language']=='zh'
print('PASS: external language settings, repeated changes, preserved bundle configuration')
