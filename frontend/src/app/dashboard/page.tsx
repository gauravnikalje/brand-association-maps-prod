export default function DashboardPage() {
  return (
    <div className="flex flex-col min-h-screen items-center justify-center p-8 bg-zinc-950 text-white">
      <h1 className="text-4xl font-bold mb-4 bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-emerald-400">
        AntiGravity BAM Dashboard
      </h1>
      <p className="text-gray-400 text-lg text-center max-w-2xl mb-8">
        Welcome to the MVP 2 Association Dashboard mockup. Once integrated with the backend API,
        this page will display dynamic heatmap grids, sentiment aggregations, and performance metrics
        tailored for your brand.
      </p>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 w-full max-w-5xl">
        {[
          { title: "Total Mentions", val: "10,146" },
          { title: "Total Bigrams", val: "22,358" },
          { title: "Taxonomy Matches", val: "2,971" },
          { title: "Overall Sentiment", val: "68% Pos" },
        ].map((item, idx) => (
          <div key={idx} className="p-6 rounded-xl border border-zinc-800 bg-zinc-900/50 flex flex-col items-center justify-center shadow-lg transition-transform hover:scale-105">
            <span className="text-sm text-zinc-400 uppercase tracking-wider mb-2">{item.title}</span>
            <span className="text-3xl font-semibold text-white">{item.val}</span>
          </div>
        ))}
      </div>
      
      <div className="mt-12 w-full max-w-5xl h-64 rounded-xl border border-zinc-800 flex items-center justify-center bg-zinc-900/30">
        <span className="text-zinc-500 italic">Association Heatmap Placeholder</span>
      </div>
    </div>
  );
}
