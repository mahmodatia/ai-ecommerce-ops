import { api } from "../api.js";
import { t, formatIntent, formatSource } from "../i18n.js";
import { badge, emptyState, escapeHtml, formatDuration, pageHead, statusBadge } from "../ui.js";

let filter="all";
export async function renderAttention(container){
  container.innerHTML = `${pageHead(t("attention"),t("noAttention"))}<div class="toolbar" style="margin-bottom:14px"><div class="toolbar-group" id="attention-filters"><button class="filter-chip active" data-filter="all">${t("all")}</button><button class="filter-chip" data-filter="awaiting_approval">${t("awaitingApproval")}</button><button class="filter-chip" data-filter="manual_review">${t("manualReview")}</button><button class="filter-chip" data-filter="low_confidence">${t("lowConfidence")}</button></div></div><div id="attention-table"></div>`;
  const data = await api("/attention?limit=200");
  const draw=()=>{
    document.querySelectorAll("#attention-filters .filter-chip").forEach(x=>x.classList.toggle("active",x.dataset.filter===filter));
    const rows=data.filter(item=>filter==="all"||item.reasons.includes(filter)||item.status===filter);
    document.getElementById("attention-table").innerHTML = rows.length ? `<div class="table-wrap"><table><thead><tr><th>${t("subject")}</th><th>${t("customer")}</th><th>${t("intent")}</th><th>${t("order")}</th><th>${t("confidence")}</th><th>${t("waitTime")}</th><th>${t("source")}</th><th>${t("action")}</th></tr></thead><tbody>${rows.map(item=>`<tr><td><strong>${escapeHtml(item.subject)}</strong><div class="small muted" style="margin-top:4px">${statusBadge(item.status)}</div></td><td>${escapeHtml(item.customer)}</td><td>${formatIntent(item.intent)}</td><td class="mono">${escapeHtml(item.order_number||"—")}</td><td>${badge(`${Math.round(item.confidence*100)}%`,item.confidence<.5?'danger':item.confidence<.75?'warning':'success')}</td><td>${formatDuration(item.wait_seconds)}</td><td>${badge(formatSource(item.source),item.source==='live_gmail'?'success':'neutral')}</td><td><a class="btn btn-secondary" href="#/cases/${item.case_id}">${t("reviewCase")}</a></td></tr>`).join("")}</tbody></table></div>` : emptyState(t("allCaughtUp"),t("noAttention"),"check");
  };
  document.getElementById("attention-filters").onclick=e=>{const b=e.target.closest("[data-filter]"); if(!b)return; filter=b.dataset.filter; draw();}; draw();
}
