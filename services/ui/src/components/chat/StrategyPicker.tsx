import React, { type FC } from "react";
import {
  FormControl,
  Select,
  MenuItem,
  ListItemIcon,
  ListItemText,
  type SelectChangeEvent,
} from "@mui/material";
import AutoFixHighIcon from "@mui/icons-material/AutoFixHigh";
import SearchIcon from "@mui/icons-material/Search";
import AccountTreeIcon from "@mui/icons-material/AccountTree";
import TuneIcon from "@mui/icons-material/Tune";
import SmartToyIcon from "@mui/icons-material/SmartToy";
import type { SearchMode } from "../../types";

interface StrategyPickerProps {
  value: string;
  onChange: (strategy: string) => void;
  strategies: SearchMode[];
  disabled?: boolean;
}

const strategyIcons: Record<string, React.ReactElement> = {
  auto: <AutoFixHighIcon fontSize="small" />,
  semantic: <SearchIcon fontSize="small" />,
  hybrid: <AccountTreeIcon fontSize="small" />,
  keyword: <TuneIcon fontSize="small" />,
  agentic: <SmartToyIcon fontSize="small" />,
};

function getIcon(id: string): React.ReactElement {
  return strategyIcons[id] ?? <SearchIcon fontSize="small" />;
}

export const StrategyPicker: FC<StrategyPickerProps> = ({
  value,
  onChange,
  strategies,
  disabled = false,
}) => {
  const handleChange = (event: SelectChangeEvent) => {
    onChange(event.target.value);
  };

  if (strategies.length === 0) {
    return null;
  }

  return (
    <FormControl size="small" sx={{ minWidth: 160 }}>
      <Select
        value={value}
        onChange={handleChange}
        disabled={disabled}
        displayEmpty
        sx={{
          color: "inherit",
          ".MuiOutlinedInput-notchedOutline": { borderColor: "rgba(255,255,255,0.3)" },
          "&:hover .MuiOutlinedInput-notchedOutline": {
            borderColor: "rgba(255,255,255,0.5)",
          },
          "&.Mui-focused .MuiOutlinedInput-notchedOutline": {
            borderColor: "primary.light",
          },
          ".MuiSelect-icon": { color: "inherit" },
        }}
        renderValue={(selected) => {
          const found = strategies.find((s) => s.id === selected);
          return found?.label ?? "Select strategy";
        }}
      >
        {strategies.map((mode) => (
          <MenuItem key={mode.id} value={mode.id}>
            <ListItemIcon sx={{ minWidth: 32 }}>{getIcon(mode.id)}</ListItemIcon>
            <ListItemText primary={mode.label} secondary={mode.summary} />
          </MenuItem>
        ))}
      </Select>
    </FormControl>
  );
};
