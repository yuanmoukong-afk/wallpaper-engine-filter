"""Mirror the native host's single callback slot, including late responses."""
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]/'src/ui'
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True)
    page=browser.new_page()
    page.route('http://recovery.test/**',lambda r:r.fulfill(content_type='text/html',body='''
      <html><body><button id="we-hidden-toggle"></button><div class="browseWallpaperImage"></div>
      <script>
      const realTimeout=window.setTimeout;
      window.setTimeout=(fn,ms,...args)=>realTimeout(fn,ms===15000?200:ms,...args);
      window.s={source:'workshop',pagination:{current:1,count:3},queryWallpapers:[{workshopid:'1'}],filter:{}};
      document.querySelector('.browseWallpaperImage').ctx=s;
      window.weCoverHide={getHiddenIds:()=>[],getBatchState:()=>null};
      window.tokens=[];
      window.browseWallpaperObject={queryWorkshop:q=>{if(q.callback){window.countCalls++;return;}
        tokens.push(q.token);
        setTimeout(()=>window.queryWorkshopCallback?.({token:q.token,pagecount:3,wallpapers:[{workshopid:'1'}]}),q.delay);
      }};
      window.countCalls=0;
      window.host={callDeferred:(object,method,q)=>new Promise((resolve,reject)=>{
        window.queryWorkshopCallback=response=>{window.queryWorkshopCallback=window.queryWorkshopCallbackError=undefined;resolve(response);};
        window.queryWorkshopCallbackError=error=>{window.queryWorkshopCallback=window.queryWorkshopCallbackError=undefined;reject(error);};
        window[object][method](q);
      })};
      window.angular={element:()=>({injector:()=>({get:name=>name==='host'?host:{when:p=>Promise.resolve(p)}})})};
      </script></body></html>'''))
    page.goto('http://recovery.test/')
    for name in ['i18n.js','progressive-pages.js','progressive-ui.js']:
        page.add_script_tag(path=str(ROOT/name))
    page.locator('#we-progressive-open').click()
    page.locator('#we-progressive-enable').click()
    page.evaluate("""()=>{
      window.results=[];
      host.callDeferred('browseWallpaperObject','queryWorkshop',{token:100,delay:300}).then(()=>results.push('unexpected'),()=>results.push('timeout'));
      host.callDeferred('browseWallpaperObject','queryWorkshop',{token:101,delay:150}).then(r=>results.push(r.token));
      setTimeout(()=>host.callDeferred('browseWallpaperObject','queryWorkshop',{totalOnly:true,callback:'onTotalCountReceived'}),30);
    }""")
    page.wait_for_function('results.length===2')
    assert page.evaluate('results')==['timeout',101],page.evaluate('results')
    assert page.evaluate('countCalls')==1
    assert page.evaluate('tokens')==[100,101]
    assert page.evaluate('window.queryWorkshopCallback===undefined')
    browser.close()
print('PASS: timeout releases queue, late token ignored, custom count callback does not overwrite active page callback')
