import { api } from "../api.js";
import { t } from "../i18n.js";
import { badge, emptyState, escapeHtml, icon, pageHead, toast } from "../ui.js";

let selectedId=null;
let mailFilter="all";
let mailSearch="";

export async function renderInbox(container){
  container.innerHTML=`${pageHead(t("supportInbox"),t("supportInboxSub"),`<button class="btn btn-secondary" id="refresh-inbox">${icon("refresh",15)} ${t("refresh")}</button>`)}<div id="inbox-root"></div>`;
  document.getElementById("refresh-inbox").onclick=()=>load();
  await load();
}

async function load(){
  const root=document.getElementById("inbox-root");
  root.innerHTML=`<div class="inbox-layout"><div class="mail-list"><div class="mail-list-head"><div class="skeleton" style="height:38px"></div></div><div class="mail-items"><div class="skeleton" style="height:120px;margin:12px"></div><div class="skeleton" style="height:120px;margin:12px"></div></div></div><div class="mail-detail"><div class="skeleton" style="height:260px"></div></div></div>`;
  try{
    const health=await api("/health");
    let messages,mode;
    if(health.gmail_mode==="live"){
      messages=await api("/gmail/messages?limit=25");
      mode="live";
    }else{
      messages=(await api("/demo/messages")).map(m=>({...m,processed:false,case_id:null,case_status:null}));
      mode="demo";
    }
    if(!messages.length){root.innerHTML=emptyState(t("allCaughtUp"),t("supportInboxSub"),"inbox");return;}
    draw(root,messages,mode);
  }catch(error){root.innerHTML=`<div class="notice notice-warning">${escapeHtml(error.message)}</div>`;}
}

function visibleMessages(messages){
  const q=mailSearch.trim().toLowerCase();
  return messages.filter(m=>{
    const filterOk=mailFilter==="all"||(mailFilter==="processed"&&m.processed)||(mailFilter==="unprocessed"&&!m.processed);
    const searchOk=!q||`${m.sender_email} ${m.subject} ${m.body}`.toLowerCase().includes(q);
    return filterOk&&searchOk;
  });
}

function draw(root,messages,mode){
  const visible=visibleMessages(messages);
  if(!selectedId || !visible.some(m=>m.id===selectedId)) selectedId=visible[0]?.id||messages[0].id;
  const selected=messages.find(m=>m.id===selectedId)||messages[0];
  const orderOf=m=>(`${m.subject}\n${m.body}`.match(/#\d{4,}/)||[])[0]||null;
  root.innerHTML=`<div class="inbox-layout"><aside class="mail-list"><div class="mail-list-head"><div class="search"><span class="search-icon">${icon("search",15)}</span><input class="input" id="mail-search" value="${escapeHtml(mailSearch)}" placeholder="${t("search")}"></div><div class="toolbar-group" id="mail-filters" style="margin-top:10px"><button class="filter-chip ${mailFilter==='all'?'active':''}" data-mail-filter="all">${t("all")}</button><button class="filter-chip ${mailFilter==='unprocessed'?'active':''}" data-mail-filter="unprocessed">${t("unprocessed")}</button><button class="filter-chip ${mailFilter==='processed'?'active':''}" data-mail-filter="processed">${t("processed")}</button></div></div><div class="mail-items" id="mail-items">${visible.length?visible.map(m=>mailItem(m,orderOf(m))).join(""):emptyState(t("noSearchResults"),"","inbox")}</div></aside><section class="mail-detail" id="mail-detail">${mailDetail(selected,orderOf(selected),mode)}</section></div>`;
  root.querySelectorAll("[data-message-id]").forEach(btn=>btn.onclick=()=>{selectedId=btn.dataset.messageId;draw(root,messages,mode);});
  document.getElementById("mail-search").oninput=e=>{mailSearch=e.target.value;draw(root,messages,mode);requestAnimationFrame(()=>{const input=document.getElementById("mail-search");input?.focus();input?.setSelectionRange(mailSearch.length,mailSearch.length);});};
  document.querySelectorAll("[data-mail-filter]").forEach(b=>b.onclick=()=>{mailFilter=b.dataset.mailFilter;draw(root,messages,mode);});
  const process=document.getElementById("process-selected");
  if(process)process.onclick=async()=>{
    process.disabled=true;
    try{
      const result=mode==="live"?await api(`/gmail/process/${encodeURIComponent(selected.id)}`,{method:"POST"}):await api(`/demo/process/${encodeURIComponent(selected.id)}`,{method:"POST"});
      toast(t("processed"),"success");
      location.hash=`#/cases/${result.case_id}`;
    }catch(error){toast(error.message,"error");process.disabled=false;}
  };
}

function mailItem(m,order){
  const active=m.id===selectedId?"active":"";
  return `<button class="mail-item ${active}" data-message-id="${escapeHtml(m.id)}"><div class="mail-row"><span class="mail-sender">${escapeHtml(m.sender_email.split("@")[0])}</span><span class="mail-time">${m.processed?t("processed"):t("unprocessed")}</span></div><div class="mail-subject">${escapeHtml(m.subject)}</div><div class="mail-preview">${escapeHtml(m.body)}</div><div class="mail-tags">${order?badge(order,"primary","mono"):""}${m.processed?badge(t("processed"),"success"):badge(t("unprocessed"),"warning")}</div></button>`;
}

function mailDetail(m,order,mode){
  return `<div class="toolbar"><div><span class="eyebrow">${mode==="live"?t("liveGmail"):t("demoData")}</span><h2 class="section-title" style="font-size:24px;margin-top:7px">${escapeHtml(m.subject)}</h2><div class="small muted" style="margin-top:7px"><span class="ltr">${escapeHtml(m.sender_email)}</span></div></div>${m.processed&&m.case_id?`<a href="#/cases/${m.case_id}" class="btn btn-primary">${t("openCase")}</a>`:`<button id="process-selected" class="btn btn-primary">${t("processEmail")}</button>`}</div>${order?`<div class="context-strip"><div class="context-cell"><div class="context-label">${t("detectedOrder")}</div><div class="context-value mono">${escapeHtml(order)}</div></div><div class="context-cell"><div class="context-label">${t("source")}</div><div class="context-value">${mode==="live"?"Gmail":t("demo")}</div></div><div class="context-cell"><div class="context-label">${t("status")}</div><div class="context-value">${m.processed?t("processed"):t("unprocessed")}</div></div><div class="context-cell"><div class="context-label">${t("action")}</div><div class="context-value">${m.processed?t("openCase"):t("processEmail")}</div></div></div>`:""}<section class="panel" style="margin-top:18px"><div class="panel-head"><h3 class="section-title" style="font-size:14px">${icon("inbox",16)} ${t("cleanedBody")}</h3>${badge(t("boilerplateRemoved"),"neutral")}</div><div class="panel-body"><div class="message-box">${escapeHtml(m.body)}</div></div></section>`;
}
