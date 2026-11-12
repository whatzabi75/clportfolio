# clportfolio

The website [clportfolio.me](https://www.clportfolio.me) and the shared backend behind its demo projects.

```
clportfolio/
├── website/                 Next.js site            → deployed by Vercel  (Root Directory: website)
│   └── src/
│       ├── app/projects/    one page per project
│       └── lib/backend.ts   the backend address (NEXT_PUBLIC_BACKEND_URL)
├── backend/                 Flask API (shared)      → deployed by Railway (Root Directory: backend)
│   ├── server.py            wires all projects together
│   ├── shared/llm.py        Anthropic client + model name for every project
│   └── projects/<name>/     logic.py (the work) + routes.py (its endpoints)
└── start-local.sh           run backend + website on your Mac
```

## Run it locally
```bash
./start-local.sh
```
Website: http://localhost:3000 · Backend: http://127.0.0.1:5050/health

First run creates `backend/venv` and installs packages (several minutes — torch is large).
Needs `backend/.env` with `ANTHROPIC_API_KEY=...` (see `backend/.env.example`).

## Add a new project
1. `backend/projects/<new_name>/` with `__init__.py`, `logic.py`, `routes.py` (copy an existing one).
2. Register its blueprint in `backend/server.py`.
3. Add `website/src/app/projects/<new-name>/page.tsx` and a card in `website/src/app/projects/page.tsx`.
4. Call the backend with `` fetch(`${BACKEND_URL}/your-route`) `` from `@/lib/backend`.

## Notes
- `backend/requirements.txt` is pinned. Upgrade one package at a time and retest.
- Locally the backend runs with `flask run` — gunicorn crashes on macOS (fork-safety); Railway (Linux) uses gunicorn.
- The Anthropic API no longer accepts `temperature` (Nov 2026). The Stochastic vs. Deterministic demo was redesigned to compare a loose vs. a strict prompt over 5 runs each (`POST /api/prompt-consistency`).
