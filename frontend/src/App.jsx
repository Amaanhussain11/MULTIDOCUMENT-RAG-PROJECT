import React, { useState } from "react";
import { DocumentSidebar } from "./components/documents/DocumentSidebar";
import { ChatContainer } from "./components/chat/ChatContainer";
import { DocumentViewer } from "./components/viewer/DocumentViewer";
import { UploadDropzone } from "./components/documents/UploadDropzone";
import { Modal } from "./components/ui/Modal";
import { useDocuments } from "./hooks/useDocuments";
import { useChat } from "./hooks/useChat";
import {
  Layers,
  PanelLeftClose,
  PanelLeftOpen,
  PanelRightClose,
  PanelRightOpen,
  Upload,
  Files,
  Activity,
  Plus,
} from "lucide-react";
import { cn } from "./utils/cn";

export function App() {
  const {
    documents,
    isLoading: isDocsLoading,
    isUploading,
    isBackendConnected,
    uploadDocuments,
    deleteDocument,
  } = useDocuments();

  // Sidebar & Viewer pane toggles (3-Column Layout from Screenshot 1)
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [isViewerOpen, setIsViewerOpen] = useState(true);
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);

  // Active document & citation selection for the Document Viewer
  const [selectedDoc, setSelectedDoc] = useState(null);
  const [viewerPage, setViewerPage] = useState(14);
  const [highlightedChunk, setHighlightedChunk] = useState(
    "Grounded generation verifies all factual claims against top-k retrieved semantic chunks before returning final synthesis to the user."
  );

  // Set default selected document once documents load
  React.useEffect(() => {
    if (!selectedDoc && documents.length > 0) {
      setSelectedDoc(documents[0]);
    }
  }, [documents, selectedDoc]);

  // Context scope selection (which documents to include in RAG query)
  const [selectedDocIdsForScope, setSelectedDocIdsForScope] = useState([]);

  // Initialize all ready docs into scope by default
  React.useEffect(() => {
    if (documents.length > 0 && selectedDocIdsForScope.length === 0) {
      setSelectedDocIdsForScope(documents.map((d) => d.document_id));
    }
  }, [documents]);

  const toggleDocScope = (id) => {
    setSelectedDocIdsForScope((prev) =>
      prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id]
    );
  };

  const selectAllScope = () => {
    if (selectedDocIdsForScope.length === documents.length) {
      setSelectedDocIdsForScope([]);
    } else {
      setSelectedDocIdsForScope(documents.map((d) => d.document_id));
    }
  };

  const {
    messages,
    isLoading: isChatLoading,
    error: chatError,
    sendMessage,
  } = useChat(isBackendConnected);

  const readyDocumentsCount = documents.filter((d) => d.status === "READY").length;

  // Handler when user clicks a citation pill [1] in the chat response
  const handleCitationClick = (source) => {
    // Find matching document or use source document name
    const foundDoc = documents.find((d) => d.document_name === source.document);
    if (foundDoc) {
      setSelectedDoc(foundDoc);
    } else {
      setSelectedDoc({
        document_id: "cited_doc",
        document_name: source.document,
      });
    }

    setViewerPage(source.page || 1);
    setHighlightedChunk(source.chunk_text || "");
    setIsViewerOpen(true); // Ensure right panel is visible
  };

  // Handler when user clicks a document in the Knowledge Base sidebar
  const handleSelectDocFromSidebar = (doc) => {
    setSelectedDoc(doc);
    setViewerPage(1);
    setHighlightedChunk(null);
    setIsViewerOpen(true);
  };

  const handleUploadSubmit = async (files) => {
    await uploadDocuments(files);
    setIsUploadModalOpen(false);
  };

  return (
    <div className="flex flex-col h-screen w-screen overflow-hidden bg-background text-text-primary selection:bg-primary/20 selection:text-primary-hover">
      {/* Top Application Header (Desktop Window styling as seen in Screenshot 1) */}
      <header className="h-12 border-b border-border bg-card flex items-center justify-between px-4 shrink-0 select-none z-20">
        {/* Left: Window Dots & App Brand */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 mr-2">
            <span className="h-3 w-3 rounded-full bg-[#EF4444]/80 border border-[#DC2626]/60 inline-block" />
            <span className="h-3 w-3 rounded-full bg-[#F59E0B]/80 border border-[#D97706]/60 inline-block" />
            <span className="h-3 w-3 rounded-full bg-[#22C55E]/80 border border-[#16A34A]/60 inline-block" />
          </div>

          <div className="flex items-center gap-2">
            <div className="flex h-6 w-6 items-center justify-center rounded-md bg-primary/10 border border-primary/20 text-primary">
              <Layers className="h-3.5 w-3.5" />
            </div>
            <span className="text-xs font-bold tracking-tight text-text-primary">
              Multi-Document RAG
            </span>
          </div>

          {/* Sidebar Toggle */}
          <button
            onClick={() => setIsSidebarOpen((prev) => !prev)}
            className="p-1 rounded text-text-muted hover:text-text-primary hover:bg-card-elevated transition-colors ml-2"
            title={isSidebarOpen ? "Hide Knowledge Base" : "Show Knowledge Base"}
          >
            {isSidebarOpen ? (
              <PanelLeftClose className="h-4 w-4" />
            ) : (
              <PanelLeftOpen className="h-4 w-4" />
            )}
          </button>
        </div>

        {/* Center: Active Context / Document Label */}
        <div className="hidden md:flex items-center gap-2 px-3 py-1 rounded-full bg-card-elevated border border-border text-[11px] text-text-secondary">
          <span className="h-1.5 w-1.5 rounded-full bg-status-success animate-pulse" />
          <span>Knowledge Base Active:</span>
          <span className="font-semibold text-text-primary">
            {selectedDocIdsForScope.length} of {documents.length} Docs
          </span>
        </div>

        {/* Right: Actions & Viewer Toggle */}
        <div className="flex items-center gap-2">
          {/* Quick Upload Button */}
          <button
            onClick={() => setIsUploadModalOpen(true)}
            className="flex items-center gap-1 px-2.5 py-1 text-xs rounded-md bg-primary hover:bg-primary-hover text-white font-medium transition-colors cursor-pointer shadow-sm shadow-primary/20"
          >
            <Plus className="h-3.5 w-3.5" />
            <span>Upload</span>
          </button>

          {/* Toggle Document Viewer Pane */}
          <button
            onClick={() => setIsViewerOpen((prev) => !prev)}
            className={cn(
              "flex items-center gap-1 px-2.5 py-1 text-xs rounded-md border transition-colors cursor-pointer",
              isViewerOpen
                ? "bg-card-elevated border-primary/40 text-text-primary"
                : "bg-card border-border text-text-muted hover:text-text-primary"
            )}
            title={isViewerOpen ? "Hide Document Viewer" : "Show Document Viewer"}
          >
            {isViewerOpen ? (
              <PanelRightClose className="h-3.5 w-3.5 text-primary" />
            ) : (
              <PanelRightOpen className="h-3.5 w-3.5" />
            )}
            <span className="hidden sm:inline text-[11px]">Doc Viewer</span>
          </button>

          {/* API Health Pill */}
          <div
            className="flex items-center gap-1.5 px-2 py-0.5 rounded text-[10px] font-mono bg-card border border-border text-text-muted"
            title="FastAPI Backend Health"
          >
            <span
              className={cn(
                "h-1.5 w-1.5 rounded-full",
                isBackendConnected ? "bg-status-success" : "bg-status-warning"
              )}
            />
            <span>{isBackendConnected ? "API: 200" : "DEMO"}</span>
          </div>
        </div>
      </header>

      {/* Main 3-Column Workspace */}
      <div className="flex flex-1 overflow-hidden relative">
        {/* Column 1: Knowledge Base Sidebar (Screenshot 1 Left Pane) */}
        {isSidebarOpen && (
          <div className="w-64 sm:w-72 lg:w-80 h-full shrink-0 z-10">
            <DocumentSidebar
              documents={documents}
              selectedDocId={selectedDoc?.document_id}
              onSelectDoc={handleSelectDocFromSidebar}
              onOpenUpload={() => setIsUploadModalOpen(true)}
              onDeleteDoc={deleteDocument}
              selectedDocIdsForScope={selectedDocIdsForScope}
              onToggleDocScope={toggleDocScope}
              onSelectAllScope={selectAllScope}
            />
          </div>
        )}

        {/* Column 2: Conversational RAG Center Panel (Screenshot 1 Center Pane) */}
        <div className="flex-1 flex flex-col h-full min-w-0">
          <ChatContainer
            messages={messages}
            isLoading={isChatLoading}
            error={chatError}
            readyDocumentsCount={readyDocumentsCount}
            onSend={sendMessage}
            onCitationClick={handleCitationClick}
            scopedDocsCount={selectedDocIdsForScope.length}
          />
        </div>

        {/* Column 3: Interactive Document Viewer & Chunk Highlighter (Screenshot 1 Right Pane) */}
        {isViewerOpen && selectedDoc && (
          <div className="w-full sm:w-[420px] md:w-[480px] lg:w-[540px] xl:w-[600px] h-full shrink-0 z-10">
            <DocumentViewer
              selectedDocName={selectedDoc.document_name}
              initialPage={viewerPage}
              highlightedChunk={highlightedChunk}
              onClose={() => setIsViewerOpen(false)}
            />
          </div>
        )}
      </div>

      {/* Multi-Document Upload Modal Dialog */}
      <Modal
        isOpen={isUploadModalOpen}
        onClose={() => !isUploading && setIsUploadModalOpen(false)}
        title="Upload to Knowledge Base"
        description="Select PDF, DOCX, or TXT files to parse, chunk, embed, and index"
        maxWidth="max-w-xl"
      >
        <UploadDropzone
          onUpload={handleUploadSubmit}
          isUploading={isUploading}
        />
      </Modal>
    </div>
  );
}

export default App;
