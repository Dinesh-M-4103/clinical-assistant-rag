# Clinical Assistant — web app

React single-page app for chatting with a patient's PDF reports. Answers stream in with clickable
citations that open the exact PDF page; side panels show the retrieved evidence, the report library
and a trace of how each answer was produced. It talks to the FastAPI backend described in
[`docs/api-contract.md`](../docs/api-contract.md).

**Stack:** Vite · React 18 · TypeScript (strict) · Tailwind CSS 3 · Radix UI primitives · TanStack
Query · React Router · zustand · react-hook-form + zod · react-markdown · react-pdf · Vitest · MSW ·
Playwright.

## Run it

```bash
npm install
npm run dev          # http://localhost:5173, API at VITE_API_BASE_URL (default http://localhost:8000)
npm run dev:mock     # same UI against in-browser MSW mocks, no backend needed
```

| Script                | What it does                                                          |
| --------------------- | --------------------------------------------------------------------- |
| `npm run build`       | Type-check and produce a production bundle in `dist/`                 |
| `npm run lint`        | ESLint (typescript-eslint, react-hooks)                               |
| `npm run typecheck`   | `tsc` for the app and for the config/e2e files                        |
| `npm test`            | Vitest + Testing Library, API mocked with MSW                         |
| `npm run test:e2e`    | Playwright flows and axe accessibility scans (starts the mock server) |
| `npm run screenshots` | Captures key screens at 4 viewport sizes in light and dark            |

Playwright browsers are installed inside the repo:
`PLAYWRIGHT_BROWSERS_PATH=./.playwright npx playwright install chromium`.

Configuration lives in `.env.example` (`VITE_API_BASE_URL`, `VITE_USE_MOCKS`).

## Layout of `src/`

```
app/          providers, router, responsive shell, pages
api/          fetch client + ApiError, zod schemas, POST-SSE parser, endpoints, query hooks
features/     patients · reports · chat · evidence · pdf · trace · workspace (inspector, UI state)
components/   shared building blocks; components/ui holds the small shadcn-style primitives
hooks/ lib/   theme, breakpoint, formatting and other helpers
mocks/        MSW handlers that implement the contract (used by tests and `dev:mock`)
```

## Design notes

- **Runtime-validated API.** Every response is parsed with zod, so the rest of the app only sees
  typed data and a contract change fails loudly at the boundary.
- **Streaming.** The chat endpoint is a POST, so `EventSource` cannot be used; `api/sse.ts` parses
  the `fetch` body stream and `features/chat/streamRunner.ts` applies events to a per-patient zustand
  session. Streams keep running if you switch patients, and Stop aborts via `AbortController`.
- **Citations without raw HTML.** `[C1]` markers are rewritten to `cite:` markdown links and rendered
  as chips by a custom link component; nothing uses `dangerouslySetInnerHTML`.
- **Privacy.** Conversations live in memory only; nothing about a patient is written to browser storage.
  The only persisted value is the theme preference.
- **PDF viewer.** The pdf.js worker is bundled locally. Highlighting the cited passage is best effort:
  text-layer items that appear inside the cited chunk are marked (see `features/pdf/highlight.ts`).
- **Responsive.** Three layouts (sidebar + inspector, icon rail + slide-over, top bar + bottom tabs),
  chosen in JS via `useBreakpoint` so only one tree is mounted.

`public/mock/sample-report.pdf` is a small generated fixture used by the mock backend, and
`public/mockServiceWorker.js` is the MSW service worker (only registered when `VITE_USE_MOCKS=true`).
