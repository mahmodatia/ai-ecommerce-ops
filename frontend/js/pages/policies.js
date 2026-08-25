import { api } from "../api.js";
import { t, formatIntent, getLanguage } from "../i18n.js";
import { badge, emptyState, escapeHtml, pageHead } from "../ui.js";

export async function renderPolicies(container){
  container.innerHTML=`${pageHead(t("policiesTitle"),t("policiesSub"))}<div id="policies-root"><div class="skeleton" style="height:420px"></div></div>`;
  try{
    const data=await api("/policies");
    const ar=getLanguage()==="ar";
    document.getElementById("policies-root").innerHTML=data.length?`<div class="two-equal">${data.map(p=>`<section class="panel"><div class="panel-head"><div><h2 class="section-title">${escapeHtml(ar?(p.name_ar||p.name):p.name)}</h2><div class="small muted" style="margin-top:4px">${formatIntent(p.intent)}</div></div>${badge(t("active"),"success")}</div><div class="panel-body"><div class="facts-grid"><div><div class="fact-label">${t("version")}</div><div class="fact-value mono">${escapeHtml(p.version)}</div></div><div><div class="fact-label">${t("status")}</div><div class="fact-value">${escapeHtml(p.status)}</div></div></div><p class="policy-copy" style="margin:16px 0 0">${escapeHtml(ar?(p.summary_ar||p.summary):p.summary)}</p><hr><div class="policy-copy">${escapeHtml(ar?(p.content_ar||p.content):p.content)}</div></div></section>`).join("")}</div>`:emptyState(t("noPolicies"),"","policies");
  }catch(e){document.getElementById("policies-root").innerHTML=`<div class="notice notice-warning">${escapeHtml(e.message)}</div>`;}
}
