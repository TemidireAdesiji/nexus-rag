import { type FC } from "react";
import ReactMarkdown from "react-markdown";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { oneDark } from "react-syntax-highlighter/dist/esm/styles/prism";
import { Box, Typography, Link } from "@mui/material";

interface MarkdownRendererProps {
  content: string;
}

export const MarkdownRenderer: FC<MarkdownRendererProps> = ({ content }) => {
  return (
    <ReactMarkdown
      components={{
        p: ({ children }) => (
          <Typography variant="body1" sx={{ mb: 1, lineHeight: 1.7 }}>
            {children}
          </Typography>
        ),
        h1: ({ children }) => (
          <Typography variant="h5" fontWeight={700} sx={{ mt: 2, mb: 1 }}>
            {children}
          </Typography>
        ),
        h2: ({ children }) => (
          <Typography variant="h6" fontWeight={600} sx={{ mt: 2, mb: 1 }}>
            {children}
          </Typography>
        ),
        h3: ({ children }) => (
          <Typography
            variant="subtitle1"
            fontWeight={600}
            sx={{ mt: 1.5, mb: 0.5 }}
          >
            {children}
          </Typography>
        ),
        a: ({ href, children }) => (
          <Link href={href} target="_blank" rel="noopener noreferrer">
            {children}
          </Link>
        ),
        ul: ({ children }) => (
          <Box component="ul" sx={{ pl: 2.5, mb: 1 }}>
            {children}
          </Box>
        ),
        ol: ({ children }) => (
          <Box component="ol" sx={{ pl: 2.5, mb: 1 }}>
            {children}
          </Box>
        ),
        li: ({ children }) => (
          <Typography
            component="li"
            variant="body1"
            sx={{ mb: 0.3, lineHeight: 1.7 }}
          >
            {children}
          </Typography>
        ),
        blockquote: ({ children }) => (
          <Box
            sx={{
              borderLeft: 3,
              borderColor: "primary.main",
              pl: 2,
              py: 0.5,
              my: 1,
              bgcolor: "action.hover",
              borderRadius: "0 4px 4px 0",
            }}
          >
            {children}
          </Box>
        ),
        code: ({ ref: _ref, node: _node, className, children, ...rest }) => {
          const match = /language-(\w+)/.exec(className || "");
          const codeString = String(children).replace(/\n$/, "");

          if (match) {
            return (
              <Box sx={{ my: 1.5, borderRadius: 1, overflow: "hidden" }}>
                <SyntaxHighlighter
                  style={oneDark}
                  language={match[1]}
                  PreTag="div"
                  customStyle={{
                    margin: 0,
                    borderRadius: 4,
                    fontSize: "0.85rem",
                  }}
                >
                  {codeString}
                </SyntaxHighlighter>
              </Box>
            );
          }

          return (
            <Box
              component="code"
              sx={{
                bgcolor: "action.selected",
                px: 0.7,
                py: 0.2,
                borderRadius: 0.5,
                fontSize: "0.875em",
                fontFamily: "'Fira Code', 'Cascadia Code', monospace",
              }}
              {...rest}
            >
              {children}
            </Box>
          );
        },
        hr: () => (
          <Box
            component="hr"
            sx={{ border: "none", borderTop: 1, borderColor: "divider", my: 2 }}
          />
        ),
        table: ({ children }) => (
          <Box
            component="table"
            sx={{
              width: "100%",
              borderCollapse: "collapse",
              my: 1,
              "& th, & td": {
                border: 1,
                borderColor: "divider",
                px: 1.5,
                py: 0.75,
                textAlign: "left",
              },
              "& th": { bgcolor: "action.hover", fontWeight: 600 },
            }}
          >
            {children}
          </Box>
        ),
      }}
    >
      {content}
    </ReactMarkdown>
  );
};
