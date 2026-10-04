/* Transactional page packing. Fetching occurs only on an explicit next request. */
(() => {
  function create({start, size, fetchPage, getHidden, isCurrent=()=>true, maxRequests=20}) {
    if (!Number.isInteger(start) || start < 1 || !Number.isInteger(size) || size < 1) throw Error('Invalid pagination');
    let state={raw:start, buffer:[], seen:new Set(), ended:false, meta:null};
    const pages=[];
    let busy=false;
    async function next() {
      if(busy)throw Error('Page request already running');
      busy=true;
      const draft={...state,buffer:state.buffer.slice(),seen:new Set(state.seen)};
      const rows=[];let from=draft.buffer[0]?.page ?? draft.raw, to=from, requests=0;
      let hidden=new Set(getHidden());
      try {
        while(rows.length<size) {
          if(!isCurrent())throw Error('Page request cancelled');
          if(!draft.buffer.length) {
            if(draft.ended || requests>=maxRequests)break;
            const raw=draft.raw, response=await fetchPage(raw);
            if(!isCurrent())throw Error('Page request cancelled');
            // Refresh after an await, not once for each wallpaper on the page.
            hidden=new Set(getHidden());
            if(!response || !Array.isArray(response.wallpapers) || !Number.isInteger(response.pagecount) || response.pagecount<0)throw Error('Unsupported page response');
            draft.meta=response;requests++;to=raw;
            draft.buffer=response.wallpapers.map(item=>({item,page:raw}));
            draft.raw=raw+1;draft.ended=raw>=response.pagecount;
            // Empty pages before the reported end can occur after filtering.
            if(!draft.buffer.length)continue;
          }
          const {item,page}=draft.buffer.shift();to=page;
          const id=String(item.workshopid || '');
          if(!/^[1-9]\d*$/.test(id))throw Error('Unsupported wallpaper ID');
          if(draft.seen.has(id))continue;
          draft.seen.add(id);
          if(!hidden.has(id))rows.push(item);
        }
        if(!isCurrent())throw Error('Page request cancelled');
        const page={items:rows,from,to,more:!!draft.buffer.length || !draft.ended,
          limited:rows.length<size && !draft.ended && requests>=maxRequests,meta:draft.meta};
        state=draft;pages.push(page);return page;
      } finally {busy=false;}
    }
    return {next,pages};
  }
  if(typeof module!=='undefined' && module.exports)module.exports={create};
  else window.weProgressivePages={create};
})();
