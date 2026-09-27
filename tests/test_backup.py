from pathlib import Path
from tempfile import TemporaryDirectory
import json, subprocess, sys, time, urllib.request, urllib.error
from playwright.sync_api import sync_playwright
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src/companion'))
from backup_service import Store, config

ROOT=Path(__file__).resolve().parents[1]/'src/ui'

with TemporaryDirectory() as temp:
    folder=Path(temp)
    store=Store(folder)
    item={'id':'101','hidden':True,'title':'测试壁纸','updatedAt':1}
    store.merge([item])
    store.merge([dict(item,hidden=False,updatedAt=2)])
    store.merge([item])
    assert Store(folder).records['101']['hidden'] is False, 'Stale backup must not resurrect an unhidden item'
    store.merge([dict(item,hidden=True,updatedAt=3)])
    (folder/'backup-state.json').unlink()
    assert Store(folder).records['101']['hidden'], 'Recover state from portable snapshot and journal'
    try: store.merge([dict(item,id='../bad')])
    except ValueError: pass
    else: raise AssertionError('Invalid ID accepted')

with TemporaryDirectory() as temp:
    folder=Path(temp); cfg=config(folder); cfg['port']=18766
    proc=None
    def launch():
        process=subprocess.Popen([sys.executable,str(ROOT.parent/'companion/backup_service.py'),'--root',str(folder),'--port','18766'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        for _ in range(80):
            try:
                with urllib.request.urlopen('http://127.0.0.1:18766/health',timeout=.5): return process
            except Exception: time.sleep(.1)
        raise AssertionError('Service did not start')
    def snapshot(): return json.loads((folder/'隐藏名单.json').read_text(encoding='utf-8'))
    def wait_snapshot(page,count):
        for _ in range(100):
            try:
                if snapshot()['count']==count:return snapshot()
            except (OSError,ValueError):pass
            page.wait_for_timeout(150)
        raise AssertionError(f'Backup count did not reach {count}: {snapshot()}')
    try:
        proc=launch()
        bad=urllib.request.Request('http://127.0.0.1:18766/sync',data=b'{"records":[]}',headers={'Origin':'https://example.com'})
        try:urllib.request.urlopen(bad)
        except urllib.error.HTTPError as error:assert error.code==403
        else:raise AssertionError('Untrusted request allowed')
        with sync_playwright() as p:
            # CEF uses this as an internal resource origin. Trust only the test origin
            # in the isolated browser so its loopback requests mirror the app.
            browser=p.chromium.launch(headless=True,args=['--unsafely-treat-insecure-origin-as-secure=http://wpx.internal'])
            page=browser.new_page()
            page.context.grant_permissions(['local-network-access'],origin='http://wpx.internal')
            page.on('console',lambda message:print('browser:',message.text))
            page.on('pageerror',lambda error:print('pageerror:',error))
            markup='''<html><head><meta charset="utf-8"></head><body><a ng-click="setListSourceRecorded('workshop')">Workshop</a>
            <div class="browseWallpaperImage" style="width:200px;height:150px;position:relative">测试标题</div>
            <script>document.querySelector('.browseWallpaperImage').ctx={$parent:{wtTag:'workshop'},wallpaper:{workshopid:'12345',title:'自动备份测试',type:'scene'}};</script></body></html>'''
            page.route('http://wpx.internal/**',lambda route:route.fulfill(body=markup,content_type='text/html'))
            script='window.weCoverBackupConfig='+json.dumps(cfg)+';\n'+(ROOT/'i18n.js').read_text(encoding='utf-8')+'\n'+(ROOT/'backup-client.js').read_text(encoding='utf-8')+'\n'+(ROOT/'batch-hide.js').read_text(encoding='utf-8')+'\n'+(ROOT/'cover-hide.js').read_text(encoding='utf-8')
            def boot():
                page.goto('http://wpx.internal/')
                page.add_script_tag(content=script)
            boot()
            page.locator('.browseWallpaperImage').hover();page.locator('.we-cover-toggle').click()
            data=wait_snapshot(page,1)
            assert data['wallpapers'][0]['title']=='自动备份测试'
            assert data['wallpapers'][0]['url'].endswith('12345')
            page.wait_for_function("weCoverHide.getBackupStatus()==='名单已自动备份'")
            page.evaluate("localStorage.removeItem('we.coverHide.v1')");boot()
            page.wait_for_function("weCoverHide.getHiddenIds().includes('12345')")
            # Simulate loss of all Wallpaper Engine UI storage, retaining independent files.
            page.evaluate('localStorage.clear()');boot()
            page.wait_for_function("weCoverHide.getHiddenIds().includes('12345')")
            assert page.locator('.browseWallpaperImage').bounding_box() is None
            # Stop companion, unhide, then restart: pending removal must synchronize.
            proc.terminate();proc.wait();proc=None
            page.locator('#we-hidden-toggle').click();page.locator('.we-cover-toggle').click()
            page.wait_for_timeout(500)
            assert page.evaluate('weCoverHide.getHiddenIds().length')==0
            proc=launch();wait_snapshot(page,0)
            page.evaluate('localStorage.clear()');boot()
            page.wait_for_function("weCoverHide.getBackupStatus()==='名单已自动备份'")
            assert page.evaluate('weCoverHide.getHiddenIds().length')==0
            page.evaluate("""for(const id of ['20202','30303']){
              const c=document.createElement('div');c.className='browseWallpaperImage';c.style='width:200px;height:150px;position:relative';
              c.ctx={$parent:{wtTag:'workshop'},wallpaper:{workshopid:id,title:'Batch '+id,type:'scene'}};document.body.append(c);
            }weCoverHide.scan();""")
            before_lines=len((folder/'隐藏记录.jsonl').read_text(encoding='utf-8').splitlines())
            page.locator('#we-batch-start').click()
            page.locator('.we-batch-keep input').first.check()
            page.locator('#we-batch-confirm').click()
            data=wait_snapshot(page,2)
            assert {r['id'] for r in data['wallpapers']}=={'20202','30303'}
            assert len((folder/'隐藏记录.jsonl').read_text(encoding='utf-8').splitlines())==before_lines+1, 'Batch must be journaled together'
            browser.close()
    finally:
        if proc:proc.terminate();proc.wait()
print('PASS: metadata, durable disk backup, restart/journal replay, cache-loss recovery, offline removal synchronization, stale-record protection, origin validation')
