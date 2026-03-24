import React, { useEffect, useState } from "react";
import { fetchOrders, fetchOrderStats } from "../services/api";

interface Order {
  id: string;
  order_number: string;
  customer_id: string;
  status: string;
  total_amount: number;
  source: string;
  created_at: string;
}

export default function OrderPanel() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [stats, setStats] = useState<{ total: number; by_status: Record<string, number> } | null>(null);

  useEffect(() => {
    fetchOrders().then((r) => setOrders(r.data)).catch(() => setOrders([]));
    fetchOrderStats().then((r) => setStats(r.data)).catch(() => null);
  }, []);

  const statusBadge: Record<string, string> = {
    draft: "bg-slate-500/20 text-slate-400",
    pending_review: "bg-yellow-500/20 text-yellow-400",
    approved: "bg-emerald-500/20 text-emerald-400",
    processing: "bg-blue-500/20 text-blue-400",
    shipped: "bg-cyan-500/20 text-cyan-400",
    delivered: "bg-green-500/20 text-green-400",
    cancelled: "bg-red-500/20 text-red-400",
    returned: "bg-orange-500/20 text-orange-400",
  };

  return (
    <div className="p-8">
      <h2 className="text-2xl font-bold mb-6">Orders</h2>

      {stats && (
        <div className="flex gap-4 mb-6 flex-wrap">
          {Object.entries(stats.by_status).map(([status, count]) => (
            <div key={status} className="bg-slate-800 rounded-lg px-4 py-2 border border-slate-700">
              <span className="text-xs text-slate-400 capitalize">{status.replace(/_/g, " ")}</span>
              <span className="ml-2 font-bold">{count}</span>
            </div>
          ))}
        </div>
      )}

      <div className="bg-slate-800 rounded-xl border border-slate-700 overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="border-b border-slate-700 text-left text-sm text-slate-400">
              <th className="p-4">Order #</th>
              <th className="p-4">Status</th>
              <th className="p-4">Total</th>
              <th className="p-4">Source</th>
              <th className="p-4">Date</th>
            </tr>
          </thead>
          <tbody>
            {orders.length === 0 ? (
              <tr>
                <td colSpan={5} className="p-8 text-center text-slate-400">
                  No orders yet. Use the Agent Monitor to process orders autonomously.
                </td>
              </tr>
            ) : (
              orders.map((order) => (
                <tr key={order.id} className="border-b border-slate-700/50 hover:bg-slate-700/30">
                  <td className="p-4 font-mono text-sm">{order.order_number}</td>
                  <td className="p-4">
                    <span className={`px-2 py-1 rounded-full text-xs ${statusBadge[order.status] || ""}`}>
                      {order.status}
                    </span>
                  </td>
                  <td className="p-4">${order.total_amount.toLocaleString()}</td>
                  <td className="p-4">
                    <span className={order.source === "agent" ? "text-emerald-400" : "text-slate-400"}>
                      {order.source}
                    </span>
                  </td>
                  <td className="p-4 text-sm text-slate-400">
                    {new Date(order.created_at).toLocaleDateString()}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
