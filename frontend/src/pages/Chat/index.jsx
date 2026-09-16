import React from "react";
import { Container } from "../../components/layout/Container";
import { ChatContainer } from "../../components/chat/ChatContainer";

export function ChatPage({
  messages,
  isLoading,
  error,
  readyDocumentsCount,
  onSend,
}) {
  return (
    <Container size="layout" className="py-6">
      <ChatContainer
        messages={messages}
        isLoading={isLoading}
        error={error}
        readyDocumentsCount={readyDocumentsCount}
        onSend={onSend}
      />
    </Container>
  );
}
