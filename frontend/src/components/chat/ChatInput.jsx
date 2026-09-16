import React, { useState, useRef, useEffect } from "react";
import { ArrowUp, CornerDownLeft } from "lucide-react";
import { Button } from "../ui/Button";

export function ChatInput({ onSend, isLoading = false, disabled = false }) {
  const [question, setQuestion] = useState("");
  const textareaRef = useRef(null);

  const handleSubmit = (e) => {
    e?.preventDefault();
    if (!question.trim() || isLoading || disabled) return;
    onSend(question.trim());
    setQuestion("");
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${Math.min(
        textareaRef.current.scrollHeight,
        180
      )}px`;
    }
  }, [question]);

  return (
    <form
      onSubmit={handleSubmit}
      className="relative flex items-end gap-2 p-2 rounded-xl bg-card border border-border focus-within:border-primary focus-within:ring-1 focus-within:ring-primary transition-all duration-150 shadow-lg shadow-black/20"
    >
      <textarea
        ref={textareaRef}
        rows={1}
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={
          disabled
            ? "Upload documents first to begin querying..."
            : "Ask a question about your documents... (Press Enter to send)"
        }
        disabled={disabled || isLoading}
        className="flex-1 max-h-44 bg-transparent px-3 py-1.5 text-sm text-text-primary placeholder:text-text-muted focus:outline-none resize-none disabled:opacity-50"
      />

      <div className="flex items-center gap-1.5 shrink-0 pb-0.5">
        <Button
          type="submit"
          size="sm"
          disabled={disabled || isLoading || !question.trim()}
          isLoading={isLoading}
          className="h-8 w-8 !p-0 rounded-lg"
          aria-label="Send query"
        >
          <ArrowUp className="h-4 w-4" />
        </Button>
      </div>
    </form>
  );
}
