import React, { useState, useEffect, useRef } from "react";
import {
  ChevronLeft,
  ChevronRight,
  ZoomIn,
  ZoomOut,
  X,
  FileText,
  Search,
  Maximize2,
  Minimize2,
  ExternalLink,
  Layers,
  Copy,
  Check,
  Filter,
  Sparkles,
} from "lucide-react";
import { Button } from "../ui/Button";
import { cn } from "../../utils/cn";

// Rich simulated page content for indexed documents to demonstrate realistic document reading & highlighting
const DOCUMENT_PAGES = {
  "Annual_AI_Research_Report_2026.pdf": {
    totalPages: 28,
    pages: {
      14: {
        title: "Section 4.2 - Grounded Generation & Factuality Verification",
        paragraphs: [
          "In modern multi-document retrieval architectures, minimizing hallucinations requires strict context filtering before prompt injection into Gemini 3.7 Flash.",
          "Grounded generation verifies all factual claims against top-k retrieved semantic chunks before returning final synthesis to the user. Every chunk retains immutable provenance including document identifier and 1-indexed page coordinates.",
          "When contradictory claims are retrieved across multiple heterogeneous documents, the generation pipeline synthesizes both viewpoints while attributing explicit source markers to each respective claim.",
          "Evaluation across 5,000 corporate documents demonstrated a 99.4% precision rate when bounded retrieval thresholds of 0.78 cosine similarity were enforced.",
        ],
        highlightedText:
          "Grounded generation verifies all factual claims against top-k retrieved semantic chunks before returning final synthesis to the user.",
      },
      15: {
        title: "Section 4.3 - Bounded Concurrency & Embedding Ingestion",
        paragraphs: [
          "Ingesting heterogeneous corpora of PDF, DOCX, and TXT files requires resilient rate-limiting mechanisms.",
          "During initial file parsing, token windows are chunked into 800 to 1200 tokens with a 150-token sliding overlap to preserve cross-boundary semantics.",
          "Batched vectors are asynchronously streamed to Qdrant with tenant-level isolation filters, safeguarding private data boundaries across multi-user environments.",
        ],
        highlightedText: null,
      },
    },
  },
  "Engineering_System_Architecture.docx": {
    totalPages: 12,
    pages: {
      3: {
        title: "3. Microservice Orchestration & Worker Concurrency",
        paragraphs: [
          "The backend service layer is built on Python and FastAPI, delegating compute-intensive tasks to asynchronous worker pools.",
          "Bounded asynchronous concurrency is enforced with worker pools to avoid API rate limiting during batch document ingestion. Workers parse documents concurrently while enforcing system backpressure.",
          "All API contracts under /api/v1 provide strict Pydantic model validation and normalized error formats.",
        ],
        highlightedText:
          "Bounded asynchronous concurrency is enforced with worker pools to avoid API rate limiting during batch document ingestion.",
      },
    },
  },
  "Meeting_Executive_Summary.txt": {
    totalPages: 4,
    pages: {
      1: {
        title: "Executive Summary - Q3 Planning",
        paragraphs: [
          "Meeting attendees confirmed priority roadmap milestones for the RAG service platform.",
          "Key priorities include user/document isolation in Qdrant, sub-second vector search latency, and interactive citation highlighting in the frontend UI.",
        ],
        highlightedText: null,
      },
    },
  },
};

export function DocumentViewer({
  selectedDocName,
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
  const [chunkDocFilter, setChunkDocFilter] = useState("ALL");
  const highlightRef = useRef(null);

  // Sync current page if initialPage prop changes (e.g. user clicks another citation)
  useEffect(() => {
    if (initialPage) {
      setCurrentPage(initialPage);
    }
  }, [initialPage, selectedDocName]);

  // Auto-scroll highlight into view smoothly
  useEffect(() => {
    if (highlightRef.current) {
      highlightRef.current.scrollIntoView({
        behavior: "smooth",
        block: "center",
      });
    }
  }, [currentPage, highlightedChunk]);

  const docData = DOCUMENT_PAGES[selectedDocName] || {
    totalPages: 24,
    pages: {},
  };

  const totalPages = docData.totalPages || 20;

  // Retrieve or generate fallback page content
  const pageData = docData.pages[currentPage] || {
    title: `Document Content - Page ${currentPage}`,
    paragraphs: [
      `This is the rendered text extracted from ${selectedDocName || "Document"} on page ${currentPage}.`,
      highlightedChunk ||
        "The retrieval pipeline parses text chunks from this document page and provides semantic vectors for Qdrant indexation.",
      "All citations are mapped directly to corresponding page numbers, giving users full transparency into verified sources.",
    ],
    highlightedText: highlightedChunk,
  };

  const handleZoomIn = () => setZoomLevel((prev) => Math.min(prev + 10, 150));
  const handleZoomOut = () => setZoomLevel((prev) => Math.max(prev - 10, 75));
  const handlePrevPage = () => setCurrentPage((prev) => Math.max(prev - 1, 1));
  const handleNextPage = () =>
    setCurrentPage((prev) => Math.min(prev + 1, totalPages));

  return (
    <div
      className={cn(
        "flex flex-col h-full bg-[#0F1014] border-l border-border transition-all duration-200",
        isFullScreen ? "fixed inset-0 z-50 bg-[#09090B]" : "relative",
        className
      )}
    >
      {/* Viewer Top Toolbar (Screenshot 1 matching) */}
      <div className="flex items-center justify-between px-4 py-2.5 border-b border-border bg-card/90 backdrop-blur-sm shrink-0">
        {/* Document Info */}
        <div className="flex items-center gap-2 min-w-0 pr-2">
          <FileText className="h-4 w-4 text-primary shrink-0" />
          <span
            className="text-xs font-semibold text-text-primary truncate"
            title={selectedDocName}
          >
            {selectedDocName || "Document Viewer"}
          </span>
        </div>

        {/* Center Controls: Zoom & Page Navigation */}
        <div className="flex items-center gap-3">
          {/* Zoom Controls */}
          <div className="flex items-center gap-1 bg-card-elevated px-2 py-1 rounded-md border border-border/80 text-xs text-text-secondary">
            <button
              onClick={handleZoomOut}
              className="p-0.5 hover:text-text-primary rounded hover:bg-card transition-colors"
              title="Zoom out"
            >
              <ZoomOut className="h-3.5 w-3.5" />
            </button>
            <span className="font-mono text-[11px] w-9 text-center font-medium">
              {zoomLevel}%
            </span>
            <button
              onClick={handleZoomIn}
              className="p-0.5 hover:text-text-primary rounded hover:bg-card transition-colors"
              title="Zoom in"
            >
              <ZoomIn className="h-3.5 w-3.5" />
            </button>
          </div>

          {/* Page Navigation (< 15 / 28 >) */}
          <div className="flex items-center gap-1.5 bg-card-elevated px-2.5 py-1 rounded-md border border-border/80 text-xs text-text-secondary">
            <button
              onClick={handlePrevPage}
              disabled={currentPage <= 1}
              className="p-0.5 hover:text-text-primary disabled:opacity-30 rounded hover:bg-card transition-colors"
              title="Previous page"
            >
              <ChevronLeft className="h-3.5 w-3.5" />
            </button>
            <span className="font-mono text-xs font-medium text-text-primary">
              {currentPage}{" "}
              <span className="text-text-muted font-normal">/ {totalPages}</span>
            </span>
            <button
              onClick={handleNextPage}
              disabled={currentPage >= totalPages}
              className="p-0.5 hover:text-text-primary disabled:opacity-30 rounded hover:bg-card transition-colors"
              title="Next page"
            >
              <ChevronRight className="h-3.5 w-3.5" />
            </button>
          </div>
        </div>

        {/* Right Tools: Fullscreen & Close */}
        <div className="flex items-center gap-1.5">
          <button
            onClick={() => setIsFullScreen((prev) => !prev)}
            className="p-1.5 text-text-muted hover:text-text-primary hover:bg-card-elevated rounded-md transition-colors"
            title={isFullScreen ? "Exit Fullscreen" : "Fullscreen"}
          >
            {isFullScreen ? (
              <Minimize2 className="h-3.5 w-3.5" />
            ) : (
              <Maximize2 className="h-3.5 w-3.5" />
            )}
          </button>
          <button
            onClick={onClose}
            className="p-1.5 text-text-muted hover:text-text-primary hover:bg-card-elevated rounded-md transition-colors"
            title="Close viewer"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* Viewer Tab Switcher (Document Reader vs Top 5 Chunks View) */}
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
              <span
                className={cn(
                  "px-1.5 py-0.2 rounded-full text-[10px] font-mono font-bold",
                  activeTab === "chunks"
                    ? "bg-white/20 text-white"
                    : "bg-primary/20 text-primary"
                )}
              >
                {chunks.length}
              </span>
            )}
          </button>
        </div>

        {activeTab === "document" ? (
          <span className="text-[11px] font-mono text-text-muted">
            Page {currentPage} of {totalPages}
          </span>
        ) : (
          <span className="text-[11px] font-mono text-text-muted">
            Multi-Document Retrieval ({chunks.length} Chunks)
          </span>
        )}
      </div>

      {/* Main Body View */}
      {activeTab === "document" ? (
        /* Main Document Reading Canvas */
        <div className="flex-1 overflow-y-auto p-4 sm:p-6 flex justify-center bg-[#09090B]">
          {/* Rendered Document Sheet (Clean, paper-like high contrast surface) */}
          <div
            style={{ transform: `scale(${zoomLevel / 100})`, transformOrigin: "top center" }}
            className="w-full max-w-xl min-h-[720px] bg-white text-neutral-900 rounded-lg shadow-2xl p-8 sm:p-10 font-serif leading-relaxed text-sm transition-transform duration-150 border border-neutral-200"
          >
            {/* Header of the simulated document */}
            <div className="border-b border-neutral-200 pb-4 mb-6 flex justify-between items-baseline text-xs text-neutral-500 font-sans">
              <span className="truncate max-w-xs uppercase tracking-wider font-semibold">
                {selectedDocName}
              </span>
              <span>
                Page {currentPage} of {totalPages}
              </span>
            </div>

            <h2 className="text-lg font-bold text-neutral-900 mb-4 font-sans tracking-tight">
              {pageData.title}
            </h2>

            {/* Paragraphs with Live Citation Highlighting */}
            <div className="space-y-4 text-[13px] sm:text-[14px] text-neutral-800 leading-6">
              {pageData.paragraphs.map((p, idx) => {
                const isMatch =
                  highlightedChunk &&
                  (p.includes(highlightedChunk) || highlightedChunk.includes(p.slice(0, 30)));

                if (isMatch) {
                  return (
                    <p
                      key={idx}
                      ref={highlightRef}
                      className="p-2.5 rounded bg-amber-100 border-l-4 border-amber-500 text-neutral-950 font-medium shadow-sm transition-all duration-300 ring-2 ring-amber-300/60"
                    >
                      <span className="inline-block px-1.5 py-0.5 rounded bg-amber-400 text-[10px] font-sans font-bold uppercase tracking-wider text-neutral-900 mr-2">
                        Cited Context
                      </span>
                      {p}
                    </p>
                  );
                }

                return <p key={idx}>{p}</p>;
              })}
            </div>

            {/* Document page footer */}
            <div className="mt-16 pt-6 border-t border-neutral-200 text-center text-xs text-neutral-400 font-sans">
              — {currentPage} —
            </div>
          </div>
        </div>
      ) : (
        /* Top-K Chunks Inspector View */
        <div className="flex-1 overflow-y-auto p-4 space-y-3 bg-[#09090B]">
          <div className="p-3 rounded-xl bg-card border border-border/80">
            <div className="flex items-center gap-2 mb-1">
              <Sparkles className="h-4 w-4 text-primary" />
              <h3 className="text-xs font-bold text-text-primary tracking-tight">
                Top {chunks.length || 5} Retrieved Semantic Chunks
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
                      <span
                        className="text-xs font-semibold text-text-primary truncate max-w-[200px]"
                        title={chunk.document_name}
                      >
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
