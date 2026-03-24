import React, { useState } from "react";
import { uploadDocument, searchDocuments } from "../services/api";

export default function DocumentPanel() {
  const [filename, setFilename] = useState("");
  const [rawText, setRawText] = useState("");
  const [result, setResult] = useState<Record<string, unknown> | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<unknown[]>([]);
  const [processing, setProcessing] = useState(false);

  const handleUpload = async () => {
    if (!filename || !rawText) return;
    setProcessing(true);
    try {
      const res = await uploadDocument(filename, rawText);
      setResult(res.data);
    } catch (e: unknown) {
      const errorMsg = e instanceof Error ? e.message : "Upload failed";
      setResult({ error: errorMsg });
    }
    setProcessing(false);
  };

  const handleSearch = async () => {
    if (!searchQuery) return;
    try {
      const res = await searchDocuments(searchQuery);
      setSearchResults(res.data.results || []);
    } catch {
      setSearchResults([]);
    }
  };

  const sampleDocs = [
    {
      name: "invoice-2024-001.pdf",
      text: "INVOICE #INV-2024-001\nDate: 2024-03-15\nVendor: Acme Industrial Supply\nBill To: Widget Manufacturing Inc\n\n1. Industrial Bolt M8x40 | Qty: 500 | $0.45 ea | $225.00\n2. Steel Plate A36 12x12\" | Qty: 20 | $89.99 ea | $1,799.80\n3. Welding Wire ER70S-6 | Qty: 10 spools | $45.00 ea | $450.00\n\nSubtotal: $2,474.80\nTax (8%): $197.98\nShipping: $125.00\nTotal: $2,797.78\nTerms: Net 30",
    },
    {
      name: "po-50234.pdf",
      text: "PURCHASE ORDER #PO-50234\nDate: 2024-03-10\nVendor: Pacific Steel Distributors\nShip To: Warehouse B - 456 Industrial Blvd\n\n1. SKU: STEEL-HR-48 | Hot Rolled Steel Sheet 4x8 | Qty: 100 | $156.00\n2. SKU: ALUM-6061 | Aluminum Bar 6061-T6 | Qty: 50 | $78.50\n3. SKU: PIPE-SCH40 | Steel Pipe Schedule 40 | Qty: 200 | $34.25\n\nTotal: $26,175.00\nDelivery: 2024-03-25",
    },
  ];

  return (
    <div className="p-8">
      <h2 className="text-2xl font-bold mb-6">Document Processing</h2>

      <div className="grid grid-cols-2 gap-6">
        {/* Upload panel */}
        <div className="bg-slate-800 rounded-xl p-6 border border-slate-700">
          <h3 className="text-lg font-semibold mb-4">Upload Document</h3>
          <div className="space-y-4">
            <div>
              <label className="text-sm text-slate-400">Filename</label>
              <input
                type="text"
                value={filename}
                onChange={(e) => setFilename(e.target.value)}
                placeholder="invoice-2024-001.pdf"
                className="w-full mt-1 px-3 py-2 bg-slate-700 rounded-lg border border-slate-600 text-white text-sm focus:outline-none focus:border-emerald-500"
              />
            </div>
            <div>
              <label className="text-sm text-slate-400">Document Text</label>
              <textarea
                value={rawText}
                onChange={(e) => setRawText(e.target.value)}
                rows={10}
                placeholder="Paste document content here..."
                className="w-full mt-1 px-3 py-2 bg-slate-700 rounded-lg border border-slate-600 text-white text-sm focus:outline-none focus:border-emerald-500 font-mono"
              />
            </div>

            <div className="flex gap-2">
              <button
                onClick={handleUpload}
                disabled={processing || !filename || !rawText}
                className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 rounded-lg text-sm font-medium disabled:opacity-50"
              >
                {processing ? "Processing…" : "Process with AI"}
              </button>
            </div>

            <div className="border-t border-slate-700 pt-4">
              <p className="text-xs text-slate-400 mb-2">Quick load sample documents:</p>
              <div className="flex gap-2">
                {sampleDocs.map((doc) => (
                  <button
                    key={doc.name}
                    onClick={() => {
                      setFilename(doc.name);
                      setRawText(doc.text);
                    }}
                    className="px-3 py-1.5 bg-slate-700 hover:bg-slate-600 rounded text-xs"
                  >
                    {doc.name}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Result panel */}
        <div className="space-y-6">
          {result && (
            <div className="bg-slate-800 rounded-xl p-6 border border-slate-700">
              <h3 className="text-lg font-semibold mb-3">Extraction Result</h3>
              <pre className="text-xs text-slate-300 bg-slate-900 p-4 rounded-lg overflow-auto max-h-80">
                {JSON.stringify(result, null, 2)}
              </pre>
            </div>
          )}

          {/* Semantic Search */}
          <div className="bg-slate-800 rounded-xl p-6 border border-slate-700">
            <h3 className="text-lg font-semibold mb-4">Semantic Search</h3>
            <div className="flex gap-2">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search documents by meaning..."
                className="flex-1 px-3 py-2 bg-slate-700 rounded-lg border border-slate-600 text-white text-sm focus:outline-none focus:border-emerald-500"
                onKeyDown={(e) => e.key === "Enter" && handleSearch()}
              />
              <button
                onClick={handleSearch}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-500 rounded-lg text-sm font-medium"
              >
                Search
              </button>
            </div>
            {searchResults.length > 0 && (
              <div className="mt-4 space-y-2">
                {searchResults.map((r: any, i: number) => (
                  <div key={i} className="p-3 bg-slate-700/50 rounded-lg">
                    <div className="flex justify-between text-xs text-slate-400">
                      <span>Score: {r.score?.toFixed(3)}</span>
                      <span>{r.payload?.filename}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
