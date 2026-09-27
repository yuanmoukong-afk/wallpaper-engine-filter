from pathlib import Path
from playwright.sync_api import sync_playwright
import json

root = Path(__file__).resolve().parents[1]/'src/ui'
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.route('http://cover-hide.test/**', lambda route: route.fulfill(body='''<html><head><style>
    .browseWallpaperImage {position:relative;width:240px;height:150px;background-image:linear-gradient(red,blue);display:inline-block}
    </style></head><body><a ng-click="setListSourceRecorded('workshop')">Workshop</a><div id="details">none</div><wallpaper-thumbnail wt-tag="workshop">
    <div class="browseWallpaperImage"><video class="videoBg"></video><span>Sample</span></div>
    <div id="next" style="display:inline-block;width:240px;height:150px">Next</div></wallpaper-thumbnail><script>window.clicks=0;const card=document.querySelector('.browseWallpaperImage');
    card.ctx={wallpaper:{workshopid:'12345',type:'scene'}};
    card.addEventListener('click',()=>{clicks++;document.querySelector('#details').textContent=card.ctx.wallpaper.workshopid});
    </script></body></html>''', content_type='text/html'))
    page.goto('http://cover-hide.test/')
    page.add_script_tag(path=str(root/'i18n.js'))
    page.add_script_tag(path=str(root/'cover-hide.js'))
    card = page.locator('.browseWallpaperImage')
    card.hover()
    button = page.locator('.we-cover-toggle')
    next_before = page.locator('#next').bounding_box()
    button.click()
    assert card.evaluate('e=>getComputedStyle(e).display') == 'none'
    assert card.bounding_box() is None
    assert page.locator('#next').bounding_box()['x'] < next_before['x'], 'Next card must fill the gap'
    assert page.evaluate('clicks') == 0, 'Hide must not select the wallpaper'
    assert card.evaluate("e=>getComputedStyle(e).backgroundImage") == 'none'
    assert page.locator('video').evaluate('e=>getComputedStyle(e).visibility') == 'hidden'
    page.locator('#we-hidden-toggle').click()
    card.click(position={'x':30,'y':80})
    assert page.locator('#details').inner_text() == '12345', 'Hidden card must open details'
    page.reload()
    page.add_script_tag(path=str(root/'i18n.js'))
    page.add_script_tag(path=str(root/'cover-hide.js'))
    assert card.bounding_box() is None, 'Whole-card hide must survive reload'
    assert 'we-cover-hidden' in card.get_attribute('class'), 'Hidden state must survive reload'
    card.evaluate("e=>e.ctx.$parent={wtTag:'installed'}")
    page.wait_for_timeout(350)
    assert card.bounding_box() is not None, 'Installed/subscribed library must remain visible'
    assert button.count() == 0, 'Installed library must not offer hiding'
    card.evaluate("e=>{e.ctx.$parent.wtTag='workshop';e.ctx.wallpaper.status='installed'}")
    page.wait_for_timeout(350)
    assert card.bounding_box() is None, 'Subscribed item in Workshop must still be hidden'
    card.evaluate("e=>e.ctx.wallpaper={workshopid:'98765',type:'scene'}")
    page.wait_for_timeout(350)
    assert 'we-cover-hidden' not in card.get_attribute('class'), 'Recycled node must not hide different wallpaper'
    card.evaluate("e=>e.ctx.wallpaper={workshopid:'12345',type:'scene'}")
    page.wait_for_timeout(350)
    assert 'we-cover-hidden' in card.get_attribute('class')
    page.screenshot(path=str(Path(__file__).resolve().parents[1]/'test-artifacts/hidden.png'))
    page.locator('#we-hidden-toggle').click()
    button.click()
    assert page.evaluate('weCoverHide.getHiddenIds().length') == 0
    assert card.evaluate('e=>getComputedStyle(e).backgroundImage') != 'none'
    assert page.locator('video').evaluate('e=>getComputedStyle(e).visibility') == 'visible'
    card.evaluate("e=>e.ctx.wallpaper={type:'folder'}")
    page.wait_for_timeout(350)
    assert button.count() == 0
    browser.close()
print(json.dumps({'passed':['whole card removed from layout', 'next card fills gap', 'show hidden then native details click', 'no selection on hide', 'persistence', 'recycled cards', 'restore', 'folder exclusion']}))
