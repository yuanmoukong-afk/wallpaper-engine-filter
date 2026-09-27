/* Durable local mirror. Files are written by the loopback-only companion. */
window.createWeHiddenBackup = function(initialIds, onUpdate) {
  const config = window.weCoverBackupConfig;
  const KEY = 'we.coverHide.records.v1';
  let records = {}, busy = false, synced = false, state = 'syncing', timer;
  const valid = r => r && /^[1-9]\d*$/.test(r.id) && typeof r.hidden === 'boolean' &&
    Number.isSafeInteger(r.updatedAt) && r.updatedAt >= 0 && typeof r.title === 'string';
  try {
    const saved = JSON.parse(localStorage.getItem(KEY) || '[]');
    if (!Array.isArray(saved) || !saved.every(valid)) throw new Error('Invalid local backup state');
    for (const r of saved) records[r.id] = r;
  } catch(error) {
    // Keep the corrupt value for diagnosis; recover IDs and durable disk state.
    state = 'recovering';
  }
  for (const id of initialIds) if (!records[id]) records[id] = {id,hidden:true,title:'',updatedAt:0};
  const persist = () => localStorage.setItem(KEY, JSON.stringify(Object.values(records)));
  const publish = () => onUpdate(Object.values(records).filter(r=>r.hidden).map(r=>r.id));
  function schedule() { clearTimeout(timer); timer = setTimeout(sync, 150); }
  async function sync() {
    if (busy) return;
    busy = true;
    const controller = new AbortController();
    const timeout = setTimeout(()=>controller.abort(),5000);
    try {
      const response = await fetch('http://127.0.0.1:'+config.port+'/sync', {
        method:'POST', headers:{'Content-Type':'application/json','X-WE-Cover-Token':config.token},
        body:JSON.stringify({records:Object.values(records)}), signal:controller.signal
      });
      if (!response.ok) throw new Error('Backup status '+response.status);
      const data = await response.json();
      if (!Array.isArray(data.records) || !data.records.every(valid)) throw new Error('Invalid backup response');
      let changed = false;
      for (const incoming of data.records) {
        const old = records[incoming.id];
        if (!old || incoming.updatedAt > old.updatedAt ||
            (incoming.updatedAt === old.updatedAt && !old.title && incoming.title)) {
          records[incoming.id] = incoming; changed = true;
        }
      }
      persist();
      synced = true;
      if (changed) publish();
      // A click during a request must remain pending until that newer state is sent.
      const remote = new Map(data.records.map(r=>[r.id,JSON.stringify(r)]));
      const pending = Object.values(records).some(r=>remote.get(r.id)!==JSON.stringify(r));
      state = pending ? 'syncing' : 'synced';
      if(pending) schedule();
    } catch(error) { state = 'pending'; }
    finally {clearTimeout(timeout); busy=false;}
  }
  function set(id, hidden, title) {
    setMany([{id,hidden,title}]);
  }
  function setMany(items) {
    const previous = records;
    records = {...records};
    for (const {id,hidden,title} of items) {
      const old = records[id];
      records[id] = {id,hidden,title:title || old?.title || '',updatedAt:Math.max(Date.now(),(old?.updatedAt||0)+1)};
    }
    try { persist(); } catch(error) { records=previous; throw error; }
    state = 'syncing'; publish(); schedule();
  }
  function observe(id,title) {
    const old=records[id];
    if(synced && old?.hidden && !old.title && title) set(id,true,title);
  }
  window.addEventListener('storage',e=>{
    if(e.key!==KEY || !e.newValue)return;
    try {
      const incoming=JSON.parse(e.newValue);
      if(!Array.isArray(incoming)||!incoming.every(valid))return;
      for(const r of incoming)if(!records[r.id]||r.updatedAt>records[r.id].updatedAt)records[r.id]=r;
      publish();schedule();
    }catch(_){}
  });
  try {persist();} catch(error) {state='storageError';}
  // The v1 display cache may have been cleared while the durable local mirror survived.
  queueMicrotask(publish);
  schedule(); setInterval(sync,10000);
  return {set,setMany,observe,sync,status:()=>window.weHideI18n.t(state)};
};
