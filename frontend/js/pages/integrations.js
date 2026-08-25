import { api } from "../api.js";
import { t } from "../i18n.js";
import { badge, escapeHtml, icon, pageHead } from "../ui.js";

export async function renderIntegrations(container){
  container.innerHTML=`${pageHead(t("integrationsTitle"),t("integrationsSub"))}<div id="integration-root"><div class="skeleton" style="height:420px"></div></div>`;
  try{
    const d=await api("/integrations/status");
    const cards=[
      {
        name:"Gmail",icon:"mail",tone:"danger",
        status:d.gmail.connected?t("connected"):d.gmail.mode==="mock"?t("mock"):t("configured"),
        caps:[t("readInbox"),t("createDrafts"),t("autoSendDisabled"),d.gmail.manual_send_enabled?t("manualSendEnabled"):t("manualSendDisabled")]
      },
      {
        name:"Shopify",icon:"store",tone:"success",
        status:d.shopify.connected?t("connected"):d.shopify.mode==="mock"?t("mock"):t("configured"),
        caps:[t("readOrders"),t("readFacts"),t("mutationsDisabled")]
      },
      {
        name:t("aiProvider"),icon:"automation",tone:"primary",status:d.ai.provider,
        caps:[t("intentClassification"),t("structuredUnderstanding"),d.ai.fallback_to_rules?t("rulesFallbackEnabled"):t("rulesFallbackDisabled")]
      },
      {
        name:t("database"),icon:"cases",tone:"neutral",status:d.database.kind,
        caps:[t("casePersistence"),t("auditRecords"),t("simulationHistory")]
      },
      {
        name:t("backgroundJobs"),icon:"clock",tone:"neutral",status:d.jobs.mode,
        caps:[`${t("modeLabel")}: ${d.jobs.mode}`,`${t("autoPoll")}: ${d.jobs.auto_poll?t("on"):t("off")}`]
      },
      {
        name:t("policyEngineName"),icon:"policies",tone:"neutral",status:`v${d.policy.version}`,
        caps:[t("deterministicRules"),t("policyConstraints"),t("noAutomaticMutations")]
      }
    ];
    document.getElementById("integration-root").innerHTML=`<div class="integration-grid">${cards.map(c=>`<section class="panel integration-card"><div class="integration-head"><div style="display:flex;gap:10px"><div class="empty-icon" style="margin:0;width:38px;height:38px">${icon(c.icon,18)}</div><div><div class="integration-name">${escapeHtml(c.name)}</div><div style="margin-top:6px">${badge(c.status,c.status===t("connected")?"success":c.tone==="primary"?"primary":"neutral")}</div></div></div></div><div class="cap-list">${c.caps.map(cap=>{const warning=cap===t("autoSendDisabled")||cap===t("manualSendDisabled")||cap===t("mutationsDisabled")||cap===t("noAutomaticMutations");return `<div class="cap"><span style="color:${warning?'var(--warning)':'var(--success)'}">${icon(warning?'attention':'check',15)}</span>${escapeHtml(cap)}</div>`}).join("")}</div></section>`).join("")}</div><div class="notice notice-info" style="margin-top:16px">${icon("shield",17)} <div><strong>${t("safetyBoundary")}</strong><div class="small" style="margin-top:3px">${t("safetyBoundaryCopy")}</div></div></div>`;
  }catch(e){document.getElementById("integration-root").innerHTML=`<div class="notice notice-warning">${escapeHtml(e.message)}</div>`;}
}
