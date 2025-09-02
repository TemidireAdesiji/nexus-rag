# NexusRAG UI

The UI is a single-page React application that provides a conversational chat interface for the NexusRAG platform. It communicates with the Gateway via HTTP and WebSocket for real-time streaming.

---

## Features

- Real-time chat with token-by-token streaming via WebSocket
- Retrieval strategy selector (vector, combined, expanded, decomposed)
- Source chunk viewer with relevance scores after each response
- Conversation history sidebar with resume and delete actions
- Responsive layout built with Material UI
- Dark and light theme support

---

## Technology Stack

- **React 18** -- Component framework
- **Vite** -- Build tool and dev server
- **TypeScript** -- Type safety
- **Material UI (MUI)** -- Component library and theming
- **WebSocket API** -- Real-time communication with the Gateway

---

## Quick Start

### With Docker

```bash
# From the project root
docker compose up ui
```

The UI is served at `http://localhost:3000`.

### Without Docker

```bash
cd services/ui

# Install dependencies
npm install

# Start the development server
npm run dev
```

The dev server starts on port 3000 with hot module replacement.

---

## Configuration

All configuration is set at build time via Vite environment variables (prefixed with `VITE_`):

| Variable | Default | Description |
|----------|---------|-------------|
| `VITE_GATEWAY_URL` | `http://localhost:5000` | Gateway API base URL |
| `VITE_GATEWAY_WS_URL` | `ws://localhost:5000` | Gateway WebSocket URL |
| `VITE_DATA_API_URL` | `http://localhost:3456` | Data API base URL |
| `VITE_APP_TITLE` | `NexusRAG` | Application title in the header |
| `VITE_DEFAULT_STRATEGY` | `vector` | Default retrieval strategy |
| `VITE_ENABLE_SOURCE_VIEW` | `true` | Show source chunks in the interface |
| `VITE_MAX_MESSAGE_LENGTH` | `4000` | Maximum characters per user message |

Set these variables before building:

```bash
VITE_GATEWAY_URL=https://api.nexusrag.example.com npm run build
```

---

## Project Structure

```
src/
  components/
    Chat/             # Chat message list, input bar, streaming display
    Sidebar/          # Conversation history, strategy selector
    Sources/          # Source chunk viewer with scores
    Layout/           # App shell, header, responsive container
  hooks/
    useChat.ts        # Chat state management and message handling
    useWebSocket.ts   # WebSocket connection lifecycle
    useConversations.ts # Conversation CRUD operations
  services/
    api.ts            # HTTP client for Gateway and Data API
    websocket.ts      # WebSocket client with reconnection logic
  theme.ts            # MUI theme configuration (light/dark)
  App.tsx             # Root component
  main.tsx            # Entry point
public/
  favicon.svg
index.html
```

---

## Available Scripts

| Command | Description |
|---------|-------------|
| `npm run dev` | Start development server with HMR |
| `npm run build` | Build for production |
| `npm run preview` | Preview the production build locally |
| `npm run lint` | Run ESLint |
| `npm run format` | Format code with Prettier |
| `npm test` | Run unit tests with Vitest |
| `npm run test:e2e` | Run end-to-end tests with Playwright |

---

## Building for Production

```bash
# Set environment variables for your production URLs
VITE_GATEWAY_URL=https://api.nexusrag.example.com \
VITE_GATEWAY_WS_URL=wss://api.nexusrag.example.com \
VITE_DATA_API_URL=https://data.nexusrag.example.com \
npm run build
```

The output is written to `dist/`. The build is a static bundle served by NGINX in the Docker image.

---

## Docker

The Dockerfile uses a multi-stage build:

1. **Stage 1 (build):** Installs dependencies and runs `npm run build`.
2. **Stage 2 (serve):** Copies the `dist/` output into an NGINX image with a custom `nginx.conf`.

```bash
# Build the image
docker build -t nexusrag-ui \
  --build-arg VITE_GATEWAY_URL=https://api.nexusrag.example.com \
  --build-arg VITE_GATEWAY_WS_URL=wss://api.nexusrag.example.com \
  .

# Run
docker run -p 3000:3000 nexusrag-ui
```

The NGINX configuration handles:
- Serving static assets with cache headers
- SPA fallback (all routes serve `index.html`)
- Gzip compression
- Security headers

---

## Theming

The MUI theme is defined in `src/theme.ts`. To customize:

```typescript
// src/theme.ts
import { createTheme } from '@mui/material/styles';

export const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',  // Change to your brand color
    },
  },
  typography: {
    fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
  },
});
```

The theme supports both light and dark mode. The user's preference is detected from the system setting and can be toggled in the UI header.

---

## WebSocket Protocol

The UI connects to `${VITE_GATEWAY_WS_URL}/ws/chat` and exchanges JSON messages:

1. **Send:** `{ "type": "chat", "payload": { "query": "...", "conversation_id": "...", "strategy": "..." } }`
2. **Receive tokens:** `{ "type": "token", "payload": { "content": "..." } }`
3. **Receive completion:** `{ "type": "done", "payload": { "sources": [...], "tokens": {...} } }`

The WebSocket client in `src/services/websocket.ts` handles automatic reconnection with exponential backoff (1s, 2s, 4s, up to 30s).

---

## Testing

### Unit Tests

```bash
npm test
```

Tests use Vitest and React Testing Library. Test files are co-located with components (`Component.test.tsx`).

### End-to-End Tests

```bash
# Start services first
docker compose up -d

# Run Playwright tests
npm run test:e2e
```

E2E tests cover:
- Sending a message and receiving a streamed response
- Switching retrieval strategies
- Viewing source chunks
- Creating and resuming conversations
- Error states (gateway unreachable, WebSocket disconnect)
