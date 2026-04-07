"use client";

import { useState } from "react";
import { 
  UploadCloud, 
  Loader2, 
  Download, 
  CheckCircle2, 
  MessageSquare, 
  Hash, 
  Percent, 
  Smile,
  FileSpreadsheet
} from "lucide-react";

export default function DashboardPage() {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [dragActive, setDragActive] = useState(false);

  const handleUpload = async () => {
    if (!file) return;
    setLoading(true);
    setError(null);
    setResult(null);

    const formData = new FormData();
    formData.append("file", file);

    try {
      // Uses the Next.js proxy route (/api/run-pipeline) which forwards
      // to the Railway backend server-side. Works on both local and Vercel.
      const response = await fetch("/api/run-pipeline", {
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

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setFile(e.dataTransfer.files[0]);
    }
  };

  const stats = [
    { title: "Total Mentions", val: result ? result.summary.total_messages.toLocaleString() : "—", icon: MessageSquare, color: "text-blue-400" },
    { title: "Total Bigrams", val: result ? result.summary.total_bigrams.toLocaleString() : "—", icon: Hash, color: "text-purple-400" },
    { title: "Taxonomy Matches", val: result ? `${result.summary.tagged_pct}%` : "—", icon: Percent, color: "text-emerald-400" },
    { title: "Overall Sentiment", val: result ? `${result.summary.positive_pct}% Pos` : "—", icon: Smile, color: "text-yellow-400" },
  ];

  return (
    <div className="relative min-h-screen flex flex-col items-center pt-24 pb-12 px-6 bg-zinc-950 text-zinc-100 overflow-hidden font-sans">
      
      {/* Ambient Background Glows */}
      <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] rounded-full opacity-20 blur-[120px] bg-blue-600/60 pointer-events-none" />
      <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] rounded-full opacity-20 blur-[120px] bg-emerald-600/60 pointer-events-none" />

      {/* Header */}
      <div className="z-10 text-center mb-12 animate-in fade-in slide-in-from-bottom-4 duration-700">
        <h1 className="text-5xl font-extrabold tracking-tight mb-4 text-transparent bg-clip-text bg-gradient-to-r from-blue-400 via-emerald-300 to-emerald-500 pb-1">
          Brand Association Maps
        </h1>
        <p className="text-zinc-400 text-lg max-w-2xl mx-auto font-light leading-relaxed">
          Upload your raw Excel data to run it through the advanced AI BAM pipeline. 
          Instantly generate fully mapped taxonomies and scored grids.
        </p>
      </div>

      {/* Upload Section */}
      <div className="z-10 w-full max-w-4xl mb-12">
        <div 
          className={`relative p-8 md:p-12 rounded-3xl border border-white/10 backdrop-blur-xl transition-all duration-300 flex flex-col items-center justify-center gap-6 shadow-2xl
            ${dragActive ? 'bg-emerald-500/10 border-emerald-500/30' : 'bg-white/5 hover:bg-white-[0.07]'}
          `}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
        >
          {/* Hidden native input overlaid for clickability */}
          <input 
            type="file" 
            accept=".xlsx"
            onChange={(e) => setFile(e.target.files?.[0] || null)}
            className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-20"
          />
          
          <div className="pointer-events-none flex flex-col items-center text-center space-y-4">
            <div className={`p-4 rounded-full transition-colors duration-300 ${file ? 'bg-emerald-500/20 text-emerald-400' : 'bg-white/5 text-zinc-400'}`}>
              {file ? <FileSpreadsheet size={48} /> : <UploadCloud strokeWidth={1.5} size={48} />}
            </div>
            <div>
              <h3 className="text-xl font-semibold mb-1">
                {file ? file.name : "Click or drag your dataset here"}
              </h3>
              <p className="text-sm text-zinc-500">
                {file ? "Ready for processing" : "Supports .xlsx up to 50MB"}
              </p>
            </div>
          </div>
          
          {/* Action Button - z-30 to sit above the hidden input */}
          <button 
            onClick={(e) => { e.stopPropagation(); handleUpload(); }}
            disabled={!file || loading}
            className="z-30 relative px-8 py-3.5 rounded-full font-semibold text-zinc-950 bg-gradient-to-r from-emerald-400 to-emerald-300 hover:from-emerald-300 hover:to-emerald-200 disabled:opacity-50 disabled:grayscale transition-all duration-300 shadow-[0_0_20px_rgba(52,211,153,0.3)] hover:shadow-[0_0_30px_rgba(52,211,153,0.5)] transform hover:-translate-y-0.5 active:translate-y-0 flex items-center gap-2"
          >
            {loading ? (
              <>
                <Loader2 className="animate-spin" size={20} />
                Processing Pipeline...
              </>
            ) : (
              "Run AI Pipeline"
            )}
          </button>

          {error && (
            <div className="absolute -bottom-8 text-red-400 text-sm font-medium animate-in fade-in">
              {error}
            </div>
          )}
        </div>
      </div>

      {/* Stats Section */}
      <div className="z-10 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 w-full max-w-6xl animate-in fade-in slide-in-from-bottom-8 duration-700 delay-150">
        {stats.map((item, idx) => {
          const Icon = item.icon;
          return (
            <div 
              key={idx} 
              className={`group relative p-6 rounded-2xl border backdrop-blur-md overflow-hidden transition-all duration-300 flex flex-col shadow-lg hover:-translate-y-1 hover:shadow-xl
                ${result ? 'border-emerald-500/20 bg-emerald-950/20 hover:border-emerald-500/40' : 'border-white/10 bg-white/5 hover:bg-white/10'}
              `}
            >
              <div className="flex items-center gap-3 mb-4">
                <div className={`p-2 rounded-lg bg-white/5 border border-white/5 ${result ? item.color : 'text-zinc-500'}`}>
                  <Icon size={20} strokeWidth={2} />
                </div>
                <span className="text-sm font-medium text-zinc-400 tracking-wide">{item.title}</span>
              </div>
              <span className={`text-4xl font-bold tracking-tight ${result ? 'text-white' : 'text-zinc-600'}`}>
                {item.val}
              </span>
              
              {/* Subtle hover gradient */}
              <div className="absolute inset-0 bg-gradient-to-tr from-white/0 via-white/0 to-white/5 opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none" />
            </div>
          );
        })}
      </div>
      
      {/* Results Actions */}
      {result && (
        <div className="z-10 mt-16 flex flex-col items-center justify-center animate-in zoom-in-95 fade-in slide-in-from-bottom-4 duration-700">
          <div className="flex items-center gap-2 text-emerald-400 mb-6 font-medium text-lg bg-emerald-950/50 px-6 py-2 rounded-full border border-emerald-500/20">
            <CheckCircle2 size={20} />
            Pipeline Completed Successfully in {result.summary.duration_sec}s
          </div>
          
          <a   
            href={`/api/download/${result.run_id}`}
            download
            className="group px-8 py-4 rounded-full font-semibold text-white border border-emerald-500/30 bg-emerald-500/10 hover:bg-emerald-500/20 transition-all duration-300 shadow-[0_0_20px_rgba(52,211,153,0.1)] hover:shadow-[0_0_30px_rgba(52,211,153,0.2)] flex items-center gap-3 backdrop-blur-md"
          >
            <Download size={20} className="text-emerald-400 group-hover:-translate-y-1 transition-transform duration-300" />
            Download Scored Excels (.zip)
          </a>
        </div>
      )}
    </div>
  );
}
