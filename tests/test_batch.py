from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]/'src/ui'
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True)
    page=browser.new_page(viewport={'width':1200,'height':700})
    html='''<html><head><meta charset="utf-8"><style>.browseWallpaperImage{position:relative;display:inline-block;width:220px;height:170px;background:#657c99;margin:4px}</style></head>
    <body><a ng-click="setListSourceRecorded('workshop')">Workshop</a><input id="browseSearchFilterText">
    <button id="next" ng-click="callbackChangePage(2)">next page</button>
    <wallpaper-thumbnail wt-tag="workshop"></wallpaper-thumbnail><script>
    window.model={source:'workshop',pagination:{current:1},filter:{text:''},queryActive:false};
    window.clicks=0;window.render=(ids)=>{let grid=document.querySelector('wallpaper-thumbnail');grid.innerHTML='';
      for(const id of ids){let c=document.createElement('div');c.className='browseWallpaperImage';c.textContent='壁纸 '+id;
      c.ctx={$parent:{wtTag:model.source,$parent:model},wallpaper:{workshopid:id,title:'壁纸 '+id,type:'scene',status:'installed'}};
      c.onclick=()=>clicks++;grid.append(c);}};render(['101','102','103']);
    </script></body></html>'''
    page.route('http://batch.test/**',lambda r:r.fulfill(body=html,content_type='text/html; charset=utf-8'))
    page.goto('http://batch.test/')
    for file in ['i18n.js','batch-hide.js','cover-hide.js']:page.add_script_tag(path=str(ROOT/file))
    start=page.locator('#we-batch-start');confirm=page.locator('#we-batch-confirm')
    start.click();assert page.locator('.we-batch-keep').count()==3
    page.locator('.we-batch-keep input').nth(1).check()
    assert page.evaluate('clicks')==0
    assert confirm.inner_text()=='隐藏其余 2 张'
    page.evaluate("weHideI18n.setLanguage('en')")
    assert confirm.inner_text()=='Hide remaining 2'
    assert page.evaluate('weCoverHide.getBatchState().kept')==1
    page.evaluate("weHideI18n.setLanguage('zh')")
    assert confirm.inner_text()=='隐藏其余 2 张'

    page.screenshot(path=str(Path(__file__).resolve().parents[1]/'test-artifacts/batch-selection.png'))
    confirm.click();assert set(page.evaluate('weCoverHide.getHiddenIds()'))=={'101','103'}
    assert page.locator('.browseWallpaperImage:visible').count()==1
    # Cancel does not modify data; keeping everything disables submission.
    start.click();page.locator('.we-batch-keep input').check();assert confirm.is_disabled()
    page.locator('#we-batch-cancel').click();assert set(page.evaluate('weCoverHide.getHiddenIds()'))=={'101','103'}
    # No selection means hide every remaining candidate on this page.
    start.click();confirm.click();assert set(page.evaluate('weCoverHide.getHiddenIds()'))=={'101','102','103'}
    # New page, then page change while selecting: no accidental write.
    page.evaluate("render(['201','202']);model.pagination.current=2;weCoverHide.scan()")
    start.click();page.locator('#next').click();assert page.evaluate('weCoverHide.getBatchState()') is None
    start.click();page.evaluate("model.pagination.current=3")
    # Validate synchronously on commit, before any polling interval runs.
    page.evaluate("document.querySelector('#we-batch-confirm').click()")
    assert set(page.evaluate('weCoverHide.getHiddenIds()'))=={'101','102','103'}
    start.click();page.locator('#browseSearchFilterText').fill('new query')
    assert page.evaluate('weCoverHide.getBatchState()') is None
    # Result replacement with a new set of IDs also exits selection.
    start.click();page.evaluate("render(['301','302']);weCoverHide.scan()")
    assert page.evaluate('weCoverHide.getBatchState()') is None
    page.evaluate("model.source='installed';render(['101','102','103']);weCoverHide.scan()")
    assert not start.is_visible();assert page.locator('.browseWallpaperImage:visible').count()==3
    browser.close()
print('PASS: keep exceptions, hide rest, hide whole page, cancel, all kept, no accidental selection, navigation/input/result-change guards, installed library unaffected')
