import React from "react";
import { BrowserRouter as Router, Routes, Route, Link } from "react-router-dom";
import Dashboard from "./components/Dashboard";
import AgentMonitor from "./components/AgentMonitor";
import OrderPanel from "./components/OrderPanel";
import InventoryPanel from "./components/InventoryPanel";
import DocumentPanel from "./components/DocumentPanel";
import MigrationPanel from "./components/MigrationPanel";

const navItems = [
  { to: "/", label: "Dashboard", icon: "📊" },
  { to: "/agents", label: "Agent Monitor", icon: "🤖" },
  { to: "/orders", label: "Orders", icon: "📦" },
  { to: "/inventory", label: "Inventory", icon: "🏭" },
  { to: "/documents", label: "Documents", icon: "📄" },
  { to: "/migration", label: "Migration", icon: "🔄" },
];

function App() {
  return (
    <Router>
      <div className="flex h-screen bg-slate-900">
        {/* Sidebar */}
        <nav className="w-64 bg-slate-800 border-r border-slate-700 flex flex-col">
          <div className="p-6 border-b border-slate-700">
            <h1 className="text-xl font-bold text-white">
              <span className="text-emerald-400">Agent</span>ERP
            </h1>
            <p className="text-xs text-slate-400 mt-1">AI-Powered ERP Platform</p>
          </div>
          <div className="flex-1 py-4">
            {navItems.map((item) => (
              <Link
                key={item.to}
                to={item.to}
                className="flex items-center px-6 py-3 text-slate-300 hover:bg-slate-700 hover:text-white transition-colors"
              >
                <span className="mr-3">{item.icon}</span>
                {item.label}
              </Link>
            ))}
          </div>
          <div className="p-4 border-t border-slate-700 text-xs text-slate-500">
            v1.0.0 &middot; Modernization Strike Team
          </div>
        </nav>

        {/* Main content */}
        <main className="flex-1 overflow-auto">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/agents" element={<AgentMonitor />} />
            <Route path="/orders" element={<OrderPanel />} />
            <Route path="/inventory" element={<InventoryPanel />} />
            <Route path="/documents" element={<DocumentPanel />} />
            <Route path="/migration" element={<MigrationPanel />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
