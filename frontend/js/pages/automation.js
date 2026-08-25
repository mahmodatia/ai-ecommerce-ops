import { api } from "../api.js";
import { t, formatIntent, formatTraceLabel, formatTraceValue } from "../i18n.js";
import { badge, emptyState, escapeHtml, formatDate, formatMs, icon, pageHead, toast } from "../ui.js";

let lastResult=null;

export async function renderAutomation(container){
  container.innerHTML=`${pageHead(t("automation"),"")}<div class="notice notice-success" style="margin-bottom:16px">${icon("shield",17)} <div><strong>${t("simulationMode")}</strong><div class="small" style="margin-top:2px">${t("simulationSafety")}</div></div></div><div class="sim-grid"><div class="stack"><section class="panel"><div class="panel-head"><h2 class="section-title">${t("simulationContext")}</h2><button class="btn btn-primary" id="run-sim">${icon("automation",16)} ${t("runSimulation")}</button></div><div class="panel-body"><div class="form-grid"><label class="form-group"><span class="form-label">${t("scenario")}</span><select id="sim-scenario" class="select"><option value="where_is_my_order">${formatIntent("where_is_my_order")}</option><option value="return_refund">${formatIntent("return_refund")}</option><option value="missing_wrong_item">${formatIntent("missing_wrong_item")}</option><option value="cancel_modify">${formatIntent("cancel_modify")}</option></select></label><label class="form-group"><span class="form-label">${t("provider")}</span><select id="sim-provider" class="select"><option value="current">${t("currentProvider")}</option><option value="rules">${t("rulesBaseline")}</option><option value="openai">${t("openaiNeedsKey")}</option></select></label><label class="form-group"><span class="form-label">${t("orderTarget")}</span><input id="sim-order" class="input mono" placeholder="#8291"></label><div class="form-group"><span class="form-label">${t("policyVersion")}</span><div id="sim-policy-version" class="input" style="color:var(--muted)">${t("loading")}</div></div></div><label class="form-group" style="margin-top:14px"><span class="form-label">${t("customerMessage")}</span><textarea id="sim-message" class="textarea" placeholder="${t("customerMessagePlaceholder")}"></textarea></label></div></section><section class="panel"><div class="panel-head"><h2 class="section-title">${t("decisionTrace")}</h2></div><div class="panel-body" id="sim-trace">${emptyState(t("noSimulations"),t("simulationSafety"),"automation")}</div></section></div><aside class="simulation-result"><section class="panel"><div class="panel-head"><h2 class="section-title">${t("processingPerformance")}</h2></div><div class="panel-body" id="sim-performance">${emptyState(t("noSimulations"),"","clock")}</div></section><section class="panel"><div class="panel-head"><h2 class="section-title">${t("generatedDraft")}</h2></div><div class="panel-body"><div id="sim-draft" class="draft-preview muted">${t("simulationSafety")}</div></div></section></aside></div><section class="panel" style="margin-top:16px"><div class="panel-head"><h2 class="section-title">${t("recentSimulations")}</h2></div><div class="panel-body" id="recent-sims"><div class="skeleton" style="height:160px"></div></div></section>`;
  document.getElementById("run-sim").onclick=run;
  try{
    const [orders, integrations]=await Promise.all([
      api("/shopify/orders?limit=1").catch(()=>[]),
      api("/integrations/status").catch(()=>null),
    ]);
    if(orders?.length && !document.getElementById("sim-order").value){
      document.getElementById("sim-order").value=orders[0].name||orders[0].order_number||"";
    }
    const version=integrations?.policy?.version;
    document.getElementById("sim-policy-version").textContent=version?`v${version}`:t("currentPolicySet");
  }catch{}
  await loadRecent();
}

async function run(){
  const btn=document.getElementById("run-sim");
  btn.disabled=true;
  try{
    lastResult=await api("/simulations",{
      method:"POST",
      body:JSON.stringify({
        scenario:document.getElementById("sim-scenario").value,
        provider:document.getElementById("sim-provider").value,
        order_number:document.getElementById("sim-order").value.trim()||null,
        message:document.getElementById("sim-message").value.trim()||null,
      })
    });
    drawResult(lastResult);
    toast(`${t("simulationMode")} · ${statusText(lastResult.status)}`,"success");
    await loadRecent();
  }catch(e){toast(e.message,"error");}
  finally{btn.disabled=false;}
}

function statusText(status){
  if(status==="pass")return t("pass");
  if(status==="needs_review")return t("needsReview");
  return t("failed");
}

function drawResult(data){
  const r=data.result;
  const timings=r.timings_ms||{};
  const total=Math.max(timings.total||data.duration_ms||1,1);
  document.getElementById("sim-performance").innerHTML=`<div style="font-size:26px;font-weight:740;letter-spacing:-.03em">${formatMs(total)}</div><div class="small muted" style="margin:3px 0 14px">${t("totalTime")}</div>${[["understanding",t("understanding")],["shopify",t("shopifyMatch")],["policy",t("policyEngine")],["decision",t("decision")],["drafting",t("drafting")]].map(([key,label])=>{const v=timings[key]||0;return `<div class="progress-row"><span class="progress-label">${label}</span><div class="progress-track"><div class="progress-fill" style="width:${Math.max(3,Math.min(100,v/total*100))}%"></div></div><span class="progress-value">${formatMs(v)}</span></div>`}).join("")}<div style="margin-top:14px">${badge(statusText(data.status),data.status==="pass"?"success":data.status==="needs_review"?"warning":"danger")}</div>`;
  document.getElementById("sim-trace").innerHTML=`<div class="trace">${(r.trace||[]).map(step=>`<div class="trace-step" data-source="${escapeHtml(step.source||"rules")}"><span class="trace-node"></span><div class="trace-label">${escapeHtml(formatTraceLabel(step.key,step.label))}</div><div class="trace-value">${escapeHtml(formatTraceValue(step.value))}</div><div class="trace-detail">${escapeHtml(step.detail||"")}</div></div>`).join("")}</div>`;
  document.getElementById("sim-draft").classList.remove("muted");
  document.getElementById("sim-draft").textContent=r.draft_reply||"—";
}

async function loadRecent(){
  try{
    const rows=await api("/simulations?limit=10");
    document.getElementById("recent-sims").innerHTML=rows.length?`<div class="table-wrap"><table><thead><tr><th>ID</th><th>${t("scenario")}</th><th>${t("provider")}</th><th>${t("order")}</th><th>${t("totalTime")}</th><th>${t("status")}</th><th>${t("created")}</th></tr></thead><tbody>${rows.map(x=>`<tr><td class="mono">${escapeHtml(x.id.slice(0,8))}</td><td>${formatIntent(x.scenario)}</td><td>${escapeHtml(x.provider)}</td><td class="mono">${escapeHtml(x.order_number||"—")}</td><td>${formatMs(x.duration_ms)}</td><td>${badge(statusText(x.status),x.status==="pass"?"success":x.status==="needs_review"?"warning":"danger")}</td><td>${formatDate(x.created_at)}</td></tr>`).join("")}</tbody></table></div>`:emptyState(t("noSimulations"),"","automation");
  }catch(e){document.getElementById("recent-sims").innerHTML=`<div class="notice notice-warning">${escapeHtml(e.message)}</div>`;}
}
