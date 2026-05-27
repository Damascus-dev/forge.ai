const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function getApiKey() {
  if (typeof window === "undefined") return "";
  return localStorage.getItem("forge_api_key") || "";
}

async function request(path, options = {}) {
  const apiKey = getApiKey();
  const headers = { "Content-Type": "application/json", ...options.headers };
  if (apiKey) {
    headers["X-API-Key"] = apiKey;
  }
  const res = await fetch(`${API}${path}`, {
    headers,
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || res.statusText);
  }
  return res.json();
}

export async function listExperiments() {
  return request("/api/v1/experiments/");
}

export async function getExperiment(id) {
  return request(`/api/v1/experiments/${id}`);
}

export async function createExperiment(name, nodeCount = 2) {
  return request("/api/v1/experiments/", {
    method: "POST",
    body: JSON.stringify({ name, node_count: nodeCount }),
  });
}

export async function startExperiment(id) {
  return request(`/api/v1/experiments/${id}/start`, { method: "POST" });
}

export async function terminateExperiment(id) {
  return request(`/api/v1/experiments/${id}/terminate`, { method: "POST" });
}

export async function listNodes(experimentId) {
  return request(`/api/v1/nodes/${experimentId}`);
}

export async function getEvents(experimentId, limit = 50) {
  return request(`/api/v1/events/${experimentId}?limit=${limit}`);
}

export async function getTimeline(experimentId) {
  return request(`/api/v1/replay/${experimentId}/timeline`);
}

export async function startReplay(experimentId) {
  return request(`/api/v1/replay/${experimentId}/start`, { method: "POST" });
}

export async function injectFault(experimentId, targetNode, faultType, params = {}) {
  return request(`/api/v1/nodes/${experimentId}/inject?fault_type=${faultType}&target_node=${targetNode}`, {
    method: "POST",
    body: JSON.stringify(params),
  });
}

export async function startAgent(experimentId, model = "ollama/qwen2.5:0.5b") {
  return request(`/api/v1/experiments/${experimentId}/agent/start`, {
    method: "POST",
    body: JSON.stringify({ model }),
  });
}

export async function runAgentStep(experimentId, agentId) {
  return request(`/api/v1/experiments/${experimentId}/agent/${agentId}/step`, {
    method: "POST",
  });
}

export async function getAgentLogs(experimentId, agentId) {
  return request(`/api/v1/experiments/${experimentId}/agent/${agentId}/logs`);
}
