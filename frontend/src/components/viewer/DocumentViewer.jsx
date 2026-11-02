import React, { useState, useEffect, useRef } from "react";
import {
  ChevronLeft,
  ChevronRight,
  ZoomIn,
  ZoomOut,
  X,
  FileText,
  Maximize2,
  Minimize2,
  ExternalLink,
  Layers,
  Sparkles,
  Loader2,
} from "lucide-react";
import { cn } from "../../utils/cn";
import { api } from "../../services/api";

export function DocumentViewer({
  selectedDocName,
  documentId,
  initialPage = 1,
  highlightedChunk = null,
  chunks = [],
  onSelectChunk,
  onClose,
  className = "",
}) {
  const [activeTab, setActiveTab] = useState("document"); // 'document' | 'chunks'
  const [currentPage, setCurrentPage] = useState(initialPage || 1);
  const [zoomLevel, setZoomLevel] = useState(100);
  const [isFullScreen, setIsFullScreen] = useState(false);

  // Real document chunks fetched from backend
  const [docChunks, setDocChunks] = useState([]);
  const [isFetchingDoc, setIsFetchingDoc] = useState(false);
  const [fetchError, setFetchError] = useState(null);
  const highlightRef = useRef(null);

  // Fetch ALL chunks for this document whenever the document changes
  useEffect(() => {
    if (!documentId) {
      console.warn("[DocumentViewer] No documentId provided — skipping fetch");
      return;
    }
    setIsFetchingDoc(true);
    setDocChunks([]);
    setFetchError(null);
    console.log("[DocumentViewer] Fetching chunks for documentId:", documentId);
    api
      .getDocumentChunks(documentId)
      .then((data) => {
        const arr = Array.isArray(data) ? data : [];
        console.log("[DocumentViewer] Received", arr.length, "chunks from backend");
        setDocChunks(arr);
      })
      .catch((err) => {
        console.error("[DocumentViewer] Failed to fetch document chunks:", err);
        setFetchError(err?.message || "Failed to load document content");
        setDocChunks([]);
      })
      .finally(() => setIsFetchingDoc(false));
  }, [documentId]);

  // Sync page when initialPage prop changes (e.g. citation click)
  useEffect(() => {
    if (initialPage) setCurrentPage(initialPage);
  }, [initialPage, selectedDocName]);

  // Auto-scroll highlight into view
  useEffect(() => {
    if (highlightRef.current) {
      highlightRef.current.scrollIntoView({ behavior: "smooth", block: "center" });
    }
  }, [currentPage, highlightedChunk]);

  // ── Derived page data from real chunks ──────────────────────────────────────
  // Use docChunks (full document) if available; fall back to top-K retrieved chunks
  const sourceChunks = docChunks.length > 0 ? docChunks : chunks;
  const usingFallback = docChunks.length === 0 && chunks.length > 0;

  // Group chunks by page_number; chunks without a page go to page 1
  const pageMap = React.useMemo(() => {
    const map = {};
    sourceChunks.forEach((c) => {
      const pg = c.page_number ?? 1;
      if (!map[pg]) map[pg] = [];
      map[pg].push(c);
    });
    return map;
  }, [sourceChunks]);

  const sortedPages = Object.keys(pageMap)
    .map(Number)
    .sort((a, b) => a - b);

  const totalPages = sortedPages.length > 0 ? Math.max(...sortedPages) : 24;

  const chunksForCurrentPage = pageMap[currentPage] || [];

  const handleZoomIn = () => setZoomLevel((prev) => Math.min(prev + 10, 150));
  const handleZoomOut = () => setZoomLevel((prev) => Math.max(prev - 10, 75));
  const handlePrevPage = () => {
    const idx = sortedPages.indexOf(currentPage);
    if (idx > 0) setCurrentPage(sortedPages[idx - 1]);
    else setCurrentPage((prev) => Math.max(prev - 1, 1));
  };
  const handleNextPage = () => {
    const idx = sortedPages.indexOf(currentPage);
    if (idx !== -1 && idx < sortedPages.length - 1) setCurrentPage(sortedPages[idx + 1]);
    else setCurrentPage((prev) => Math.min(prev + 1, totalPages));
  };

  // Check if a chunk text matches the highlighted citation
  const isChunkHighlighted = (text) => {
    if (!highlightedChunk || !text) return false;
    return (
      text.includes(highlightedChunk) ||
      highlightedChunk.includes(text.slice(0, 60))
    );
  };

  return (
    <div
      className={cn(
        "flex flex-col h-full bg-[#0F1014] border-l border-border transition-all duration-200",
        isFullScreen ? "fixed inset-0 z-50 bg-[#09090B]" : "relative",
        className
      )}
    >
      {/* ── Top Toolbar ──────────────────────────────────────────────────────── */}
      <div className="flex items-center justify-between px-4 py-2.5 border-b border-border bg-card/90 backdrop-blur-sm shrink-0">
        <div className="flex items-center gap-2 min-w-0 pr-2">
          <FileText className="h-4 w-4 text-primary shrink-0" />
          <span
            className="text-xs font-semibold text-text-primary truncate"
            title={selectedDocName}
          >
            {selectedDocName || "Document Viewer"}
          </span>
        </div>

        <div className="flex items-center gap-3">
          {/* Zoom Controls */}
          <div className="flex items-center gap-1 bg-card-elevated px-2 py-1 rounded-md border border-border/80 text-xs text-text-secondary">
            <button onClick={handleZoomOut} className="p-0.5 hover:text-text-primary rounded hover:bg-card transition-colors" title="Zoom out">
              <ZoomOut className="h-3.5 w-3.5" />
            </button>
            <span className="font-mono text-[11px] w-9 text-center font-medium">{zoomLevel}%</span>
            <button onClick={handleZoomIn} className="p-0.5 hover:text-text-primary rounded hover:bg-card transition-colors" title="Zoom in">
              <ZoomIn className="h-3.5 w-3.5" />
            </button>
          </div>

          {/* Page Navigation */}
          <div className="flex items-center gap-1.5 bg-card-elevated px-2.5 py-1 rounded-md border border-border/80 text-xs text-text-secondary">
            <button onClick={handlePrevPage} disabled={currentPage <= 1} className="p-0.5 hover:text-text-primary disabled:opacity-30 rounded hover:bg-card transition-colors">
              <ChevronLeft className="h-3.5 w-3.5" />
            </button>
            <span className="font-mono text-xs font-medium text-text-primary">
              {currentPage} <span className="text-text-muted font-normal">/ {totalPages}</span>
            </span>
            <button onClick={handleNextPage} disabled={currentPage >= totalPages} className="p-0.5 hover:text-text-primary disabled:opacity-30 rounded hover:bg-card transition-colors">
              <ChevronRight className="h-3.5 w-3.5" />
            </button>
          </div>
        </div>

        <div className="flex items-center gap-1.5">
          <button onClick={() => setIsFullScreen((prev) => !prev)} className="p-1.5 text-text-muted hover:text-text-primary hover:bg-card-elevated rounded-md transition-colors">
            {isFullScreen ? <Minimize2 className="h-3.5 w-3.5" /> : <Maximize2 className="h-3.5 w-3.5" />}
          </button>
          <button onClick={onClose} className="p-1.5 text-text-muted hover:text-text-primary hover:bg-card-elevated rounded-md transition-colors">
            <X className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* ── Tab Switcher ─────────────────────────────────────────────────────── */}
      <div className="flex items-center justify-between px-4 py-1.5 border-b border-border bg-[#12141A] shrink-0">
        <div className="flex items-center gap-1.5">
          <button
            type="button"
            onClick={() => setActiveTab("document")}
            className={cn(
              "flex items-center gap-1.5 px-3 py-1 rounded-md text-xs font-medium transition-all cursor-pointer",
              activeTab === "document"
                ? "bg-primary text-white shadow-sm"
                : "text-text-muted hover:text-text-primary hover:bg-card-elevated"
            )}
          >
            <FileText className="h-3.5 w-3.5" />
            <span>Document Reader</span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab("chunks")}
            className={cn(
              "flex items-center gap-1.5 px-3 py-1 rounded-md text-xs font-medium transition-all cursor-pointer",
              activeTab === "chunks"
                ? "bg-primary text-white shadow-sm"
                : "text-text-muted hover:text-text-primary hover:bg-card-elevated"
            )}
          >
            <Layers className="h-3.5 w-3.5" />
            <span>Top Chunks</span>
            {chunks && chunks.length > 0 && (
              <span className={cn(
                "px-1.5 py-0.5 rounded-full text-[10px] font-mono font-bold",
                activeTab === "chunks" ? "bg-white/20 text-white" : "bg-primary/20 text-primary"
              )}>
                {chunks.length}
              </span>
            )}
          </button>
        </div>

        {activeTab === "document" ? (
          <span className="text-[11px] font-mono text-text-muted">Page {currentPage} of {totalPages}</span>
        ) : (
          <span className="text-[11px] font-mono text-text-muted">
            Multi-Document Retrieval ({chunks.length} Chunks)
          </span>
        )}
      </div>

      {/* ── Main Body ────────────────────────────────────────────────────────── */}
      {activeTab === "document" ? (
        <div className="flex-1 overflow-y-auto p-4 sm:p-6 flex justify-center bg-[#09090B]">
          <div
            style={{ transform: `scale(${zoomLevel / 100})`, transformOrigin: "top center" }}
            className="w-full max-w-xl min-h-[720px] bg-white text-neutral-900 rounded-lg shadow-2xl p-8 sm:p-10 font-serif leading-relaxed text-sm transition-transform duration-150 border border-neutral-200"
          >
            {/* Document header */}
            <div className="border-b border-neutral-200 pb-4 mb-6 flex justify-between items-baseline text-xs text-neutral-500 font-sans">
              <span className="truncate max-w-xs uppercase tracking-wider font-semibold">
                {selectedDocName}
              </span>
              <span>Page {currentPage} of {totalPages}</span>
            </div>

            <h2 className="text-base font-bold text-neutral-900 mb-4 font-sans tracking-tight">
              Page {currentPage}
            </h2>

            {/* Content area */}
            {isFetchingDoc ? (
              <div className="flex flex-col items-center justify-center py-20 gap-3 text-neutral-400 font-sans">
                <Loader2 className="h-6 w-6 animate-spin text-blue-500" />
                <span className="text-sm">Loading document content…</span>
              </div>
            ) : chunksForCurrentPage.length > 0 ? (
              <>
                {usingFallback && (
                  <div className="mb-4 p-2.5 rounded bg-amber-50 border border-amber-200 text-amber-700 text-xs font-sans">
                    ⚠ Showing only retrieved chunks (full document unavailable). Ask a question to see relevant content.
                  </div>
                )}
                <div className="space-y-5 text-[13px] sm:text-[14px] text-neutral-800 leading-7 font-sans">
                {chunksForCurrentPage.map((chunk, idx) => {
                  const highlighted = isChunkHighlighted(chunk.text);
                  if (highlighted) {
                    return (
                      <p
                        key={chunk.chunk_id || idx}
                        ref={highlightRef}
                        className="p-2.5 rounded bg-amber-100 border-l-4 border-amber-500 text-neutral-950 font-medium shadow-sm transition-all duration-300 ring-2 ring-amber-300/60 whitespace-pre-wrap"
                      >
                        <span className="inline-block px-1.5 py-0.5 rounded bg-amber-400 text-[10px] font-sans font-bold uppercase tracking-wider text-neutral-900 mr-2">
                          Cited Context
                        </span>
                        {chunk.text}
                      </p>
                    );
                  }
                  return (
                    <p key={chunk.chunk_id || idx} className="whitespace-pre-wrap">
                      {chunk.text}
                    </p>
                  );
                })}
              </div>
            ) : sourceChunks.length === 0 && !isFetchingDoc ? (
              <div className="py-16 text-center text-neutral-400 font-sans text-sm space-y-2">
                {fetchError ? (
                  <>
                    <p className="font-semibold text-red-400">⚠ Could not load document content</p>
                    <p className="text-xs font-mono bg-neutral-100 text-neutral-600 rounded px-3 py-1.5 inline-block">{fetchError}</p>
                    <p className="text-xs text-neutral-500 mt-2">Make sure the backend server is running at port 8000.</p>
                  </>
                ) : (
                  <>
                    <p className="font-semibold">No content indexed for this document.</p>
                    <p className="text-xs text-neutral-500">
                      Make sure the document was uploaded and processed successfully.
                    </p>
                  </>
                )}
              </div>
            ) : (
              <div className="py-16 text-center text-neutral-400 font-sans text-sm">
                <p>No content on page {currentPage}.</p>
                <p className="text-xs mt-1 text-neutral-500">
                  Available pages: {sortedPages.slice(0, 8).join(", ")}
                  {sortedPages.length > 8 ? "…" : ""}
                </p>
              </div>
            )}

            <div className="mt-16 pt-6 border-t border-neutral-200 text-center text-xs text-neutral-400 font-sans">
              — {currentPage} —
            </div>
          </div>
        </div>
      ) : (
        /* ── Top-K Chunks Inspector View ────────────────────────────────────── */
        <div className="flex-1 overflow-y-auto p-4 space-y-3 bg-[#09090B]">
          <div className="p-3 rounded-xl bg-card border border-border/80">
            <div className="flex items-center gap-2 mb-1">
              <Sparkles className="h-4 w-4 text-primary" />
              <h3 className="text-xs font-bold text-text-primary tracking-tight">
                Top {chunks.length || 0} Retrieved Semantic Chunks
              </h3>
            </div>
            <p className="text-[11px] text-text-secondary">
              Ranked cross-document passages retrieved via vector similarity search. Click "Focus in Page" to jump directly to any excerpt.
            </p>
          </div>

          {chunks && chunks.length > 0 ? (
            chunks.map((chunk, idx) => {
              const rank = idx + 1;
              const scorePercent =
                chunk.score != null
                  ? (Math.min(Math.max(chunk.score, 0), 1) * 100).toFixed(1)
                  : null;

              return (
                <div
                  key={chunk.chunk_id || idx}
                  className="p-3.5 rounded-xl bg-card border border-border hover:border-primary/50 transition-all space-y-2.5 group shadow-sm"
                >
                  <div className="flex items-center justify-between gap-2">
                    <div className="flex items-center gap-2 min-w-0">
                      <span className="flex items-center justify-center h-5 w-5 rounded-md font-mono text-[10px] font-bold bg-primary/20 text-primary border border-primary/30 shrink-0">
                        #{rank}
                      </span>
                      <span className="text-xs font-semibold text-text-primary truncate max-w-[200px]" title={chunk.document_name}>
                        {chunk.document_name}
                      </span>
                      {chunk.page_number && (
                        <span className="px-1.5 py-0.5 rounded bg-card-elevated border border-border text-[10px] font-mono text-text-muted shrink-0">
                          p.{chunk.page_number}
                        </span>
                      )}
                    </div>
                    {scorePercent && (
                      <span className="px-2 py-0.5 rounded bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 font-mono text-[11px] font-semibold shrink-0">
                        {scorePercent}% match
                      </span>
                    )}
                  </div>

                  <div className="p-2.5 rounded-lg bg-[#0E1015] border border-border/70 text-xs font-mono text-text-secondary leading-relaxed">
                    {chunk.text}
                  </div>

                  <div className="flex items-center justify-between pt-1">
                    <span className="text-[10px] font-mono text-text-muted">
                      ID: {chunk.chunk_id || `chunk_${idx}`}
                    </span>
                    <button
                      type="button"
                      onClick={() => {
                        if (onSelectChunk) {
                          onSelectChunk(chunk);
                        } else {
                          setCurrentPage(chunk.page_number || 1);
                        }
                        setActiveTab("document");
                      }}
                      className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium bg-primary/10 hover:bg-primary/20 text-primary-hover border border-primary/30 transition-colors cursor-pointer"
                    >
                      <ExternalLink className="h-3 w-3" />
                      <span>Focus in Page</span>
                    </button>
                  </div>
                </div>
              );
            })
          ) : (
            <div className="p-8 text-center text-xs text-text-muted">
              No retrieved chunks available yet. Ask a question to inspect semantic chunks.
            </div>
          )}
        </div>
      )}
    </div>
  );
}
