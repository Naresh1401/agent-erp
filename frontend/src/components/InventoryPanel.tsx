import React, { useEffect, useState } from "react";
import { fetchProducts, fetchAlerts } from "../services/api";

interface Product {
  id: string;
  sku: string;
  name: string;
  category: string;
  unit_price: number;
  quantity_on_hand: number;
  reorder_point: number;
}

interface Alert {
  product_id: string;
  sku: string;
  name: string;
  quantity_on_hand: number;
  reorder_point: number;
  severity: string;
}

export default function InventoryPanel() {
  const [products, setProducts] = useState<Product[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);

  useEffect(() => {
    fetchProducts().then((r) => setProducts(r.data)).catch(() => setProducts([]));
    fetchAlerts().then((r) => setAlerts(r.data)).catch(() => setAlerts([]));
  }, []);

  return (
    <div className="p-8">
      <h2 className="text-2xl font-bold mb-6">Inventory</h2>

      {/* Alerts */}
      {alerts.length > 0 && (
        <div className="mb-8">
          <h3 className="text-lg font-semibold mb-3 text-red-400">Stock Alerts</h3>
          <div className="grid grid-cols-3 gap-3">
            {alerts.map((alert) => (
              <div
                key={alert.product_id}
                className={`rounded-lg p-4 border ${
                  alert.severity === "critical"
                    ? "bg-red-500/10 border-red-500/30"
                    : "bg-yellow-500/10 border-yellow-500/30"
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="font-mono text-sm">{alert.sku}</span>
                  <span
                    className={`text-xs px-2 py-0.5 rounded-full ${
                      alert.severity === "critical" ? "bg-red-500/20 text-red-400" : "bg-yellow-500/20 text-yellow-400"
                    }`}
                  >
                    {alert.severity}
                  </span>
                </div>
                <p className="text-sm mt-1">{alert.name}</p>
                <p className="text-xs text-slate-400 mt-1">
                  Stock: {alert.quantity_on_hand} / Reorder at: {alert.reorder_point}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Product Table */}
      <div className="bg-slate-800 rounded-xl border border-slate-700 overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="border-b border-slate-700 text-left text-sm text-slate-400">
              <th className="p-4">SKU</th>
              <th className="p-4">Product</th>
              <th className="p-4">Category</th>
              <th className="p-4">Price</th>
              <th className="p-4">Stock</th>
              <th className="p-4">Status</th>
            </tr>
          </thead>
          <tbody>
            {products.length === 0 ? (
              <tr>
                <td colSpan={6} className="p-8 text-center text-slate-400">
                  No products yet. Seed the database or use the Data Migration agent.
                </td>
              </tr>
            ) : (
              products.map((p) => {
                const status =
                  p.quantity_on_hand === 0
                    ? "Out of Stock"
                    : p.quantity_on_hand <= p.reorder_point
                    ? "Low Stock"
                    : "In Stock";
                const statusColor =
                  status === "Out of Stock"
                    ? "text-red-400"
                    : status === "Low Stock"
                    ? "text-yellow-400"
                    : "text-emerald-400";

                return (
                  <tr key={p.id} className="border-b border-slate-700/50 hover:bg-slate-700/30">
                    <td className="p-4 font-mono text-sm">{p.sku}</td>
                    <td className="p-4">{p.name}</td>
                    <td className="p-4 text-slate-400">{p.category}</td>
                    <td className="p-4">${p.unit_price.toFixed(2)}</td>
                    <td className="p-4">{p.quantity_on_hand}</td>
                    <td className={`p-4 text-sm font-medium ${statusColor}`}>{status}</td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
