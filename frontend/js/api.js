const BASE = window.location.port === "5500" ? "http://127.0.0.1:8000/api/v1" : "/api/v1";

export function getToken(){ return sessionStorage.getItem("aiops_token") || ""; }
export function setToken(token){ token ? sessionStorage.setItem("aiops_token", token) : sessionStorage.removeItem("aiops_token"); }

export async function api(path, options={}){
  const headers = new Headers(options.headers || {});
  const token = getToken();
  if(token) headers.set("Authorization", `Bearer ${token}`);
  if(options.body && !(options.body instanceof FormData) && !headers.has("Content-Type")) headers.set("Content-Type","application/json");
  const response = await fetch(`${BASE}${path}`, {...options, headers});
  let data = null;
  const contentType = response.headers.get("content-type") || "";
  if(contentType.includes("application/json")) data = await response.json();
  if(!response.ok){
    const error = new Error(data?.detail || `Request failed (${response.status})`);
    error.status = response.status;
    throw error;
  }
  return data;
}

export { BASE };
