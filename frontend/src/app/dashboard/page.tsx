"use client";

import { useState } from "react";

export default function DashboardPage() {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const handleUpload = async () => {
    if (!file) return;
    setLoading(true);
    setError(null);
    setResult(null);

    const formData = new FormData();
    formData.append("file", file);

    try {
      // Calling the backend API running on port 8000
      const response = await fetch("http://localhost:8000/api/run-pipeline", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error(await response.text());
      }

      const data = await response.json();
      setResult(data);
    } catch (err: any) {
      setError(err.message || "An error occurred while running the pipeline.");
    } finally {
      setLoading(false);
    }
  };

  // Extract from result if available, otherwise use placeholders
  const stats = [
    { title: "Total Mentions", val: result ? result.summary.total_messages.toLocaleString() : "—" },
    { title: "Total Bigrams", val: result ? result.summary.total_bigrams.toLocaleString() : "—" },
    { title: "Taxonomy Matches", val: result ? `${result.summary.tagged_pct}%` : "—" },
    { title: "Overall Sentiment", val: result ? `${result.summary.positive_pct}% Pos` : "—" },
  ];

  return (
    <div className="flex flex-col min-h-screen items-center p-8 bg-zinc-950 text-white">
      <h1 className="text-4xl font-bold mb-4 mt-8 bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-emerald-400">
        Brand Association Maps
      </h1>
      <p className="text-gray-400 text-lg text-center max-w-2xl mb-8">
        Upload your raw Excel data below to run it through the BAM pipeline. 
        Once complete, you can download the fully mapped and scored Excel grids.
      </p>

      {/* Upload Section */}
      <div className="w-full max-w-5xl mb-12 p-6 rounded-xl border border-zinc-800 bg-zinc-900 flex flex-col items-center justify-center gap-4 shadow-lg">
        <input 
          type="file" 
          accept=".xlsx"
          onChange={(e) => setFile(e.target.files?.[0] || null)}
          className="block w-full max-w-md text-sm text-zinc-400 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-zinc-800 file:text-emerald-400 hover:file:bg-zinc-700 cursor-pointer"
        />
        
        <button 
          onClick={handleUpload}
          disabled={!file || loading}
          className="px-6 py-3 mt-4 rounded-full font-bold text-zinc-950 bg-emerald-400 hover:bg-emerald-300 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {loading ? "Processing Pipeline... (This may take a minute)" : "Run AI Pipeline"}
        </button>

        {error && <div className="text-red-400 mt-2 text-sm">{error}</div>}
      </div>

      {/* Stats Section */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 w-full max-w-5xl">
        {stats.map((item, idx) => (
          <div key={idx} className={`p-6 rounded-xl border ${result ? 'border-emerald-500/30 bg-emerald-900/10' : 'border-zinc-800 bg-zinc-900/50'} flex flex-col items-center justify-center shadow-lg transition-all`}>
            <span className="text-sm text-zinc-400 uppercase tracking-wider mb-2">{item.title}</span>
            <span className="text-3xl font-semibold text-white">{item.val}</span>
          </div>
        ))}
      </div>
      
      {/* Results Actions */}
      {result && (
        <div className="mt-8 flex flex-col items-center justify-center animate-in fade-in zoom-in duration-500">
          <div className="text-emerald-400 mb-6 font-medium text-lg">
            ✅ Pipeline Completed in {result.summary.duration_sec}s
          </div>
          <a   
            href={`http://localhost:8000/api/download/${result.run_id}`}
            download
            className="px-8 py-4 rounded-full font-bold text-white border-2 border-emerald-400 bg-emerald-500/20 hover:bg-emerald-500/40 transition-colors shadow-[0_0_15px_rgba(52,211,153,0.3)]"
          >
            Download Scored Excels (.zip / .xlsx)
          </a>
        </div>
      )}
    </div>
  );
}
