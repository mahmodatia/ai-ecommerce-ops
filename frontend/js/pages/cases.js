import { api } from "../api.js";
import { t, formatAction, formatIntent, formatSource } from "../i18n.js";
import { badge, emptyState, escapeHtml, formatDate, pageHead, statusBadge } from "../ui.js";

export async function renderCases(container){
  container.innerHTML=`${pageHead(t("casesTitle"),t("casesSub"))}<div class="toolbar" style="margin-bottom:14px"><div class="toolbar-group" style="flex:1"><div class="search" style="max-width:380px;flex:1"><input id="case-search" class="input" placeholder="${t("searchCases")}"></div><select id="case-status" class="select" style="width:auto"><option value="">${t("all")}</option><option value="awaiting_approval">${t("awaitingApproval")}</option><option value="decision_ready">${t("decisionReady")}</option><option value="approved">${t("approvedStatus")}</option><option value="rejected">${t("rejectedStatus")}</option><option value="gmail_draft_created">${t("draftCreatedStatus")}</option></select><select id="case-intent" class="select" style="width:auto"><option value="">${t("all")}</option><option value="where_is_my_order">${formatIntent("where_is_my_order")}</option><option value="return_refund">${formatIntent("return_refund")}</option><option value="missing_wrong_item">${formatIntent("missing_wrong_item")}</option><option value="cancel_modify">${formatIntent("cancel_modify")}</option><option value="unknown">${formatIntent("unknown")}</option></select><select id="case-source" class="select" style="width:auto"><option value="">${t("source")}: ${t("all")}</option><option value="live_gmail">${formatSource("live_gmail")}</option><option value="mock">${formatSource("mock")}</option><option value="shopify_test">${formatSource("shopify_test")}</option></select><select id="case-sort" class="select" style="width:auto"><option value="newest">${t("newest")}</option><option value="oldest">${t("oldest")}</option><option value="confidence">${t("highestConfidence")}</option></select></div></div><div id="case-list"><div class="skeleton" style="height:360px"></div></div>`;
  try{
    const data=await api("/cases?limit=300");
    const draw=()=>{
      const q=document.getElementById("case-search").value.trim().toLowerCase();
      const status=document.getElementById("case-status").value;
      const intent=document.getElementById("case-intent").value;
      const source=document.getElementById("case-source").value;
      const sort=document.getElementById("case-sort").value;
      const rows=data.filter(c=>(!q||`${c.id} ${c.sender_email} ${c.subject} ${c.order_number||""}`.toLowerCase().includes(q))&&(!status||c.status===status)&&(!intent||c.intent===intent)&&(!source||c.source===source));
      rows.sort((a,b)=>sort==="oldest"?new Date(a.created_at)-new Date(b.created_at):sort==="confidence"?b.confidence-a.confidence:new Date(b.created_at)-new Date(a.created_at));
      document.getElementById("case-list").innerHTML=rows.length?`<div class="table-wrap"><table><thead><tr><th>${t("caseLabel")}</th><th>${t("customer")}</th><th>${t("intent")}</th><th>${t("order")}</th><th>${t("recommendedAction")}</th><th>${t("confidence")}</th><th>${t("status")}</th><th>${t("updated")}</th><th></th></tr></thead><tbody>${rows.map(c=>`<tr><td><strong>${escapeHtml(c.subject)}</strong><div class="small muted mono" style="margin-top:4px">${escapeHtml(c.id.slice(0,10))}</div></td><td class="ltr">${escapeHtml(c.sender_email)}</td><td>${formatIntent(c.intent)}</td><td class="mono">${escapeHtml(c.order_number||"—")}</td><td>${formatAction(c.recommended_action)}</td><td>${badge(`${Math.round(c.confidence*100)}%`,c.confidence<.5?"danger":c.confidence<.75?"warning":"success")}</td><td>${statusBadge(c.status)}<div style="margin-top:5px">${badge(formatSource(c.source),c.source==="live_gmail"?"success":"neutral")}</div></td><td>${formatDate(c.updated_at)}</td><td><a class="btn btn-secondary" href="#/cases/${c.id}">${t("openCase")}</a></td></tr>`).join("")}</tbody></table></div>`:emptyState(t("noCases"),"","cases");
    };
    ["case-search","case-status","case-intent","case-source","case-sort"].forEach(id=>document.getElementById(id).addEventListener(id==="case-search"?"input":"change",draw));
    draw();
  }catch(error){document.getElementById("case-list").innerHTML=`<div class="notice notice-warning">${escapeHtml(error.message)}</div>`;}
}
