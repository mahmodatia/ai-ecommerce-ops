import { api } from "../api.js";
import { t, formatFinancial, formatFulfillment } from "../i18n.js";
import { badge, emptyState, escapeHtml, formatDate, pageHead } from "../ui.js";

export async function renderOrders(container){
  container.innerHTML=`${pageHead(t("ordersTitle"),t("ordersSub"),badge(t("readOnly"),"success"))}<div class="toolbar" style="margin-bottom:14px"><div class="search" style="max-width:420px;flex:1"><input class="input" id="order-search" placeholder="${t("search")}"></div><select class="select" id="order-fulfillment" style="width:auto"><option value="">${t("fulfillment")}: ${t("all")}</option></select></div><div id="orders-root"><div class="skeleton" style="height:420px"></div></div>`;
  try{
    const [orders,status]=await Promise.all([api("/shopify/orders?limit=50"),api("/shopify/status")]);
    const fulfillmentValues=[...new Set(orders.map(o=>o.displayFulfillmentStatus||o.fulfillment_status).filter(Boolean))].sort();
    document.getElementById("order-fulfillment").insertAdjacentHTML("beforeend",fulfillmentValues.map(v=>`<option value="${escapeHtml(v)}">${escapeHtml(formatFulfillment(v))}</option>`).join(""));
    const draw=()=>{
      const q=document.getElementById("order-search").value.trim().toLowerCase();
      const fulfillment=document.getElementById("order-fulfillment").value;
      const rows=orders.filter(o=>{
        const current=o.displayFulfillmentStatus||o.fulfillment_status||"";
        const haystack=`${o.name||o.order_number||""} ${o.customer?.displayName||o.customer?.name||""} ${o.customer?.email||""}`.toLowerCase();
        return (!q||haystack.includes(q))&&(!fulfillment||current===fulfillment);
      });
      document.getElementById("orders-root").innerHTML=rows.length?`<div class="table-wrap"><table><thead><tr><th>${t("orderNumber")}</th><th>${t("customer")}</th><th>${t("payment")}</th><th>${t("fulfillment")}</th><th>${t("total")}</th><th>${t("tracking")}</th><th>${t("created")}</th><th>${t("source")}</th></tr></thead><tbody>${rows.map(o=>`<tr><td class="mono"><strong>${escapeHtml(o.name||o.order_number||"—")}</strong></td><td>${escapeHtml(o.customer?.displayName||o.customer?.name||"—")}<div class="small muted ltr">${escapeHtml(o.customer?.email||"")}</div></td><td>${escapeHtml(formatFinancial(o.displayFinancialStatus||o.financial_status||"—"))}</td><td>${escapeHtml(formatFulfillment(o.displayFulfillmentStatus||o.fulfillment_status||"—"))}</td><td>${o.totalAmount!=null?`${escapeHtml(o.totalAmount)} ${escapeHtml(o.currency||"")}`:"—"}</td><td class="mono">${escapeHtml(o.trackingNumber||"—")}</td><td>${formatDate(o.createdAt||o.placed_at)}</td><td>${badge(status.mode==="live"?t("liveShopify"):t("demoData"),status.mode==="live"?"success":"primary")}</td></tr>`).join("")}</tbody></table></div>`:emptyState(t("noOrders"),"","orders");
    };
    document.getElementById("order-search").oninput=draw;
    document.getElementById("order-fulfillment").onchange=draw;
    draw();
  }catch(e){document.getElementById("orders-root").innerHTML=`<div class="notice notice-warning">${escapeHtml(e.message)}</div>`;}
}
