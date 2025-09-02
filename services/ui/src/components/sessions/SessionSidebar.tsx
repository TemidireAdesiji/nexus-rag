import { type FC } from "react";
import {
  Box,
  Drawer,
  List,
  ListItemButton,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Typography,
  Button,
  Divider,
  Tooltip,
  CircularProgress,
} from "@mui/material";
import AddCommentOutlinedIcon from "@mui/icons-material/AddCommentOutlined";
import DeleteOutlineIcon from "@mui/icons-material/DeleteOutline";
import ChatIcon from "@mui/icons-material/Chat";
import type { ConversationRecord } from "../../types";

interface SessionSidebarProps {
  open: boolean;
  onClose: () => void;
  sessions: ConversationRecord[];
  currentSessionId: string | null;
  onCreateSession: () => void;
  onLoadSession: (id: string) => void;
  onDeleteSession: (id: string) => void;
  loading: boolean;
}

export const SessionSidebar: FC<SessionSidebarProps> = ({
  open,
  onClose,
  sessions,
  currentSessionId,
  onCreateSession,
  onLoadSession,
  onDeleteSession,
  loading,
}) => {
  const drawerWidth = 300;

  return (
    <Drawer
      anchor="left"
      open={open}
      onClose={onClose}
      sx={{
        "& .MuiDrawer-paper": {
          width: drawerWidth,
          bgcolor: "background.default",
          borderRight: 1,
          borderColor: "divider",
        },
      }}
    >
      <Box sx={{ p: 2 }}>
        <Typography variant="h6" fontWeight={700} sx={{ mb: 1 }}>
          Sessions
        </Typography>
        <Button
          fullWidth
          variant="outlined"
          startIcon={<AddCommentOutlinedIcon />}
          onClick={() => {
            onCreateSession();
            onClose();
          }}
          sx={{ textTransform: "none", borderRadius: 2 }}
        >
          New Conversation
        </Button>
      </Box>
      <Divider />
      {loading ? (
        <Box sx={{ display: "flex", justifyContent: "center", py: 4 }}>
          <CircularProgress size={28} />
        </Box>
      ) : sessions.length === 0 ? (
        <Box sx={{ textAlign: "center", py: 4, px: 2 }}>
          <ChatIcon sx={{ fontSize: 40, color: "text.disabled", mb: 1 }} />
          <Typography variant="body2" color="text.secondary">
            No sessions yet. Start a new conversation.
          </Typography>
        </Box>
      ) : (
        <List sx={{ flex: 1, overflow: "auto", px: 1 }}>
          {sessions.map((session) => {
            const isActive = session.sessionId === currentSessionId;
            return (
              <ListItemButton
                key={session.sessionId}
                selected={isActive}
                onClick={() => {
                  onLoadSession(session.sessionId);
                  onClose();
                }}
                sx={{
                  borderRadius: 1.5,
                  mb: 0.5,
                  pr: 6,
                }}
              >
                <ListItemText
                  primary={
                    <Typography
                      variant="body2"
                      fontWeight={isActive ? 600 : 400}
                      noWrap
                    >
                      {session.sessionId.slice(0, 8)}...
                    </Typography>
                  }
                  secondary={
                    <Typography variant="caption" color="text.secondary">
                      {session.messageCount} messages &middot;{" "}
                      {new Date(session.createdAt).toLocaleDateString()}
                    </Typography>
                  }
                />
                <ListItemSecondaryAction>
                  <Tooltip title="Delete session">
                    <IconButton
                      edge="end"
                      size="small"
                      onClick={(e) => {
                        e.stopPropagation();
                        onDeleteSession(session.sessionId);
                      }}
                      sx={{
                        color: "text.secondary",
                        "&:hover": { color: "error.main" },
                      }}
                    >
                      <DeleteOutlineIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                </ListItemSecondaryAction>
              </ListItemButton>
            );
          })}
        </List>
      )}
    </Drawer>
  );
};
