import { useMemo, useState } from "react";
import {
  ThemeProvider,
  createTheme,
  CssBaseline,
  useMediaQuery,
} from "@mui/material";
import { ChatLayout } from "./components/chat/ChatLayout";
import { ErrorBoundary } from "./components/shared/ErrorBoundary";

function App() {
  const prefersDark = useMediaQuery("(prefers-color-scheme: dark)");
  const [mode] = useState<"light" | "dark">(prefersDark ? "dark" : "dark");

  const theme = useMemo(
    () =>
      createTheme({
        palette: {
          mode,
          primary: {
            main: "#4fc3f7",
            dark: "#0288d1",
            light: "#80d8ff",
            contrastText: "#0a1929",
          },
          secondary: {
            main: "#66bb6a",
            dark: "#338a3e",
            light: "#98ee99",
          },
          background:
            mode === "dark"
              ? {
                  default: "#0a1929",
                  paper: "#0f2744",
                }
              : {
                  default: "#f5f7fa",
                  paper: "#ffffff",
                },
          divider:
            mode === "dark" ? "rgba(79, 195, 247, 0.12)" : "rgba(0,0,0,0.12)",
          text:
            mode === "dark"
              ? {
                  primary: "#e3f2fd",
                  secondary: "#90caf9",
                  disabled: "rgba(227,242,253,0.4)",
                }
              : undefined,
        },
        typography: {
          fontFamily:
            "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
          h6: { fontWeight: 700 },
        },
        shape: {
          borderRadius: 8,
        },
        components: {
          MuiButton: {
            styleOverrides: {
              root: { textTransform: "none", fontWeight: 600 },
            },
          },
          MuiPaper: {
            styleOverrides: {
              root: {
                backgroundImage: "none",
              },
            },
          },
          MuiCssBaseline: {
            styleOverrides: {
              body: {
                scrollbarWidth: "thin",
                scrollbarColor:
                  mode === "dark"
                    ? "rgba(79,195,247,0.3) transparent"
                    : "rgba(0,0,0,0.2) transparent",
              },
            },
          },
        },
      }),
    [mode],
  );

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <ErrorBoundary>
        <ChatLayout />
      </ErrorBoundary>
    </ThemeProvider>
  );
}

export default App;
