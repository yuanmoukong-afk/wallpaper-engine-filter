"""Install a quiet per-user companion, or restore a portable JSON backup."""
from pathlib import Path
import json, subprocess, sys, time, urllib.request, urllib.error, winreg
from backup_service import ROOT, config, normalized

RUN_KEY = r'Software\Microsoft\Windows\CurrentVersion\Run'
RUN_NAME = 'WallpaperHiddenListBackup'
SCRIPT = Path(__file__).with_name('backup_service.py')

def request(path, payload=None):
    cfg=config()
    req=urllib.request.Request('http://127.0.0.1:'+str(cfg['port'])+path,
        data=None if payload is None else json.dumps(payload).encode(),
        headers={'Content-Type':'application/json','X-WE-Cover-Token':cfg['token']})
    with urllib.request.urlopen(req,timeout=8) as response: return json.load(response)

def ensure(register=True):
    pythonw=Path(sys.executable).with_name('pythonw.exe')
    if not pythonw.exists(): raise RuntimeError('pythonw.exe is required for quiet startup')
    def register_startup():
        if register:
            command=subprocess.list2cmdline([str(pythonw),str(SCRIPT),'--root',str(ROOT)])
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER,RUN_KEY) as key:
                winreg.SetValueEx(key,RUN_NAME,0,winreg.REG_SZ,command)
    try:
        if request('/health').get('service')=='we-hidden-backup':
            request('/sync', {'records':[]})
            register_startup()
            return
    except urllib.error.HTTPError as error:
        if error.code==403: raise RuntimeError('Another backup installation uses this port. Stop that installation before switching.') from error
    except Exception: pass
    subprocess.Popen([str(pythonw),str(SCRIPT),'--root',str(ROOT)],cwd=SCRIPT.parent,
        creationflags=subprocess.CREATE_NO_WINDOW,stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    for _ in range(40):
        try:
            if request('/health').get('service')=='we-hidden-backup':
                request('/sync', {'records':[]})
                register_startup()
                return
        except Exception: pass
        time.sleep(.1)
    raise RuntimeError('Backup companion did not start; inspect backup-service-errors.log')

def stop():
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER,RUN_KEY,0,winreg.KEY_SET_VALUE) as key: winreg.DeleteValue(key,RUN_NAME)
    except FileNotFoundError: pass
    try: request('/shutdown',{})
    except Exception: pass

def restore(path, replace=False):
    data=json.loads(Path(path).read_text(encoding='utf-8-sig'))
    if not isinstance(data,dict) or data.get('schemaVersion')!=1: raise ValueError('Unrecognized backup format')
    rows=data.get('wallpapers')
    if 'hiddenIds' in data:
        ids=data['hiddenIds']
        if not isinstance(ids,list) or any(not isinstance(i,str) for i in ids): raise ValueError('Invalid hidden IDs')
        rows=[{'id':i} for i in ids]
    if not isinstance(rows,list) or len(rows)>100000: raise ValueError('Invalid hidden list')
    stamp=int(time.time()*1000)
    records=[normalized({'id':str(r['id']),'title':'' if r.get('title','').startswith('（旧记录') else r.get('title',''),'hidden':True,'updatedAt':stamp}) for r in rows]
    ensure()
    current=request('/sync',{'records':[]})['records']
    stamp=max(stamp,max((r['updatedAt'] for r in current),default=0)+1)
    records=[dict(r,updatedAt=stamp) for r in records]
    if replace:
        from backup_service import atomic_json
        archive=ROOT/'restore-backups'
        archive.mkdir(parents=True,exist_ok=True)
        atomic_json(archive/('before-'+str(time.time_ns())+'.json'),{'schemaVersion':1,'wallpapers':[{'id':r['id'],'title':r['title']} for r in current if r['hidden']]})
        desired={r['id'] for r in records}
        records += [dict(r,hidden=False,updatedAt=stamp) for r in current if r['hidden'] and r['id'] not in desired]
    request('/sync',{'records':records})
    print(f"Restored {sum(r['hidden'] for r in records)} hidden IDs. The open browser applies the restored list within 10 seconds; otherwise reopen it after repair.")

if __name__=='__main__':
    action=sys.argv[1] if len(sys.argv)>1 else 'start'
    if action=='start': ensure(); print('Backup companion running. Automatic Windows login startup enabled.')
    elif action=='stop': stop(); print('Backup companion stopped. Backup files preserved.')
    elif action=='restore': restore(sys.argv[2] if len(sys.argv)>2 else ROOT/'隐藏名单.json')
    elif action=='replace' and len(sys.argv)>2: restore(sys.argv[2],replace=True)
    else: raise SystemExit('Expected start, stop, restore [backup.json], or replace backup.json')
