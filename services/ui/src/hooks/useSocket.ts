import { useCallback, useEffect, useRef, useState } from "react";
import { io, Socket } from "socket.io-client";
import type { ConversationMessage, DocumentSource, TraceStep } from "../types";

interface SocketChunk {
  token?: string;
  done?: boolean;
  sources?: DocumentSource[];
  traceSteps?: TraceStep[];
  error?: string;
}

type ConnectionStatus = "connected" | "disconnected" | "reconnecting";

interface UseSocketReturn {
  connectionStatus: ConnectionStatus;
  sendViaSocket: (
    question: string,
    strategy: string,
    sessionId: string,
  ) => void;
  streamingMessage: ConversationMessage | null;
  streamError: string | null;
  isStreaming: boolean;
}

export function useSocket(
  onMessageComplete: (message: ConversationMessage) => void,
): UseSocketReturn {
  const socketRef = useRef<Socket | null>(null);
  const [connectionStatus, setConnectionStatus] =
    useState<ConnectionStatus>("disconnected");
  const [streamingMessage, setStreamingMessage] =
    useState<ConversationMessage | null>(null);
  const [streamError, setStreamError] = useState<string | null>(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const contentBufferRef = useRef("");
  const onCompleteRef = useRef(onMessageComplete);
  onCompleteRef.current = onMessageComplete;

  useEffect(() => {
    const wsUrl = import.meta.env.VITE_WS_URL || window.location.origin;
    const socket = io(wsUrl, {
      path: "/ws/socket.io",
      transports: ["websocket", "polling"],
      reconnection: true,
      reconnectionAttempts: 10,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 5000,
    });

    socketRef.current = socket;

    socket.on("connect", () => setConnectionStatus("connected"));
    socket.on("disconnect", () => setConnectionStatus("disconnected"));
    socket.on("reconnect_attempt", () => setConnectionStatus("reconnecting"));
    socket.on("reconnect", () => setConnectionStatus("connected"));

    socket.on("chunk", (data: SocketChunk) => {
      if (data.error) {
        setStreamError(data.error);
        setIsStreaming(false);
        return;
      }

      if (data.token) {
        contentBufferRef.current += data.token;
        setStreamingMessage({
          role: "assistant",
          content: contentBufferRef.current,
          timestamp: new Date().toISOString(),
        });
      }

      if (data.done) {
        const finalMessage: ConversationMessage = {
          role: "assistant",
          content: contentBufferRef.current,
          timestamp: new Date().toISOString(),
          sources: data.sources,
          traceSteps: data.traceSteps,
        };
        setStreamingMessage(null);
        setIsStreaming(false);
        onCompleteRef.current(finalMessage);
        contentBufferRef.current = "";
      }
    });

    return () => {
      socket.disconnect();
    };
  }, []);

  const sendViaSocket = useCallback(
    (question: string, strategy: string, sessionId: string) => {
      if (!socketRef.current?.connected) {
        setStreamError("Socket is not connected. Please wait and try again.");
        return;
      }
      setStreamError(null);
      setIsStreaming(true);
      contentBufferRef.current = "";
      setStreamingMessage({
        role: "assistant",
        content: "",
        timestamp: new Date().toISOString(),
      });
      socketRef.current.emit("query", { question, strategy, session_id: sessionId });
    },
    [],
  );

  return { connectionStatus, sendViaSocket, streamingMessage, streamError, isStreaming };
}
