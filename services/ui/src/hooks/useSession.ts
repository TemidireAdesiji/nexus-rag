import { useCallback, useEffect, useState } from "react";
import type { ConversationRecord, ConversationMessage } from "../types";
import {
  openConversation,
  listConversations,
  loadConversation,
  closeConversation,
} from "../lib/api";

const SESSION_KEY = "nexusrag_session_id";

interface UseSessionReturn {
  sessionId: string | null;
  sessions: ConversationRecord[];
  sessionsLoading: boolean;
  createSession: () => Promise<string>;
  loadSession: (id: string) => Promise<ConversationMessage[]>;
  deleteSession: (id: string) => Promise<void>;
  refreshSessions: () => Promise<void>;
}

export function useSession(): UseSessionReturn {
  const [sessionId, setSessionId] = useState<string | null>(() =>
    localStorage.getItem(SESSION_KEY),
  );
  const [sessions, setSessions] = useState<ConversationRecord[]>([]);
  const [sessionsLoading, setSessionsLoading] = useState(false);

  const persistSession = useCallback((id: string | null) => {
    setSessionId(id);
    if (id) {
      localStorage.setItem(SESSION_KEY, id);
    } else {
      localStorage.removeItem(SESSION_KEY);
    }
  }, []);

  const refreshSessions = useCallback(async () => {
    setSessionsLoading(true);
    try {
      const list = await listConversations();
      setSessions(list);
    } catch {
      setSessions([]);
    } finally {
      setSessionsLoading(false);
    }
  }, []);

  const createSession = useCallback(async (): Promise<string> => {
    const { sessionId: newId } = await openConversation();
    persistSession(newId);
    await refreshSessions();
    return newId;
  }, [persistSession, refreshSessions]);

  const loadSession = useCallback(
    async (id: string): Promise<ConversationMessage[]> => {
      const detail = await loadConversation(id);
      persistSession(id);
      return detail.messages;
    },
    [persistSession],
  );

  const deleteSession = useCallback(
    async (id: string) => {
      await closeConversation(id);
      if (sessionId === id) {
        persistSession(null);
      }
      await refreshSessions();
    },
    [sessionId, persistSession, refreshSessions],
  );

  useEffect(() => {
    refreshSessions();
  }, [refreshSessions]);

  return {
    sessionId,
    sessions,
    sessionsLoading,
    createSession,
    loadSession,
    deleteSession,
    refreshSessions,
  };
}
