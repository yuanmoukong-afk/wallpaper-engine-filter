/* Wallpaper Engine 2.8: local, reversible card hiding. */
(() => {
  'use strict';
  if (window.weCoverHide) return;
  const t=(key,values)=>window.weHideI18n.t(key,values);
  const KEY = 'we.coverHide.v1';
  let showHidden = false;
  let backup;
  let batch;
  let hidden;
  try {
    const saved = JSON.parse(localStorage.getItem(KEY) || '[]');
    if (!Array.isArray(saved)) throw new Error('Invalid saved list');
    hidden = new Set(saved.filter(id => typeof id === 'string' && /^\d+$/.test(id)));
  } catch (error) {
    console.error('[cover-hide] Cannot read saved list', error);
    if (!window.weCoverBackupConfig) return;
    hidden = new Set(); // The independent backup can rebuild cleared/damaged UI storage.
  }
  const style = document.createElement('style');
  style.id = 'we-cover-hide-style';
  style.textContent = `
    html:not(.we-show-hidden) .browseWallpaperImage.we-cover-hidden { display:none!important; }
    #we-hidden-toggle { margin-left:8px; cursor:pointer; }
    .browseWallpaperImage.we-cover-hidden { background-image:none!important; background-color:#292d33!important; }
    .browseWallpaperImage.we-cover-hidden > .videoBg { visibility:hidden!important; }
    .we-cover-label { position:absolute; left:0; right:0; top:40%; text-align:center; color:#b9c1ca;
      font:12px sans-serif; pointer-events:none; z-index:3; text-shadow:none; }
    .we-cover-toggle { position:absolute; top:5px; right:5px; z-index:30; padding:4px 6px;
      border:1px solid #8b929b; border-radius:4px; color:#fff; background:#252a32;
      cursor:pointer; font:11px sans-serif; line-height:16px; opacity:0; }
    .browseWallpaperImage:hover > .we-cover-toggle,
    .browseWallpaperImage:focus-within > .we-cover-toggle,
    .we-cover-hidden > .we-cover-toggle { opacity:1; }
    .we-cover-toggle:focus-visible { outline:2px solid #72bdff; }
  `;
  document.head.appendChild(style);
  function idFor(card) {
    const data = card.ctx && card.ctx.wallpaper;
    const grid = card.closest('wallpaper-thumbnail');
    if (grid && /asset/i.test(grid.getAttribute('wt-tag') || '')) return null;
    if (!data || data.type === 'folder' || data.type === 'highlightItem') return null;
    const id = String(data.workshopid || '');
    return /^\d+$/.test(id) && id !== '0' ? id : null;
  }
  function isDiscovery(card) {
    // The page source decides scope, not subscription/download status.
    // A subscribed wallpaper can still be hidden in Workshop search results.
    const scopeTag = card.ctx?.$parent?.wtTag;
    const tag = scopeTag || card.closest('wallpaper-thumbnail')?.getAttribute('wt-tag')?.replace(/^['"]|['"]$/g, '');
    return ['workshop', 'explore', 'exploreHighlights', 'homeHighlights'].includes(tag);
  }
  function paint(card) {
    const id = idFor(card);
    let button = card.querySelector(':scope > .we-cover-toggle');
    let label = card.querySelector(':scope > .we-cover-label');
    if (id && hidden.has(id) && backup) backup.observe(id, card.ctx.wallpaper.title || '');
    if (!id || !isDiscovery(card)) {
      card.classList.remove('we-cover-hidden');
      button?.remove(); label?.remove();
      return;
    }
    if (!button) {
      button = document.createElement('button');
      button.type = 'button';
      button.className = 'we-cover-toggle';
      // Only the small button intercepts input; the rest of the card stays native.
      for (const event of ['mousedown', 'mouseup', 'dblclick', 'contextmenu', 'keydown', 'keyup']) {
        button.addEventListener(event, e => e.stopPropagation());
      }
      button.addEventListener('click', e => {
        e.preventDefault(); e.stopPropagation();
        const currentId = idFor(card); // Read again because the app recycles cards.
        if (!currentId) return;
        const next = new Set(hidden);
        next.has(currentId) ? next.delete(currentId) : next.add(currentId);
        try {
          if (backup) backup.set(currentId, next.has(currentId), card.ctx.wallpaper.title || '');
          localStorage.setItem(KEY, JSON.stringify([...next]));
        }
        catch (error) { window.alert(t('saveError')); return; }
        hidden = next;
        scan();
      });
      card.appendChild(button);
      label = document.createElement('span');
      label.className = 'we-cover-label';
      label.textContent = t('hiddenLabel');
      card.appendChild(label);
    }
    const blocked = hidden.has(id);
    card.classList.toggle('we-cover-hidden', blocked);
    label.textContent = t('hiddenLabel');
    const text = t(blocked ? 'restore' : 'hide');
    if (button.textContent !== text) button.textContent = text;
    button.title = t(blocked ? 'restoreHint' : 'hideHint');
    button.setAttribute('aria-pressed', String(blocked));
    label.hidden = !blocked;
  }
  function scan() {
    let toggle = document.getElementById('we-hidden-toggle');
    const workshop = document.querySelector('[ng-click="setListSourceRecorded(\'workshop\')"]');
    if (!toggle && workshop) {
      toggle = document.createElement('button');
      toggle.id = 'we-hidden-toggle';
      toggle.type = 'button';
      toggle.className = 'btn-primary browserSourceButton';
      toggle.title = t('revealHint');
      toggle.addEventListener('click', () => {
        showHidden = !showHidden;
        document.documentElement.classList.toggle('we-show-hidden', showHidden);
        scan();
      });
      workshop.after(toggle);
    }
    if (toggle) {
      const active = [...document.querySelectorAll('.browseWallpaperImage')].some(isDiscovery);
      const display = active ? '' : 'none';
      if (toggle.style.display !== display) toggle.style.display = display;
      const text = t(showHidden ? 'collapseHidden' : 'showHidden', {count:hidden.size});
      if (toggle.textContent !== text) toggle.textContent = text;
      toggle.setAttribute('aria-pressed', String(showHidden));
      toggle.title = t('revealHint') + (backup ? backup.status() : '');
      window.weHideI18n.mount(toggle);
    }
    document.querySelectorAll('.browseWallpaperImage').forEach(paint);
    batch?.refresh();
  }
  let pending = false;
  const observer = new MutationObserver(records => {
    if (!records.some(r => (r.type === 'attributes' && r.target.matches('.browseWallpaperImage')) || [...r.addedNodes].some(n => n.nodeType === 1 &&
      (n.matches('.browseWallpaperImage') || n.querySelector('.browseWallpaperImage'))))) return;
    if (!pending) { pending = true; requestAnimationFrame(() => { pending = false; scan(); }); }
  });
  function start() {
    scan();
    observer.observe(document.body, {childList:true, subtree:true, attributes:true, attributeFilter:['style']});
    // Also covers context reassignment without DOM mutations during paging.
    setInterval(scan, 250);
  }
  window.addEventListener('storage', e => {
    if (e.key !== KEY) return;
    try { const list = JSON.parse(e.newValue || '[]'); if (Array.isArray(list)) { hidden = new Set(list); scan(); } } catch (_) {}
  });
  window.weCoverHide = {version:'4.2.0', scan, getHiddenIds:() => [...hidden], getBackupStatus:()=>backup?.status(), getBatchState:()=>batch?.state()};
  if(window.createWeBatchHide)batch=window.createWeBatchHide({idFor,isDiscovery,getHidden:()=>[...hidden],apply:items=>{
    if(backup){backup.setMany(items);return;}
    const next=new Set(hidden);for(const item of items)next.add(item.id);
    localStorage.setItem(KEY,JSON.stringify([...next]));hidden=next;scan();
  }});
  if (window.weCoverBackupConfig && window.createWeHiddenBackup) {
    backup = window.createWeHiddenBackup([...hidden], ids => {
      hidden = new Set(ids);
      localStorage.setItem(KEY, JSON.stringify(ids));
      scan();
    });
  }
  window.addEventListener('we-hide-language-change',scan);
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start, {once:true});
  else start();
})();
