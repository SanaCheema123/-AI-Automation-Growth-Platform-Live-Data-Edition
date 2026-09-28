const API_URL = (import.meta.env.VITE_API_URL || "/api/v1").replace(/\/$/, "");
const TOKEN_KEY = "aigrowth.token";

export class ApiError extends Error {
  constructor(message, status = 0, data = null, requestId = null) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.data = data;
    this.requestId = requestId;
  }
}

export function getToken(){ return localStorage.getItem(TOKEN_KEY); }
export function setToken(token){ token ? localStorage.setItem(TOKEN_KEY, token) : localStorage.removeItem(TOKEN_KEY); }

function requestId(){ return globalThis.crypto?.randomUUID?.() || `web-${Date.now()}-${Math.random().toString(16).slice(2)}`; }
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));

async function request(path, options = {}) {
  const {timeout = 15000, retries = options.method && options.method !== "GET" ? 0 : 1, ...fetchOptions} = options;
  let lastError;
  for (let attempt = 0; attempt <= retries; attempt += 1) {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeout);
    const headers = {"Content-Type":"application/json", "X-Request-ID":requestId(), ...(fetchOptions.headers || {})};
    const token = getToken();
    if (token) headers.Authorization = `Bearer ${token}`;
    try {
      const response = await fetch(`${API_URL}${path}`, {...fetchOptions, headers, signal: controller.signal});
      let data = null;
      const text = await response.text();
      if (text) { try { data = JSON.parse(text); } catch { data = text; } }
      if (!response.ok) {
        if (response.status === 401) {
          setToken(null);
          globalThis.dispatchEvent?.(new Event("aigrowth:unauthorized"));
        }
        const detail = typeof data === "object" && data?.detail
          ? (Array.isArray(data.detail) ? data.detail.map(x => x.msg || x).join(", ") : data.detail)
          : `Request failed (${response.status})`;
        const error = new ApiError(String(detail), response.status, data, response.headers.get("X-Request-ID"));
        if (attempt < retries && response.status >= 500) { lastError = error; await sleep(250 * (attempt + 1)); continue; }
        throw error;
      }
      return data;
    } catch (error) {
      const normalized = error.name === "AbortError"
        ? new ApiError("Request timed out. Please retry.", 0)
        : error instanceof ApiError ? error : new ApiError("Unable to reach the backend service.", 0);
      lastError = normalized;
      if (attempt < retries && normalized.status !== 401) { await sleep(250 * (attempt + 1)); continue; }
      throw normalized;
    } finally { clearTimeout(timer); }
  }
  throw lastError || new ApiError("Request failed", 0);
}

export const api = {
  get:(path)=>request(path),
  post:(path,body)=>request(path,{method:"POST",body:JSON.stringify(body ?? {})}),
  patch:(path,body)=>request(path,{method:"PATCH",body:JSON.stringify(body ?? {})}),
  del:(path)=>request(path,{method:"DELETE"}),
  auth:{
    login:(body)=>request("/auth/login",{method:"POST",body:JSON.stringify(body)}),
    register:(body)=>request("/auth/register",{method:"POST",body:JSON.stringify(body)}),
    me:()=>request("/auth/me")
  },
  leads:{
    list:(query="")=>request(`/leads${query}`),
    create:(body)=>request("/leads",{method:"POST",body:JSON.stringify(body)}),
    get:(id)=>request(`/leads/${id}`),
    update:(id,body)=>request(`/leads/${id}`,{method:"PATCH",body:JSON.stringify(body)}),
    qualify:(id)=>request(`/leads/${id}/qualify`,{method:"POST",body:"{}",timeout:45000})
  },
  events:{list:()=>request("/events"),create:(body)=>request("/events",{method:"POST",body:JSON.stringify(body)})},
  workflows:{
    list:()=>request("/workflows"),
    create:(body)=>request("/workflows",{method:"POST",body:JSON.stringify(body)}),
    update:(id,body)=>request(`/workflows/${id}`,{method:"PATCH",body:JSON.stringify(body)}),
    activate:(id,on)=>request(`/workflows/${id}/${on?"activate":"deactivate"}`,{method:"POST",body:"{}"}),
    run:(id,body)=>request(`/workflows/${id}/run`,{method:"POST",body:JSON.stringify(body)}),
    runs:()=>request("/workflows/runs"),
    runDetail:(id)=>request(`/workflows/runs/${id}`),
    retry:(id)=>request(`/workflows/runs/${id}/retry`,{method:"POST",body:"{}"})
  },
  approvals:{
    list:(status="pending")=>request(`/approvals?status=${encodeURIComponent(status)}`),
    approve:(id,body={execute:true})=>request(`/approvals/${id}/approve`,{method:"POST",body:JSON.stringify(body)}),
    reject:(id,body={})=>request(`/approvals/${id}/reject`,{method:"POST",body:JSON.stringify(body)}),
    edit:(id,value)=>request(`/approvals/${id}`,{method:"PATCH",body:JSON.stringify({edited_value:value})}),
    create:(body)=>request("/approvals/manual",{method:"POST",body:JSON.stringify(body)})
  },
  ai:{
    qualify:(body)=>request("/ai/lead-qualification",{method:"POST",body:JSON.stringify(body),timeout:45000}),
    outreach:(body)=>request("/ai/outreach",{method:"POST",body:JSON.stringify(body),timeout:45000}),
    meeting:(body)=>request("/ai/meeting-analysis",{method:"POST",body:JSON.stringify(body),timeout:45000}),
    content:(body)=>request("/ai/content",{method:"POST",body:JSON.stringify(body),timeout:45000}),
    copilot:(body)=>request("/ai/copilot",{method:"POST",body:JSON.stringify(body),timeout:45000})
  },
  analytics:(days=30)=>request(`/analytics/overview?days=${days}`),
  integrations:()=>request("/system/integrations"),
  runtime:()=>request("/system/runtime"),
  audit:()=>request("/audit-logs")
};
