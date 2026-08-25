import { api } from "../api.js";
import { t, formatIntent, formatAuditAction } from "../i18n.js";
import { badge, emptyState, escapeHtml, formatDuration, icon, pageHead, statusBadge } from "../ui.js";

const modeLabel=value=>value==="live"?t("live"):value==="mock"?t("mock"):value;

export async function renderOverview(container){
  container.innerHTML = `${pageHead(t("overview"),"")}<div class="card-grid" id="metrics"><div class="skeleton" style="height:116px"></div><div class="skeleton" style="height:116px"></div><div class="skeleton" style="height:116px"></div><div class="skeleton" style="height:116px"></div></div><div class="two-col" style="margin-top:16px"><div class="stack"><section class="panel"><div class="panel-head"><h2 class="section-title">${t("attentionRequired")}</h2><a class="btn btn-ghost" href="#/attention">${t("reviewCase")} ${icon("arrow",15)}</a></div><div class="panel-body" id="attention-preview"></div></section><section class="panel"><div class="panel-head"><h2 class="section-title">${t("recentActivity")}</h2><a class="btn btn-ghost" href="#/audit">${t("audit")}</a></div><div class="panel-body" id="activity-preview"></div></section></div><section class="panel"><div class="panel-head"><h2 class="section-title">${t("systemHealth")}</h2></div><div class="panel-body" id="health-preview"></div></section></div>`;
  try{
    const [stats, signals, attention, integrations, audit] = await Promise.all([
      api("/cases/stats"), api("/signals/overview"), api("/attention?limit=3"), api("/integrations/status"), api("/audit?limit=6")
    ]);
    const m = signals.metrics || {};
    document.getElementById("metrics").innerHTML = [
      [t("needsAttention"),(stats.by_status?.awaiting_approval||0)+(stats.by_status?.decision_ready||0),t("reviewRequired")],
      [t("acceptance"),`${(m.recommendation_acceptance_rate||0).toFixed(1)}%`,`${signals.sample_size||0} ${t("sampleSize").toLowerCase()}`],
      [t("avgReview"),formatDuration(m.average_review_seconds||0),t("reviewFirst")],
      [t("draftsCreated"),stats.by_status?.gmail_draft_created||0,t("noAutoSend")]
    ].map(([label,value,foot])=>`<div class="metric"><div class="metric-label">${escapeHtml(label)}</div><div class="metric-value">${escapeHtml(value)}</div><div class="metric-foot">${escapeHtml(foot)}</div></div>`).join("");

    const att = document.getElementById("attention-preview");
    att.innerHTML = attention.length ? `<div class="attention-list">${attention.map(item=>`<div class="attention-item"><div class="attention-main"><div class="attention-icon">${icon("attention",17)}</div><div><div class="attention-title">${escapeHtml(item.subject)}</div><div class="attention-meta"><span>${formatIntent(item.intent)}</span><span class="mono">${escapeHtml(item.order_number||"—")}</span><span>${Math.round(item.confidence*100)}%</span>${statusBadge(item.status)}</div></div></div><a class="btn btn-secondary" href="#/cases/${item.case_id}">${t("reviewCase")}</a></div>`).join("")}</div>` : emptyState(t("allCaughtUp"),t("noAttention"),"check");

    const health = document.getElementById("health-preview");
    const rows = [
      ["API",true,t("healthy")],
      ["Gmail", integrations.gmail.connected || integrations.gmail.mode==="mock", modeLabel(integrations.gmail.mode)],
      ["Shopify", integrations.shopify.connected || integrations.shopify.mode==="mock", modeLabel(integrations.shopify.mode)],
      [t("database"), integrations.database.configured, integrations.database.kind],
      [t("backgroundJobs"), true, integrations.jobs.mode],
      [t("aiProvider"), true, integrations.ai.provider],
      [t("policyEngineName"), true, integrations.policy.version]
    ];
    health.innerHTML = rows.map(([name,ok,value])=>`<div class="status-line"><div class="status-name"><span style="color:${ok?'var(--success)':'var(--danger)'}">${icon(ok?'check':'x',16)}</span>${escapeHtml(name)}</div><div class="status-value">${badge(String(value),ok?'success':'danger')}</div></div>`).join("");

    const activity = document.getElementById("activity-preview");
    activity.innerHTML = audit.length ? audit.map(event=>`<div class="status-line"><div><div class="status-name">${icon(event.status==="approved"||event.status==="created"?'check':'audit',16)}<span>${escapeHtml(formatAuditAction(event.action))}</span></div><div class="small muted" style="margin-top:4px">${escapeHtml(event.order_number||event.case_id)}</div></div><div class="status-value">${escapeHtml(event.actor)}</div></div>`).join("") : emptyState(t("noAudit"),"","audit");
  }catch(error){ container.insertAdjacentHTML("beforeend",`<div class="notice notice-warning" style="margin-top:16px">${escapeHtml(error.message)}</div>`); }
}
