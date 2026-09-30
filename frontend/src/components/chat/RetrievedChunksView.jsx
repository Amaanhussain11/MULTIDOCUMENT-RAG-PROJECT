import React, { useState } from "react";
import {
  Layers,
  ChevronDown,
  ChevronUp,
  FileText,
  ExternalLink,
  Copy,
  Check,
  Percent,
  Sparkles,
  Filter,
} from "lucide-react";
import { cn } from "../../utils/cn";

/**
 * Visual badge styling based on rank (1 through 5)
 */
const RANK_STYLES = {
  1: {
    bg: "bg-amber-500/10",
    border: "border-amber-500/30",
    text: "text-amber-400",
    bar: "bg-gradient-to-r from-amber-500 to-amber-300",
  },
  2: {
    bg: "bg-emerald-500/10",
    border: "border-emerald-500/30",
    text: "text-emerald-400",
    bar: "bg-gradient-to-r from-emerald-500 to-emerald-300",
  },
  3: {
    bg: "bg-sky-500/10",
    border: "border-sky-500/30",
    text: "text-sky-400",
    bar: "bg-gradient-to-r from-sky-500 to-sky-300",
  },
  4: {
    bg: "bg-indigo-500/10",
    border: "border-indigo-500/30",
    text: "text-indigo-400",
    bar: "bg-gradient-to-r from-indigo-500 to-indigo-300",
  },
  5: {
    bg: "bg-purple-500/10",
    border: "border-purple-500/30",
    text: "text-purple-400",
    bar: "bg-gradient-to-r from-purple-500 to-purple-300",
  },
};

/**
 * File extension badge helper
 */
function getFileTypeBadge(filename = "") {
  if (filename.endsWith(".pdf")) {
    return { label: "PDF", bg: "bg-rose-500/10 text-rose-400 border-rose-500/20" };
  }
  if (filename.endsWith(".docx")) {
    return { label: "DOCX", bg: "bg-blue-500/10 text-blue-400 border-blue-500/20" };
  }
  return { label: "TXT", bg: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20" };
}

export function RetrievedChunksView({ chunks = [], onChunkClick }) {
  const [isExpanded, setIsExpanded] = useState(true);
  const [copiedId, setCopiedId] = useState(null);
  const [selectedDocFilter, setSelectedDocFilter] = useState("ALL");

  if (!chunks || chunks.length === 0) return null;

  // Group chunks by document to display multi-document origin summary
  const docGroups = chunks.reduce((acc, chunk) => {
    const docName = chunk.document_name || "Unknown Document";
    acc[docName] = (acc[docName] || 0) + 1;
    return acc;
  }, {});

  const uniqueDocsCount = Object.keys(docGroups).length;

  const filteredChunks =
    selectedDocFilter === "ALL"
      ? chunks
      : chunks.filter((c) => c.document_name === selectedDocFilter);

  const handleCopyChunk = (chunk, e) => {
    e.stopPropagation();
    navigator.clipboard.writeText(chunk.text);
    setCopiedId(chunk.chunk_id || chunk.chunk_index);
    setTimeout(() => setCopiedId(null), 2000);
  };

  return (
    <div className="pt-3 border-t border-border/70 my-2">
      {/* Top Header & Accordion Toggle */}
      <div className="flex flex-wrap items-center justify-between gap-2 p-2.5 rounded-xl bg-[#14161F] border border-border/80">
        <div className="flex items-center gap-2">
          <div className="flex h-6 w-6 items-center justify-center rounded-md bg-primary/20 text-primary">
            <Layers className="h-3.5 w-3.5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold text-text-primary tracking-tight">
                Top {chunks.length} Retrieved Chunks
              </span>
              <span className="px-2 py-0.5 rounded-full text-[10px] font-medium bg-primary/10 border border-primary/30 text-primary-hover">
                {uniqueDocsCount} {uniqueDocsCount === 1 ? "Document" : "Multiple Documents"}
              </span>
            </div>
            <p className="text-[10px] text-text-muted">
              Semantic context ranked by vector similarity from vector store
            </p>
          </div>
        </div>

        <button
          type="button"
          onClick={() => setIsExpanded((prev) => !prev)}
          className="flex items-center gap-1 px-2 py-1 rounded-md text-[11px] font-medium text-text-secondary hover:text-text-primary bg-card hover:bg-card-hover border border-border transition-colors cursor-pointer"
        >
          <span>{isExpanded ? "Collapse Chunks" : "Show Chunks"}</span>
          {isExpanded ? (
            <ChevronUp className="h-3.5 w-3.5 text-text-muted" />
          ) : (
            <ChevronDown className="h-3.5 w-3.5 text-text-muted" />
          )}
        </button>
      </div>

      {/* Multi-Document Filter Pills Bar */}
      {isExpanded && uniqueDocsCount > 1 && (
        <div className="flex items-center gap-1.5 overflow-x-auto py-2 px-1 text-[11px] scrollbar-none">
          <span className="text-[10px] uppercase font-semibold text-text-muted shrink-0 flex items-center gap-1 mr-1">
            <Filter className="h-3 w-3" /> Filter Doc:
          </span>
          <button
            type="button"
            onClick={() => setSelectedDocFilter("ALL")}
            className={cn(
              "px-2 py-0.5 rounded-md border text-[11px] font-medium transition-all shrink-0 cursor-pointer",
              selectedDocFilter === "ALL"
                ? "bg-primary/20 border-primary text-primary-hover shadow-sm"
                : "bg-card border-border text-text-muted hover:text-text-primary"
            )}
          >
            All Docs ({chunks.length})
          </button>
          {Object.entries(docGroups).map(([docName, count]) => {
            const badge = getFileTypeBadge(docName);
            const isSelected = selectedDocFilter === docName;
            return (
              <button
                key={docName}
                type="button"
                onClick={() => setSelectedDocFilter(docName)}
                className={cn(
                  "flex items-center gap-1 px-2 py-0.5 rounded-md border text-[11px] font-medium transition-all shrink-0 cursor-pointer max-w-[200px] truncate",
                  isSelected
                    ? "bg-primary/20 border-primary text-primary-hover shadow-sm"
                    : "bg-card border-border text-text-muted hover:text-text-primary"
                )}
                title={docName}
              >
                <span
                  className={cn(
                    "text-[9px] px-1 py-0.2 rounded font-mono font-bold border",
                    badge.bg
                  )}
                >
                  {badge.label}
                </span>
                <span className="truncate">{docName}</span>
                <span className="text-[10px] text-text-muted">({count})</span>
              </button>
            );
          })}
        </div>
      )}

      {/* Chunks List (Cards) */}
      {isExpanded && (
        <div className="space-y-2 mt-2">
          {filteredChunks.map((chunk, idx) => {
            const globalRank = chunks.indexOf(chunk) + 1;
            const rankStyle = RANK_STYLES[globalRank] || RANK_STYLES[5];
            const fileBadge = getFileTypeBadge(chunk.document_name);
            const isCopied = copiedId === (chunk.chunk_id || chunk.chunk_index);

            const scorePercent =
              chunk.score != null
                ? (Math.min(Math.max(chunk.score, 0), 1) * 100).toFixed(1)
                : null;

            return (
              <div
                key={chunk.chunk_id || `chunk-${idx}`}
                className="group relative p-3 rounded-xl bg-card border border-border/80 hover:border-primary/50 hover:bg-[#15171F] transition-all duration-150 shadow-sm"
              >
                {/* Chunk Top Meta: Rank, Document Name, Page, Score */}
                <div className="flex flex-wrap items-center justify-between gap-2 mb-2">
                  <div className="flex items-center gap-2 min-w-0">
                    {/* Rank Pill */}
                    <span
                      className={cn(
                        "flex items-center justify-center h-5 px-1.5 rounded-md font-mono text-[10px] font-bold border",
                        rankStyle.bg,
                        rankStyle.border,
                        rankStyle.text
                      )}
                    >
                      #{globalRank}
                    </span>

                    {/* Document Name */}
                    <div className="flex items-center gap-1.5 min-w-0">
                      <span
                        className={cn(
                          "text-[9px] px-1 py-0.5 rounded font-mono font-bold border shrink-0",
                          fileBadge.bg
                        )}
                      >
                        {fileBadge.label}
                      </span>
                      <span
                        className="text-xs font-semibold text-text-primary truncate max-w-[220px] sm:max-w-xs"
                        title={chunk.document_name}
                      >
                        {chunk.document_name}
                      </span>
                    </div>

                    {/* Page / Section badge */}
                    {chunk.page_number != null ? (
                      <span className="px-1.5 py-0.5 rounded bg-card-elevated border border-border text-[10px] font-mono text-text-secondary shrink-0">
                        Page {chunk.page_number}
                      </span>
                    ) : (
                      <span className="px-1.5 py-0.5 rounded bg-card-elevated border border-border text-[10px] font-mono text-text-secondary shrink-0">
                        Chunk {chunk.chunk_index + 1}
                      </span>
                    )}
                  </div>

                  {/* Similarity Score Meter */}
                  {scorePercent && (
                    <div
                      className="flex items-center gap-1.5 px-2 py-0.5 rounded-md bg-[#181B22] border border-border shrink-0"
                      title={`Cosine Similarity Score: ${chunk.score}`}
                    >
                      <div className="w-10 h-1.5 bg-background rounded-full overflow-hidden">
                        <div
                          className={cn("h-full rounded-full", rankStyle.bar)}
                          style={{ width: `${scorePercent}%` }}
                        />
                      </div>
                      <span className="text-[11px] font-mono font-semibold text-text-primary">
                        {scorePercent}%
                      </span>
                      <span className="text-[9px] text-text-muted uppercase">match</span>
                    </div>
                  )}
                </div>

                {/* Chunk Text Content */}
                <div className="relative p-2.5 rounded-lg bg-[#0E1015] border border-border/60 text-xs font-mono text-text-secondary leading-relaxed select-text group-hover:text-text-primary group-hover:border-border transition-colors">
                  <div className="border-l-2 border-primary/40 pl-2">
                    <p className="whitespace-pre-wrap">{chunk.text}</p>
                  </div>
                </div>

                {/* Chunk Footer Actions */}
                <div className="flex items-center justify-between mt-2 pt-2 border-t border-border/40 text-[11px]">
                  <span className="text-[10px] font-mono text-text-muted">
                    ID: {chunk.chunk_id || `chunk_${idx}`}
                  </span>

                  <div className="flex items-center gap-1.5">
                    {/* Copy Button */}
                    <button
                      type="button"
                      onClick={(e) => handleCopyChunk(chunk, e)}
                      className="inline-flex items-center gap-1 px-2 py-1 rounded-md text-[11px] bg-card-elevated hover:bg-card-hover border border-border text-text-secondary hover:text-text-primary transition-colors cursor-pointer"
                      title="Copy chunk text"
                    >
                      {isCopied ? (
                        <>
                          <Check className="h-3 w-3 text-status-success" />
                          <span className="text-status-success font-medium">Copied!</span>
                        </>
                      ) : (
                        <>
                          <Copy className="h-3 w-3" />
                          <span>Copy</span>
                        </>
                      )}
                    </button>

                    {/* View in Document Viewer Button */}
                    <button
                      type="button"
                      onClick={() => onChunkClick && onChunkClick(chunk)}
                      className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-[11px] font-medium bg-primary/10 hover:bg-primary/20 text-primary-hover border border-primary/30 transition-colors cursor-pointer"
                      title="Jump to this page and highlight in Document Viewer"
                    >
                      <ExternalLink className="h-3 w-3" />
                      <span>Inspect in Viewer</span>
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

export default RetrievedChunksView;
