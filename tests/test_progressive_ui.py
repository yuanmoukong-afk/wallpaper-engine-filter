from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1] / 'src/ui'
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True)
    page=browser.new_page()
    html='''<html><head></head><body><a ng-click="setListSourceRecorded('workshop')">Workshop</a>
    <input id="browseSearchFilterText"><div class="browseWallpaperPagination">Native pages</div>
    <wallpaper-thumbnail wt-tag="workshop"></wallpaper-thumbnail><script>
    window.calls=[];let outstanding=0;window.collision=false;
    const data={1:[11,12,13],2:[21,22,23],3:[31,32,33],4:[41,42]};
    window.s={source:'workshop',pagination:{current:1,count:4},queryActive:false,filter:{text:''},
      queryWallpapers:data[1].map(id=>({workshopid:String(id),title:'Item '+id})),sortedWallpapers:[]};
    window.render=()=>{const grid=document.querySelector('wallpaper-thumbnail');grid.innerHTML='';
      for(const w of s.queryWallpapers){const c=document.createElement('div');c.className='browseWallpaperImage';c.style='position:relative;width:120px;height:80px';
      c.ctx={wallpaper:w,$parent:{wtTag:s.source,$parent:s}};c.textContent=w.title;grid.append(c);}};render();
    window.countQueries=0;
    window.browseWallpaperObject={queryWorkshop:q=>{if(q.totalOnly)countQueries++;}};
    window.host={callDeferred:async(a,b,q)=>{if(q.totalOnly)return new Promise(()=>{});calls.push(q.page);if(outstanding++)collision=true;
      await new Promise(r=>setTimeout(r,35));outstanding--;
      return {token:q.token,pagecount:4,wallpapers:data[q.page].map(id=>({workshopid:String(id),title:'Item '+id}))};}};
    window.angular={element:()=>({injector:()=>({get:name=>name==='host'?host:{when:p=>p}})})};
    let token=0;window.safeApply=()=>{};
    s.callbackChangePage=(n,a,force)=>{s.queryActive=true;s.pagination.current=n;
      host.callDeferred('browseWallpaperObject','queryWorkshop',{page:n,token:++token,text:s.filter.text}).then(r=>{
       s.queryWallpapers=r.wallpapers;s.sortedWallpapers=r.wallpapers;s.queryActive=false;render();
      },()=>{s.queryActive=false;});};
    localStorage.setItem('we.coverHide.v1',JSON.stringify(['21','22','32']));
    </script></body></html>'''
    page.route('http://fixture.test/**',lambda r:r.fulfill(body=html,content_type='text/html'))
    page.goto('http://fixture.test/')
    for name in ['i18n.js','batch-hide.js','cover-hide.js','progressive-pages.js','progressive-ui.js']:
        page.add_script_tag(path=str(ROOT/name))
    page.locator('#we-progressive-open').click()
    page.locator('#we-progressive-enable').click()
    assert page.evaluate('calls')==[]
    assert page.locator('#we-hide-language').count()==0
    page.locator('#we-progressive-next').click()
    page.wait_for_function('weProgressiveUI.state().index===0 && !s.queryActive')
    assert page.evaluate('s.queryWallpapers.map(w=>w.workshopid)')==['23','31','33']
    assert page.evaluate('calls')==[2,3]
    # A hide never requests a replacement; navigation alone fetches more.
    page.locator('.browseWallpaperImage').first.hover()
    page.locator('.we-cover-toggle').first.click()
    page.wait_for_timeout(300)
    assert page.evaluate('calls')==[2,3]
    page.locator('#we-progressive-next').click()
    page.wait_for_function('weProgressiveUI.state().index===1 && !s.queryActive')
    assert page.evaluate('s.queryWallpapers.map(w=>w.workshopid)')==['41','42']
    page.locator('#we-progressive-prev').click()
    page.wait_for_function('weProgressiveUI.state().index===0 && !s.queryActive')
    assert page.evaluate('s.queryWallpapers.map(w=>w.workshopid)')==['31','33']
    assert page.evaluate('calls')==[2,3,4]
    page.evaluate("s.filter.text='changed';s.callbackChangePage(1)")
    page.wait_for_function('weProgressiveUI.state()===null && !s.queryActive')
    assert not page.evaluate("document.body.classList.contains('we-progressive-active')")
    assert not page.evaluate('collision')
    # Native count queries return via their own callback, never this promise.
    # Putting one in the page queue used to block every subsequent page forever.
    page.evaluate("host.callDeferred('browseWallpaperObject','queryWorkshop',{totalOnly:true,callback:'onTotalCountReceived'})")
    for _ in range(3):
        page.evaluate("s.source='installed';render()")
        page.wait_for_timeout(300)
        page.evaluate("s.source='workshop';s.callbackChangePage(1)")
        page.wait_for_function('!s.queryActive',timeout=2000)
    assert page.evaluate('countQueries')==1
    assert not page.evaluate('collision')
    browser.close()
print('PASS: native response adapter, explicit navigation, no instant refill, cached back, filter exit, serialized queries, no language selector')
