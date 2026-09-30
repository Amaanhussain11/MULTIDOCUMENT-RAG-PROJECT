import React, { useState } from "react";
import {
  Plus,
  Search,
  FileText,
  Trash2,
  HardDrive,
  BookOpen,
  Quote,
  CheckSquare,
  Square,
  Eye,
} from "lucide-react";
import { Badge } from "../ui/Badge";
import { formatBytes, getFileTypeLabel } from "../../utils/formatters";
import { cn } from "../../utils/cn";

export function DocumentSidebar({
  documents = [],
  selectedDocId,
  onSelectDoc,
  onOpenUpload,
  onDeleteDoc,
  selectedDocIdsForScope = [],
  onToggleDocScope,
  onSelectAllScope,
  className = "",
}) {
  const [searchQuery, setSearchQuery] = useState("");

  const filteredDocuments = documents.filter((doc) =>
    doc.document_name?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const totalBytes = documents.reduce((acc, doc) => acc + (doc.file_size || 0), 0);
  const totalPages = documents.reduce((acc, doc) => acc + (doc.page_count || (doc.status === "READY" ? 15 : 0)), 0);
  const totalChunks = documents.reduce((acc, doc) => acc + (doc.chunk_count || 0), 0);


  const allSelected =
    documents.length > 0 &&
    documents.every((d) => selectedDocIdsForScope.includes(d.document_id));

  // File extension badge colors
  const extColors = {
    PDF: "text-red-400 bg-red-500/10 border-red-500/20",
    DOCX: "text-blue-400 bg-blue-500/10 border-blue-500/20",
    TXT: "text-amber-400 bg-amber-500/10 border-amber-500/20",
  };

  return (
    <aside
      className={cn(
        "flex flex-col h-full bg-card border-r border-border select-none text-text-primary",
        className
      )}
    >
      {/* Sidebar Header (Screenshot 1 matching) */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-border bg-card/80">
        <div className="flex items-center gap-2">
          <span className="text-xs uppercase tracking-wider font-bold text-text-primary">
            Knowledge Base
          </span>
          <span className="text-[11px] font-mono px-1.5 py-0.2 rounded-full bg-card-elevated border border-border text-text-secondary">
            {documents.length}
          </span>
        </div>

        <div className="flex items-center gap-1">
          <button
            onClick={onOpenUpload}
            className="p-1 rounded-md text-text-secondary hover:text-primary hover:bg-card-elevated transition-colors cursor-pointer"
            title="Upload Document"
          >
            <Plus className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* Search Input */}
      <div className="p-3 border-b border-border/70">
        <div className="relative">
          <Search className="absolute left-2.5 top-2 h-3.5 w-3.5 text-text-muted" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search documents..."
            className="w-full h-8 pl-8 pr-2 text-xs rounded-md bg-[#181B22] border border-border text-text-primary placeholder:text-text-muted focus:outline-none focus:border-primary transition-colors"
          />
        </div>

        {/* Bulk Scope Toggle */}
        {documents.length > 0 && (
          <div className="flex items-center justify-between mt-2 pt-1 px-1 text-[11px] text-text-muted">
            <button
              onClick={onSelectAllScope}
              className="flex items-center gap-1.5 hover:text-text-primary transition-colors cursor-pointer"
            >
              {allSelected ? (
                <CheckSquare className="h-3 w-3 text-primary" />
              ) : (
                <Square className="h-3 w-3" />
              )}
              <span>Query All</span>
            </button>
            <span>
              {selectedDocIdsForScope.length} of {documents.length} selected
            </span>
          </div>
        )}
      </div>

      {/* Document List */}
      <div className="flex-1 overflow-y-auto p-2 space-y-1">
        {filteredDocuments.length === 0 ? (
          <div className="p-6 text-center text-xs text-text-muted">
            {documents.length === 0
              ? "No documents in Knowledge Base. Click [+] above to upload."
              : "No matching documents found."}
          </div>
        ) : (
          filteredDocuments.map((doc) => {
            const isSelected = selectedDocId === doc.document_id;
            const isScoped = selectedDocIdsForScope.includes(doc.document_id);
            const ext = getFileTypeLabel(doc.document_name, doc.file_type);

            return (
              <div
                key={doc.document_id}
                onClick={() => onSelectDoc(doc)}
                className={cn(
                  "group relative flex items-center justify-between p-2 rounded-lg border transition-all duration-150 cursor-pointer text-xs",
                  isSelected
                    ? "bg-card-elevated border-primary/50 text-text-primary shadow-sm"
                    : "bg-transparent border-transparent hover:bg-card-hover hover:border-border text-text-secondary"
                )}
              >
                <div className="flex items-center gap-2 min-w-0 pr-1">
                  {/* Context Scope Checkbox */}
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      onToggleDocScope(doc.document_id);
                    }}
                    className="p-0.5 text-text-muted hover:text-primary transition-colors shrink-0"
                    title={
                      isScoped
                        ? "Included in chat context scope"
                        : "Excluded from chat context scope"
                    }
                  >
                    {isScoped ? (
                      <CheckSquare className="h-3.5 w-3.5 text-primary" />
                    ) : (
                      <Square className="h-3.5 w-3.5" />
                    )}
                  </button>

                  {/* File Type Pill */}
                  <span
                    className={cn(
                      "font-mono text-[10px] font-bold px-1.5 py-0.5 rounded border shrink-0",
                      extColors[ext] || "text-primary bg-primary/10 border-primary/20"
                    )}
                  >
                    {ext}
                  </span>

                  {/* Filename & size */}
                  <div className="min-w-0">
                    <p
                      className="font-medium text-text-primary truncate"
                      title={doc.document_name}
                    >
                      {doc.document_name}
                    </p>
                    <p className="text-[10px] text-text-muted">
                      {formatBytes(doc.file_size)}
                    </p>
                  </div>
                </div>

                {/* Status or Delete */}
                <div className="flex items-center gap-1 shrink-0">
                  <Badge status={doc.status} size="xs" />

                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      onDeleteDoc(doc.document_id, doc.document_name);
                    }}
                    className="opacity-0 group-hover:opacity-100 p-1 text-text-muted hover:text-status-error hover:bg-status-error/10 rounded transition-all"
                    title="Delete document"
                  >
                    <Trash2 className="h-3 w-3" />
                  </button>
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Bottom Metadata & Usage Footer (Screenshot 1 matching) */}
      <div className="p-3 border-t border-border bg-[#09090B] text-[11px] text-text-muted space-y-1.5 shrink-0">
        <div className="flex items-center justify-between">
          <span className="flex items-center gap-1.5 text-text-secondary">
            <HardDrive className="h-3 w-3 text-primary" /> Usage
          </span>
          <span className="font-mono font-medium text-text-primary">
            {formatBytes(totalBytes)}
          </span>
        </div>

        <div className="flex items-center justify-between">
          <span className="flex items-center gap-1.5 text-text-secondary">
            <BookOpen className="h-3 w-3 text-primary" /> Total Pages
          </span>
          <span className="font-mono font-medium text-text-primary">
            {totalPages}
          </span>
        </div>

        <div className="flex items-center justify-between">
          <span className="flex items-center gap-1.5 text-text-secondary">
            <Quote className="h-3 w-3 text-primary" /> Chunks Indexed
          </span>
          <span className="font-mono font-medium text-text-primary">
            {totalChunks}
          </span>
        </div>
      </div>
    </aside>
  );
}
