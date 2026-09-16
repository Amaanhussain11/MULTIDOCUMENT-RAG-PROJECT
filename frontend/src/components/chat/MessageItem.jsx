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
} from "lucide-react";
import { Skeleton } from "../ui/Skeleton";
import { cn } from "../../utils/cn";

export function MessageItem({ message, onCitationClick }) {
  const [copied, setCopied] = useState(false);
  const [feedback, setFeedback] = useState(null); // 'like' | 'dislike'
  const { role, content, sources = [], isLoading = false } = message;

  const isUser = role === "user";

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
              {/* Answer Content */}
              <div className="leading-relaxed text-text-primary whitespace-pre-wrap">
                {content}
              </div>

              {/* Verified Sources Bar (Numbered citations as in Screenshot 1) */}
              {sources && sources.length > 0 && (
                <div className="pt-3 border-t border-border/60">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-[11px] uppercase tracking-wider font-semibold text-text-muted">
                      Cited References
                    </span>
                    <span className="text-[10px] text-text-muted">
                      Click to view in document viewer
                    </span>
                  </div>

                  <div className="flex flex-wrap gap-2">
                    {sources.map((src, idx) => (
                      <button
                        key={`${src.document}-${src.page}-${idx}`}
                        type="button"
                        onClick={() => onCitationClick && onCitationClick(src)}
                        className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium bg-[#181B22] border border-border hover:border-primary text-text-secondary hover:text-text-primary transition-all duration-150 cursor-pointer group shadow-sm"
                        title={`Jump to ${src.document} page ${src.page}`}
                      >
                        <span className="flex h-4 w-4 items-center justify-center rounded-full bg-primary/20 text-primary text-[10px] font-mono font-bold group-hover:bg-primary group-hover:text-white transition-colors">
                          {idx + 1}
                        </span>
                        <span className="truncate max-w-[130px]">{src.document}</span>
                        {src.page && (
                          <span className="font-mono text-[11px] text-text-muted">
                            p.{src.page}
                          </span>
                        )}
                        <ExternalLink className="h-2.5 w-2.5 text-text-muted group-hover:text-primary transition-colors ml-0.5" />
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Action & Feedback Bar (Screenshot 1 matching thumbs up, down, copy) */}
              <div className="flex items-center justify-between pt-2 border-t border-border/40 text-xs text-text-muted">
                <span className="text-[10px] font-mono text-text-muted">
                  Gemini 3.7 Flash • Grounded RAG
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
