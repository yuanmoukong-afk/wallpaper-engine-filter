const assert=require('node:assert/strict');
const {create}=require('../src/ui/progressive-pages.js');
const row=id=>({workshopid:String(id)});
(async()=>{
  let hidden=new Set(['21','22','24','32']),calls=[];
  const raw={2:[21,22,23,24],3:[23,31,32,33],4:[41,42]};
  const engine=create({start:2,size:4,getHidden:()=>[...hidden],fetchPage:async page=>{
    calls.push(page);return {wallpapers:raw[page].map(row),pagecount:4};
  }});
  assert.deepEqual(calls,[],'No fetching merely on activation');
  const first=await engine.next();assert.deepEqual(first.items.map(r=>r.workshopid),['23','31','33','41']);
  assert.deepEqual(calls,[2,3,4]);assert.equal(first.from,2);assert.equal(first.to,4);
  hidden.add('31');assert.equal(engine.pages[0].items.length,4,'Hiding does not replenish a cached page');
  assert.deepEqual(calls,[2,3,4]);
  const last=await engine.next();assert.deepEqual(last.items.map(r=>r.workshopid),['42']);assert.equal(last.more,false);
  let fail=true;
  const retry=create({start:1,size:3,getHidden:()=>[],fetchPage:async n=>{
    if(n===2 && fail)throw Error('Network failed');return {wallpapers:[row(n)],pagecount:3};
  }});
  await assert.rejects(retry.next());assert.equal(retry.pages.length,0);
  fail=false;assert.deepEqual((await retry.next()).items.map(r=>r.workshopid),['1','2','3']);
  const bounded=create({start:1,size:2,maxRequests:2,getHidden:()=>['1','2','3'],fetchPage:async n=>({wallpapers:[row(n)],pagecount:3})});
  assert.equal((await bounded.next()).limited,true);
  assert.equal((await bounded.next()).more,false);
  let alive=true;
  const cancelled=create({start:1,size:1,getHidden:()=>[],isCurrent:()=>alive,fetchPage:async()=>{alive=false;return {wallpapers:[row(1)],pagecount:1};}});
  await assert.rejects(cancelled.next());assert.equal(cancelled.pages.length,0);
  let reads=0;
  const large=create({start:1,size:50,getHidden:()=>{reads++;return Array.from({length:3000},(_,i)=>String(i+1));},
    fetchPage:async n=>({wallpapers:Array.from({length:50},(_,i)=>row((n-1)*50+i+1)),pagecount:100})});
  assert.equal((await large.next()).limited,true);
  assert.equal(reads,21,'Build the hidden lookup once per fetched page, not once per item');
  let evolving=[];
  const changedDuringRead=create({start:1,size:1,getHidden:()=>evolving,fetchPage:async()=>{
    evolving=['1'];return {wallpapers:[row(1),row(2)],pagecount:1};
  }});
  assert.deepEqual((await changedDuringRead.next()).items.map(r=>r.workshopid),['2']);
  console.log('PASS: start boundary, packing, leftovers, deduplication, no instant refill, retry, bounded scan, cancellation');
})().catch(e=>{console.error(e);process.exitCode=1;});
