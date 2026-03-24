import React, { useState } from "react";
import { dispatchAgent, fetchTasks, fetchTaskLogs } from "../services/api";

interface Task {
  id: string;
  agent_type: string;
  status: string;
  tokens_used: number;
  cost_usd: number;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
  output_data: Record<string, unknown>;
  error_message: string | null;
}

interface LogEntry {
  step_name: string;
  step_order: number;
  llm_model: string | null;
  tokens_in: number;
  tokens_out: number;
  duration_ms: number | null;
}

export default function AgentMonitor() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [dispatching, setDispatching] = useState(false);
  const [result, setResult] = useState<Record<string, unknown> | null>(null);

  const loadTasks = async () => {
    try {
      const res = await fetchTasks();
      setTasks(res.data);
    } catch {
      setTasks([]);
    }
  };

  const handleDispatch = async (agentType: string, inputData: unknown) => {
    setDispatching(true);
    setResult(null);
    try {
      const res = await dispatchAgent(agentType, inputData);
      setResult(res.data);
      loadTasks();
    } catch (e: unknown) {
      const errorMsg = e instanceof Error ? e.message : "Unknown error";
      setResult({ error: errorMsg });
    }
    setDispatching(false);
  };

  const viewLogs = async (task: Task) => {
    setSelectedTask(task);
    try {
      const res = await fetchTaskLogs(task.id);
      setLogs(res.data);
    } catch {
      setLogs([]);
    }
  };

  const agentTypes = [
    {
      type: "document_processor",
      label: "Document Processor",
      description: "Parse & extract data from legacy documents",
      sampleInput: {
        filename: "invoice-2024-001.pdf",
        raw_text:
          "INVOICE #INV-2024-001\nDate: 2024-03-15\nVendor: Acme Corp\nBill To: Widget Inc\n\nItem: Industrial Bolt M8x40 | Qty: 500 | Price: $0.45 | Total: $225.00\nItem: Steel Plate A36 | Qty: 20 | Price: $89.99 | Total: $1,799.80\n\nSubtotal: $2,024.80\nTax (8%): $161.98\nTotal: $2,186.78\nPayment Terms: Net 30",
      },
    },
    {
      type: "order_agent",
      label: "Order Processor",
      description: "Validate, price, risk-assess & approve orders",
      sampleInput: {
        order_data: {
          customer_id: "c1234567-89ab-cdef-0123-456789abcdef",
          items: [
            { product_id: "p1234567-89ab-cdef-0123-456789abcdef", quantity: 100, unit_price: 24.99 },
            { product_id: "p2345678-9abc-def0-1234-56789abcdef0", quantity: 50, unit_price: 89.99 },
          ],
        },
        customer: { name: "Widget Inc", tier: "gold", order_history: 47 },
      },
    },
    {
      type: "inventory_agent",
      label: "Inventory Intelligence",
      description: "Analyze stock levels, detect anomalies, forecast demand",
      sampleInput: {
        products: [
          { id: "1", sku: "BOLT-M8", name: "Industrial Bolt M8x40", category: "Fasteners", quantity_on_hand: 0, reorder_point: 100, unit_price: 0.45 },
          { id: "2", sku: "PLATE-A36", name: "Steel Plate A36", category: "Raw Materials", quantity_on_hand: 15, reorder_point: 20, unit_price: 89.99 },
          { id: "3", sku: "CABLE-CAT6", name: "Cable Cat6 1000ft", category: "Electronics", quantity_on_hand: 850, reorder_point: 50, unit_price: 125.0 },
          { id: "4", sku: "WIDGET-A200", name: "Widget A-200", category: "Assemblies", quantity_on_hand: 5, reorder_point: 25, unit_price: 340.0 },
        ],
      },
    },
    {
      type: "migration_agent",
      label: "Data Migration",
      description: "Map legacy schemas to modern data models",
      sampleInput: {
        legacy_schema: {
          tbl_cust: { CUST_NO: "INT", CUST_NM: "VARCHAR(100)", CUST_ADDR: "VARCHAR(500)", CUST_PH: "VARCHAR(20)", CUST_EMAIL: "VARCHAR(100)" },
          tbl_ord: { ORD_NO: "INT", CUST_NO: "INT FK→tbl_cust", ORD_DT: "DATETIME", ORD_TOT: "DECIMAL(10,2)", ORD_STAT: "CHAR(1)" },
          tbl_ord_dtl: { ORD_NO: "INT FK→tbl_ord", ITEM_NO: "INT", QTY: "INT", PRICE: "DECIMAL(8,2)" },
        },
        legacy_sample_data: [
          { table: "tbl_cust", row: { CUST_NO: 1001, CUST_NM: "WIDGET INC", CUST_ADDR: "123 MAIN ST", CUST_PH: "555-0100", CUST_EMAIL: "INFO@WIDGET.COM" } },
          { table: "tbl_ord", row: { ORD_NO: 50001, CUST_NO: 1001, ORD_DT: "2024-01-15 00:00:00", ORD_TOT: 2499.95, ORD_STAT: "C" } },
        ],
      },
    },
  ];

  const statusColor: Record<string, string> = {
    completed: "text-emerald-400 bg-emerald-500/20",
    failed: "text-red-400 bg-red-500/20",
    running: "text-blue-400 bg-blue-500/20",
    queued: "text-yellow-400 bg-yellow-500/20",
  };

  return (
    <div className="p-8">
      <h2 className="text-2xl font-bold mb-6">Agent Monitor</h2>

      {/* Dispatch Panel */}
      <div className="grid grid-cols-2 gap-4 mb-8">
        {agentTypes.map((agent) => (
          <div key={agent.type} className="bg-slate-800 rounded-xl p-5 border border-slate-700">
            <h3 className="font-semibold text-lg">{agent.label}</h3>
            <p className="text-sm text-slate-400 mt-1 mb-4">{agent.description}</p>
            <button
              onClick={() => handleDispatch(agent.type, agent.sampleInput)}
              disabled={dispatching}
              className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
            >
              {dispatching ? "Running…" : "Run Agent"}
            </button>
          </div>
        ))}
      </div>

      {/* Result */}
      {result && (
        <div className="bg-slate-800 rounded-xl p-5 border border-slate-700 mb-8">
          <h3 className="font-semibold mb-3">Latest Result</h3>
          <pre className="text-xs text-slate-300 bg-slate-900 p-4 rounded-lg overflow-auto max-h-96">
            {JSON.stringify(result, null, 2)}
          </pre>
        </div>
      )}

      {/* Task History */}
      <div className="bg-slate-800 rounded-xl p-5 border border-slate-700 mb-8">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold text-lg">Task History</h3>
          <button onClick={loadTasks} className="px-3 py-1.5 bg-slate-700 hover:bg-slate-600 rounded-lg text-sm">
            Refresh
          </button>
        </div>
        {tasks.length === 0 ? (
          <p className="text-slate-400 text-sm">No tasks yet. Click "Refresh" or dispatch an agent above.</p>
        ) : (
          <div className="space-y-2">
            {tasks.map((task) => (
              <div
                key={task.id}
                className="flex items-center justify-between p-3 bg-slate-700/50 rounded-lg cursor-pointer hover:bg-slate-700"
                onClick={() => viewLogs(task)}
              >
                <div className="flex items-center gap-3">
                  <span className={`px-2 py-0.5 rounded-full text-xs ${statusColor[task.status] || "text-slate-400"}`}>
                    {task.status}
                  </span>
                  <span className="text-sm font-medium">{task.agent_type.replace(/_/g, " ")}</span>
                </div>
                <div className="text-xs text-slate-400">
                  {task.tokens_used} tokens &middot; ${task.cost_usd?.toFixed(4)}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Task Logs */}
      {selectedTask && (
        <div className="bg-slate-800 rounded-xl p-5 border border-slate-700">
          <h3 className="font-semibold text-lg mb-4">
            Execution Logs: {selectedTask.agent_type.replace(/_/g, " ")}
          </h3>
          <div className="relative">
            {logs.map((log, i) => (
              <div key={i} className="flex gap-4 mb-4">
                <div className="flex flex-col items-center">
                  <div className="w-8 h-8 rounded-full bg-emerald-600 flex items-center justify-center text-xs font-bold">
                    {log.step_order}
                  </div>
                  {i < logs.length - 1 && <div className="w-0.5 flex-1 bg-slate-600 mt-1" />}
                </div>
                <div className="flex-1 bg-slate-700/50 rounded-lg p-3">
                  <p className="font-medium text-sm">{log.step_name}</p>
                  <div className="flex gap-4 mt-1 text-xs text-slate-400">
                    {log.llm_model && <span>Model: {log.llm_model}</span>}
                    {log.duration_ms && <span>{log.duration_ms}ms</span>}
                    {(log.tokens_in > 0 || log.tokens_out > 0) && (
                      <span>
                        Tokens: {log.tokens_in}→{log.tokens_out}
                      </span>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
