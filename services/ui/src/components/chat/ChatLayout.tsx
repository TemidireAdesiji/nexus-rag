import React, { type FC, useCallback, useEffect, useState } from "react";
import {
  AppBar,
  Toolbar,
  Typography,
  IconButton,
  Box,
  Tooltip,
  Chip,
  Snackbar,
  Alert,
} from "@mui/material";
import MenuIcon from "@mui/icons-material/Menu";
import InfoOutlinedIcon from "@mui/icons-material/InfoOutlined";
import WifiIcon from "@mui/icons-material/Wifi";
import WifiOffIcon from "@mui/icons-material/WifiOff";
import SyncIcon from "@mui/icons-material/Sync";
import { useChat } from "../../hooks/useChat";
import { useSession } from "../../hooks/useSession";
import { fetchSearchModes } from "../../lib/api";
import type { SearchMode } from "../../types";
import { MessageList } from "./MessageList";
import { MessageInput } from "./MessageInput";
import { StrategyPicker } from "./StrategyPicker";
import { SessionSidebar } from "../sessions/SessionSidebar";
import { SystemPanel } from "../system/SystemPanel";

const connectionIcons: Record<string, React.ReactElement> = {
  connected: <WifiIcon fontSize="small" />,
  disconnected: <WifiOffIcon fontSize="small" />,
  reconnecting: <SyncIcon fontSize="small" />,
};

const connectionColors: Record<string, string> = {
  connected: "success.main",
  disconnected: "error.main",
  reconnecting: "warning.main",
};

export const ChatLayout: FC = () => {
  const {
    sessionId,
    sessions,
    sessionsLoading,
    createSession,
    loadSession,
    deleteSession,
  } = useSession();

  const {
    messages,
    setMessages,
    loading,
    error,
    clearError,
    strategy,
    setStrategy,
    sendMessage,
    cacheHit,
    connectionStatus,
    streamingMessage,
    availableStrategies,
    setAvailableStrategies,
  } = useChat(sessionId);

  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [systemOpen, setSystemOpen] = useState(false);
  const [notification, setNotification] = useState<string | null>(null);

  useEffect(() => {
    fetchSearchModes()
      .then((modes: SearchMode[]) => {
        setAvailableStrategies(modes);
        if (modes.length > 0 && !modes.find((m) => m.id === strategy)) {
          setStrategy(modes[0].id);
        }
      })
      .catch(() => {
        setAvailableStrategies([
          {
            id: "auto",
            label: "Auto",
            summary: "Automatic strategy selection",
          },
        ]);
      });
  }, [setAvailableStrategies, setStrategy, strategy]);

  useEffect(() => {
    if (!sessionId) {
      createSession().catch(() =>
        setNotification("Failed to create a new session"),
      );
    }
  }, [sessionId, createSession]);

  const handleLoadSession = useCallback(
    async (id: string) => {
      try {
        const loadedMessages = await loadSession(id);
        setMessages(loadedMessages);
      } catch {
        setNotification("Failed to load session");
      }
    },
    [loadSession, setMessages],
  );

  const handleCreateSession = useCallback(async () => {
    try {
      await createSession();
      setMessages([]);
    } catch {
      setNotification("Failed to create session");
    }
  }, [createSession, setMessages]);

  const handleDeleteSession = useCallback(
    async (id: string) => {
      try {
        await deleteSession(id);
        if (id === sessionId) {
          setMessages([]);
        }
      } catch {
        setNotification("Failed to delete session");
      }
    },
    [deleteSession, sessionId, setMessages],
  );

  const handleFileUploaded = useCallback((message: string) => {
    setNotification(message);
  }, []);

  return (
    <Box sx={{ display: "flex", flexDirection: "column", height: "100vh" }}>
      <AppBar
        position="static"
        elevation={0}
        sx={{
          bgcolor: "background.paper",
          borderBottom: 1,
          borderColor: "divider",
        }}
      >
        <Toolbar sx={{ gap: 1 }}>
          <Tooltip title="Sessions">
            <IconButton
              edge="start"
              onClick={() => setSidebarOpen(true)}
              sx={{ color: "text.primary" }}
            >
              <MenuIcon />
            </IconButton>
          </Tooltip>

          <Typography
            variant="h6"
            fontWeight={800}
            sx={{
              background: "linear-gradient(135deg, #4fc3f7 0%, #66bb6a 100%)",
              WebkitBackgroundClip: "text",
              WebkitTextFillColor: "transparent",
              mr: 1,
            }}
          >
            NexusRAG
          </Typography>

          <Box sx={{ flex: 1 }} />

          <StrategyPicker
            value={strategy}
            onChange={setStrategy}
            strategies={availableStrategies}
            disabled={loading}
          />

          <Tooltip title={`Connection: ${connectionStatus}`}>
            <Chip
              icon={connectionIcons[connectionStatus]}
              label={connectionStatus}
              size="small"
              variant="outlined"
              sx={{
                color: connectionColors[connectionStatus],
                borderColor: connectionColors[connectionStatus],
                textTransform: "capitalize",
                display: { xs: "none", sm: "flex" },
              }}
            />
          </Tooltip>

          <Tooltip title="System info">
            <IconButton
              onClick={() => setSystemOpen(true)}
              sx={{ color: "text.primary" }}
            >
              <InfoOutlinedIcon />
            </IconButton>
          </Tooltip>
        </Toolbar>
      </AppBar>

      <Box
        sx={{
          flex: 1,
          display: "flex",
          flexDirection: "column",
          overflow: "hidden",
          bgcolor: "background.default",
        }}
      >
        <MessageList
          messages={messages}
          streamingMessage={streamingMessage}
          loading={loading}
          cacheHit={cacheHit}
        />
        <MessageInput
          onSend={sendMessage}
          onFileUploaded={handleFileUploaded}
          disabled={loading || !sessionId}
        />
      </Box>

      <SessionSidebar
        open={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        sessions={sessions}
        currentSessionId={sessionId}
        onCreateSession={handleCreateSession}
        onLoadSession={handleLoadSession}
        onDeleteSession={handleDeleteSession}
        loading={sessionsLoading}
      />

      <SystemPanel open={systemOpen} onClose={() => setSystemOpen(false)} />

      <Snackbar
        open={!!error}
        autoHideDuration={6000}
        onClose={clearError}
        anchorOrigin={{ vertical: "bottom", horizontal: "center" }}
      >
        <Alert severity="error" onClose={clearError} variant="filled">
          {error}
        </Alert>
      </Snackbar>

      <Snackbar
        open={!!notification}
        autoHideDuration={4000}
        onClose={() => setNotification(null)}
        anchorOrigin={{ vertical: "bottom", horizontal: "center" }}
      >
        <Alert
          severity="info"
          onClose={() => setNotification(null)}
          variant="filled"
        >
          {notification}
        </Alert>
      </Snackbar>
    </Box>
  );
};
