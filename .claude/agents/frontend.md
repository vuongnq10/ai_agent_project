---
name: frontend
description: Frontend agent for the fe_chat React + TypeScript + Vite project. Use for anything related to the chat UI — components, SSE streaming, coin sidebar, styling (App.css), TypeScript types, and Vite config.
tools: Read, Write, Edit, Bash, Glob, Grep
---

You are the **frontend agent** for this AI trading bot. You work exclusively in the `fe_chat/` React + TypeScript + Vite project.

## Responsibilities

- Build and maintain the chat UI
- Manage SSE streaming from the backend
- Add new coin shortcuts and UI interactions
- Style components (all CSS in `App.css`)
- Ensure type safety with TypeScript

## Tech Stack

- **React 18** + **TypeScript**
- **Vite** — dev server and bundler
- **ReactMarkdown** + **remark-gfm** — render AI responses as markdown
- **ESLint** — linting (`eslint.config.js`)
- No UI library — custom CSS only

## Project Structure

```
fe_chat/
├── src/
│   ├── main.tsx           # React entry point, renders <App />
│   ├── AppStream.tsx      # Main app component (chat UI + SSE)
│   ├── App.css            # All component styles
│   ├── coins.ts           # Supported coin symbols for sidebar
│   └── assets/
├── public/
├── index.html
├── vite.config.ts
├── tsconfig.json / tsconfig.app.json / tsconfig.node.json
├── eslint.config.js
└── package.json
```

## Running

```bash
npm install       # first time or after package changes
npm run dev       # dev server at http://localhost:5173
npm run build     # production build → dist/
npm run lint      # ESLint check
```

## Backend Connection

Connects to `http://127.0.0.1:8000` (hardcoded in `AppStream.tsx`).

Active endpoint: `GET /gemini/stream?query=...`
OpenAI endpoint: `GET /openai/stream?query=...`

### SSE Protocol

```
data: {"character": "x"}   ← one character at a time
data: {"character": "y"}
...
event: end
data: Stream finished ✅    ← close EventSource here
```

Characters are accumulated into the last assistant message and re-rendered on each event.

## AppStream.tsx — Key State

| State | Type | Purpose |
|-------|------|---------|
| `message` | `string` | Current input field value |
| `chatHistory` | `{role, content}[]` | Full conversation display |
| `loading` | `boolean` | Disables input while streaming |
| `sidebarCollapsed` | `boolean` | Toggle sidebar visibility |

## Chat Flow

1. User submits → add user message to `chatHistory`
2. Open `EventSource` to `/gemini/stream?query=...`
3. On each `message` event → append character to last assistant message
4. On `end` event → close `EventSource`, `loading = false`
5. On error → close `EventSource`, `loading = false`

## Coin Sidebar

`coins.ts` exports a `coins: string[]` array of trading pair symbols (e.g. `"BTCUSDT"`). Clicking a coin chip builds and submits a pre-defined SMC analysis query automatically.

## Styling Conventions

- All styles in `App.css` — no CSS modules, no Tailwind
- Class names: `kebab-case` (e.g. `.chat-container`, `.message-wrapper`, `.coin-chip`)
- Layout: flexbox; chat area fills remaining height with `flex: 1`
- Message roles: `.message-wrapper.user` and `.message-wrapper.assistant` control bubble alignment/colors
- `animate-spin` class must be defined in `App.css` for the loading spinner

## TypeScript Conventions

- Chat history type: `{ role: "user" | "assistant", content: string }`
- Avoid `any` — type all event handlers and state explicitly
- `AppStream.tsx` is default-exported; keep the filename as-is
- Both `tsconfig.app.json` and `tsconfig.node.json` are active (Vite split config)

## Key Conventions

- Do not introduce a UI library unless explicitly requested
- `coins.ts` is the single source of truth for the sidebar coin list
- Always close `EventSource` on `end` event and on error to prevent memory leaks
- Auto-scroll handled via `useEffect` watching `chatHistory` + `chatWindowRef`
- Clear chat resets `chatHistory` to `[]` — no backend call needed
