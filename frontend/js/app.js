import { api, setToken } from "./api.js";
import { BRAND } from "./brand.js";
import { t, getLanguage, setLanguage, formatIntent, formatStatus } from "./i18n.js";
import { icon, escapeHtml, badge, toast } from "./ui.js";
import { renderOverview } from "./pages/overview.js";
import { renderAttention } from "./pages/attention.js";
import { renderInbox } from "./pages/inbox.js";
import { renderCases } from "./pages/cases.js";
import { renderCase } from "./pages/case.js";
import { renderAutomation } from "./pages/automation.js";
import { renderSignals } from "./pages/signals.js";
import { renderPolicies } from "./pages/policies.js";
import { renderOrders } from "./pages/orders.js";
import { renderIntegrations } from "./pages/integrations.js";
import { renderAudit } from "./pages/audit.js";
import { renderSettings } from "./pages/settings.js";

setLanguage(getLanguage());

const navGroups = [
  {label:"operations", items:[["overview","overview"],["attention","attention"],["inbox","inbox"],["cases","cases"]]},
  {label:"intelligence", items:[["automation","automation"],["signals","signals"],["policies","policies"]]},
  {label:"system", items:[["orders","orders"],["integrations","integrations"],["audit","audit"],["settings","settings"]]},
];

let shellReady=false;
let health=null;
let authStatus=null;

function logoMarkup(extra=""){
  return `<span class="brand-logo ${extra}"><img src="${escapeHtml(BRAND.logoPath)}" alt="${escapeHtml(BRAND.logoAlt)}"></span>`;
}

async function boot(){
  try{
    authStatus=await api("/auth/status");
    if(authStatus.required && !sessionStorage.getItem("aiops_token")){
      renderLogin(); return;
    }
    health=await api("/health");
    await renderShell();
    await route();
  }catch(error){
    if(error.status===401){ renderLogin(); return; }
    document.getElementById("app").innerHTML=`<div class="login-screen"><div class="login-card"><div class="login-brand">${logoMarkup()}<div><strong>${escapeHtml(BRAND.name)}</strong><div class="small muted">${t("somethingWrong")}</div></div></div><div class="notice notice-warning">${escapeHtml(error.message)}</div><button class="btn btn-primary" style="width:100%;margin-top:16px" onclick="location.reload()">${t("retry")}</button></div></div>`;
  }
}

function renderLogin(){
  document.getElementById("app").innerHTML=`<div class="login-screen"><div class="login-card"><div class="login-brand">${logoMarkup()}<div><h1 class="login-title">${escapeHtml(BRAND.name)}</h1><div class="small muted">${t("appSubtitle")}</div></div></div><form class="login-form" id="login-form"><label class="form-group"><span class="form-label">${t("username")}</span><input class="input" name="username" autocomplete="username" required></label><label class="form-group"><span class="form-label">${t("password")}</span><input class="input" name="password" type="password" autocomplete="current-password" required></label><button class="btn btn-primary" type="submit">${t("signIn")}</button></form><div class="login-help">${t("authHelp")}</div><div class="lang-switch" style="margin-top:18px;width:max-content"><button type="button" data-lang="en" class="${getLanguage()==='en'?'active':''}">EN</button><button type="button" data-lang="ar" class="${getLanguage()==='ar'?'active':''}">العربية</button></div></div></div>`;
  document.getElementById("login-form").onsubmit=async e=>{
    e.preventDefault();
    const form=Object.fromEntries(new FormData(e.target).entries());
    const btn=e.target.querySelector("button[type=submit]");
    btn.disabled=true;
    try{
      const result=await api("/auth/login",{method:"POST",body:JSON.stringify(form)});
      setToken(result.token);
      location.reload();
    }catch(error){toast(error.message,"error");btn.disabled=false;}
  };
  document.querySelectorAll("[data-lang]").forEach(b=>b.onclick=()=>{setLanguage(b.dataset.lang);renderLogin();});
}

async function renderShell(){
  const app=document.getElementById("app");
  const envMode=health?.environment||"demo";
  const isLive=envMode==="live";
  const envLabel=envMode==="live"?t("live"):envMode==="mixed"?t("mixed"):t("demo");
  const envTone=envMode==="live"?"success":envMode==="mixed"?"warning":"primary";
  app.innerHTML=`<div class="app-shell"><aside class="sidebar" id="sidebar"><div class="sidebar-brand">${logoMarkup()}<div class="sidebar-brand-copy"><strong>${escapeHtml(BRAND.name)}</strong><span>${t("appSubtitle")}</span></div></div><nav class="sidebar-nav">${navGroups.map(group=>`<div class="nav-group"><div class="nav-label">${t(group.label)}</div>${group.items.map(([key,iconName])=>`<a class="nav-link" data-route="${key}" href="#/${key}">${icon(iconName,17)}<span>${t(key)}</span>${key==='attention'?'<span class="nav-count" id="attention-count">—</span>':''}${key==='inbox'?'<span class="nav-count" id="inbox-count">—</span>':''}</a>`).join('')}</div>`).join('')}</nav><div class="sidebar-foot"><div class="profile-mini"><div class="avatar">OP</div><div class="profile-copy"><strong>${t("operator")}</strong><span>${envLabel} · ${health?.auth_mode==='password'?t('private'):t('local')}</span></div></div></div></aside><main class="main"><header class="topbar"><div class="topbar-left"><button class="icon-btn mobile-menu" id="mobile-menu" aria-label="${t('menu')}">${icon('menu',18)}</button><div class="app-title">${escapeHtml(BRAND.name)}</div><span class="top-divider"></span><span id="env-badge">${badge(envLabel,envTone)}</span></div><div class="topbar-right"><button class="icon-btn" id="global-search" title="${t('globalSearch')}" aria-label="${t('globalSearch')}">${icon('search',17)}</button><span class="global-search-hint">${t('searchShortcut')}</span><div class="lang-switch"><button data-lang="en" class="${getLanguage()==='en'?'active':''}">EN</button><button data-lang="ar" class="${getLanguage()==='ar'?'active':''}">العربية</button></div><button class="icon-btn" title="${t('notifications')}" aria-label="${t('notifications')}">${icon('bell',17)}</button><button class="icon-btn" title="${t('profile')}" aria-label="${t('profile')}">${icon('user',17)}</button></div></header><div class="content">${envMode!=="live"?`<div class="environment-banner">${icon("shield",16)} <strong>${envMode==="mixed"?t("mixedBanner"):t("demoBanner")}</strong></div>`:""}<div id="page"></div></div></main></div>`;
  document.querySelector(".topbar .lang-switch")?.remove();
  document.querySelector(".global-search-hint")?.remove();
  const notificationButton=document.querySelector('.topbar button[title="'+t("notifications")+'"]');
  if(notificationButton){notificationButton.classList.add("notification-btn"); notificationButton.insertAdjacentHTML("beforeend",'<span class="notification-dot" aria-hidden="true"></span>');}
  shellReady=true;
  document.getElementById("mobile-menu").onclick=()=>document.getElementById("sidebar").classList.toggle("open");
  document.getElementById("global-search").onclick=openGlobalSearch;
  document.querySelectorAll("[data-lang]").forEach(b=>b.onclick=()=>{setLanguage(b.dataset.lang);location.reload();});
  document.querySelectorAll(".nav-link").forEach(a=>a.onclick=()=>document.getElementById("sidebar").classList.remove("open"));
  document.addEventListener("keydown",globalShortcut);
  updateCounts();
}

function globalShortcut(event){
  if((event.metaKey||event.ctrlKey) && event.key.toLowerCase()==="k"){
    event.preventDefault();
    openGlobalSearch();
  }
}

async function openGlobalSearch(){
  const root=document.getElementById("modal-root");
  root.innerHTML=`<div class="modal-backdrop"><div class="modal" role="dialog" aria-modal="true"><div class="modal-head"><div><strong>${t('globalSearch')}</strong><div class="small muted" style="margin-top:3px">${t('globalSearchHelp')}</div></div><button class="icon-btn" data-close>${icon('x',17)}</button></div><div class="modal-body"><div class="search"><span class="search-icon">${icon('search',15)}</span><input id="global-search-input" class="input" autocomplete="off" placeholder="${t('searchCases')}"></div><div class="search-results" id="global-search-results"><div class="small muted">${t('loading')}</div></div></div></div></div>`;
  const close=()=>{root.innerHTML="";};
  root.querySelector("[data-close]").onclick=close;
  root.querySelector(".modal-backdrop").onclick=e=>{if(e.target===e.currentTarget)close();};
  const input=document.getElementById("global-search-input");
  input.focus();
  let cases=[];
  try{cases=await api("/cases?limit=300");}catch(error){document.getElementById("global-search-results").innerHTML=`<div class="notice notice-warning">${escapeHtml(error.message)}</div>`;return;}
  const draw=()=>{
    const q=input.value.trim().toLowerCase();
    const results=(q?cases.filter(c=>`${c.id} ${c.sender_email} ${c.subject} ${c.order_number||''}`.toLowerCase().includes(q)):cases.slice(0,8)).slice(0,12);
    const box=document.getElementById("global-search-results");
    box.innerHTML=results.length?results.map(c=>`<button class="search-result" data-case="${escapeHtml(c.id)}"><span class="search-result-main"><span class="search-result-title">${escapeHtml(c.subject)}</span><span class="search-result-meta"><span class="mono">${escapeHtml(c.order_number||c.id.slice(0,8))}</span> · ${escapeHtml(c.sender_email)} · ${formatIntent(c.intent)} · ${formatStatus(c.status)}</span></span><span class="search-result-go">${icon('arrow',16)}</span></button>`).join(""):`<div class="empty-state" style="padding:28px 12px"><strong>${t('noSearchResults')}</strong></div>`;
    box.querySelectorAll("[data-case]").forEach(b=>b.onclick=()=>{location.hash=`#/cases/${b.dataset.case}`;close();});
  };
  input.oninput=draw;
  draw();
}

async function updateCounts(){
  try{
    const attention=await api("/attention?limit=200");
    const a=document.getElementById("attention-count"); if(a)a.textContent=attention.length;
    if(health?.gmail_mode==="live"){
      const messages=await api("/gmail/messages?limit=25");
      const i=document.getElementById("inbox-count"); if(i)i.textContent=messages.filter(m=>!m.processed).length;
    }else{
      const messages=await api("/demo/messages");
      const i=document.getElementById("inbox-count"); if(i)i.textContent=messages.length;
    }
  }catch{}
}

function routeInfo(){
  const raw=(location.hash||"#/overview").replace(/^#\//,"");
  const parts=raw.split("/").filter(Boolean);
  if(parts[0]==="cases" && parts[1]) return {key:"cases",detail:true,id:parts[1]};
  return {key:parts[0]||"overview",detail:false};
}

async function route(){
  if(!shellReady)return;
  const info=routeInfo();
  document.querySelectorAll(".nav-link").forEach(a=>a.classList.toggle("active",a.dataset.route===info.key));
  const page=document.getElementById("page");
  page.innerHTML=`<div class="skeleton" style="height:40px;width:40%;margin-bottom:22px"></div><div class="skeleton" style="height:420px"></div>`;
  try{
    if(info.detail && info.key==="cases") return await renderCase(page,info.id);
    const pages={overview:renderOverview,attention:renderAttention,inbox:renderInbox,cases:renderCases,automation:renderAutomation,signals:renderSignals,policies:renderPolicies,orders:renderOrders,integrations:renderIntegrations,audit:renderAudit,settings:renderSettings};
    const renderer=pages[info.key]||renderOverview;
    await renderer(page);
    updateCounts();
  }catch(error){
    if(error.status===401){setToken("");renderLogin();return;}
    page.innerHTML=`<div class="notice notice-warning">${escapeHtml(error.message)}</div>`;
  }
}

window.addEventListener("hashchange",route);
boot();
