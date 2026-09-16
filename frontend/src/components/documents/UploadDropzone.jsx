import React, { useState, useRef } from "react";
import { UploadCloud, File, AlertCircle, CheckCircle2, X } from "lucide-react";
import { Button } from "../ui/Button";
import { formatBytes } from "../../utils/formatters";
import { SUPPORTED_EXTENSIONS, MAX_FILE_SIZE_BYTES, MAX_FILE_SIZE_MB } from "../../constants";
import { cn } from "../../utils/cn";

export function UploadDropzone({ onUpload, isUploading = false }) {
  const [isDragOver, setIsDragOver] = useState(false);
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [errorMessage, setErrorMessage] = useState("");
  const inputRef = useRef(null);

  const validateFiles = (fileList) => {
    const valid = [];
    const errors = [];

    Array.from(fileList).forEach((file) => {
      const ext = "." + file.name.split(".").pop().toLowerCase();
      if (!SUPPORTED_EXTENSIONS.includes(ext)) {
        errors.push(`"${file.name}" is unsupported. Only PDF, DOCX, and TXT are allowed.`);
        return;
      }
      if (file.size > MAX_FILE_SIZE_BYTES) {
        errors.push(`"${file.name}" exceeds the ${MAX_FILE_SIZE_MB}MB size limit.`);
        return;
      }
      // Check duplicate
      if (valid.some((f) => f.name === file.name && f.size === file.size)) {
        return;
      }
      valid.push(file);
    });

    if (errors.length > 0) {
      setErrorMessage(errors[0]);
    } else {
      setErrorMessage("");
    }

    return valid;
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragOver(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer?.files?.length) {
      const valid = validateFiles(e.dataTransfer.files);
      setSelectedFiles((prev) => [...prev, ...valid]);
    }
  };

  const handleFileInput = (e) => {
    if (e.target.files?.length) {
      const valid = validateFiles(e.target.files);
      setSelectedFiles((prev) => [...prev, ...valid]);
    }
  };

  const removeFile = (index) => {
    setSelectedFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const handleUploadSubmit = async () => {
    if (selectedFiles.length === 0 || isUploading) return;
    try {
      await onUpload(selectedFiles);
      setSelectedFiles([]);
      setErrorMessage("");
    } catch (err) {
      setErrorMessage(err.message || "Upload failed");
    }
  };

  return (
    <div className="w-full space-y-4">
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
        className={cn(
          "relative flex flex-col items-center justify-center p-8 rounded-xl border border-dashed transition-all duration-200 cursor-pointer bg-card/60",
          isDragOver
            ? "border-primary bg-primary/5 shadow-inner"
            : "border-border hover:border-border-active hover:bg-card-hover/80"
        )}
      >
        <input
          ref={inputRef}
          type="file"
          multiple
          accept=".pdf,.docx,.txt,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document,text/plain"
          onChange={handleFileInput}
          className="hidden"
        />

        <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-card-elevated border border-border text-primary mb-3">
          <UploadCloud className="h-6 w-6" />
        </div>

        <p className="text-sm font-medium text-text-primary text-center">
          <span className="text-primary hover:text-primary-hover font-semibold">Click to upload</span> or drag and drop
        </p>
        <p className="mt-1 text-xs text-text-muted text-center">
          PDF, DOCX, or TXT (up to {MAX_FILE_SIZE_MB}MB each)
        </p>
      </div>

      {errorMessage && (
        <div className="flex items-center gap-2 p-3 text-xs rounded-lg bg-status-error/10 border border-status-error/20 text-rose-400">
          <AlertCircle className="h-4 w-4 shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}

      {selectedFiles.length > 0 && (
        <div className="space-y-3 p-4 rounded-xl bg-card border border-border">
          <div className="flex items-center justify-between text-xs text-text-secondary pb-2 border-b border-border/60">
            <span>Ready for upload ({selectedFiles.length} files)</span>
            <Button
              size="sm"
              variant="ghost"
              onClick={() => setSelectedFiles([])}
              className="text-xs h-7 px-2"
            >
              Clear All
            </Button>
          </div>

          <ul className="space-y-2 max-h-48 overflow-y-auto pr-1">
            {selectedFiles.map((file, idx) => (
              <li
                key={`${file.name}-${idx}`}
                className="flex items-center justify-between p-2.5 rounded-lg bg-card-elevated border border-border text-xs"
              >
                <div className="flex items-center gap-2.5 truncate">
                  <File className="h-4 w-4 text-primary shrink-0" />
                  <span className="font-medium text-text-primary truncate">{file.name}</span>
                  <span className="text-[11px] text-text-muted shrink-0">
                    ({formatBytes(file.size)})
                  </span>
                </div>
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    removeFile(idx);
                  }}
                  className="p-1 text-text-muted hover:text-text-primary transition-colors"
                >
                  <X className="h-3.5 w-3.5" />
                </button>
              </li>
            ))}
          </ul>

          <div className="pt-2">
            <Button
              onClick={handleUploadSubmit}
              isLoading={isUploading}
              disabled={isUploading}
              className="w-full"
            >
              {isUploading ? "Uploading & Processing..." : `Upload ${selectedFiles.length} Documents`}
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
