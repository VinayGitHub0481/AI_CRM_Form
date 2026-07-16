# HCP CRM Assistant — LangGraph Agent

An AI CRM assistant for Medical Representatives (MRs) to log HCP (Healthcare
Professional) interactions, edit them, search history, schedule follow-ups,
and answer questions from uploaded documents — all via natural language,
backed by a LangGraph agent with tool-calling and persistent state.

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Project Structure](#project-structure)
4. [Setup](#setup)
5. [Environment Variables](#environment-variables)
6. [Running the Agent](#running-the-agent)
7. [Tools Reference](#tools-reference)
8. [State Schema](#state-schema)
9. [Design Decisions](#design-decisions)
10. [Known Limitations](#known-limitations)
11. [Troubleshooting](#troubleshooting)

---

## Overview

The assistant understands natural-language requests from an MR and maps them
to one of six tools:

| Intent | Tool |
|---|---|
| Log a completed meeting/interaction | `interaction_tool` |
| Edit an existing interaction | `edit_log_tool` |
| Look up past interactions for an HCP | `search_history_tool` |
| Upload a document (brochure, PDF, etc.) | `upload_file_tool` |
| Ask a question about an uploaded document | `write_query_tool` |
| Schedule a future follow-up appointment | `follow_up_tool` |

Tool results write directly into a shared LangGraph state object (`form`,
`followUp`, `outcome`, `summary`), which a frontend can read to keep an HCP
interaction form in sync with the conversation in real time.

---

## Architecture

```
                         ┌─────────┐
            START ─────▶ │  agent  │◀────────────────┐
                         └────┬────┘                  │
                              │                        │
                  tool call?  │  no tool call           │ agent (narrate)
                  ┌───────────┴───────────┐             │
                  │ yes                   │ no          │
                  ▼                       ▼             │
             ┌─────────┐             ┌──────┐            │
             │  tools  │             │ trim │            │
             └────┬────┘             └───┬──┘            │
                  │                      │               │
        silent tool only?                ▼               │
        (e.g. upload_file_tool)         END               │
                  │                                       │
        ┌─────────┴─────────┐                             │
        │ yes                │ no                          │
        ▼                    └─────────────────────────────┘
     ┌──────┐
     │ trim │
     └───┬──┘
         ▼
        END
```

**Key nodes:**

- **`agent`** — invokes the LLM (Groq `llama-3.1-8b-instant`) with the
  system prompt, an internal-only state snapshot (current form/follow-up
  data), and a trimmed slice of recent messages. Decides whether to call a
  tool or reply directly.
- **`tools`** — a LangGraph `ToolNode` that executes whichever tool(s) the
  LLM requested. Tools return `Command(update={...})` so they write
  straight into graph state (no intermediate parsing step).
- **`trim`** — prunes old messages out of *persisted* state (not just what's
  sent to the LLM) so the MongoDB checkpoint doesn't grow unbounded.

**Routing logic:**

- `should_continue` (after `agent`): tool call present → `tools`, else → `trim`.
- `after_tools` (after `tools`): if every tool called was in `SILENT_TOOLS`
  (currently just `upload_file_tool`), skip straight to `trim` — no need for
  the LLM to narrate a file upload before the user has asked anything about
  it. Otherwise loop back to `agent` so the LLM can turn the tool result
  into a natural-language reply.

---

## Project Structure

```
server/
├── langgraph_agent.py   # graph definition: State, nodes, routing, compile
├── tools.py             # the 6 @tool-decorated functions, LangChain-facing
├── service.py           # DB access layer (SQLAlchemy) — the actual CRUD
├── validatedt.py        # validate_date_time() — date/time parsing & validation
├── prompts.py           # SYSTEM_PROMPT given to the LLM
└── rag_form/
    ├── rag_service.py   # upload_material() — ingests uploaded docs
    └── rag_extract.py   # query_service() — RAG lookup over uploaded docs

db/
├── database.py          # engine, Sessiondata, get_db()
└── models.py             # Interaction_data, Follow_Up (SQLAlchemy models)
```

---

## Setup

```bash
# 1. Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# 2. Install dependencies
pip install langgraph langchain-groq langchain-core python-dotenv \
            sqlalchemy dateparser pymongo langgraph-checkpoint-mongodb

# 3. Set up your .env file (see below)

# 4. Make sure your MySQL database and MongoDB instance are reachable
```

---

## Environment Variables

Create a `.env` file in the project root:

```env
API_KEY=your_groq_api_key
MONGO_DB_URL=mongodb://localhost:27017
```

- `API_KEY` — Groq API key, used by `ChatGroq` in `langgraph_agent.py`.
- `MONGO_DB_URL` — connection string for `MongoDBSaver`, which persists
  graph state/checkpoints across turns and conversations.

MySQL connection details are configured separately in `db/database.py`
(`engine`, `Sessiondata`) — check that file for the exact connection
string format expected.

---

## Running the Agent

```python
from server.langgraph_agent import graph

config = {"configurable": {"thread_id": "some-conversation-id"}}

result = graph.invoke(
    {"messages": [("human", "Log a meeting with Dr. Vin about product syrup, positive sentiment")]},
    config=config,
)

print(result["form"])       # current HCP interaction form state
print(result["followUp"])   # current follow-up state
```

`thread_id` is what MongoDBSaver uses to persist and resume a specific
conversation's state across calls — use one per user/session.

To inspect state without sending a new message (e.g. for a frontend polling
the form):

```python
snapshot = graph.get_state(config)
form_data = snapshot.values.get("form", {})
follow_up_data = snapshot.values.get("followUp", {})
```

---

## Tools Reference

### `interaction_tool`
Logs a **new** completed interaction. Required: `hcp_name`. Everything else
(`interaction_type`, `meeting_date`, `meeting_time`, `attendees`,
`hcp_sentiment`, `topics`, `materials`) is optional and only ever set from
what the user actually states — never invented or defaulted, except
`hcp_sentiment` which defaults to `"neutral"` on a brand-new log with no
sentiment mentioned.

### `edit_log_tool`
Modifies an **existing** interaction. Identifies the record via `hcp_id`
(preferred, sourced from current form state) or `hcp_name` (fallback).
Supports editing: `hcp_sentiment`, `interaction_type`, `meeting_date`,
`meeting_time`, `attendees`, `topics`, `materials`, and renaming via
`hcp_name`. Only fields explicitly provided are changed.

### `search_history_tool`
Looks up the last 3 interactions for a given HCP name (fuzzy match via
`ILIKE`), returns a natural-language summary. Raw CRM field labels are never
shown to the end user per the system prompt.

### `upload_file_tool`
Ingests an uploaded document (PDF/brochure) via `upload_material()`. Never
invents file paths. This is a "silent" tool — the graph skips straight to
`END` after it runs rather than having the LLM narrate, since the natural
next step is the user asking a question about the document.

### `write_query_tool`
Answers questions about uploaded documents via RAG (`query_service()`).
Never answers from the model's own general knowledge.

### `follow_up_tool`
Schedules a **new** future appointment. Requires a prior interaction to
exist for that HCP (looks one up to establish the FK relationship). Cannot
currently look up, modify, or cancel an existing follow-up — see
[Known Limitations](#known-limitations).

---

## State Schema

```python
class State(TypedDict):
    messages: Annotated[List, add_messages]           # conversation history
    form: Annotated[Dict[str, Any], merge_dicts]       # HCP interaction form
    outcome: str                                       # history-lookup text
    followUp: Annotated[Dict[str, Any], merge_dicts]   # follow-up appointment data
    summary: str                                       # RAG answer text
```

`form` keys: `hcpId`, `hcpName`, `interactionType`, `date`, `time`,
`attendees`, `sentiment`, `topicsDiscussed`, `materialsShared`.

`followUp` keys: `required`, `hcpName`, `date`, `time`, `purpose`.

**Note on `merge_dicts`:** `form` and `followUp` use a custom reducer so
that a tool returning a partial update (e.g. `upload_file_tool` only
setting `materialsShared`) merges into existing state instead of replacing
it wholesale. Without this, every partial update would wipe out unrelated
fields.

---

## Design Decisions

- **Tools write to state via `Command`, not via message content.** Earlier
  versions stuffed structured data into `ToolMessage.content` as JSON and
  parsed it back out downstream. This added token overhead, was fragile,
  and made state updates depend on string parsing succeeding. Now each tool
  returns `Command(update={...})` directly.
- **`tools → agent` loop, not `tools → END`.** The LLM must get a turn after
  a tool call to convert the raw result into a natural-language reply — the
  graph used to end immediately after a tool ran, so the user only ever saw
  a raw tool call or its output.
- **Persisted-state trimming is separate from the LLM's context window.**
  `MAX_MESSAGES_TO_LLM` controls what's sent to the model each turn;
  `MAX_MESSAGES_IN_STATE` (enforced by the `trim` node using `RemoveMessage`)
  controls what MongoDB actually keeps long-term.
- **Large tool results are capped before being sent to the LLM.**
  `search_history_tool` and `write_query_tool` can produce long text. The
  full text is kept in `outcome`/`summary` state for the frontend, but what
  gets sent to the LLM (and re-sent on every subsequent turn until it ages
  out of the window) is capped at ~600 characters to reduce token usage and
  avoid tripping Groq's rate limits.
- **The system prompt explicitly maps state keys to tool argument names**
  (e.g. `hcpId` → `hcp_id`, `sentiment` → `hcp_sentiment`) and instructs the
  model never to repeat the internal state snapshot back to the user
  verbatim — both added after observing the model occasionally echoing raw
  state as if it were a natural-language answer.

---

## Known Limitations

- **`follow_up_tool` can only create new follow-ups.** There's no
  cancel/reschedule/update path yet — the underlying service function only
  inserts a new `Follow_Up` row. If a user asks to cancel or reschedule an
  existing follow-up, the assistant is instructed to say that's not
  supported rather than silently creating an unrelated duplicate entry.
- **A prior interaction must exist before a follow-up can be scheduled**,
  since `follow_up_scedule` looks up the HCP's most recent interaction to
  populate the foreign key. A brand-new HCP with no logged interaction
  cannot yet get a follow-up scheduled directly.
- **Small model, occasional tool mis-selection.** `llama-3.1-8b-instant` is
  fast and cheap but can occasionally re-trigger `interaction_tool` for what
  should be an edit, especially on ambiguous follow-up phrasing. The system
  prompt and injected state context mitigate this but don't eliminate it
  entirely — `llama-3.3-70b-versatile` (commented out in `langgraph_agent.py`)
  is a stronger option if this becomes a recurring issue.
- **No hard cap on tool-call loop depth.** `agent → tools → agent → ...` can
  in principle loop many times in one turn if the model keeps deciding to
  call tools. Consider adding a turn/loop counter to `State` as a safety
  valve if this is observed in practice.

---

## Troubleshooting

**"Rate limited" errors from Groq**
Check `MAX_MESSAGES_TO_LLM` and the 600-char cap on tool message content —
both exist specifically to control token usage per call. Also confirm
`max_retries` on `ChatGroq` is giving transient 429s room to back off
(currently set to 4).

**Edits aren't reflected in the form / an edit re-logs instead of updating**
Check the console/logs for which tool actually fired (`print("tool calls", ...)`
in `should_continue`). If `interaction_tool` fired for what was meant as an
edit, that's the known model mis-selection issue above — check whether
`hcpId` was actually present in the injected state context at that point in
the conversation.

**A field (e.g. `interactionType`) never seems to update**
Confirm the field is actually accepted as a parameter all the way through:
`edit_log_tool` (tools.py) → `edit_log_info` (service.py) → the SQLAlchemy
column assignment. A field missing from any one of these three stops the
update silently rather than erroring.

**MongoDB checkpoint growing very large**
Check `MAX_MESSAGES_IN_STATE` and confirm the `trim` node is actually being
reached — it only prunes the persisted message list when message count
exceeds that threshold.