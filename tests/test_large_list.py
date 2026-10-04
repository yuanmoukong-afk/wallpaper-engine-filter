"""Large hidden list: no library metadata writes, no reentrant painting."""
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]/'src/ui'
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True)
    page=browser.new_page()
    errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    page.route('http://large.test/**',lambda r:r.fulfill(content_type='text/html',body='''
      <html><head></head><body><a ng-click="setListSourceRecorded('workshop')">Workshop</a>
      <wallpaper-thumbnail wt-tag="installed"></wallpaper-thumbnail><script>
      const records=Array.from({length:3000},(_,i)=>({id:String(i+1),hidden:true,title:'',updatedAt:1}));
      localStorage.setItem('we.coverHide.v1',JSON.stringify(records.map(r=>r.id)));
      localStorage.setItem('we.coverHide.records.v1',JSON.stringify(records));
      window.writes=0;const save=Storage.prototype.setItem;
      Storage.prototype.setItem=function(...args){writes++;return save.apply(this,args);};
      window.weCoverBackupConfig={port:1,token:'test'};
      window.fetch=async(url,options)=>({ok:true,json:async()=>JSON.parse(options.body)});
      window.render=(source,count)=>{
        const grid=document.querySelector('wallpaper-thumbnail');grid.innerHTML='';grid.setAttribute('wt-tag',source);
        for(let i=1;i<=count;i++){
          const card=document.createElement('div');card.className='browseWallpaperImage';
          card.ctx={$parent:{wtTag:source},wallpaper:{workshopid:String(i),title:'Example '+i}};
          grid.append(card);
        }
      };
      </script></body></html>'''))
    page.goto('http://large.test/')
    for name in ['i18n.js','backup-client.js','batch-hide.js','cover-hide.js']:
        page.add_script_tag(path=str(ROOT/name))
    page.wait_for_function("weCoverHide.getBackupStatus()==='名单已自动备份'")
    installed=page.evaluate("""()=>{writes=0;render('installed',3000);const start=performance.now();
      weCoverHide.scan();return {ms:performance.now()-start,writes,buttons:document.querySelectorAll('.we-cover-toggle').length};}""")
    assert installed['writes']==0 and installed['buttons']==0,installed
    page.wait_for_timeout(400)
    assert page.evaluate('writes')==0,'Browsing installed wallpapers must not rewrite backups'
    page.evaluate("writes=0;render('workshop',200);weCoverHide.scan()")
    page.wait_for_timeout(550)
    assert page.evaluate('writes')==1,'Metadata enrichment should write once for the page without republishing IDs'
    assert page.evaluate('weCoverHide.getHiddenIds().length')==3000
    # Recycle those same nodes across the boundary, including cleanup.
    page.evaluate("""document.querySelectorAll('.browseWallpaperImage').forEach(c=>c.ctx.$parent.wtTag='installed');weCoverHide.scan()""")
    assert page.locator('.we-cover-hidden,.we-cover-toggle').count()==0
    page.evaluate("""document.querySelectorAll('.browseWallpaperImage').forEach(c=>c.ctx.$parent.wtTag='workshop');weCoverHide.scan()""")
    assert page.locator('.we-cover-hidden').count()==200
    assert page.evaluate('weCoverHide.getHiddenIds().length')==3000
    assert not errors,errors
    print(f'PASS: 3000 hidden IDs / 3000 installed cards: {installed["ms"]:.1f} ms, zero backup writes; 200 titles batched once; recycled cards remain scoped')
    browser.close()
