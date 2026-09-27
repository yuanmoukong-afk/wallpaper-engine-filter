from pathlib import Path
import subprocess
import sys
root=Path(__file__).resolve().parents[1]
(root/'test-artifacts').mkdir(exist_ok=True)
for test in sorted((root/'tests').glob('test_*.py')):
    print('Running',test.name,flush=True)
    subprocess.run([sys.executable,str(test)],cwd=root,check=True)
for test in sorted((root/'tests').glob('test_*.cjs')):
    subprocess.run(['node',str(test)],cwd=root,check=True)
print('All checks passed.')
