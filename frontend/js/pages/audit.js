import { api } from "../api.js";
import {
  t,
  formatAction,
  formatAuditAction,
  formatAuditStatus,
  formatIntent,
  formatSource,
} from "../i18n.js";
import { badge, emptyState, escapeHtml, formatDate, pageHead } from "../ui.js";

function detailText(item){
  const d=item.details||{};
  const bits=[];
  if(d.intent) bits.push(formatIntent(d.intent));
  if(d.recommended_action) bits.push(formatAction(d.recommended_action));
  if(d.source) bits.push(formatSource(d.source));
  if(d.order_number) bits.push(d.order_number);
  if(d.notes) bits.push(d.notes);
  if(d.actor && d.actor!==item.actor) bits.push(d.actor);
  if(d.gmail_draft_id) bits.push(`Draft ${String(d.gmail_draft_id).slice(0,10)}`);
  if(d.approved_by) bits.push(d.approved_by);
  if(d.rejected_by) bits.push(d.rejected_by);
  if(d.edited_by) bits.push(d.edited_by);
  return bits.filter(Boolean).join(" · ") || "—";
}

export async function renderAudit(container){
  container.innerHTML=`${pageHead(t("auditTitle"),t("auditSub"))}<div class="toolbar" style="margin-bottom:14px"><div class="search" style="max-width:420px;flex:1"><input class="input" id="audit-search" placeholder="${t("search")}"></div><select class="select" id="audit-status" style="width:auto"><option value="">${t("status")}: ${t("all")}</option><option value="created">${formatAuditStatus("created")}</option><option value="approved">${formatAuditStatus("approved")}</option><option value="rejected">${formatAuditStatus("rejected")}</option><option value="edited">${formatAuditStatus("edited")}</option><option value="corrected">${formatAuditStatus("corrected")}</option></select></div><div id="audit-root"><div class="skeleton" style="height:420px"></div></div>`;
  try{
    const data=await api("/audit?limit=300");
    const draw=()=>{
      const q=document.getElementById("audit-search").value.trim().toLowerCase();
      const status=document.getElementById("audit-status").value;
      const rows=data.filter(x=>{
        const details=detailText(x);
        const haystack=`${x.actor} ${x.action} ${x.case_id} ${x.order_number||""} ${details}`.toLowerCase();
        return (!status||x.status===status)&&(!q||haystack.includes(q));
      });
      document.getElementById("audit-root").innerHTML=rows.length?`<div class="table-wrap"><table><thead><tr><th>${t("timestamp")}</th><th>${t("actor")}</th><th>${t("action")}</th><th>${t("caseLabel")}</th><th>${t("order")}</th><th>${t("status")}</th><th>${t("details")}</th></tr></thead><tbody>${rows.map(x=>`<tr><td>${formatDate(x.timestamp)}</td><td>${escapeHtml(x.actor)}</td><td>${escapeHtml(formatAuditAction(x.action))}</td><td class="mono"><a href="#/cases/${x.case_id}" style="color:var(--primary)">${escapeHtml(x.case_id.slice(0,8))}</a></td><td class="mono">${escapeHtml(x.order_number||"—")}</td><td>${badge(formatAuditStatus(x.status),x.status==="approved"||x.status==="created"?"success":x.status==="rejected"?"danger":"neutral")}</td><td><span class="small muted">${escapeHtml(detailText(x))}</span></td></tr>`).join("")}</tbody></table></div>`:emptyState(t("noAudit"),"","audit");
    };
    document.getElementById("audit-search").oninput=draw;
    document.getElementById("audit-status").onchange=draw;
    draw();
  }catch(e){document.getElementById("audit-root").innerHTML=`<div class="notice notice-warning">${escapeHtml(e.message)}</div>`;}
}
