import React, { type FC, useState, useRef, type KeyboardEvent } from "react";
import {
  Box,
  TextField,
  IconButton,
  Tooltip,
  CircularProgress,
} from "@mui/material";
import SendIcon from "@mui/icons-material/Send";
import AttachFileIcon from "@mui/icons-material/AttachFile";
import { ingestDocument } from "../../lib/api";

interface MessageInputProps {
  onSend: (message: string) => void;
  onFileUploaded?: (message: string) => void;
  disabled: boolean;
}

export const MessageInput: FC<MessageInputProps> = ({
  onSend,
  onFileUploaded,
  disabled,
}) => {
  const [value, setValue] = useState("");
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleSend = () => {
    const trimmed = value.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setValue("");
  };

  const handleKeyDown = (event: KeyboardEvent<HTMLDivElement>) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      handleSend();
    }
  };

  const handleFileClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setUploading(true);
    try {
      const result = await ingestDocument(file);
      onFileUploaded?.(result.message || `Uploaded: ${file.name}`);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Upload failed";
      onFileUploaded?.(`Upload error: ${message}`);
    } finally {
      setUploading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    }
  };

  return (
    <Box
      sx={{
        display: "flex",
        alignItems: "flex-end",
        gap: 1,
        p: 2,
        borderTop: 1,
        borderColor: "divider",
        bgcolor: "background.paper",
      }}
    >
      <input
        ref={fileInputRef}
        type="file"
        hidden
        accept=".pdf,.txt,.md,.csv,.json,.docx"
        onChange={handleFileChange}
      />
      <Tooltip title="Upload document">
        <span>
          <IconButton
            onClick={handleFileClick}
            disabled={disabled || uploading}
            size="small"
            sx={{ color: "text.secondary" }}
          >
            {uploading ? (
              <CircularProgress size={20} />
            ) : (
              <AttachFileIcon />
            )}
          </IconButton>
        </span>
      </Tooltip>
      <TextField
        fullWidth
        multiline
        maxRows={6}
        placeholder="Ask a question..."
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={handleKeyDown}
        disabled={disabled}
        variant="outlined"
        size="small"
        sx={{
          "& .MuiOutlinedInput-root": {
            borderRadius: 2,
            bgcolor: "action.hover",
          },
        }}
      />
      <Tooltip title="Send message">
        <span>
          <IconButton
            onClick={handleSend}
            disabled={disabled || !value.trim()}
            color="primary"
            sx={{
              bgcolor: "primary.main",
              color: "primary.contrastText",
              "&:hover": { bgcolor: "primary.dark" },
              "&.Mui-disabled": { bgcolor: "action.disabledBackground" },
              width: 40,
              height: 40,
            }}
          >
            <SendIcon fontSize="small" />
          </IconButton>
        </span>
      </Tooltip>
    </Box>
  );
};
