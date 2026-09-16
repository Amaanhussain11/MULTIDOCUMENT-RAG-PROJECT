import React, { useState } from "react";
import { FileText, ExternalLink } from "lucide-react";
import { Modal } from "../ui/Modal";

export function SourcePill({ source }) {
  const [isOpen, setIsOpen] = useState(false);
  const { document, page, chunk_text } = source;

  return (
    <>
      <button
        onClick={() => setIsOpen(true)}
        className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium bg-[#181B22] border border-border hover:border-primary/40 text-text-secondary hover:text-text-primary transition-all duration-150 group cursor-pointer"
        title={`View context from ${document}`}
      >
        <FileText className="h-3 w-3 text-primary group-hover:text-primary-hover shrink-0" />
        <span className="truncate max-w-[140px]">{document}</span>
        {page && (
          <span className="text-[11px] font-mono text-text-muted">
            • p.{page}
          </span>
        )}
        <ExternalLink className="h-2.5 w-2.5 opacity-40 group-hover:opacity-100 transition-opacity ml-0.5" />
      </button>

      <Modal
        isOpen={isOpen}
        onClose={() => setIsOpen(false)}
        title="Source Reference"
        description="Grounded citation retrieved from vector store"
      >
        <div className="space-y-3 text-xs">
          <div className="flex items-center justify-between p-3 rounded-lg bg-[#181B22] border border-border">
            <div className="flex items-center gap-2">
              <FileText className="h-4 w-4 text-primary" />
              <span className="font-semibold text-text-primary">{document}</span>
            </div>
            {page && (
              <span className="px-2 py-0.5 rounded bg-card border border-border font-mono text-[11px] text-text-secondary">
                Page {page}
              </span>
            )}
          </div>

          <div className="p-3 rounded-lg bg-card-hover border border-border/80 text-text-secondary space-y-2">
            <p className="text-[11px] uppercase tracking-wider font-semibold text-text-muted">
              Retrieved Context
            </p>
            <p className="text-xs leading-relaxed text-text-primary font-mono whitespace-pre-wrap">
              {chunk_text || `Content extracted from ${document} (Page ${page || 1}) was used by Gemini to formulate the grounded answer.`}
            </p>
          </div>
        </div>
      </Modal>
    </>
  );
}
