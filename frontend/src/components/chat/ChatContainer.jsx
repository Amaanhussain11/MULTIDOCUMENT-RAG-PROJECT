import React, { useRef, useEffect } from "react";
import { MessageItem } from "./MessageItem";
import { ChatInput } from "./ChatInput";
import { Sparkles, Layers, FileText, CheckCircle2, ChevronDown } from "lucide-react";
import { cn } from "../../utils/cn";

export function ChatContainer({
  messages = [],
  onSend,
  isLoading = false,
  readyDocumentsCount = 0,
  error = null,
  onCitationClick,
  onChunkClick,
  scopedDocsCount = 0,
  className = "",
}) {
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  const starterPrompts = [
    "What are the main conclusions across all uploaded documents?",
    "Summarize the key methodologies and findings.",
    "Are there any conflicting statements or differences?",
    "Extract the most important action items or recommendations.",
  ];

  return (
    <div className={cn("flex flex-col h-full bg-background relative", className)}>
      {/* Scope Header Pill Bar (Screenshot 1 matching "+ All sources") */}
      <div className="flex items-center justify-between px-4 py-2.5 border-b border-border bg-card/60 backdrop-blur-sm shrink-0">
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-[#181B22] border border-border text-xs text-text-primary">
            <Layers className="h-3.5 w-3.5 text-primary" />
            <span className="font-medium">
              {scopedDocsCount > 0
                ? `${scopedDocsCount} Sources Active`
                : "All Sources Active"}
            </span>
          </div>

          <span className="text-[11px] text-text-muted hidden sm:inline">
            {readyDocumentsCount} ready documents in Knowledge Base
          </span>
        </div>

        <span className="text-[11px] font-mono text-text-muted">
          FastAPI + Gemini 3.7 Flash
        </span>
      </div>

      {/* Messages Scroll View */}
      <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-4">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-center py-8 space-y-6">
            <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-card-elevated border border-border text-primary shadow-inner">
              <Sparkles className="h-7 w-7" />
            </div>

            <div className="space-y-1.5 max-w-md">
              <h3 className="text-xl font-bold text-text-primary tracking-tight">
                Hello! How can I help you today?
              </h3>
              <p className="text-xs text-text-secondary leading-relaxed">
                Ask any question about your documents. Answers are verified and cited directly from indexed knowledge base chunks.
              </p>
            </div>

            {readyDocumentsCount > 0 && (
              <div className="w-full max-w-md space-y-2 pt-2 text-left">
                <p className="text-[11px] uppercase tracking-wider font-semibold text-text-muted px-1">
                  Example questions
                </p>
                <div className="grid grid-cols-1 gap-2">
                  {starterPrompts.map((prompt, i) => (
                    <button
                      key={i}
                      onClick={() => onSend(prompt)}
                      className="text-left p-3 rounded-xl bg-card border border-border hover:border-primary/50 hover:bg-card-hover text-xs text-text-primary transition-all duration-150 cursor-pointer shadow-sm group flex items-center justify-between"
                    >
                      <span>"{prompt}"</span>
                      <span className="text-text-muted group-hover:text-primary transition-colors text-[11px]">
                        Ask →
                      </span>
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {messages.map((msg, index) => (
          <MessageItem
            key={index}
            message={msg}
            onCitationClick={onCitationClick}
            onChunkClick={onChunkClick}
          />
        ))}

        {error && (
          <div className="p-3 rounded-xl bg-status-error/10 border border-status-error/20 text-xs text-rose-300">
            {error}
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input Dock (Screenshot 1 matching bottom input) */}
      <div className="p-4 border-t border-border bg-card/40 backdrop-blur-sm shrink-0">
        <ChatInput
          onSend={onSend}
          isLoading={isLoading}
          disabled={readyDocumentsCount === 0}
        />
        <div className="flex items-center justify-between mt-2 text-[10px] text-text-muted px-1">
          <span>Click on citation chips `[1]` to jump into the document view and highlighted excerpt.</span>
          <span>Press Enter ↵ to send</span>
        </div>
      </div>
    </div>
  );
}
