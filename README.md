# AI Advisory Board

AI Advisory Board is a multi-agent investor simulation app that reviews startup materials and gives fundraising guidance through an iterative critique loop.

The project mirrors ArchAI's core orchestration pattern:
- specialist agents produce independent analysis,
- a supervisor critiques and requests revisions,
- the loop repeats up to a fixed limit,
- the supervisor synthesizes a final recommendation.

## What you get

- 4 investor personalities reviewing the same startup packet:
  - **Maya Chen (Market Maven)**: market size, GTM, growth wedge
  - **Daniel Ross (Finance Hawk)**: unit economics, runway, forecast realism
  - **Priya Nair (Product Operator)**: product execution and retention dynamics
  - **Owen Brooks (Risk Guardian)**: legal/regulatory/security/downside analysis
- Supervisor-led iterative loop (up to 3 rounds) to tighten quality and resolve disagreements
- Group-chat style Streamlit UI showing each investor's messages
- Right-side executive summary panel with:
  - advantages,
  - disadvantages,
  - recommended optimal route,
  - 30-day action plan
- Document ingestion for `.pdf`, `.pptx`, `.ppt`, `.docx`, `.txt`, `.md`
- Persistent session storage in SQLite with recent-session restore in the sidebar

## Architecture

```
Founder request + uploaded docs
  -> Supervisor creates BoardBrief
  -> Iteration loop:
       4 investors produce InvestorReview
       Supervisor produces BoardCritique + revision instructions
       (repeat until convergence or max iterations)
  -> Supervisor produces ExecutiveBoardSummary
  -> UI displays chat transcript + final summary
```

## Project structure

```
ai_advisory_board/
├── app/
│   ├── Home.py
│   └── pages/
│       └── 1_Board_Chat.py
├── agents/
│   ├── base.py
│   ├── investor_agents.py
│   └── supervisor_agent.py
├── models/
│   ├── inputs.py
│   └── outputs.py
├── orchestration/
│   ├── prompts.py
│   └── workflow.py
├── services/
│   ├── document_service.py
│   └── session_service.py
├── ui/
│   ├── components.py
│   └── state.py
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── requirements.txt
└── pyproject.toml
```

## Setup

1. Create and activate environment (Python 3.12+).
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Configure environment:

```bash
cp .env.example .env
```

Set your API key in `.env`.

4. Run Streamlit:

```bash
streamlit run app/Home.py
```

## Session persistence

- Sessions are stored in SQLite at `DB_PATH` (default: `data/advisory_board.db`).
- The Board Chat sidebar shows recent sessions and allows reloading a prior snapshot.
- Database files are ignored by git (`data/*.db`) and safe to persist locally.

## Run with Docker

1. Create `.env` and set at least `OPENAI_API_KEY`:

```bash
cp .env.example .env
```

2. Build and run:

```bash
docker compose up --build
```

3. Open `http://localhost:8501`.

`docker-compose.yml` mounts `./data` to `/app/data`, so session storage persists across container restarts.

## Notes on `.ppt`

Legacy `.ppt` parsing is supported through on-the-fly conversion via LibreOffice (`soffice`).
If LibreOffice is not installed, `.ppt` files will be skipped with a warning in the UI.

## Next extension ideas

- add citation spans from source docs for each investor claim,
- stream token-level responses in chat bubbles,
- support custom investor personas from the UI.
