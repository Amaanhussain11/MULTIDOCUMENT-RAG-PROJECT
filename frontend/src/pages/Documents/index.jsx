import React, { useState } from "react";
import { Container } from "../../components/layout/Container";
import { DocumentList } from "../../components/documents/DocumentList";
import { UploadDropzone } from "../../components/documents/UploadDropzone";
import { Modal } from "../../components/ui/Modal";
import { Button } from "../../components/ui/Button";
import { Plus, Files, CheckCircle2, Clock } from "lucide-react";
import { formatBytes } from "../../utils/formatters";

export function DocumentsPage({
  documents = [],
  isLoading = false,
  isUploading = false,
  onUpload,
  onDelete,
}) {
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);

  const totalBytes = documents.reduce((acc, doc) => acc + (doc.file_size || 0), 0);
  const readyCount = documents.filter((d) => d.status === "READY").length;
  const processingCount = documents.filter(
    (d) => d.status === "PROCESSING" || d.status === "QUEUED"
  ).length;

  const handleUploadComplete = async (files) => {
    await onUpload(files);
    setIsUploadModalOpen(false);
  };

  return (
    <Container size="content" className="py-8 space-y-8">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-text-primary">
            Document Library
          </h1>
          <p className="mt-1 text-xs sm:text-sm text-text-secondary">
            Upload PDF, DOCX, and TXT files for semantic chunking and RAG querying.
          </p>
        </div>

        <Button
          onClick={() => setIsUploadModalOpen(true)}
          icon={Plus}
          className="self-start sm:self-auto"
        >
          Upload Documents
        </Button>
      </div>

      {/* Metrics Bar */}
      <div className="grid grid-cols-3 gap-3 sm:gap-4">
        <div className="p-3.5 sm:p-4 rounded-xl bg-card border border-border">
          <div className="flex items-center gap-2 text-xs text-text-muted mb-1">
            <Files className="h-3.5 w-3.5 text-text-secondary" />
            <span>Total Documents</span>
          </div>
          <div className="text-xl sm:text-2xl font-bold text-text-primary">
            {documents.length}
          </div>
        </div>

        <div className="p-3.5 sm:p-4 rounded-xl bg-card border border-border">
          <div className="flex items-center gap-2 text-xs text-text-muted mb-1">
            <CheckCircle2 className="h-3.5 w-3.5 text-status-success" />
            <span>Indexed & Ready</span>
          </div>
          <div className="text-xl sm:text-2xl font-bold text-text-primary">
            {readyCount}
          </div>
        </div>

        <div className="p-3.5 sm:p-4 rounded-xl bg-card border border-border">
          <div className="flex items-center gap-2 text-xs text-text-muted mb-1">
            <Clock className="h-3.5 w-3.5 text-primary" />
            <span>Total Volume</span>
          </div>
          <div className="text-xl sm:text-2xl font-bold text-text-primary">
            {formatBytes(totalBytes)}
          </div>
        </div>
      </div>

      {/* Main Document Listing */}
      <DocumentList
        documents={documents}
        isLoading={isLoading}
        onDelete={onDelete}
        onOpenUpload={() => setIsUploadModalOpen(true)}
      />

      {/* Upload Modal Dialog */}
      <Modal
        isOpen={isUploadModalOpen}
        onClose={() => !isUploading && setIsUploadModalOpen(false)}
        title="Upload Documents"
        description="Select multiple files to process and index into Qdrant"
        maxWidth="max-w-xl"
      >
        <UploadDropzone
          onUpload={handleUploadComplete}
          isUploading={isUploading}
        />
      </Modal>
    </Container>
  );
}
