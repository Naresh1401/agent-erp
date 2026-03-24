import axios from "axios";

const API_BASE = process.env.REACT_APP_API_URL || "";

const api = axios.create({
  baseURL: `${API_BASE}/api/v1`,
  headers: { "Content-Type": "application/json" },
});

// ── Dashboard ──────────────────────────────────────────────
export const fetchDashboard = () => api.get("/analytics/dashboard");

// ── Orders ─────────────────────────────────────────────────
export const fetchOrders = (params?: Record<string, string>) =>
  api.get("/orders/", { params });

export const fetchOrderStats = () => api.get("/orders/stats/summary");

export const createOrder = (data: unknown) => api.post("/orders/", data);

// ── Inventory ──────────────────────────────────────────────
export const fetchProducts = (params?: Record<string, string>) =>
  api.get("/inventory/products", { params });

export const fetchAlerts = () => api.get("/inventory/alerts");

export const adjustInventory = (
  productId: string,
  quantityChange: number,
  reason: string
) =>
  api.post(
    `/inventory/products/${productId}/adjust?quantity_change=${quantityChange}&reason=${encodeURIComponent(reason)}`
  );

// ── Agents ─────────────────────────────────────────────────
export const dispatchAgent = (agentType: string, inputData: unknown) =>
  api.post("/agents/dispatch", {
    agent_type: agentType,
    input_data: inputData,
  });

export const fetchTasks = (params?: Record<string, string>) =>
  api.get("/agents/tasks", { params });

export const fetchTaskLogs = (taskId: string) =>
  api.get(`/agents/tasks/${taskId}/logs`);

// ── Documents ──────────────────────────────────────────────
export const uploadDocument = (filename: string, rawText: string) =>
  api.post("/documents/upload", { filename, raw_text: rawText });

export const searchDocuments = (query: string, limit = 10) =>
  api.post("/documents/search", { query, limit });

// ── Data Management ────────────────────────────────────────
export const seedStep = (step: string) => api.post(`/seed/${step}`);
export const getSeedSteps = () => api.get("/seed/steps");
export const resetData = () => api.post("/reset");

export default api;
