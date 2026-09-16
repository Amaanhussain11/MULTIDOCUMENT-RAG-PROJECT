import { useState, useEffect, useCallback, useRef } from "react";
import { api } from "../services/api";

// Initial placeholder mock documents so the user sees a rich interactive preview even before the backend is booted
const DEMO_DOCUMENTS = [
  {
    document_id: "doc_101",
    document_name: "Annual_AI_Research_Report_2026.pdf",
    file_type: "application/pdf",
    file_size: 2450000,
    status: "READY",
    created_at: new Date(Date.now() - 3600000 * 2).toISOString(),
  },
  {
    document_id: "doc_102",
    document_name: "Engineering_System_Architecture.docx",
    file_type: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    file_size: 1120000,
    status: "READY",
    created_at: new Date(Date.now() - 3600000 * 5).toISOString(),
  },
  {
    document_id: "doc_103",
    document_name: "Meeting_Executive_Summary.txt",
    file_type: "text/plain",
    file_size: 34000,
    status: "PROCESSING",
    created_at: new Date(Date.now() - 60000).toISOString(),
  },
];

export function useDocuments() {
  const [documents, setDocuments] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState(null);
  const [isBackendConnected, setIsBackendConnected] = useState(null);
  const pollingRef = useRef(null);

  const fetchDocuments = useCallback(async () => {
    try {
      const data = await api.getDocuments();
      setDocuments(Array.isArray(data) ? data : data?.documents || []);
      setIsBackendConnected(true);
      setError(null);
    } catch (err) {
      // Backend not running yet: gracefully fall back to rich demo dataset
      setIsBackendConnected(false);
      setDocuments((prev) => (prev.length === 0 ? DEMO_DOCUMENTS : prev));
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Poll for document processing status updates
  useEffect(() => {
    fetchDocuments();

    pollingRef.current = setInterval(() => {
      // Automatically transition any local PROCESSING mock to READY after 6s if in demo mode
      setDocuments((prev) =>
        prev.map((doc) =>
          doc.status === "PROCESSING" ? { ...doc, status: "READY" } : doc
        )
      );

      // If backend was connected, re-fetch
      if (isBackendConnected) {
        fetchDocuments();
      }
    }, 5000);

    return () => clearInterval(pollingRef.current);
  }, [fetchDocuments, isBackendConnected]);

  const uploadDocuments = async (files) => {
    setIsUploading(true);
    setError(null);
    try {
      if (isBackendConnected) {
        await api.uploadDocuments(files);
        await fetchDocuments();
      } else {
        // Optimistic / Demo upload simulation
        const newDocs = Array.from(files).map((file, i) => ({
          document_id: `demo_${Date.now()}_${i}`,
          document_name: file.name,
          file_type: file.type || "text/plain",
          file_size: file.size,
          status: "PROCESSING",
          created_at: new Date().toISOString(),
        }));
        setDocuments((prev) => [...newDocs, ...prev]);

        // Transition to READY after 4 seconds
        setTimeout(() => {
          setDocuments((prev) =>
            prev.map((d) =>
              newDocs.some((n) => n.document_id === d.document_id)
                ? { ...d, status: "READY" }
                : d
            )
          );
        }, 4000);
      }
    } catch (err) {
      setError(err.message || "Failed to upload documents.");
      throw err;
    } finally {
      setIsUploading(false);
    }
  };

  const deleteDocument = async (id) => {
    try {
      if (isBackendConnected) {
        await api.deleteDocument(id);
      }
      setDocuments((prev) => prev.filter((d) => d.document_id !== id));
    } catch (err) {
      setError(err.message || "Failed to delete document.");
      throw err;
    }
  };

  return {
    documents,
    isLoading,
    isUploading,
    error,
    isBackendConnected,
    uploadDocuments,
    deleteDocument,
    refetch: fetchDocuments,
  };
}
