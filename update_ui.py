import re
import os

filepath = r"c:\Users\kittu\Downloads\GIT\RAGReady\rag_pipeline_visualizer.html"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# Extract the script content (we keep everything inside <script> intact)
script_match = re.search(r'(<script>\s*const SAMPLES.*?)</script>', content, re.DOTALL)
if not script_match:
    print("Could not find script block!")
    exit(1)
script_content = script_match.group(1) + "</script>"

new_html = """<!DOCTYPE html>
<html lang="en" class="dark">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Production RAG Pipeline Visualizer</title>
<script src="https://cdn.tailwindcss.com"></script>
<link href="https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500;600;700&family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<script>
  tailwind.config = {
    darkMode: 'class',
    theme: {
      extend: {
        fontFamily: { sans: ['Inter', 'sans-serif'], mono: ['Fira Code', 'monospace'] },
        colors: {
          bgroot: '#020617', card: '#0F172A', cardborder: '#1E293B',
          brand: '#8B5CF6', hoverbrand: '#7C3AED',
          success: '#22C55E', warning: '#F59E0B', danger: '#EF4444',
          textmain: '#F8FAFC', textmuted: '#94A3B8'
        }
      }
    }
  }
</script>
<style>
  body { background-color: #020617; color: #F8FAFC; font-family: 'Inter', sans-serif; }
  .glass { background: #0F172A; border: 1px solid #1E293B; border-radius: 12px; }
  
  /* Pipeline Stages */
  .pipe-box { border: 2px solid #1E293B; transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); background: #020617; }
  .pipe-box:hover { border-color: #8B5CF6; transform: translateY(-2px); box-shadow: 0 4px 12px rgba(139, 92, 246, 0.2); cursor: pointer; }
  .pipe-box.processing { border-color: #F59E0B; background: rgba(245,158,11,0.05); box-shadow: 0 0 15px rgba(245,158,11,0.3); animation: pulse-border 1.5s infinite; }
  .pipe-box.done { border-color: #22C55E; background: rgba(34,197,94,0.05); }
  @keyframes pulse-border { 0% { box-shadow: 0 0 0 0 rgba(245,158,11, 0.4); } 70% { box-shadow: 0 0 0 10px rgba(245,158,11, 0); } 100% { box-shadow: 0 0 0 0 rgba(245,158,11, 0); } }
  .pipe-icon { font-size: 1.5rem; margin-bottom: 0.5rem; opacity: 0.8; }
  .pipe-box:hover .pipe-icon { opacity: 1; text-shadow: 0 0 8px rgba(139, 92, 246, 0.4); }
  .pipe-name { font-size: 0.75rem; font-weight: 600; color: #F8FAFC; }
  .pipe-time { font-size: 0.65rem; color: #94A3B8; margin-top: 4px; font-family: 'Fira Code', monospace; }
  .pipe-arrow { font-size: 1.25rem; color: #1E293B; font-weight: bold; margin-bottom: 2rem; transition: color 0.3s; }
  .pipe-arrow.done { color: #8B5CF6; }
  
  /* Tabs */
  .tab-row { display: flex; border-bottom: 1px solid #1E293B; overflow-x: auto; margin-bottom: 1.5rem; }
  .tab { padding: 1rem 1.5rem; font-size: 0.875rem; font-weight: 600; color: #94A3B8; border-bottom: 2px solid transparent; cursor: pointer; transition: all 0.2s; white-space: nowrap; }
  .tab:hover { color: #F8FAFC; }
  .tab.active { border-bottom-color: #8B5CF6; color: #8B5CF6; }
  .tab-content { display: none; }
  .tab-content.active { display: block; }
  
  /* Chunks rendered by JS */
  .chunk-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1rem; }
  .chunk-card { background: #020617; border: 1px solid #1E293B; border-radius: 8px; padding: 1rem; cursor: pointer; transition: all 0.2s; }
  .chunk-card:hover { border-color: rgba(139, 92, 246, 0.4); }
  .chunk-card.selected { border-color: #8B5CF6; background: rgba(139, 92, 246, 0.05); }
  .chunk-id { font-family: 'Fira Code', monospace; font-size: 0.75rem; color: #8B5CF6; font-weight: 600; margin-bottom: 0.5rem; }
  .chunk-text { font-size: 0.875rem; color: #cbd5e1; line-height: 1.6; }
  .chunk-meta { display: flex; gap: 0.5rem; margin-top: 1rem; align-items: center; }
  .chunk-badge { font-size: 0.65rem; padding: 0.125rem 0.5rem; border-radius: 9999px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; }
  
  /* Retrieval rendered by JS */
  .retrieval-cols { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1.5rem; }
  .ret-item { background: #020617; border-radius: 8px; padding: 0.75rem 1rem; margin-bottom: 0.5rem; border: 1px solid #1E293B; transition: all 0.2s; }
  .ret-item:hover { border-color: rgba(139, 92, 246, 0.4); }
  .ret-rank { display: inline-flex; align-items: center; justify-content: center; width: 24px; height: 24px; background: rgba(139, 92, 246, 0.1); color: #8B5CF6; border-radius: 50%; font-size: 0.7rem; font-weight: 700; margin-right: 0.5rem; }
  .ret-score-bar { height: 4px; border-radius: 2px; margin: 0.5rem 0; }
  .ret-text { font-size: 0.8rem; color: #94A3B8; line-height: 1.5; font-family: 'Inter', sans-serif; }
  
  /* Reranker rendered by JS */
  .rerank-row { display: grid; grid-template-columns: 1fr max-content; align-items: center; gap: 1rem; margin-bottom: 0.5rem; background: #020617; border-radius: 8px; padding: 0.75rem 1rem; border: 1px solid #1E293B; }
  .rank-up { color: #22C55E; } .rank-down { color: #EF4444; } .rank-same { color: #94A3B8; }
  .score-pill { padding: 0.125rem 0.75rem; border-radius: 9999px; font-size: 0.75rem; font-weight: 600; font-family: 'Fira Code', monospace; }
  .score-high { background: rgba(34,197,94,0.1); color: #4ade80; border: 1px solid rgba(34,197,94,0.2); }
  .score-mid { background: rgba(245,158,11,0.1); color: #fbbf24; border: 1px solid rgba(245,158,11,0.2); }
  .score-low { background: rgba(239,68,68,0.1); color: #f87171; border: 1px solid rgba(239,68,68,0.2); }
  
  /* Generation rendered by JS */
  .answer-box { background: #020617; border: 1px solid #1E293B; border-radius: 12px; padding: 1.5rem; font-size: 0.95rem; line-height: 1.8; color: #F8FAFC; box-shadow: inset 0 2px 4px rgba(0,0,0,0.1); }
  .citation { background: rgba(139, 92, 246, 0.1); color: #c4b5fd; border: 1px solid rgba(139, 92, 246, 0.3); border-radius: 4px; font-size: 0.75rem; padding: 0.125rem 0.375rem; cursor: pointer; font-family: 'Fira Code', monospace; transition: all 0.2s; }
  .citation:hover { background: rgba(139, 92, 246, 0.2); color: #ddd6fe; border-color: #8B5CF6; }
  .confidence-badge { display: inline-flex; align-items: center; padding: 0.25rem 0.75rem; border-radius: 9999px; font-size: 0.75rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; font-family: 'Fira Code', monospace; }
  .conf-high { background: rgba(34,197,94,0.1); color: #4ade80; border: 1px solid rgba(34,197,94,0.3); }
  .conf-medium { background: rgba(245,158,11,0.1); color: #fbbf24; border: 1px solid rgba(245,158,11,0.3); }
  .conf-low, .conf-refused { background: rgba(239,68,68,0.1); color: #f87171; border: 1px solid rgba(239,68,68,0.3); }
  
  /* Eval rendered by JS */
  .eval-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; }
  .eval-metric { background: #020617; border-radius: 8px; padding: 1.25rem; border: 1px solid #1E293B; }
  .eval-metric-name { font-size: 0.75rem; color: #94A3B8; text-transform: uppercase; letter-spacing: 0.05em; font-weight: 600; margin-bottom: 0.5rem; }
  .eval-score { font-size: 2rem; font-weight: 700; font-family: 'Fira Code', monospace; line-height: 1; margin-bottom: 0.5rem; }
  .pass-badge { display: inline-flex; align-items: center; padding: 0.125rem 0.5rem; border-radius: 9999px; font-size: 0.65rem; font-weight: 700; letter-spacing: 0.05em; }
  .pass { background: rgba(34,197,94,0.1); color: #22C55E; border: 1px solid rgba(34,197,94,0.3); }
  .fail { background: rgba(239,68,68,0.1); color: #EF4444; border: 1px solid rgba(239,68,68,0.3); }
  .eval-bar-bg { background: rgba(15, 23, 42, 0.8); border-radius: 9999px; height: 6px; margin-top: 0.75rem; overflow: hidden; }
  .eval-bar-fill { height: 100%; transition: width 1s cubic-bezier(0.4, 0, 0.2, 1); }
  
  /* Cost Tab rendered by JS */
  .cost-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 1rem; }
  .cost-item { background: #020617; border-radius: 8px; padding: 1.25rem; border: 1px solid #1E293B; }
  .cost-val { font-size: 1.5rem; font-weight: 700; color: #8B5CF6; font-family: 'Fira Code', monospace; }
  .cost-label { font-size: 0.75rem; color: #94A3B8; margin-top: 0.25rem; font-weight: 500; }
  
  /* Loading */
  .spinner { display: inline-block; width: 16px; height: 16px; border: 2px solid #1E293B; border-top-color: #8B5CF6; border-radius: 50%; animation: spin 0.8s linear infinite; vertical-align: middle; margin-right: 6px; }
  @keyframes spin { to { transform: rotate(360deg); } }
  
  ::-webkit-scrollbar { height: 6px; width: 6px; }
  ::-webkit-scrollbar-track { background: #020617; border-radius: 3px; }
  ::-webkit-scrollbar-thumb { background: #1E293B; border-radius: 3px; }
  ::-webkit-scrollbar-thumb:hover { background: #334155; }
</style>
</head>
<body class="min-h-screen pb-20 selection:bg-brand selection:text-white">

<header class="sticky top-0 z-50 bg-[#020617]/80 backdrop-blur-md border-b border-cardborder px-8 py-4 flex justify-between items-center shadow-sm">
  <div class="flex items-center gap-3">
    <div class="w-10 h-10 rounded-lg bg-brand/10 border border-brand/30 flex items-center justify-center text-brand">
      <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path></svg>
    </div>
    <div>
      <h1 class="text-xl font-bold text-textmain tracking-tight">Production RAG Pipeline</h1>
      <p class="text-xs text-textmuted font-mono mt-0.5">Real-time Telemetry &amp; Analysis • OLED Theme</p>
    </div>
  </div>
  <div class="px-3 py-1 rounded-full border border-success/30 bg-success/10 text-success text-[10px] font-mono tracking-widest uppercase font-bold flex items-center gap-2">
    <div class="w-2 h-2 rounded-full bg-success animate-pulse"></div> Live View
  </div>
</header>

<main class="max-w-7xl mx-auto mt-8 px-4 sm:px-6 lg:px-8 flex flex-col gap-6">

  <!-- Pipeline Flow -->
  <section class="glass p-6">
    <h2 class="text-[11px] font-bold text-textmuted tracking-[0.15em] uppercase mb-6 flex items-center gap-2">
      <svg class="w-4 h-4 text-brand" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path></svg>
      Architecture Topology
    </h2>
    <div class="flex items-center justify-between pb-2 overflow-x-auto gap-1" id="pipelineFlow">
      <div class="flex flex-col items-center cursor-pointer group" onclick="jumpToStage('ingest')">
        <div class="pipe-box w-28 py-4 rounded-xl text-center relative" id="stage-ingest">
          <div class="pipe-icon">📄</div>
          <div class="pipe-name">Document</div>
          <div class="pipe-time" id="t-ingest">&mdash;</div>
        </div>
      </div>
      <div class="pipe-arrow" id="arr-1">&rarr;</div>
      <div class="flex flex-col items-center cursor-pointer group" onclick="jumpToStage('chunk')">
        <div class="pipe-box w-28 py-4 rounded-xl text-center relative" id="stage-chunk">
          <div class="pipe-icon">✂️</div>
          <div class="pipe-name">Chunker</div>
          <div class="pipe-time" id="t-chunk">&mdash;</div>
        </div>
      </div>
      <div class="pipe-arrow" id="arr-2">&rarr;</div>
      <div class="flex flex-col items-center cursor-pointer group" onclick="jumpToStage('index')">
        <div class="pipe-box w-28 py-4 rounded-xl text-center relative" id="stage-index">
          <div class="pipe-icon">🗄️</div>
          <div class="pipe-name">Dual Index</div>
          <div class="pipe-time" id="t-index">&mdash;</div>
        </div>
      </div>
      <div class="pipe-arrow" id="arr-3">&rarr;</div>
      <div class="flex flex-col items-center cursor-pointer group" onclick="jumpToStage('retrieve')">
        <div class="pipe-box w-28 py-4 rounded-xl text-center relative" id="stage-retrieve">
          <div class="pipe-icon">🔎</div>
          <div class="pipe-name">Hybrid Ret.</div>
          <div class="pipe-time" id="t-retrieve">&mdash;</div>
        </div>
      </div>
      <div class="pipe-arrow" id="arr-4">&rarr;</div>
      <div class="flex flex-col items-center cursor-pointer group" onclick="jumpToStage('rerank')">
        <div class="pipe-box w-28 py-4 rounded-xl text-center relative" id="stage-rerank">
          <div class="pipe-icon">📊</div>
          <div class="pipe-name">Reranker</div>
          <div class="pipe-time" id="t-rerank">&mdash;</div>
        </div>
      </div>
      <div class="pipe-arrow" id="arr-5">&rarr;</div>
      <div class="flex flex-col items-center cursor-pointer group" onclick="jumpToStage('generate')">
        <div class="pipe-box w-28 py-4 rounded-xl text-center relative" id="stage-generate">
          <div class="pipe-icon">🤖</div>
          <div class="pipe-name">LLM Gen</div>
          <div class="pipe-time" id="t-generate">&mdash;</div>
        </div>
      </div>
      <div class="pipe-arrow" id="arr-6">&rarr;</div>
      <div class="flex flex-col items-center cursor-pointer group" onclick="jumpToStage('eval')">
        <div class="pipe-box w-28 py-4 rounded-xl text-center relative" id="stage-eval">
          <div class="pipe-icon">✅</div>
          <div class="pipe-name">Evaluation</div>
          <div class="pipe-time" id="t-eval">&mdash;</div>
        </div>
      </div>
    </div>
  </section>

  <!-- Step 1: Ingestion -->
  <section class="glass p-6" id="sec-ingest">
    <h2 class="text-sm font-bold text-textmain mb-4 flex items-center gap-2">
      <div class="w-6 h-6 rounded-md bg-cardborder flex items-center justify-center text-textmain text-xs">1</div> 
      Ingest Knowledge Base
    </h2>
    <div class="bg-brand/10 border-l-2 border-brand text-brand/80 p-4 text-xs font-mono rounded-r-lg mb-4 flex gap-3 leading-relaxed">
      <svg class="w-4 h-4 text-brand shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
      <div>Document is split into overlapping chunks, vectorized via <code>all-MiniLM-L6-v2</code> into ChromaDB, and keyword-indexed via BM25 in parallel.</div>
    </div>
    <textarea id="docInput" class="w-full h-32 bg-[#020617] border border-cardborder rounded-lg p-4 text-sm text-textmain font-mono focus:border-brand focus:ring-1 focus:ring-brand outline-none transition-all resize-y shadow-inner" placeholder="Paste your document here...">Retrieval Augmented Generation (RAG) is a technique that enhances large language models by retrieving relevant information from external documents before generating a response. RAG systems combine the strengths of retrieval-based and generation-based approaches. The retrieval component searches a knowledge base using vector similarity or keyword matching. The generation component uses the retrieved context to produce grounded, accurate answers. RAG significantly reduces hallucination compared to pure generation. Modern RAG systems use hybrid retrieval combining BM25 keyword search with dense vector search. A reranker then scores each retrieved chunk for relevance. The final answer cites specific chunks from the source documents.</textarea>
    <div class="flex gap-3 mt-4 flex-wrap">
      <button onclick="ingestDoc()" class="bg-brand hover:bg-hoverbrand text-white px-6 py-2 rounded-lg text-sm font-semibold transition-all shadow-[0_4px_14px_0_rgba(139,92,246,0.39)] hover:shadow-[0_6px_20px_rgba(139,92,246,0.23)] hover:-translate-y-0.5 flex items-center gap-2">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"></path></svg> Ingest Payload
      </button>
      <button onclick="loadSampleDoc('rag')" class="bg-card border border-cardborder hover:border-textmuted text-textmuted hover:text-textmain px-4 py-2 rounded-lg text-sm font-medium transition-all">Sample: RAG</button>
      <button onclick="loadSampleDoc('ml')" class="bg-card border border-cardborder hover:border-textmuted text-textmuted hover:text-textmain px-4 py-2 rounded-lg text-sm font-medium transition-all">Sample: ML</button>
      <button onclick="loadSampleDoc('code')" class="bg-card border border-cardborder hover:border-textmuted text-textmuted hover:text-textmain px-4 py-2 rounded-lg text-sm font-medium transition-all">Sample: Code</button>
    </div>
  </section>

  <!-- Results Section -->
  <div id="resultsSection" style="display: none;" class="flex flex-col gap-6">
    
    <!-- Stats Row -->
    <div class="grid grid-cols-2 lg:grid-cols-4 xl:grid-cols-7 gap-4">
      <div class="glass p-4 text-center">
        <div class="text-2xl font-bold font-mono text-brand mb-1" id="sChunks">0</div>
        <div class="text-[10px] text-textmuted uppercase tracking-wider font-semibold">Total Chunks</div>
      </div>
      <div class="glass p-4 text-center">
        <div class="text-2xl font-bold font-mono text-brand mb-1" id="sTokens">0</div>
        <div class="text-[10px] text-textmuted uppercase tracking-wider font-semibold">Total Tokens</div>
      </div>
      <div class="glass p-4 text-center">
        <div class="text-2xl font-bold font-mono text-brand mb-1" id="sVecDim">384</div>
        <div class="text-[10px] text-textmuted uppercase tracking-wider font-semibold">Vector Dim</div>
      </div>
      <div class="glass p-4 text-center">
        <div class="text-2xl font-bold font-mono text-brand mb-1" id="sRetrieved">0</div>
        <div class="text-[10px] text-textmuted uppercase tracking-wider font-semibold">K-Retrieved</div>
      </div>
      <div class="glass p-4 text-center">
        <div class="text-2xl font-bold font-mono text-brand mb-1" id="sFinal">5</div>
        <div class="text-[10px] text-textmuted uppercase tracking-wider font-semibold">Context Window</div>
      </div>
      <div class="glass p-4 text-center">
        <div class="text-2xl font-bold font-mono text-brand mb-1" id="sTotalMs">0ms</div>
        <div class="text-[10px] text-textmuted uppercase tracking-wider font-semibold">Total Latency</div>
      </div>
      <div class="glass p-4 text-center border-success/30 bg-success/5">
        <div class="text-2xl font-bold font-mono text-success mb-1" id="sCost">$0.00</div>
        <div class="text-[10px] text-success/80 uppercase tracking-wider font-semibold">Est. Cost</div>
      </div>
    </div>

    <!-- Step 2: Query -->
    <section class="glass p-6" id="sec-retrieve">
      <h2 class="text-sm font-bold text-textmain mb-4 flex items-center gap-2">
        <div class="w-6 h-6 rounded-md bg-cardborder flex items-center justify-center text-textmain text-xs">2</div> 
        Query Engine
      </h2>
      <div class="bg-brand/10 border-l-2 border-brand text-brand/80 p-4 text-xs font-mono rounded-r-lg mb-4 flex gap-3 leading-relaxed">
        <svg class="w-4 h-4 text-brand shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
        <div>Parallel execution of Vector + sparse (BM25) search &rarr; Reciprocal Rank Fusion (RRF) &rarr; Cross-Encoder Reranking &rarr; Extractive QA / LLM Synthesis.</div>
      </div>
      <input type="text" id="queryInput" class="w-full bg-[#020617] border border-cardborder rounded-lg p-4 text-sm text-textmain focus:border-brand focus:ring-1 focus:ring-brand outline-none transition-all shadow-inner" value="What is RAG and how does it reduce hallucination?">
      <div class="flex gap-3 mt-4 flex-wrap">
        <button onclick="runQuery()" class="bg-brand hover:bg-hoverbrand text-white px-6 py-2 rounded-lg text-sm font-semibold transition-all shadow-[0_4px_14px_0_rgba(139,92,246,0.39)] hover:shadow-[0_6px_20px_rgba(139,92,246,0.23)] hover:-translate-y-0.5 flex items-center gap-2">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path></svg> Run Query Pipeline
        </button>
        <button onclick="setQ('How does hybrid retrieval work?')" class="bg-card border border-cardborder hover:border-textmuted text-textmuted hover:text-textmain px-4 py-2 rounded-lg text-sm font-medium transition-all">Hybrid?</button>
        <button onclick="setQ('What is the role of the reranker?')" class="bg-card border border-cardborder hover:border-textmuted text-textmuted hover:text-textmain px-4 py-2 rounded-lg text-sm font-medium transition-all">Reranker?</button>
        <button onclick="setQ('Who invented quantum computing?')" class="bg-card border border-cardborder hover:border-danger/50 text-textmuted hover:text-danger px-4 py-2 rounded-lg text-sm font-medium transition-all">Out of scope &times;</button>
      </div>
    </section>

    <!-- Deep Dive Tabs -->
    <section class="glass overflow-hidden shadow-2xl">
      <div class="tab-row bg-[#020617]/50 pt-2 px-2 m-0 border-b border-cardborder flex items-end">
        <div class="tab active rounded-t-lg bg-card border-x border-t border-cardborder/50 text-brand px-6 py-3 font-semibold shadow-[0_-4px_10px_rgba(0,0,0,0.2)] relative z-10 font-mono tracking-tight" onclick="switchActiveTab(this, 'chunks')"><span class="mr-2">🗄️</span> Vector DB (Chunks)</div>
        <div class="tab px-6 py-3 font-medium text-textmuted hover:text-textmain transition-colors font-mono tracking-tight" onclick="switchActiveTab(this, 'retrieval')"><span class="mr-2">🔎</span> Hybrid Retrieval</div>
        <div class="tab px-6 py-3 font-medium text-textmuted hover:text-textmain transition-colors font-mono tracking-tight" onclick="switchActiveTab(this, 'rerank')"><span class="mr-2">⚖️</span> Cross Reranker</div>
        <div class="tab px-6 py-3 font-medium text-textmuted hover:text-textmain transition-colors font-mono tracking-tight" onclick="switchActiveTab(this, 'generation')"><span class="mr-2">🤖</span> Generator (LLM)</div>
        <div class="tab px-6 py-3 font-medium text-textmuted hover:text-textmain transition-colors font-mono tracking-tight" onclick="switchActiveTab(this, 'eval')"><span class="mr-2">📈</span> Ragas Eval</div>
        <div class="tab px-6 py-3 font-medium text-textmuted hover:text-textmain transition-colors font-mono tracking-tight" onclick="switchActiveTab(this, 'cost')"><span class="mr-2">💳</span> Telemetry & Cost</div>
      </div>

      <div class="p-8 bg-card relative z-0 min-h-[400px]">
        
        <!-- Chunks Tab -->
        <div id="tab-chunks" class="tab-content active">
          <div class="bg-[#020617] border border-cardborder rounded-lg p-4 mb-6 text-sm text-textmuted flex gap-3 items-center shadow-inner">
            <svg class="w-5 h-5 text-brand shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"></path></svg>
            <div>Stored <strong class="text-brand font-mono font-bold" id="chunkCount">0</strong> chunks. Dimensions: 384. Vectors in Memory.</div>
          </div>
          <div id="chunkGrid" class="chunk-grid"></div>
        </div>

        <!-- Retrieval Tab -->
        <div id="tab-retrieval" class="tab-content">
          <div class="bg-[#020617] border border-cardborder rounded-lg p-3 text-center font-mono text-sm text-brand mb-8 shadow-inner font-bold tracking-widest">
            RRF Score(d) = &Sigma; 1 / (k + rank(d)) <span class="text-textmuted font-normal ml-3">| k = 60</span> 
          </div>
          <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div class="bg-[#020617] p-5 rounded-xl border border-cardborder shadow-sm">
              <h3 class="text-xs font-bold text-blue-400 tracking-wider uppercase border-b border-cardborder pb-3 mb-4 flex items-center gap-2"><div class="w-2 h-2 rounded-full bg-blue-400 shadow-[0_0_8px_rgba(96,165,250,0.8)]"></div> Dense Vector</h3>
              <p class="text-[11px] text-textmuted mb-4 font-mono leading-relaxed">Similarity on embeddings.</p>
              <div id="vectorResults"></div>
            </div>
            <div class="bg-[#020617] p-5 rounded-xl border border-cardborder shadow-sm">
              <h3 class="text-xs font-bold text-amber-400 tracking-wider uppercase border-b border-cardborder pb-3 mb-4 flex items-center gap-2"><div class="w-2 h-2 rounded-full bg-amber-400 shadow-[0_0_8px_rgba(251,191,36,0.8)]"></div> Sparse (BM25)</h3>
              <p class="text-[11px] text-textmuted mb-4 font-mono leading-relaxed">Exact keyword TF-IDF matches.</p>
              <div id="bm25Results"></div>
            </div>
            <div class="bg-[#0F172A] p-5 rounded-xl border-2 border-brand/30 shadow-[0_0_20px_rgba(139,92,246,0.1)] relative">
              <div class="absolute -top-3 -right-3 bg-brand text-white text-[10px] font-bold px-3 py-1 rounded-full shadow-lg">WINNER</div>
              <h3 class="text-xs font-bold text-brand tracking-wider uppercase border-b border-cardborder pb-3 mb-4 flex items-center gap-2"><div class="w-2 h-2 rounded-full bg-brand shadow-[0_0_8px_rgba(139,92,246,0.8)]"></div> RRF Fused</h3>
              <p class="text-[11px] text-textmuted mb-4 font-mono leading-relaxed">Combined algorithm rankings.</p>
              <div id="fusedResults"></div>
            </div>
          </div>
        </div>

        <!-- Reranker Tab -->
        <div id="tab-rerank" class="tab-content">
          <div class="bg-brand/10 border-l-2 border-brand text-brand/80 p-4 text-xs font-mono rounded-r-lg mb-6 flex gap-3 leading-relaxed">
             <svg class="w-4 h-4 text-brand shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
            <div>Cross-Encoder Scoring evaluated. Low score chunks dropped (threshold: 0.35). Observe the rank shifts to see the accuracy bump.</div>
          </div>
          <div class="grid grid-cols-[1fr_120px] gap-4 px-4 pb-2 text-[10px] font-bold text-textmuted uppercase tracking-widest border-b border-cardborder mb-3">
            <div>Document Payload</div>
            <div class="text-center">Shift / Score</div>
          </div>
          <div id="rerankRows" class="flex flex-col"></div>
        </div>

        <!-- Generation Tab -->
        <div id="tab-generation" class="tab-content">
          <div class="flex items-center gap-3 mb-6 bg-[#020617] border border-cardborder p-3 rounded-lg w-max shadow-inner">
            <span class="text-[11px] font-bold text-textmuted uppercase tracking-wider">Context Confidence:</span>
            <div id="confBadge" class="score-high"></div>
            <div class="h-4 w-[1px] bg-cardborder mx-2"></div>
            <div class="text-[11px] font-mono text-textmuted flex items-center gap-1">
              <svg class="w-3 h-3 text-brand" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z"></path></svg>
              Gemini 2.0 Flash
            </div>
          </div>
          
          <div id="answerBox" class="answer-box">
             <em class="text-textmuted">Run a query to stream response...</em>
          </div>

          <div class="mt-8">
            <h3 class="text-[11px] font-bold text-textmuted tracking-widest uppercase mb-4 flex items-center gap-2 border-b border-cardborder pb-2">
              <svg class="w-4 h-4 text-brand" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"></path></svg>
              Verified Citations
            </h3>
            <div id="citationsList" class="flex flex-col gap-3"></div>
          </div>
        </div>

        <!-- Evaluation Tab -->
        <div id="tab-eval" class="tab-content">
          <div class="flex items-center gap-4 mb-8 bg-success/10 border border-success/30 rounded-xl p-5 shadow-sm">
            <div class="w-12 h-12 rounded-full bg-success/20 flex items-center justify-center text-success shrink-0"><svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg></div>
            <div>
              <div class="font-bold text-success text-sm tracking-wide" id="overallBadge">CI/CD GATE PASSING</div>
              <div class="text-xs text-success/80 mt-1">Evaluation assertions succeeded. Safe to deploy.</div>
            </div>
          </div>
          <div id="evalGrid" class="eval-grid"></div>
        </div>

        <!-- Cost Tab -->
        <div id="tab-cost" class="tab-content">
          <div id="costGrid" class="cost-grid mb-8"></div>
          <div class="bg-[#020617] border border-cardborder rounded-xl p-6 shadow-inner">
            <h3 class="text-sm font-bold text-textmain mb-6 flex items-center gap-2">
              <svg class="w-5 h-5 text-success" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"></path></svg>
              Cost Arbitrage (vs standard prompts)
            </h3>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div class="bg-card border border-success/30 rounded-lg p-5 relative overflow-hidden group">
                <div class="absolute inset-0 bg-gradient-to-br from-success/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity"></div>
                <div class="text-success font-bold text-sm mb-3 flex items-center gap-2"><svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg> RAG Pipeline</div>
                <div class="text-sm text-textmuted leading-relaxed font-mono">
                  Retrieve top chunks (~600 tokens)<br>
                  Cost &rarr; <strong class="text-success text-lg mt-2 block">~$0.0001/req</strong>
                </div>
              </div>
              <div class="bg-card border border-danger/30 rounded-lg p-5 relative overflow-hidden group">
                <div class="absolute inset-0 bg-gradient-to-br from-danger/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity"></div>
                <div class="text-danger font-bold text-sm mb-3 flex items-center gap-2"><svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg> Giant Context Prompting</div>
                <div class="text-sm text-textmuted leading-relaxed font-mono">
                  Pass entire doc (50K+ tokens)<br>
                  Cost &rarr; <strong class="text-danger text-lg mt-2 block">~$0.005/req (50x)</strong>
                </div>
              </div>
            </div>
          </div>
        </div>

      </div>
    </section>
  </div>

</main>

<script>
  function switchActiveTab(element, name) {
    document.querySelectorAll('.tab').forEach(t => {
      t.classList.remove('active', 'bg-card', 'border-x', 'border-t', 'border-cardborder/50', 'text-brand', 'shadow-[0_-4px_10px_rgba(0,0,0,0.2)]', 'z-10');
      t.classList.add('text-textmuted');
    });
    element.classList.remove('text-textmuted');
    element.classList.add('active', 'bg-card', 'border-x', 'border-t', 'border-cardborder/50', 'text-brand', 'shadow-[0_-4px_10px_rgba(0,0,0,0.2)]', 'z-10');
    switchTab(name);
  }
</script>
"""

with open(filepath, "w", encoding="utf-8") as f:
    f.write(new_html)
    f.write("\n")
    f.write(script_content)

print("Redesigned Visualizer HTML and CSS created successfully.")
