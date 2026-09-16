import React from "react";
import { FileText, Trash2, Calendar } from "lucide-react";
import { Badge } from "../ui/Badge";
import { formatBytes, formatDate, getFileTypeLabel } from "../../utils/formatters";
import { cn } from "../../utils/cn";

export function DocumentCard({ document, onDelete, isDeleting = false }) {
  const {
    document_id,
    document_name,
    file_type,
    file_size,
    status,
    created_at,
  } = document;

  const fileExt = getFileTypeLabel(document_name, file_type);

  // Subtle color distinction for file types
  const extColors = {
    PDF: "text-red-400 bg-red-400/10 border-red-400/20",
    DOCX: "text-blue-400 bg-blue-400/10 border-blue-400/20",
    TXT: "text-amber-400 bg-amber-400/10 border-amber-400/20",
  };

  return (
    <div className="group relative flex flex-col justify-between p-4 rounded-xl bg-card border border-border hover:border-border-active transition-all duration-150 hover:bg-card-hover/90">
      <div className="space-y-3">
        {/* Top Header: File Icon + Status Badge */}
        <div className="flex items-start justify-between gap-2">
          <div className="flex items-center gap-2.5 min-w-0">
            <div
              className={cn(
                "flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border font-mono text-[11px] font-semibold",
                extColors[fileExt] || "text-primary bg-primary/10 border-primary/20"
              )}
            >
              {fileExt}
            </div>
            <div className="min-w-0">
              <h4
                className="text-sm font-semibold text-text-primary truncate"
                title={document_name}
              >
                {document_name}
              </h4>
              <p className="text-[11px] text-text-muted">
                {formatBytes(file_size)}
              </p>
            </div>
          </div>

          <Badge status={status} size="sm" />
        </div>

        {/* Date & Metadata */}
        <div className="flex items-center gap-1.5 text-[11px] text-text-muted pt-1">
          <Calendar className="h-3 w-3" />
          <span>{formatDate(created_at)}</span>
        </div>
      </div>

      {/* Footer Actions */}
      <div className="flex items-center justify-between pt-3 mt-3 border-t border-border/60">
        <span className="text-[11px] font-mono text-text-muted truncate max-w-[150px]">
          ID: {document_id ? document_id.slice(0, 8) : "—"}
        </span>

        <button
          onClick={() => onDelete(document_id, document_name)}
          disabled={isDeleting}
          className="p-1.5 rounded-md text-text-muted hover:text-status-error hover:bg-status-error/10 transition-colors disabled:opacity-40"
          title="Delete document"
          aria-label={`Delete ${document_name}`}
        >
          <Trash2 className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
}
