# 🩺 HCP CRM Assistant — LangGraph Agent

> An AI-powered CRM assistant for Medical Representatives — log HCP interactions, edit records, search history, schedule follow-ups, and query uploaded documents, all through natural conversation.

---

## ✨ What It Does

- 📝 **Logs** completed HCP meetings and interactions
- ✏️ **Edits** existing interaction records (sentiment, type, date, materials, etc.)
- 🔍 **Searches** past CRM history for any HCP
- 📄 **Uploads & reads** pharma documents (brochures, PDFs)
- 💬 **Answers questions** about those documents using RAG
- 📅 **Schedules** future follow-up appointments

All of it flows into a live **form state** your frontend can read in real time — no manual data entry, no parsing chat text.

---

## 🧠 How It Thinks

```
   START ──▶ 🤖 agent ──▶ tool needed? ──▶ 🛠️ tools ──▶ 🤖 agent (replies) ──▶ ✂️ trim ──▶ END
                  │                                              │
                  └──────────── no tool needed ──────────────────┘
```

- **🤖 agent** — the LLM brain (Groq `llama-3.1-8b-instant`) picks the right tool or just replies
- **🛠️ tools** — executes the tool, writes results *straight into state* (no fragile parsing step)
- **✂️ trim** — keeps conversation history lean so tokens (and your Groq rate limit) stay under control

---

## 🗂️ Project Structure

```
server/
 ├── 🧩 langgraph_agent.py   → graph wiring, state, routing logic
 ├── 🛠️ tools.py             → the 6 tools the agent can call
 ├── 🗄️ service.py           → database read/write logic
 ├── 📆 validatedt.py        → date & time parsing/validation
 ├── 💬 prompts.py           → the system prompt
 └── rag_form/
      ├── rag_service.py    → document ingestion
      └── rag_extract.py    → document Q&A (RAG)

db/
 ├── database.py            → DB engine & session
 └── models.py               → Interaction_data, Follow_Up tables
```

---

## ⚙️ Setup

```bash
# 1️⃣ Create a virtual environment
python -m venv venv
venv\Scripts\activate

# 2️⃣ Install dependencies
pip install langgraph langchain-groq langchain-core python-dotenv \
            sqlalchemy dateparser pymongo langgraph-checkpoint-mongodb

# 3️⃣ Add your .env file 

# 4️⃣ Make sure MySQL + MongoDB are running
```

**`.env` file:**
```env
API_KEY=your_groq_api_key
MONGO_DB_URL=mongodb://localhost:27017
```

---

## ▶️ Running It

```python
from server.langgraph_agent import graph

config = {"configurable": {"thread_id": "conversation-1"}}

result = graph.invoke(
    {"messages": [("human", "Log a meeting with Dr. Vin, positive sentiment")]},
    config=config,
)

print(result["form"])       # 📋 current interaction form
print(result["followUp"])   # 📅 current follow-up data
```

Read state anytime without sending a message:
```python
snapshot = graph.get_state(config)
form_data = snapshot.values.get("form", {})
```

---

## 🛠️ Tools at a Glance

| Tool | Purpose | Key Notes |
|---|---|---|
| 📝 `interaction_tool` | Log a new interaction | Only `hcp_name` required; never invents data |
| ✏️ `edit_log_tool` | Edit an existing interaction | Uses `hcp_id` when available (most reliable) |
| 🔍 `search_history_tool` | Look up past interactions | Returns last 3, summarized naturally |
| 📄 `upload_file_tool` | Ingest an uploaded document | Silent — no narration until asked about it |
| 💬 `write_query_tool` | Answer questions on documents | Never answers from general knowledge |
| 📅 `follow_up_tool` | Schedule a future appointment | Create-only — no cancel/reschedule yet |

---

## 📋 State at a Glance

**`form`** →
- `hcpId` · `hcpName` · `interactionType` · `date` · `time`
- `attendees` · `sentiment` · `topicsDiscussed` · `materialsShared`

**`followUp`** →
- `required` · `hcpName` · `date` · `time` · `purpose`

> 💡 `form` and `followUp` use a **merge reducer** — a tool returning a partial update (like just `materialsShared`) merges into existing state instead of wiping everything else out.

---

## 🎯 Key Design Choices

- ✅ Tools write **directly to state** via `Command` — no JSON-in-message parsing
- ✅ Agent always gets a turn **after** a tool call, so replies are natural, not raw tool output
- ✅ Large tool results (history, RAG answers) are **capped before hitting the LLM**, full text still saved in state
- ✅ System prompt explicitly maps `state keys → tool arguments`, and tells the model **never to repeat internal state** back to the user
- ✅ Persisted message history is **trimmed separately** from what's sent to the LLM each turn

---

## ⚠️ Known Limitations

- 🚫 No cancel/reschedule for follow-ups yet — create-only
- 🚫 A follow-up requires an existing prior interaction for that HCP
- 🤏 Small model (`llama-3.1-8b-instant`) can occasionally mis-route an edit as a new log — `llama-3.3-70b-versatile` is a stronger fallback
- 🔁 No hard cap yet on tool-call loop depth in a single turn

---

## 🩹 Troubleshooting

| Symptom | Check This |
|---|---|
| ⏱️ Rate limit errors from Groq | `MAX_MESSAGES_TO_LLM`, the 600-char tool-message cap, `max_retries` |
| 🔁 Edit re-logs instead of updating | Was `hcpId` present in state context at that point? Which tool actually fired? |
| ❌ A field never updates | Confirm it's wired through `tools.py` → `service.py` → the DB column |
| 📦 MongoDB checkpoint growing huge | Confirm `trim` node is firing and `MAX_MESSAGES_IN_STATE` is set sensibly |

---

<p align="center">Built with 🧠 LangGraph · ⚡ Groq · 🗄️ MongoDB + MySQL</p>
