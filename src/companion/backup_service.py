"""Loopback-only durable backup for Wallpaper Engine hidden IDs."""
from pathlib import Path
from http.server import BaseHTTPRequestHandler, HTTPServer
import argparse
import datetime as dt
import json
import os
import re
import secrets
import threading

ROOT = Path(os.environ.get('WEWH_DATA_DIR') or (Path(os.environ.get('LOCALAPPDATA', Path.home())) / 'WallpaperEngineWorkshopHide'))
PORT = 18765

def atomic_json(path, value):
    temp = path.with_suffix(path.suffix + '.tmp')
    with temp.open('w', encoding='utf-8') as f:
        json.dump(value, f, ensure_ascii=False, indent=2)
        f.write('\n'); f.flush(); os.fsync(f.fileno())
    os.replace(temp, path)

def config(root=ROOT):
    root.mkdir(parents=True, exist_ok=True)
    path = root / 'backup-config.json'
    if not path.exists():
        atomic_json(path, {'port':PORT, 'token':secrets.token_hex(32)})
    return json.loads(path.read_text(encoding='utf-8'))

def normalized(record):
    if not isinstance(record, dict): raise ValueError('Invalid record')
    ident = str(record.get('id', ''))
    stamp = record.get('updatedAt')
    if not re.fullmatch(r'[1-9][0-9]{0,24}', ident): raise ValueError('Invalid ID')
    if type(record.get('hidden')) is not bool: raise ValueError('Invalid hidden flag')
    if type(stamp) is not int or stamp < 0 or stamp > 9999999999999: raise ValueError('Invalid timestamp')
    title = record.get('title', '')
    if not isinstance(title, str) or len(title) > 2000: raise ValueError('Invalid title')
    return {'id':ident, 'hidden':record['hidden'], 'title':title, 'updatedAt':stamp}

class Store:
    def __init__(self, root):
        root.mkdir(parents=True, exist_ok=True)
        self.root = root
        self.statefile = root / 'backup-state.json'
        self.snapshot = root / '隐藏名单.json'
        self.journal = root / '隐藏记录.jsonl'
        self.records = {}
        self.dirty = False
        if self.statefile.exists():
            state = json.loads(self.statefile.read_text(encoding='utf-8'))
            self.records = {r['id']:normalized(r) for r in state['records']}
        elif self.snapshot.exists():
            data = json.loads(self.snapshot.read_text(encoding='utf-8'))
            self.records = {str(r['id']): normalized({'id':r['id'], 'title':'' if r.get('title','').startswith('（旧记录') else r.get('title',''), 'hidden':True, 'updatedAt':r.get('updatedAt',0)}) for r in data['wallpapers']}
        # The journal is written first. Replay handles interruption between file writes.
        if self.journal.exists():
            with self.journal.open(encoding='utf-8') as f:
                for line in f:
                    try: batch = json.loads(line)['records']
                    except (ValueError, KeyError): continue
                    for record in batch:
                        item = normalized(record); old = self.records.get(item['id'])
                        if old is None or item['updatedAt'] >= old['updatedAt']: self.records[item['id']] = item
        self.persist()

    def persist(self):
        records = sorted(self.records.values(), key=lambda r:int(r['id']))
        atomic_json(self.statefile, {'schemaVersion':1, 'records':records})
        atomic_json(self.snapshot, {
            '说明':'Wallpaper Engine 隐藏名单。由本地备份程序自动维护；请保留此文件。',
            'schemaVersion':1,
            'savedAt':dt.datetime.now().astimezone().isoformat(),
            'count':sum(r['hidden'] for r in records),
            'wallpapers':[dict(id=r['id'], title=r['title'] or '（旧记录，尚未补齐标题）',
                url='https://steamcommunity.com/sharedfiles/filedetails/?id='+r['id'], updatedAt=r['updatedAt'])
                for r in records if r['hidden']]})

    def merge(self, incoming):
        if not isinstance(incoming,list) or len(incoming)>100000: raise ValueError('Invalid records')
        incoming = [normalized(r) for r in incoming] # Validate the full batch before any write.
        changes = {}
        for item in incoming:
            old = changes.get(item['id'], self.records.get(item['id']))
            if old is None or item['updatedAt'] > old['updatedAt']:
                if old and not item['title']: item['title'] = old['title']
                if old != item: changes[item['id']] = item
            elif item['updatedAt'] == old['updatedAt'] and not old['title'] and item['title']:
                changes[item['id']] = dict(old, title=item['title'])
        if changes:
            with self.journal.open('a', encoding='utf-8') as f:
                f.write(json.dumps({'time':dt.datetime.now().astimezone().isoformat(), 'records':list(changes.values())},ensure_ascii=False)+'\n')
                f.flush(); os.fsync(f.fileno())
            self.records.update(changes)
            self.dirty = True
        if self.dirty:
            self.persist()
            self.dirty = False
        return list(self.records.values())

def serve(root=ROOT, port=None):
    cfg = config(root)
    store = Store(root)
    class Handler(BaseHTTPRequestHandler):
        def allowed(self):
            return self.headers.get('Origin') in (None,'http://wpx.internal') and self.headers.get('Host') in ('127.0.0.1:'+str(port or cfg['port']), 'localhost:'+str(port or cfg['port']))
        def reply(self, code, data):
            raw=json.dumps(data,ensure_ascii=False).encode('utf-8')
            self.send_response(code)
            self.send_header('Content-Type','application/json; charset=utf-8')
            self.send_header('Content-Length',str(len(raw)))
            if self.headers.get('Origin')=='http://wpx.internal':
                self.send_header('Access-Control-Allow-Origin','http://wpx.internal')
                self.send_header('Access-Control-Allow-Headers','Content-Type, X-WE-Cover-Token')
                self.send_header('Access-Control-Allow-Methods','POST, GET, OPTIONS')
                self.send_header('Access-Control-Allow-Private-Network','true')
            self.end_headers(); self.wfile.write(raw)
        def do_OPTIONS(self):
            self.reply(200 if self.allowed() else 403,{})
        def do_GET(self):
            if not self.allowed(): return self.reply(403,{})
            if self.path=='/health': return self.reply(200,{'service':'we-hidden-backup','version':1})
            self.reply(404,{})
        def do_POST(self):
            if not self.allowed() or not secrets.compare_digest(self.headers.get('X-WE-Cover-Token',''),cfg['token']): return self.reply(403,{})
            if self.path=='/shutdown':
                self.reply(200,{}); threading.Thread(target=self.server.shutdown,daemon=True).start(); return
            if self.path!='/sync': return self.reply(404,{})
            try:
                size=int(self.headers.get('Content-Length','0'))
                if size<1 or size>16_000_000: raise ValueError('Invalid size')
                data=json.loads(self.rfile.read(size))
                records=store.merge(data['records'])
                self.reply(200,{'records':records})
            except (ValueError,KeyError,TypeError): self.reply(400,{'error':'Invalid backup data'})
            except OSError: self.reply(500,{'error':'Backup could not be written; retry later'})
        def log_message(self,*args): pass
    HTTPServer(('127.0.0.1', port or cfg['port']),Handler).serve_forever()

if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--root',type=Path,default=ROOT); parser.add_argument('--port',type=int)
    args=parser.parse_args()
    try: serve(args.root,args.port)
    except Exception as error:
        with (args.root/'backup-service-errors.log').open('a',encoding='utf-8') as f:
            f.write(dt.datetime.now().isoformat()+' '+repr(error)+'\n')
        raise
