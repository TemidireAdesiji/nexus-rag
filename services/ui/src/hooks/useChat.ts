import { useCallback, useState } from "react";
import type { ConversationMessage, SearchMode } from "../types";
import { submitInquiry } from "../lib/api";
import { useSocket } from "./useSocket";

interface UseChatReturn {
  messages: ConversationMessage[];
  setMessages: React.Dispatch<React.SetStateAction<ConversationMessage[]>>;
  loading: boolean;
  error: string | null;
  clearError: () => void;
  strategy: string;
  setStrategy: (s: string) => void;
  sendMessage: (question: string) => Promise<void>;
  cacheHit: boolean;
  connectionStatus: string;
  streamingMessage: ConversationMessage | null;
  availableStrategies: SearchMode[];
  setAvailableStrategies: React.Dispatch<React.SetStateAction<SearchMode[]>>;
}

export function useChat(sessionId: string | null): UseChatReturn {
  const [messages, setMessages] = useState<ConversationMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [strategy, setStrategy] = useState("auto");
  const [cacheHit, setCacheHit] = useState(false);
  const [availableStrategies, setAvailableStrategies] = useState<SearchMode[]>(
    [],
  );

  const handleStreamComplete = useCallback((message: ConversationMessage) => {
    setMessages((prev) => [...prev, message]);
    setLoading(false);
  }, []);

  const {
    connectionStatus,
    sendViaSocket,
    streamingMessage,
    streamError,
    isStreaming,
  } = useSocket(handleStreamComplete);

  const sendMessage = useCallback(
    async (question: string) => {
      if (!sessionId || !question.trim()) return;

      const userMessage: ConversationMessage = {
        role: "user",
        content: question.trim(),
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, userMessage]);
      setError(null);
      setLoading(true);
      setCacheHit(false);

      if (connectionStatus === "connected") {
        sendViaSocket(question.trim(), strategy, sessionId);
        return;
      }

      try {
        const result = await submitInquiry(question.trim(), strategy, sessionId);
        const assistantMessage: ConversationMessage = {
          role: "assistant",
          content: result.answer,
          timestamp: new Date().toISOString(),
          sources: result.sources,
          traceSteps: result.traceSteps,
        };
        setMessages((prev) => [...prev, assistantMessage]);
        setCacheHit(result.apiKeys.length === 0 && result.documentCount > 0);
      } catch (err) {
        const message =
          err instanceof Error ? err.message : "An unexpected error occurred";
        setError(message);
      } finally {
        setLoading(false);
      }
    },
    [sessionId, strategy, connectionStatus, sendViaSocket],
  );

  const clearError = useCallback(() => setError(null), []);

  const combinedError = error || streamError || null;
  const combinedLoading = loading || isStreaming;

  return {
    messages,
    setMessages,
    loading: combinedLoading,
    error: combinedError,
    clearError,
    strategy,
    setStrategy,
    sendMessage,
    cacheHit,
    connectionStatus,
    streamingMessage,
    availableStrategies,
    setAvailableStrategies,
  };
}
