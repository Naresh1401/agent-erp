import React, { useEffect, useState } from "react";
import { fetchDashboard } from "../services/api";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
} from "chart.js";
import { Bar, Doughnut } from "react-chartjs-2";

ChartJS.register(CategoryScale, LinearScale, BarElement, ArcElement, Title, Tooltip, Legend);

interface DashboardData {
  total_orders: number;
  total_products: number;
  total_customers: number;
  total_agent_tasks: number;
  active_anomalies: number;
  orders_by_status: Record<string, number>;
  recent_agent_tasks: Array<{
    id: string;
    agent_type: string;
    status: string;
    created_at: string;
    tokens_used: number;
    cost_usd: number;
  }>;
  top_anomalies: Array<{
    id: string;
    type: string;
    severity: string;
    description: string;
  }>;
}

const StatCard: React.FC<{ label: string; value: number | string; accent: string }> = ({
  label,
  value,
  accent,
}) => (
  <div className="bg-slate-800 rounded-xl p-6 border border-slate-700">
    <p className="text-sm text-slate-400">{label}</p>
    <p className={`text-3xl font-bold mt-2 ${accent}`}>{value}</p>
  </div>
);

export default function Dashboard() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const loadDashboard = (isRefresh = false) => {
    if (isRefresh) setRefreshing(true);
    else setLoading(true);

    fetchDashboard()
      .then((res) => setData(res.data))
      .catch(() => {})
      .finally(() => {
        setLoading(false);
        setRefreshing(false);
      });
  };

  useEffect(() => {
    loadDashboard();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-400" />
      </div>
    );
  }

  if (!data) return null;

  const orderStatusData = {
    labels: Object.keys(data.orders_by_status),
    datasets: [
      {
        data: Object.values(data.orders_by_status),
        backgroundColor: [
          "#6366f1", "#8b5cf6", "#10b981", "#f59e0b",
          "#3b82f6", "#06b6d4", "#ef4444", "#f97316",
        ],
      },
    ],
  };

  const agentTypeCount: Record<string, number> = {};
  data.recent_agent_tasks.forEach((t) => {
    agentTypeCount[t.agent_type] = (agentTypeCount[t.agent_type] || 0) + 1;
  });

  const agentBarData = {
    labels: Object.keys(agentTypeCount),
    datasets: [
      {
        label: "Tasks",
        data: Object.values(agentTypeCount),
        backgroundColor: "#10b981",
        borderRadius: 6,
      },
    ],
  };

  const severityColor: Record<string, string> = {
    critical: "bg-red-500",
    high: "bg-orange-500",
    medium: "bg-yellow-500",
    low: "bg-blue-500",
  };

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold">Dashboard</h2>
        <button
          onClick={() => loadDashboard(true)}
          disabled={refreshing}
          className="flex items-center gap-2 px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
        >
          <svg
            className={`w-4 h-4 ${refreshing ? "animate-spin" : ""}`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
            />
          </svg>
          {refreshing ? "Refreshing…" : "Refresh"}
        </button>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-5 gap-4 mb-8">
        <StatCard label="Total Orders" value={data.total_orders} accent="text-blue-400" />
        <StatCard label="Products" value={data.total_products} accent="text-emerald-400" />
        <StatCard label="Customers" value={data.total_customers} accent="text-purple-400" />
        <StatCard label="Agent Tasks" value={data.total_agent_tasks} accent="text-cyan-400" />
        <StatCard label="Active Anomalies" value={data.active_anomalies} accent="text-red-400" />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-2 gap-6 mb-8">
        <div className="bg-slate-800 rounded-xl p-6 border border-slate-700">
          <h3 className="text-lg font-semibold mb-4">Orders by Status</h3>
          <div className="h-64 flex items-center justify-center">
            <Doughnut data={orderStatusData} options={{ maintainAspectRatio: false, plugins: { legend: { labels: { color: "#94a3b8" } } } }} />
          </div>
        </div>
        <div className="bg-slate-800 rounded-xl p-6 border border-slate-700">
          <h3 className="text-lg font-semibold mb-4">Agent Activity</h3>
          <div className="h-64">
            <Bar
              data={agentBarData}
              options={{
                maintainAspectRatio: false,
                scales: { y: { ticks: { color: "#94a3b8" } }, x: { ticks: { color: "#94a3b8" } } },
                plugins: { legend: { display: false } },
              }}
            />
          </div>
        </div>
      </div>

      {/* Bottom Row: Recent Tasks + Anomalies */}
      <div className="grid grid-cols-2 gap-6">
        <div className="bg-slate-800 rounded-xl p-6 border border-slate-700">
          <h3 className="text-lg font-semibold mb-4">Recent Agent Tasks</h3>
          <div className="space-y-3">
            {data.recent_agent_tasks.map((task) => (
              <div key={task.id} className="flex items-center justify-between p-3 bg-slate-700/50 rounded-lg">
                <div>
                  <span className="font-medium text-sm">{task.agent_type.replace(/_/g, " ")}</span>
                  <span
                    className={`ml-2 px-2 py-0.5 rounded-full text-xs ${
                      task.status === "completed" ? "bg-emerald-500/20 text-emerald-400" : "bg-red-500/20 text-red-400"
                    }`}
                  >
                    {task.status}
                  </span>
                </div>
                <div className="text-xs text-slate-400">
                  {task.tokens_used} tokens &middot; ${task.cost_usd.toFixed(3)}
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-slate-800 rounded-xl p-6 border border-slate-700">
          <h3 className="text-lg font-semibold mb-4">Active Anomalies</h3>
          <div className="space-y-3">
            {data.top_anomalies.map((anomaly) => (
              <div key={anomaly.id} className="flex items-start gap-3 p-3 bg-slate-700/50 rounded-lg">
                <span className={`mt-1 w-2 h-2 rounded-full flex-shrink-0 ${severityColor[anomaly.severity] || "bg-gray-500"}`} />
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium">{anomaly.type.replace(/_/g, " ")}</span>
                    <span className="text-xs text-slate-400 uppercase">{anomaly.severity}</span>
                  </div>
                  <p className="text-xs text-slate-400 mt-1">{anomaly.description}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
