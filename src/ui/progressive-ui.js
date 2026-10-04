/* Opt-in Workshop packing through the native response renderer, never subscriptions. */
(() => {
  if(window.weProgressiveUI || !window.weProgressivePages)return;
  let panel,button,input,note,startButton,prevButton,nextButton,stopButton;
  let session=null,intent=null,queue=Promise.resolve(),host,original,qService;
  let message='',opened=false;
  const messages={
    zh:{open:'递进浏览',start:'启用递进',from:'从原始页开始',prev:'上一页',next:'递进下一页',stop:'退出递进',
      ready:'点击下一页开始补位；隐藏时不会立即补位。',busy:'正在读取后续页面…',
      range:'整理页 {page} · 原始页 {from}–{to}',limit:'本次已检查 20 页，可继续下一页。',
      unavailable:'当前界面不支持递进，请在创意工坊加载完成后再试。',error:'读取失败，已退出递进。',
      changed:'搜索条件或页面已改变，递进已退出。',invalid:'请输入有效的原始页码。'},
    en:{open:'Progressive browsing',start:'Enable',from:'Start at original page',prev:'Previous',next:'Next filled page',stop:'Exit',
      ready:'Click Next to fill a page. Hiding a card does not refill it.',busy:'Reading following pages…',
      range:'Filled page {page} · Original pages {from}–{to}',limit:'Checked 20 pages; continue with Next.',
      unavailable:'Wait for Workshop results to finish loading, then try again.',error:'Loading failed; progressive mode exited.',
      changed:'Search or page changed; progressive mode exited.',invalid:'Enter a valid original page number.'}
  };
  function t(key,values={}) {
    const lang=window.weHideI18n?.getLanguage()==='en'?'en':'zh';
    return messages[lang][key].replace(/\{(\w+)\}/g,(_,k)=>values[k]??'');
  }
  function scope() {
    for(const c of document.querySelectorAll('.browseWallpaperImage'))
      for(let s=c.ctx;s;s=s.$parent)if(s.pagination && typeof s.source==='string')return s;
    return null;
  }
  const signature=s=>JSON.stringify([s.source,s.filter,s.filterAuthor,s.filterPreset,
    document.getElementById('browseSearchFilterText')?.value]);
  function apply(s){if(window.safeApply)window.safeApply(s);else s?.$evalAsync?.();}
  function deactivate(reason='',reload=false) {
    const old=session;session=null;intent=null;message=reason;
    document.body.classList.remove('we-progressive-active');
    if(reload && old && old.scope.source==='workshop' && !old.scope.queryActive) {
      const raw=old.engine?.pages[old.index]?.from ?? old.originalPage;
      old.scope.callbackChangePage(raw,false,true);apply(old.scope);
    }
    refresh();
  }
  function connect() {
    if(host)return true;
    for(const el of [document.body,document.documentElement,document.querySelector('[ng-app]')]){
      try {const injector=window.angular?.element(el).injector();host=injector?.get('host');qService=injector?.get('$q');}catch(_){}
      if(host && qService)break;
    }
    if(!host || !qService || typeof host.callDeferred!=='function'){host=null;return false;}
    original=host.callDeferred;
    // Native callDeferred uses one global callback per method, so page reads
    // must remain serial. Count queries use a different, explicit callback:
    // their callDeferred promise never settles and must not enter this queue.
    function nativePage(args) {
      const query=args[2];
      return new Promise((resolve,reject)=>{
        let timer,guard,errorCallback;
        const clean=()=>{
          clearTimeout(timer);
          if(guard && window.queryWorkshopCallback===guard)window.queryWorkshopCallback=undefined;
          if(errorCallback && window.queryWorkshopCallbackError===errorCallback)window.queryWorkshopCallbackError=undefined;
        };
        timer=setTimeout(()=>{clean();reject(Error('Workshop request timed out'));},15000);
        try {
          const pending=original.apply(host,args);
          const callback=window.queryWorkshopCallback;
          errorCallback=window.queryWorkshopCallbackError;
          if(typeof callback==='function' && query?.token!==undefined){
            guard=function(response){
              // A response arriving after timeout must not consume a newer callback.
              if(response?.token!==query.token)return;
              return callback.apply(this,arguments);
            };
            window.queryWorkshopCallback=guard;
          }
          Promise.resolve(pending).then(value=>{clean();resolve(value);},error=>{clean();reject(error);});
        }catch(error){clean();reject(error);}
      });
    }
    host.callDeferred=function(object,method,query) {
      if(object!=='browseWallpaperObject' || method!=='queryWorkshop')return original.apply(this,arguments);
      if(query?.callback){
        if(typeof window[object]?.[method]==='function'){
          // The named native callback owns this result (e.g. totalOnly counts).
          return qService.when(window[object][method].apply(window[object],[...arguments].slice(2)));
        }
        return original.apply(this,arguments);
      }
      const args=[...arguments], own=intent;intent=null;
      if(!own && session)deactivate('changed');
      const job=async()=>{
        if(!own || own.session!==session)return nativePage(args);
        const active=own.session;
        try {
          active.query=query;
          if(!active.engine)active.engine=window.weProgressivePages.create({
            start:active.start,size:active.size,getHidden:()=>window.weCoverHide.getHiddenIds(),
            isCurrent:()=>session===active && signature(active.scope)===active.signature,
            fetchPage:page=>nativePage([object,method,{...active.query,page}])
          });
          const packed=own.index<active.engine.pages.length ? active.engine.pages[own.index] : await active.engine.next();
          if(session!==active || signature(active.scope)!==active.signature)throw Error('Cancelled');
          active.index=own.index;active.busy=false;
          const hidden=new Set(window.weCoverHide.getHiddenIds());
          return {...packed.meta,token:query.token,wallpapers:packed.items.filter(w=>!hidden.has(String(w.workshopid)))};
        }catch(error){if(session===active)deactivate('error');throw error;}
      };
      const pending=queue.catch(()=>{}).then(job);queue=pending.catch(()=>{});
      return qService.when(pending);
    };
    return true;
  }
  function begin() {
    const s=scope(),n=Number(input.value);
    if(!s || s.source!=='workshop' || s.queryActive || s.isUsingBackup || !connect()) {message='unavailable';refresh();return;}
    if(!Number.isInteger(n) || n<1 || n>s.pagination.count){message='invalid';refresh();return;}
    session={scope:s,start:n,size:Math.max(1,Math.min(500,s.queryWallpapers?.length || s.sortedWallpapers?.length || 50)),
      originalPage:s.pagination.current,signature:signature(s),index:-1,engine:null,busy:false};
    message='';document.body.classList.add('we-progressive-active');refresh();
  }
  function navigate(delta) {
    const active=session;if(!active || active.busy || active.scope.queryActive)return;
    const index=active.index+delta;
    if(index<0)return;
    if(delta>0 && active.index>=0 && !active.engine.pages[active.index].more)return;
    active.busy=true;intent={session:active,index};
    // Native handler validates the complete filter and prepares thumbnail metadata.
    // Keep its hidden original-page control anchored; our panel labels packed pages.
    active.scope.callbackChangePage(active.scope.pagination.current,false,true);
    apply(active.scope);refresh();
  }
  function mount() {
    const anchor=document.getElementById('we-batch-start') || document.getElementById('we-hidden-toggle');
    if(!anchor)return;
    if(!button?.isConnected){
      button=document.createElement('button');button.id='we-progressive-open';button.type='button';
      button.className='btn-primary browserSourceButton';button.style.marginLeft='8px';
      button.onclick=()=>{opened=!opened;if(opened && !session)input.value=Math.min((scope()?.pagination.current||1)+1,scope()?.pagination.count||1);refresh();};anchor.after(button);
    }
    if(panel)return;
    const style=document.createElement('style');style.textContent=`
      .we-progressive-active .browseWallpaperPagination{visibility:hidden!important}
      #we-progressive-panel{position:fixed;right:18px;bottom:18px;z-index:8500;max-width:calc(100vw - 36px);display:flex;align-items:center;gap:9px;flex-wrap:wrap;padding:12px;border:1px solid #8291a3;border-radius:7px;background:#202832;color:white;font:13px sans-serif;box-shadow:0 4px 20px #0008}
      #we-progressive-panel[hidden]{display:none!important}
      #we-progressive-panel button,#we-progressive-panel input{background:#344457;color:white;border:1px solid #8291a3;border-radius:4px;padding:6px}
      #we-progressive-panel button:disabled{opacity:.5}
      #we-progressive-panel input{width:75px}
    `;document.head.append(style);
    panel=document.createElement('div');panel.id='we-progressive-panel';
    const label=document.createElement('label');label.id='we-progressive-label';input=document.createElement('input');
    const caption=document.createElement('span');caption.id='we-progressive-from-label';label.prepend(caption);
    input.id='we-progressive-from';input.type='number';input.min='1';label.append(input);panel.append(label);
    const add=(id,fn)=>{const b=document.createElement('button');b.id=id;b.type='button';b.onclick=fn;panel.append(b);return b;};
    startButton=add('we-progressive-enable',begin);prevButton=add('we-progressive-prev',()=>navigate(-1));
    nextButton=add('we-progressive-next',()=>navigate(1));stopButton=add('we-progressive-stop',()=>{deactivate('',true);opened=false;refresh();});
    note=document.createElement('span');note.setAttribute('aria-live','polite');panel.append(note);document.body.append(panel);
  }
  function refresh() {
    mount();if(!panel)return;
    const s=scope();
    if(session && signature(session.scope)!==session.signature){deactivate('changed');return;}
    const supported=s?.source==='workshop';
    button.textContent=t('open');button.style.display=supported?'':'none';
    panel.hidden=!opened || !supported || !!window.weCoverHide?.getBatchState();
    document.getElementById('we-progressive-from-label').textContent=t('from')+' ';
    input.disabled=!!session;input.title=t('from');input.setAttribute('aria-label',t('from'));
    input.placeholder=t('from');
    startButton.textContent=t('start');startButton.hidden=!!session;
    prevButton.textContent=t('prev');nextButton.textContent=t('next');stopButton.textContent=t('stop');
    prevButton.hidden=nextButton.hidden=!session;
    prevButton.disabled=!session || session.index<1 || session.busy || !!s?.queryActive;
    nextButton.disabled=!session || session.busy || !!s?.queryActive || (session.index>=0 && !session.engine.pages[session.index].more);
    stopButton.disabled=!!session?.busy;
    let text=message?t(message):t('ready');
    if(session?.busy)text=t('busy');
    else if(session?.index>=0){const p=session.engine.pages[session.index];text=t('range',{page:session.index+1,from:p.from,to:p.to})+(p.limited?' · '+t('limit'):'');}
    if(note.textContent!==text)note.textContent=text;
  }
  window.weProgressiveUI={state:()=>session?{start:session.start,index:session.index,busy:session.busy,pages:session.engine?.pages.length||0}:null};
  setInterval(refresh,250);
})();
