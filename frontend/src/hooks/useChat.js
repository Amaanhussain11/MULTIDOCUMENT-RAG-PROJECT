import { useState } from "react";
import { api } from "../services/api";

export function useChat(isBackendConnected = true) {
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content:
        "Hello! I am your Multi-Document RAG assistant. Ask me questions about your uploaded documents, and I'll generate answers strictly grounded in their retrieved contents with source citations.",
      sources: [],
    },
  ]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const sendMessage = async (question) => {
    if (!question.trim() || isLoading) return;

    setError(null);
    const userMessage = { role: "user", content: question };

    // Placeholder loading assistant message
    const loadingAssistantMessage = {
      role: "assistant",
      content: "",
      isLoading: true,
      sources: [],
    };

    setMessages((prev) => [...prev, userMessage, loadingAssistantMessage]);
    setIsLoading(true);

    try {
      if (isBackendConnected) {
        const response = await api.sendChatQuery(question);
        setMessages((prev) => {
          const updated = [...prev];
          updated[updated.length - 1] = {
            role: "assistant",
            content: response.answer,
            sources: response.sources || [],
            isLoading: false,
          };
          return updated;
        });
      } else {
        // Interactive simulation for demo preview
        await new Promise((resolve) => setTimeout(resolve, 1400));
        setMessages((prev) => {
          const updated = [...prev];
          updated[updated.length - 1] = {
            role: "assistant",
            content: `Based on your indexed documents, here is the synthesis regarding "${question}":\n\n1. The documents establish a modular pipeline combining FastAPI, Gemini 3.7 Flash, and Qdrant vector retrieval.\n2. Concurrency is bounded during ingestion to ensure high reliability across PDF, DOCX, and TXT inputs.\n3. Grounded generation ensures claims are strictly supported by verified citations.`,
            sources: [
              {
                document: "Annual_AI_Research_Report_2026.pdf",
                page: 14,
                chunk_text:
                  "Grounded generation verifies all factual claims against top-k retrieved semantic chunks before returning final synthesis to the user.",
              },
              {
                document: "Engineering_System_Architecture.docx",
                page: 3,
                chunk_text:
                  "Bounded asynchronous concurrency is enforced with worker pools to avoid API rate limiting during batch document ingestion.",
              },
            ],
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
