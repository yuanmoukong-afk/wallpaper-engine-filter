/* Small dependency-free UI dictionary. Wallpaper titles are never translated. */
(() => {
  const KEY='we.coverHide.language';
  const messages={
    zh:{hide:'隐藏壁纸',restore:'恢复壁纸',hiddenLabel:'已隐藏 · 点击查看详情',
      hideHint:'从搜索列表隐藏这张壁纸，不占位置；可通过显示已隐藏找回',restoreHint:'将这张壁纸恢复到正常搜索列表',
      showHidden:'显示已隐藏（{count}）',collapseHidden:'收起已隐藏（{count}）',revealHint:'临时显示当前页被隐藏的壁纸。',
      saveError:'隐藏记录保存失败，本次未更改。',batchError:'批量隐藏保存失败，未完成操作。',
      batchStart:'批量隐藏本页',batchHint:'先勾选要保留的壁纸，再隐藏本页其余壁纸',
      keepHint:'勾选表示保留',keep:'保留这张',kept:'已保留',keepLabel:'保留这张壁纸',
      summary:'保留 {kept} 张，共 {total} 张',hideRest:'隐藏其余 {count} 张',cancel:'取消',
      sharedListError:'共享名单格式有误，未导入修改',syncing:'正在备份',recovering:'等待从文件恢复',synced:'名单已自动备份',
      pending:'备份待同步（本地记录已保留）',storageError:'备份待同步（本地存储不可写）'},
    en:{hide:'Hide wallpaper',restore:'Restore wallpaper',hiddenLabel:'Hidden · Click for details',
      hideHint:'Hide this card from discovery results without leaving a gap. Use Show hidden to restore it.',restoreHint:'Restore this wallpaper to discovery results.',
      showHidden:'Show hidden ({count})',collapseHidden:'Collapse hidden ({count})',revealHint:'Temporarily reveal hidden wallpapers on this page. ',
      saveError:'Could not save the hidden list. No change was applied.',batchError:'Could not save the batch. The operation was not completed.',
      batchStart:'Hide this page…',batchHint:'Select the wallpapers you want to keep, then hide the rest of this page.',
      keepHint:'Checked means keep',keep:'Keep this',kept:'Keeping',keepLabel:'Keep this wallpaper',
      summary:'Keep {kept} of {total}',hideRest:'Hide remaining {count}',cancel:'Cancel',
      sharedListError:'Invalid shared list; edits were not imported',syncing:'Backing up…',recovering:'Waiting to restore from file',synced:'Hidden list backed up',
      pending:'Backup pending (saved in the app)',storageError:'Backup pending (local storage is not writable)'}
  };
  let language=window.weCoverUIConfig?.language==='en'?'en':'zh';
  function t(key,values={}){return (messages[language][key]||key).replace(/\{(\w+)\}/g,(_,name)=>String(values[name]??''));}
  function setLanguage(value){
    if(!(value in messages))return;
    language=value;
    window.dispatchEvent(new Event('we-hide-language-change'));
  }
  function mount(){document.getElementById('we-hide-language')?.remove();}
  window.weHideI18n={t,setLanguage,mount,getLanguage:()=>language};
})();
