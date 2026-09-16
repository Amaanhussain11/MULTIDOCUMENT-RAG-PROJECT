import React, { useState } from "react";
import { DocumentCard } from "./DocumentCard";
import { Skeleton } from "../ui/Skeleton";
import { Modal } from "../ui/Modal";
import { Button } from "../ui/Button";
import { Files, AlertTriangle, Search, Filter } from "lucide-react";
import { Input } from "../ui/Input";

export function DocumentList({
  documents = [],
  isLoading = false,
  onDelete,
  onOpenUpload,
}) {
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [isDeleting, setIsDeleting] = useState(false);

  // Filter documents by search and status
  const filteredDocuments = documents.filter((doc) => {
    const matchesSearch = doc.document_name
      ?.toLowerCase()
      .includes(searchQuery.toLowerCase());
    const matchesStatus =
      statusFilter === "ALL" || doc.status?.toUpperCase() === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const handleDeleteConfirm = async () => {
    if (!deleteTarget) return;
    setIsDeleting(true);
    try {
      await onDelete(deleteTarget.id);
      setDeleteTarget(null);
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <div className="space-y-4">
      {/* Search and Filters Bar */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-text-muted" />
          <Input
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search documents..."
            className="pl-9"
          />
        </div>

        {/* Status Filter Chips */}
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 sm:pb-0">
          {["ALL", "READY", "PROCESSING", "FAILED"].map((status) => (
            <button
              key={status}
              onClick={() => setStatusFilter(status)}
              className={`px-2.5 py-1 text-xs rounded-md font-medium border transition-colors ${
                statusFilter === status
                  ? "bg-card-elevated border-primary text-text-primary"
                  : "bg-card border-border text-text-secondary hover:text-text-primary"
              }`}
            >
              {status}
            </button>
          ))}
        </div>
      </div>

      {/* Loading Skeletons */}
      {isLoading && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              className="p-4 rounded-xl bg-card border border-border space-y-3"
            >
              <div className="flex items-center gap-3">
                <Skeleton className="h-9 w-9 rounded-lg" />
                <div className="space-y-1.5 flex-1">
                  <Skeleton className="h-4 w-3/4" />
                  <Skeleton className="h-3 w-1/3" />
                </div>
              </div>
              <Skeleton className="h-3 w-1/2 pt-2" />
            </div>
          ))}
        </div>
      )}

      {/* Empty State (Section 2.8) */}
      {!isLoading && documents.length === 0 && (
        <div className="flex flex-col items-center justify-center p-12 rounded-xl bg-card border border-border text-center">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-card-elevated border border-border text-text-muted mb-4">
            <Files className="h-6 w-6" />
          </div>
          <h3 className="text-base font-semibold text-text-primary">
            No documents yet
          </h3>
          <p className="mt-1 text-xs text-text-secondary max-w-sm">
            Upload your first documents to start asking questions about them.
          </p>
          <div className="mt-5">
            <Button onClick={onOpenUpload}>Upload Documents</Button>
          </div>
        </div>
      )}

      {/* No search results */}
      {!isLoading && documents.length > 0 && filteredDocuments.length === 0 && (
        <div className="p-8 rounded-xl bg-card border border-border text-center text-xs text-text-secondary">
          No documents matching your search criteria.
        </div>
      )}

      {/* Documents Grid */}
      {!isLoading && filteredDocuments.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredDocuments.map((doc) => (
            <DocumentCard
              key={doc.document_id}
              document={doc}
              onDelete={(id, name) => setDeleteTarget({ id, name })}
            />
          ))}
        </div>
      )}

      {/* Delete Confirmation Modal */}
      <Modal
        isOpen={Boolean(deleteTarget)}
        onClose={() => !isDeleting && setDeleteTarget(null)}
        title="Delete Document"
        description="Are you sure you want to permanently remove this document from the vector store?"
      >
        <div className="space-y-4">
          <div className="p-3 rounded-lg bg-status-error/10 border border-status-error/20 flex items-start gap-2.5 text-xs text-rose-300">
            <AlertTriangle className="h-4 w-4 shrink-0 text-status-error mt-0.5" />
            <div>
              <span className="font-semibold">{deleteTarget?.name}</span> will be deleted along with all its chunk embeddings. This cannot be undone.
            </div>
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <Button
              variant="secondary"
              onClick={() => setDeleteTarget(null)}
              disabled={isDeleting}
            >
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={handleDeleteConfirm}
              isLoading={isDeleting}
            >
              Delete Permanently
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
