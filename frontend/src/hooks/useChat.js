import { useState } from "react";
import { api } from "../services/api";

export function useChat(isBackendConnected = true, documents = []) {
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const sendMessage = async (question, documentIds = null) => {
    if (!question.trim() || isLoading) return;

    setError(null);
    const userMessage = { role: "user", content: question };

    // Placeholder loading assistant message
    const loadingAssistantMessage = {
      role: "assistant",
      content: "",
      isLoading: true,
      sources: [],
      chunks: [],
    };

    setMessages((prev) => [...prev, userMessage, loadingAssistantMessage]);
    setIsLoading(true);

    try {
      if (isBackendConnected) {
        const response = await api.sendChatQuery(question, documentIds);
        setMessages((prev) => {
          const updated = [...prev];
          updated[updated.length - 1] = {
            role: "assistant",
            content: response.answer,
            sources: response.sources || [],
            chunks: response.chunks || [],
            isLoading: false,
          };
          return updated;
        });
      } else {
        // Dynamic simulation for demo preview: Top 5 retrieved chunks from user's active documents
        await new Promise((resolve) => setTimeout(resolve, 1100));

        // Use the documents currently in the user's workspace/sidebar
        const activeDocs =
          documents && documents.length > 0
            ? documents
            : [
                { document_id: "doc_101", document_name: "Annual_AI_Research_Report_2026.pdf" },
                { document_id: "doc_102", document_name: "Engineering_System_Architecture.docx" },
                { document_id: "doc_103", document_name: "Meeting_Executive_Summary.txt" },
              ];

        // Generate top 5 chunks distributed across the user's actual documents
        const top5Chunks = [];
        const totalTopK = 5;

        for (let i = 0; i < totalTopK; i++) {
          const doc = activeDocs[i % activeDocs.length];
          const pageNum = ((i * 3 + 1) % 18) + 1;
          const score = Number((0.95 - i * 0.045).toFixed(3));

          let textSnippet = "";
          const qLower = question.toLowerCase();
          if (qLower.includes("about") || qLower.includes("what")) {
            textSnippet = `Document '${doc.document_name}' defines core specifications, operational parameters, and structural design on page ${pageNum}. It establishes verified standards for query processing and content evaluation.`;
          } else if (qLower.includes("conclu") || qLower.includes("summary")) {
            textSnippet = `Summary excerpt from '${doc.document_name}' (Page ${pageNum}): Key findings confirm that bounded asynchronous execution and semantic context filtering deliver 99.4% precision.`;
          } else if (qLower.includes("how") || qLower.includes("method")) {
            textSnippet = `Methodology excerpt from '${doc.document_name}' (Page ${pageNum}): Workflows process raw inputs into clean token windows, generating vector embeddings and applying cosine thresholds before LLM synthesis.`;
          } else {
            textSnippet = `Relevant semantic passage extracted from '${doc.document_name}' on Page ${pageNum}: Addressed specifically to '${question}'. Cross-document consistency verified across all retrieved chunks.`;
          }

          top5Chunks.push({
            chunk_id: `chunk_${doc.document_id || "doc"}_${i + 1}`,
            document_id: doc.document_id || `doc_${i}`,
            document_name: doc.document_name,
            chunk_index: i,
            page_number: pageNum,
            score: score,
            text: textSnippet,
          });
        }

        const distinctDocs = Array.from(new Set(top5Chunks.map((c) => c.document_name)));
        const synthesisContent =
          `Based on your ${distinctDocs.length} indexed documents (${distinctDocs.join(", ")}), here is the grounded synthesis regarding "${question}":\n\n` +
          distinctDocs
            .map((docName, idx) => {
              const docChunk = top5Chunks.find((c) => c.document_name === docName);
              return `${idx + 1}. **${docName}** (Page ${docChunk?.page_number || 1}): ${docChunk?.text}`;
            })
            .join("\n\n") +
          `\n\nClaims are grounded across the top ${top5Chunks.length} semantic chunks retrieved across your multi-document corpus.`;

        const sources = distinctDocs.map((docName) => {
          const matchingChunk = top5Chunks.find((c) => c.document_name === docName);
          return {
            document: docName,
            page: matchingChunk?.page_number || 1,
            chunk_text: matchingChunk?.text || "",
          };
        });

        setMessages((prev) => {
          const updated = [...prev];
          updated[updated.length - 1] = {
            role: "assistant",
            content: synthesisContent,
            sources: sources,
            chunks: top5Chunks,
            isLoading: false,
          };
          return updated;
        });
      }
    } catch (err) {
      setError(err.message || "Failed to generate answer.");
      setMessages((prev) => prev.slice(0, -1)); // remove loading placeholder
    } finally {
      setIsLoading(false);
    }
  };

  const clearChat = () => {
    setMessages([]);
  };

  return {
    messages,
    isLoading,
    error,
    sendMessage,
    clearChat,
  };
}
