import { type FC, useEffect, useState } from "react";
import {
  Dialog,
  DialogTitle,
  DialogContent,
  IconButton,
  Typography,
  Box,
  Chip,
  Divider,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  CircularProgress,
  Alert,
} from "@mui/material";
import CloseIcon from "@mui/icons-material/Close";
import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import ErrorIcon from "@mui/icons-material/Error";
import WarningAmberIcon from "@mui/icons-material/WarningAmber";
import BuildCircleIcon from "@mui/icons-material/BuildCircle";
import MemoryIcon from "@mui/icons-material/Memory";
import StorageIcon from "@mui/icons-material/Storage";
import PeopleIcon from "@mui/icons-material/People";
import CachedIcon from "@mui/icons-material/Cached";
import type { WellnessReport, PlatformDetails } from "../../types";
import { checkWellness, fetchPlatformDetails } from "../../lib/api";

interface SystemPanelProps {
  open: boolean;
  onClose: () => void;
}

const statusConfig = {
  healthy: { icon: <CheckCircleIcon />, color: "success" as const, label: "Healthy" },
  degraded: { icon: <WarningAmberIcon />, color: "warning" as const, label: "Degraded" },
  unhealthy: { icon: <ErrorIcon />, color: "error" as const, label: "Unhealthy" },
};

export const SystemPanel: FC<SystemPanelProps> = ({ open, onClose }) => {
  const [wellness, setWellness] = useState<WellnessReport | null>(null);
  const [platform, setPlatform] = useState<PlatformDetails | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!open) return;

    setLoading(true);
    setError(null);

    Promise.all([checkWellness(), fetchPlatformDetails()])
      .then(([health, info]) => {
        setWellness(health);
        setPlatform(info);
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : "Failed to load system info");
      })
      .finally(() => setLoading(false));
  }, [open]);

  const status = wellness ? statusConfig[wellness.status] : null;

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="sm"
      fullWidth
      PaperProps={{
        sx: { borderRadius: 3, bgcolor: "background.default" },
      }}
    >
      <DialogTitle sx={{ display: "flex", alignItems: "center", gap: 1 }}>
        <MemoryIcon color="primary" />
        <Typography variant="h6" fontWeight={700} sx={{ flex: 1 }}>
          System Status
        </Typography>
        <IconButton onClick={onClose} size="small">
          <CloseIcon />
        </IconButton>
      </DialogTitle>
      <DialogContent dividers>
        {loading && (
          <Box sx={{ display: "flex", justifyContent: "center", py: 4 }}>
            <CircularProgress />
          </Box>
        )}

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        {wellness && status && (
          <>
            <Box sx={{ display: "flex", alignItems: "center", gap: 1.5, mb: 2 }}>
              <Chip
                icon={status.icon}
                label={status.label}
                color={status.color}
                variant="outlined"
                sx={{ fontWeight: 600 }}
              />
              <Typography variant="body2" color="text.secondary">
                {wellness.appName} &middot; {wellness.environment}
              </Typography>
            </Box>

            <List dense disablePadding>
              <ListItem>
                <ListItemIcon sx={{ minWidth: 36 }}>
                  <StorageIcon fontSize="small" color="primary" />
                </ListItemIcon>
                <ListItemText
                  primary="Pipeline"
                  secondary={wellness.pipelineReady ? "Ready" : "Not ready"}
                />
                {wellness.pipelineReady ? (
                  <CheckCircleIcon fontSize="small" color="success" />
                ) : (
                  <ErrorIcon fontSize="small" color="error" />
                )}
              </ListItem>
              <ListItem>
                <ListItemIcon sx={{ minWidth: 36 }}>
                  <StorageIcon fontSize="small" color="primary" />
                </ListItemIcon>
                <ListItemText
                  primary="Backend"
                  secondary={wellness.backendReachable ? "Reachable" : "Unreachable"}
                />
                {wellness.backendReachable ? (
                  <CheckCircleIcon fontSize="small" color="success" />
                ) : (
                  <ErrorIcon fontSize="small" color="error" />
                )}
              </ListItem>
              <ListItem>
                <ListItemIcon sx={{ minWidth: 36 }}>
                  <PeopleIcon fontSize="small" color="primary" />
                </ListItemIcon>
                <ListItemText
                  primary="Active Sessions"
                  secondary={String(wellness.activeSessions)}
                />
              </ListItem>
              <ListItem>
                <ListItemIcon sx={{ minWidth: 36 }}>
                  <CachedIcon fontSize="small" color="primary" />
                </ListItemIcon>
                <ListItemText
                  primary="Cache Entries"
                  secondary={String(wellness.cacheEntries)}
                />
              </ListItem>
            </List>
          </>
        )}

        {platform && (
          <>
            <Divider sx={{ my: 2 }} />
            <Typography variant="subtitle2" fontWeight={700} gutterBottom>
              Platform Details
            </Typography>
            <Box sx={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 1, mb: 2 }}>
              <InfoItem label="API Version" value={platform.apiVersion} />
              <InfoItem label="LLM Model" value={platform.llmModel} />
              <InfoItem label="Embedding" value={platform.embeddingModel} />
              <InfoItem label="Reranker" value={platform.rerankerModel} />
              <InfoItem label="Max Query" value={`${platform.maxQueryLength} chars`} />
              <InfoItem label="Environment" value={platform.environment} />
            </Box>

            {platform.availableTools.length > 0 && (
              <>
                <Typography variant="subtitle2" fontWeight={700} gutterBottom>
                  Available Tools
                </Typography>
                <Box sx={{ display: "flex", flexWrap: "wrap", gap: 0.75 }}>
                  {platform.availableTools.map((tool) => (
                    <Chip
                      key={tool}
                      icon={<BuildCircleIcon />}
                      label={tool}
                      size="small"
                      variant="outlined"
                    />
                  ))}
                </Box>
              </>
            )}
          </>
        )}
      </DialogContent>
    </Dialog>
  );
};

const InfoItem: FC<{ label: string; value: string }> = ({ label, value }) => (
  <Box
    sx={{
      bgcolor: "action.hover",
      borderRadius: 1,
      px: 1.5,
      py: 1,
    }}
  >
    <Typography variant="caption" color="text.secondary">
      {label}
    </Typography>
    <Typography variant="body2" fontWeight={500} noWrap>
      {value}
    </Typography>
  </Box>
);
