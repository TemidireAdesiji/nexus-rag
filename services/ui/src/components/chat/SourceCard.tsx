import { type FC, useState } from "react";
import {
  Card,
  CardContent,
  CardActionArea,
  Typography,
  Collapse,
  Box,
  Chip,
  LinearProgress,
} from "@mui/material";
import DescriptionOutlinedIcon from "@mui/icons-material/DescriptionOutlined";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import type { DocumentSource } from "../../types";

interface SourceCardProps {
  source: DocumentSource;
  index: number;
}

export const SourceCard: FC<SourceCardProps> = ({ source, index }) => {
  const [expanded, setExpanded] = useState(false);
  const relevancePercent = Math.round(source.relevance * 100);

  const relevanceColor =
    relevancePercent >= 80
      ? "success"
      : relevancePercent >= 50
        ? "warning"
        : "error";

  return (
    <Card
      variant="outlined"
      sx={{
        bgcolor: "background.paper",
        border: 1,
        borderColor: "divider",
        transition: "border-color 0.2s",
        "&:hover": { borderColor: "primary.main" },
      }}
    >
      <CardActionArea onClick={() => setExpanded((prev) => !prev)}>
        <CardContent sx={{ py: 1.5, "&:last-child": { pb: 1.5 } }}>
          <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
            <DescriptionOutlinedIcon
              fontSize="small"
              sx={{ color: "primary.light" }}
            />
            <Typography
              variant="body2"
              fontWeight={600}
              sx={{ flex: 1, overflow: "hidden", textOverflow: "ellipsis" }}
            >
              Source {index + 1}: {source.origin}
            </Typography>
            <Chip
              label={`${relevancePercent}%`}
              size="small"
              color={relevanceColor}
              variant="outlined"
            />
            <ExpandMoreIcon
              sx={{
                transform: expanded ? "rotate(180deg)" : "none",
                transition: "transform 0.2s",
                color: "text.secondary",
              }}
            />
          </Box>
          <Box sx={{ mt: 0.75 }}>
            <LinearProgress
              variant="determinate"
              value={relevancePercent}
              color={relevanceColor}
              sx={{ height: 3, borderRadius: 1 }}
            />
          </Box>
        </CardContent>
      </CardActionArea>
      <Collapse in={expanded}>
        <CardContent sx={{ pt: 0, pb: 1.5, "&:last-child": { pb: 1.5 } }}>
          <Typography
            variant="body2"
            color="text.secondary"
            sx={{
              whiteSpace: "pre-wrap",
              fontFamily: "'Fira Code', monospace",
              fontSize: "0.8rem",
              bgcolor: "action.hover",
              p: 1.5,
              borderRadius: 1,
              maxHeight: 200,
              overflow: "auto",
            }}
          >
            {source.excerpt}
          </Typography>
        </CardContent>
      </Collapse>
    </Card>
  );
};
