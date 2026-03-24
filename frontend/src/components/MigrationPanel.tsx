import React, { useState } from "react";
import { dispatchAgent } from "../services/api";

export default function MigrationPanel() {
  const [result, setResult] = useState<Record<string, unknown> | null>(null);
  const [running, setRunning] = useState(false);

  const sampleLegacy = {
    legacy_schema: {
      tbl_cust: {
        CUST_NO: "INT PRIMARY KEY",
        CUST_NM: "VARCHAR(100)",
        CUST_ADDR: "VARCHAR(500)",
        CUST_PH: "VARCHAR(20)",
        CUST_EMAIL: "VARCHAR(100)",
        CR_LMT: "DECIMAL(10,2)",
        CUST_TYP: "CHAR(1)", // R=retail, W=wholesale
        ACCT_BAL: "DECIMAL(10,2)",
        LST_ORD_DT: "DATETIME",
      },
      tbl_item: {
        ITEM_NO: "INT PRIMARY KEY",
        ITEM_DESC: "VARCHAR(200)",
        ITEM_CAT: "CHAR(3)",
        LIST_PRC: "DECIMAL(8,2)",
        COST: "DECIMAL(8,2)",
        QOH: "INT",
        REORD_PT: "INT",
        REORD_QTY: "INT",
        VEND_NO: "INT",
      },
      tbl_ord: {
        ORD_NO: "INT PRIMARY KEY",
        CUST_NO: "INT FK→tbl_cust",
        ORD_DT: "DATETIME",
        SHIP_DT: "DATETIME",
        ORD_TOT: "DECIMAL(10,2)",
        TAX_AMT: "DECIMAL(8,2)",
        FRT_AMT: "DECIMAL(8,2)",
        ORD_STAT: "CHAR(1)", // O=open, C=closed, X=cancelled
        SLSREP: "INT",
      },
      tbl_ord_dtl: {
        ORD_NO: "INT FK→tbl_ord",
        LINE_NO: "INT",
        ITEM_NO: "INT FK→tbl_item",
        QTY_ORD: "INT",
        QTY_SHIP: "INT",
        UNIT_PRC: "DECIMAL(8,2)",
        DISC_PCT: "DECIMAL(4,2)",
      },
      tbl_vend: {
        VEND_NO: "INT PRIMARY KEY",
        VEND_NM: "VARCHAR(100)",
        VEND_ADDR: "VARCHAR(500)",
        VEND_PH: "VARCHAR(20)",
        LEAD_TM: "INT",
      },
    },
    legacy_sample_data: [
      {
        table: "tbl_cust",
        row: { CUST_NO: 1001, CUST_NM: "WIDGET MFG INC", CUST_ADDR: "123 MAIN ST, DALLAS TX 75201", CUST_PH: "214-555-0100", CUST_EMAIL: "INFO@WIDGET.COM", CR_LMT: 50000.0, CUST_TYP: "W", ACCT_BAL: 12345.67, LST_ORD_DT: "2024-02-15 00:00:00" },
      },
      {
        table: "tbl_item",
        row: { ITEM_NO: 5001, ITEM_DESC: "BOLT HEX M8X40 GR8.8 ZP", ITEM_CAT: "FST", LIST_PRC: 0.45, COST: 0.22, QOH: 12500, REORD_PT: 5000, REORD_QTY: 10000, VEND_NO: 201 },
      },
      {
        table: "tbl_ord",
        row: { ORD_NO: 50001, CUST_NO: 1001, ORD_DT: "2024-01-15 00:00:00", SHIP_DT: "2024-01-18 00:00:00", ORD_TOT: 2499.95, TAX_AMT: 199.99, FRT_AMT: 75.0, ORD_STAT: "C", SLSREP: 101 },
      },
    ],
  };

  const handleRun = async () => {
    setRunning(true);
    setResult(null);
    try {
      const res = await dispatchAgent("migration_agent", sampleLegacy);
      setResult(res.data);
    } catch (e: unknown) {
      const errorMsg = e instanceof Error ? e.message : "Migration failed";
      setResult({ error: errorMsg });
    }
    setRunning(false);
  };

  return (
    <div className="p-8">
      <h2 className="text-2xl font-bold mb-6">Legacy Data Migration</h2>

      <div className="grid grid-cols-2 gap-6">
        {/* Legacy Schema View */}
        <div className="bg-slate-800 rounded-xl p-6 border border-slate-700">
          <h3 className="text-lg font-semibold mb-4">Legacy ERP Schema</h3>
          <p className="text-sm text-slate-400 mb-4">
            This simulates a legacy ERP with cryptic table/column names, CHAR status codes,
            and denormalized data — typical of 1990s-era systems that need modernization.
          </p>
          <pre className="text-xs text-slate-300 bg-slate-900 p-4 rounded-lg overflow-auto max-h-96">
            {JSON.stringify(sampleLegacy.legacy_schema, null, 2)}
          </pre>
          <div className="mt-4">
            <button
              onClick={handleRun}
              disabled={running}
              className="w-full px-4 py-3 bg-emerald-600 hover:bg-emerald-500 rounded-lg font-medium transition-colors disabled:opacity-50"
            >
              {running ? "AI Agent Analyzing Schema…" : "Run Migration Agent"}
            </button>
          </div>
        </div>

        {/* Result */}
        <div className="bg-slate-800 rounded-xl p-6 border border-slate-700">
          <h3 className="text-lg font-semibold mb-4">Migration Plan</h3>
          {result ? (
            <pre className="text-xs text-slate-300 bg-slate-900 p-4 rounded-lg overflow-auto max-h-[600px]">
              {JSON.stringify(result, null, 2)}
            </pre>
          ) : (
            <div className="flex items-center justify-center h-64 text-slate-400">
              <p>Run the migration agent to see the AI-generated plan</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
