import { useState, useEffect, useCallback, useRef } from "react";
import { api } from "../services/api";

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
      setIsBackendConnected(false);
      setDocuments([]);
      setError(err.message || "Unable to connect to backend server.");
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Poll for document processing status updates
  useEffect(() => {
    fetchDocuments();

    pollingRef.current = setInterval(() => {
      // If backend is connected, re-fetch active documents
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
      await api.uploadDocuments(files);
      setIsBackendConnected(true);
      await fetchDocuments();
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
