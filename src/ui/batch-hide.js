/* Select exceptions, then hide the remainder of this exact page in one write. */
window.createWeBatchHide = function({idFor,isDiscovery,getHidden,apply}) {
  const t=(key,values)=>window.weHideI18n.t(key,values);
  let batch=null, panel, startButton;
  const decorated=new Set();
  const style=document.createElement('style');
  style.textContent=`
    #we-batch-start{margin-left:8px;cursor:pointer}
    #we-batch-panel{position:fixed;left:18px;bottom:18px;z-index:9000;display:flex;align-items:center;
      gap:12px;flex-wrap:wrap;max-width:calc(100vw - 36px);padding:14px 18px;border:1px solid #708096;
      border-radius:8px;background:#202832;color:#fff;box-shadow:0 5px 24px #0008;font:13px sans-serif}
    #we-batch-panel[hidden]{display:none!important}
    #we-batch-panel button{padding:8px 12px;border-radius:5px;border:1px solid #8493a5;color:white;background:#394554;cursor:pointer}
    #we-batch-panel #we-batch-confirm{background:#9e4038}
    #we-batch-panel button:disabled{opacity:.5;cursor:default}
    .we-batch-keep{position:absolute;right:5px;top:5px;z-index:45;background:#253647;color:white;
      border:1px solid #8faac4;border-radius:5px;padding:5px 7px;display:flex;align-items:center;gap:5px;cursor:pointer;font:12px sans-serif}
    .we-batch-keep input{margin:0!important;cursor:pointer}
    .we-batch-kept{outline:3px solid #65cd9f;outline-offset:-3px}
    .we-batch-kept>.we-batch-keep{background:#155539;border-color:#65cd9f}
    .we-batch-member>.we-cover-toggle{display:none!important}
  `;
  document.head.appendChild(style);
  const cards=()=>[...document.querySelectorAll('.browseWallpaperImage')].filter(c=>idFor(c)&&isDiscovery(c));
  function browserScope(card) {
    for(let s=card?.ctx?.$parent;s;s=s.$parent) if(s.pagination && typeof s.source==='string')return s;
    return null;
  }
  function signature() {
    const all=cards(), s=browserScope(all[0]);
    return JSON.stringify({ids:all.map(idFor), source:s?.source, page:s?.pagination?.current,
      filter:s?.filter, author:s?.filterAuthor, preset:s?.filterPreset,
      // Reading input catches text edits even before the application's debounce fires.
      search:document.getElementById('browseSearchFilterText')?.value,
      busy:!!s?.queryActive});
  }
  function busy(){return !!browserScope(cards()[0])?.queryActive;}
  function cancel(){batch=null;refresh();}
  function begin(){
    if(busy())return;
    const hidden=new Set(getHidden());
    const available=cards().filter(c=>!hidden.has(idFor(c))&&c.getClientRects().length);
    if(!available.length)return;
    batch={signature:signature(),ids:new Set(available.map(idFor)),keep:new Set()};
    refresh();
  }
  function commit(){
    if(!batch)return;
    if(busy()||signature()!==batch.signature){cancel();return;}
    const ids=new Set([...batch.ids].filter(id=>!batch.keep.has(id)));
    const entries=new Map(cards().filter(c=>ids.has(idFor(c))).map(c=>[idFor(c),{id:idFor(c),hidden:true,title:c.ctx.wallpaper.title||''}]));
    if(entries.size!==ids.size){cancel();return;}
    if(!entries.size)return;
    // End selection before apply publishes/repaints the new hidden set.
    const previous=batch;batch=null;
    try{apply([...entries.values()]);}catch(error){batch=previous;window.alert(t('batchError'));}
    refresh();
  }
  function ensureUI(){
    const anchor=document.getElementById('we-hidden-toggle');
    if(!anchor)return;
    if(!startButton?.isConnected){
      startButton=document.createElement('button');startButton.id='we-batch-start';
      startButton.type='button';startButton.className='btn-primary browserSourceButton';
      startButton.textContent=t('batchStart');startButton.title=t('batchHint');
      startButton.addEventListener('click',begin);anchor.after(startButton);
    }
    if(!panel){
      panel=document.createElement('div');panel.id='we-batch-panel';panel.hidden=true;
      const hint=document.createElement('span');hint.textContent=t('keepHint');panel.append(hint);
      const count=document.createElement('span');count.id='we-batch-count';count.setAttribute('aria-live','polite');panel.append(count);
      const confirm=document.createElement('button');confirm.type='button';confirm.id='we-batch-confirm';confirm.addEventListener('click',commit);panel.append(confirm);
      const stop=document.createElement('button');stop.type='button';stop.id='we-batch-cancel';stop.textContent=t('cancel');stop.addEventListener('click',cancel);panel.append(stop);
      document.body.append(panel);
    }
  }
  function refresh(){
    ensureUI();
    if(batch&&(busy()||signature()!==batch.signature))batch=null;
    if(startButton){startButton.textContent=t('batchStart');startButton.title=t('batchHint');}
    if(panel){panel.firstElementChild.textContent=t('keepHint');panel.querySelector('#we-batch-cancel').textContent=t('cancel');}
    const all=cards();
    const hidden=new Set(getHidden());
    if(startButton){startButton.style.display=all.length?'':'none';startButton.disabled=!!batch||!!browserScope(all[0])?.queryActive||!all.some(c=>!hidden.has(idFor(c)));}
    const reveal=document.getElementById('we-hidden-toggle');if(reveal)reveal.disabled=!!batch;
    for(const card of new Set([...decorated,...(batch?all:[])])){
      const id=idFor(card), member=!!batch&&isDiscovery(card)&&batch.ids.has(id);
      card.classList.toggle('we-batch-member',member);
      card.classList.toggle('we-batch-kept',member&&batch.keep.has(id));
      let label=card.querySelector(':scope>.we-batch-keep');
      if(!member){label?.remove();decorated.delete(card);continue;}
      decorated.add(card);
      if(!label){
        label=document.createElement('label');label.className='we-batch-keep';
        const input=document.createElement('input');input.type='checkbox';input.setAttribute('aria-label',t('keepLabel'));
        const text=document.createElement('span');label.append(input,text);
        for(const name of ['click','mousedown','mouseup','dblclick','contextmenu','keydown','keyup'])label.addEventListener(name,e=>e.stopPropagation());
        input.addEventListener('change',e=>{
          e.stopPropagation();
          if(!batch||signature()!==batch.signature){cancel();return;}
          const current=idFor(card);input.checked?batch.keep.add(current):batch.keep.delete(current);refresh();
        });
        card.append(label);
      }
      label.querySelector('input').checked=batch.keep.has(id);
      label.querySelector('input').setAttribute('aria-label',t('keepLabel'));
      const caption=t(batch.keep.has(id)?'kept':'keep');
      if(label.querySelector('span').textContent!==caption)label.querySelector('span').textContent=caption;
    }
    if(panel){
      panel.hidden=!batch;
      if(batch){
        const remaining=batch.ids.size-batch.keep.size;
        const summary=t('summary',{kept:batch.keep.size,total:batch.ids.size});
        if(panel.querySelector('#we-batch-count').textContent!==summary)panel.querySelector('#we-batch-count').textContent=summary;
        const confirm=panel.querySelector('#we-batch-confirm');const caption=t('hideRest',{count:remaining});
        if(confirm.textContent!==caption)confirm.textContent=caption;
        confirm.disabled=remaining===0;
      }
    }
  }
  // Cancel before native navigation/filter changes can dispatch an async query.
  for(const name of ['input','change'])document.addEventListener(name,e=>{
    if(batch&&!e.target.closest('.we-batch-keep,#we-batch-panel,#we-batch-start,#we-hide-language'))cancel();
  },true);
  document.addEventListener('click',e=>{
    if(!batch||e.target.closest('.we-batch-keep,#we-batch-panel,#we-batch-start,#we-hide-language'))return;
    const action=e.target.closest('[ng-click]')?.getAttribute('ng-click')||'';
    if(/Page|Source|Filter|Search|Explore|Navigation|Sort/i.test(action))cancel();
  },true);
  document.addEventListener('keydown',e=>{if(batch&&e.key==='Escape')cancel();});
  return {refresh,state:()=>batch?{total:batch.ids.size,kept:batch.keep.size}:null};
};
