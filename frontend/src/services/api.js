import { API_BASE_URL } from "../constants";

/**
 * Handles HTTP responses and normalizes error messages according to Section 12 of specification.md
 */
async function handleResponse(response) {
  if (!response.ok) {
    let errorDetails = {
      code: "UNKNOWN_ERROR",
      message: "An unexpected error occurred. Please try again.",
    };

    try {
      const data = await response.json();
      if (data?.error) {
        errorDetails = data.error;
      } else if (data?.detail) {
        errorDetails = {
          code: "REQUEST_ERROR",
          message: typeof data.detail === "string" ? data.detail : JSON.stringify(data.detail),
        };
      }
    } catch {
      errorDetails.message = response.statusText || `HTTP error ${response.status}`;
    }

    const err = new Error(errorDetails.message || "Request failed");
    err.code = errorDetails.code;
    err.status = response.status;
    throw err;
  }

  // Check for 204 No Content
  if (response.status === 204) {
    return null;
  }

  return response.json();
}

/**
 * Central API Service Layer (Section 3.4 & Section 6)
 */
export const api = {
  /**
   * Health Check: GET /api/v1/health
   */
  async checkHealth() {
    const res = await fetch(`${API_BASE_URL}/health`);
    return handleResponse(res);
  },

  /**
   * List Documents: GET /api/v1/documents
   */
  async getDocuments() {
    const res = await fetch(`${API_BASE_URL}/documents`);
    return handleResponse(res);
  },

  /**
   * Get Single Document: GET /api/v1/documents/{document_id}
   */
  async getDocument(documentId) {
    const res = await fetch(`${API_BASE_URL}/documents/${encodeURIComponent(documentId)}`);
    return handleResponse(res);
  },

  /**
   * Upload Multiple Documents: POST /api/v1/documents/upload
   * @param {File[]} files
   */
  async uploadDocuments(files) {
    const formData = new FormData();
    for (const file of files) {
      formData.append("files", file);
    }

    const res = await fetch(`${API_BASE_URL}/documents/upload`, {
      method: "POST",
      body: formData,
    });
    return handleResponse(res);
  },

  /**
   * Delete Document: DELETE /api/v1/documents/{document_id}
   */
  async deleteDocument(documentId) {
    const res = await fetch(`${API_BASE_URL}/documents/${encodeURIComponent(documentId)}`, {
      method: "DELETE",
    });
    return handleResponse(res);
  },

  /**
   * Query Documents via Chat: POST /api/v1/chat
   * @param {string} question
   */
  async sendChatQuery(question) {
    const res = await fetch(`${API_BASE_URL}/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ question }),
    });
    return handleResponse(res);
  },
};
