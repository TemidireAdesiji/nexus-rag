import { type FC, useEffect, useRef } from "react";
import {
  Box,
  Typography,
  Avatar,
  Paper,
  CircularProgress,
  Stack,
  Chip,
} from "@mui/material";
import PersonIcon from "@mui/icons-material/Person";
import SmartToyOutlinedIcon from "@mui/icons-material/SmartToyOutlined";
import CachedIcon from "@mui/icons-material/Cached";
import ChatBubbleOutlineIcon from "@mui/icons-material/ChatBubbleOutline";
import type { ConversationMessage } from "../../types";
import { MarkdownRenderer } from "../shared/MarkdownRenderer";
import { SourceCard } from "./SourceCard";

interface MessageListProps {
  messages: ConversationMessage[];
  streamingMessage: ConversationMessage | null;
  loading: boolean;
  cacheHit: boolean;
}

export const MessageList: FC<MessageListProps> = ({
  messages,
  streamingMessage,
  loading,
  cacheHit,
}) => {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, streamingMessage?.content, loading]);

  if (messages.length === 0 && !streamingMessage && !loading) {
    return (
      <Box
        sx={{
          flex: 1,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          gap: 2,
          color: "text.secondary",
          p: 4,
        }}
      >
        <ChatBubbleOutlineIcon sx={{ fontSize: 56, opacity: 0.4 }} />
        <Typography variant="h6" fontWeight={500}>
          Start a conversation
        </Typography>
        <Typography variant="body2" textAlign="center" sx={{ maxWidth: 400 }}>
          Ask a question about your documents. The AI will search through
          ingested data and provide relevant answers with source references.
        </Typography>
      </Box>
    );
  }

  const allMessages = streamingMessage
    ? [...messages, streamingMessage]
    : messages;

  return (
    <Box
      sx={{
        flex: 1,
        overflow: "auto",
        px: { xs: 1.5, sm: 3 },
        py: 2,
      }}
    >
      {allMessages.map((msg, idx) => {
        const isUser = msg.role === "user";
        const isLast = idx === allMessages.length - 1;
        const isCurrentStreaming =
          isLast && streamingMessage !== null && !isUser;

        return (
          <Box
            key={`${msg.timestamp}-${idx}`}
            sx={{
              display: "flex",
              gap: 1.5,
              mb: 2.5,
              flexDirection: isUser ? "row-reverse" : "row",
              alignItems: "flex-start",
            }}
          >
            <Avatar
              sx={{
                width: 34,
                height: 34,
                bgcolor: isUser ? "primary.main" : "secondary.main",
                mt: 0.5,
              }}
            >
              {isUser ? (
                <PersonIcon fontSize="small" />
              ) : (
                <SmartToyOutlinedIcon fontSize="small" />
              )}
            </Avatar>
            <Paper
              elevation={0}
              sx={{
                px: 2,
                py: 1.5,
                maxWidth: { xs: "85%", sm: "72%", md: "65%" },
                borderRadius: 2.5,
                bgcolor: isUser ? "primary.dark" : "background.paper",
                border: isUser ? "none" : 1,
                borderColor: "divider",
              }}
            >
              {isUser ? (
                <Typography variant="body1" sx={{ whiteSpace: "pre-wrap" }}>
                  {msg.content}
                </Typography>
              ) : (
                <MarkdownRenderer content={msg.content} />
              )}

              {isCurrentStreaming && (
                <Box
                  sx={{ display: "flex", alignItems: "center", gap: 1, mt: 1 }}
                >
                  <CircularProgress size={14} />
                  <Typography variant="caption" color="text.secondary">
                    Generating...
                  </Typography>
                </Box>
              )}

              {!isUser && cacheHit && isLast && !isCurrentStreaming && (
                <Chip
                  icon={<CachedIcon />}
                  label="Cached response"
                  size="small"
                  variant="outlined"
                  color="info"
                  sx={{ mt: 1 }}
                />
              )}

              {msg.sources && msg.sources.length > 0 && (
                <Stack spacing={1} sx={{ mt: 1.5 }}>
                  <Typography
                    variant="caption"
                    color="text.secondary"
                    fontWeight={600}
                  >
                    Sources ({msg.sources.length})
                  </Typography>
                  {msg.sources.map((src, sIdx) => (
                    <SourceCard
                      key={`${src.origin}-${sIdx}`}
                      source={src}
                      index={sIdx}
                    />
                  ))}
                </Stack>
              )}

              <Typography
                variant="caption"
                color="text.disabled"
                sx={{
                  display: "block",
                  mt: 0.75,
                  textAlign: isUser ? "right" : "left",
                }}
              >
                {new Date(msg.timestamp).toLocaleTimeString()}
              </Typography>
            </Paper>
          </Box>
        );
      })}

      {loading && !streamingMessage && (
        <Box
          sx={{ display: "flex", gap: 1.5, mb: 2.5, alignItems: "flex-start" }}
        >
          <Avatar
            sx={{ width: 34, height: 34, bgcolor: "secondary.main", mt: 0.5 }}
          >
            <SmartToyOutlinedIcon fontSize="small" />
          </Avatar>
          <Paper
            elevation={0}
            sx={{
              px: 2.5,
              py: 2,
              borderRadius: 2.5,
              border: 1,
              borderColor: "divider",
              display: "flex",
              alignItems: "center",
              gap: 1.5,
            }}
          >
            <CircularProgress size={18} />
            <Typography variant="body2" color="text.secondary">
              Searching documents...
            </Typography>
          </Paper>
        </Box>
      )}

      <div ref={bottomRef} />
    </Box>
  );
};
