import React, { useState } from "react";
import {
  Copy,
  Check,
  Sparkles,
  User,
  ThumbsUp,
  ThumbsDown,
  FileText,
  ExternalLink,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import { Skeleton } from "../ui/Skeleton";
import { RetrievedChunksView } from "./RetrievedChunksView";
import { cn } from "../../utils/cn";

/**
 * Parses answer text and renders clickable citation tags [S1], [S2], etc.
 */
function renderAnswerText(content, citations, onCitationClick) {
  if (!content) return null;
  const parts = content.split(/(\[S\d+\])/g);

  return parts.map((part, idx) => {
    const match = part.match(/^\[(S\d+)\]$/);
    if (match) {
      const sourceId = match[1];
      const foundCitation = citations.find((c) => c.source_id === sourceId);
      return (
        <button
          key={`cite-${sourceId}-${idx}`}
          type="button"
          onClick={() => {
            if (foundCitation && onCitationClick) {
              onCitationClick(foundCitation);
            }
          }}
          className="inline-flex items-center px-1.5 py-0.5 mx-0.5 rounded text-[11px] font-mono font-bold bg-primary/20 text-primary-hover border border-primary/30 hover:bg-primary hover:text-white transition-all cursor-pointer align-baseline"
          title={
            foundCitation
              ? `${foundCitation.document_name} • ${
                  foundCitation.page_start && foundCitation.page_end && foundCitation.page_start !== foundCitation.page_end
                    ? `pp. ${foundCitation.page_start}-${foundCitation.page_end}`
                    : `p. ${foundCitation.page_number || 1}`
                }`
              : `Citation [${sourceId}]`
          }
        >
          {part}
        </button>
      );
    }
    return <span key={`text-${idx}`}>{part}</span>;
  });
}

export function MessageItem({ message, onCitationClick }) {
  const [copied, setCopied] = useState(false);
  const [feedback, setFeedback] = useState(null); // 'like' | 'dislike'
  const [expandedCitations, setExpandedCitations] = useState({});

  const {
    role,
    content,
    citations = [],
    retrieved_chunks = [],
    sources = [],
    chunks = [],
    isLoading = false,
  } = message;

  const isUser = role === "user";

  const toggleCitation = (key) => {
    setExpandedCitations((prev) => ({
      ...prev,
      [key]: !prev[key],
    }));
  };

  const handleCopy = () => {
    if (!content) return;
    navigator.clipboard.writeText(content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (isUser) {
    return (
      <div className="flex justify-end my-3">
        <div className="flex items-start gap-2.5 max-w-xl">
          <div className="px-4 py-2.5 rounded-2xl rounded-tr-sm bg-primary text-white text-xs sm:text-sm shadow-md shadow-primary/20 leading-relaxed font-medium">
            {content}
          </div>
          <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-card-elevated border border-border text-text-secondary text-xs">
            <User className="h-3.5 w-3.5" />
          </div>
        </div>
      </div>
    );
  }

  // Normalize citations list
  const activeCitations =
    citations && citations.length > 0
      ? citations
      : sources.map((s, i) => ({
          source_id: s.source_id || `S${i + 1}`,
          document_name: s.document || "Document",
          page_number: s.page,
          text: s.chunk_text || "",
          score: s.score || 0,
        }));

  // Top 5 chunks to display in dedicated section
  const displayChunks =
    retrieved_chunks && retrieved_chunks.length > 0
      ? retrieved_chunks
      : chunks;

  return (
    <div className="flex justify-start my-3">
      <div className="flex items-start gap-2.5 max-w-2xl w-full">
        <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-primary/10 border border-primary/20 text-primary mt-1">
          <Sparkles className="h-3.5 w-3.5" />
        </div>

        <div className="flex-1 space-y-3 p-4 rounded-2xl rounded-tl-sm bg-card border border-border text-xs sm:text-sm">
          {isLoading ? (
            <div className="space-y-2.5 py-1">
              <div className="flex items-center gap-2 text-xs text-text-muted">
                <span className="h-1.5 w-1.5 rounded-full bg-primary animate-ping" />
                <span>Retrieving context & synthesizing answer...</span>
              </div>
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-5/6" />
              <Skeleton className="h-4 w-2/3" />
            </div>
          ) : (
            <>
              {/* Answer Content with Clickable Citations */}
              <div className="leading-relaxed text-text-primary whitespace-pre-wrap">
                {renderAnswerText(content, activeCitations, onCitationClick)}
              </div>

              {/* Verified Sources Collapsible Cards */}
              {activeCitations && activeCitations.length > 0 && (
                <div className="pt-3 border-t border-border/60 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-[11px] uppercase tracking-wider font-semibold text-text-muted">
                      Sources ({activeCitations.length})
                    </span>
                    <span className="text-[10px] text-text-muted">
                      Click card to expand verbatim text
                    </span>
                  </div>

                  <div className="space-y-1.5">
                    {activeCitations.map((cite, idx) => {
                      const key = cite.source_id || `cite-${idx}`;
                      const isExpanded = !!expandedCitations[key];
                      const pageLabel =
                        cite.page_start &&
                        cite.page_end &&
                        cite.page_start !== cite.page_end
                          ? `pp. ${cite.page_start}-${cite.page_end}`
                          : cite.page_number != null
                          ? `p. ${cite.page_number}`
                          : "General";

                      return (
                        <div
                          key={cite.chunk_id || key}
                          className="rounded-lg bg-[#14161F] border border-border/80 overflow-hidden text-xs transition-colors"
                        >
                          {/* Header row */}
                          <div
                            onClick={() => toggleCitation(key)}
                            className="flex items-center justify-between px-3 py-2 cursor-pointer hover:bg-card-hover transition-colors"
                          >
                            <div className="flex items-center gap-2 min-w-0">
                              <span className="flex h-4 px-1.5 items-center justify-center rounded bg-primary/20 text-primary text-[10px] font-mono font-bold shrink-0">
                                [{cite.source_id || `S${idx + 1}`}]
                              </span>
                              <span
                                className="font-semibold text-text-primary truncate max-w-[200px] sm:max-w-xs"
                                title={cite.document_name}
                              >
                                {cite.document_name}
                              </span>
                              <span className="text-[11px] font-mono text-text-muted shrink-0">
                                {pageLabel}
                              </span>
                            </div>

                            <div className="flex items-center gap-2 shrink-0">
                              <button
                                type="button"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  onCitationClick && onCitationClick(cite);
                                }}
                                className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-medium text-primary hover:text-white hover:bg-primary transition-colors cursor-pointer"
                                title="Inspect in document viewer"
                              >
                                <span>Inspect</span>
                                <ExternalLink className="h-2.5 w-2.5" />
                              </button>
                              {isExpanded ? (
                                <ChevronUp className="h-3.5 w-3.5 text-text-muted" />
                              ) : (
                                <ChevronDown className="h-3.5 w-3.5 text-text-muted" />
                              )}
                            </div>
                          </div>

                          {/* Verbatim Source Text on Expansion */}
                          {isExpanded && (
                            <div className="px-3 pb-3 pt-1 border-t border-border/40 bg-[#0C0E12]">
                              <p className="text-[11px] font-mono text-text-secondary leading-relaxed whitespace-pre-wrap select-text pl-2 border-l-2 border-primary/50">
                                {cite.text || "No excerpt text available."}
                              </p>
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* Dedicated Retrieved Chunks (Top 5) Section */}
              {displayChunks && displayChunks.length > 0 && (
                <RetrievedChunksView
                  chunks={displayChunks}
                  onChunkClick={onCitationClick}
                />
              )}

              {/* Action & Feedback Bar */}
              <div className="flex items-center justify-between pt-2 border-t border-border/40 text-xs text-text-muted">
                <span className="text-[10px] font-mono text-text-muted">
                  Gemini Grounded RAG • Verified Citations
                </span>

                <div className="flex items-center gap-1">
                  {/* Copy button */}
                  <button
                    onClick={handleCopy}
                    className="p-1.5 rounded-md hover:text-text-primary hover:bg-card-elevated transition-colors"
                    title="Copy response"
                  >
                    {copied ? (
                      <Check className="h-3.5 w-3.5 text-status-success" />
                    ) : (
                      <Copy className="h-3.5 w-3.5" />
                    )}
                  </button>

                  {/* Thumbs up */}
                  <button
                    onClick={() => setFeedback("like")}
                    className={cn(
                      "p-1.5 rounded-md hover:text-text-primary hover:bg-card-elevated transition-colors",
                      feedback === "like" ? "text-status-success bg-status-success/10" : ""
                    )}
                    title="Good response"
                  >
                    <ThumbsUp className="h-3.5 w-3.5" />
                  </button>

                  {/* Thumbs down */}
                  <button
                    onClick={() => setFeedback("dislike")}
                    className={cn(
                      "p-1.5 rounded-md hover:text-text-primary hover:bg-card-elevated transition-colors",
                      feedback === "dislike" ? "text-status-error bg-status-error/10" : ""
                    )}
                    title="Poor response"
                  >
                    <ThumbsDown className="h-3.5 w-3.5" />
                  </button>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
