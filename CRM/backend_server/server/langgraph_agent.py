

from dotenv import load_dotenv
load_dotenv()

from typing_extensions import TypedDict
from typing import List, Annotated, Dict, Any

from langchain_core.messages import AIMessage, RemoveMessage
from langchain_groq import ChatGroq

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.mongodb import MongoDBSaver

import os

from server.tools import (
    interaction_tool,
    edit_log_tool,
    upload_file_tool,
    write_query_tool,
    search_history_tool,
    follow_up_tool,
)
from server.prompts import SYSTEM_PROMPT


secret_key = os.getenv("API_KEY")
MONGODB_URL = os.getenv("MONGO_DB_URL")

# how many messages to keep in state / send to the LLM
MAX_MESSAGES_IN_STATE = 12
MAX_MESSAGES_TO_LLM = 5

# taking this as silent tool because no tool should be called after this 
SILENT_TOOLS = {"upload_file_tool"}

llm = ChatGroq(
    model="llama-3.1-8b-instant",        # "llama-3.3-70b-versatile"
    api_key=secret_key,
    temperature=0,
    max_tokens=800,
    max_retries=4,
)

# list of tools and binding
tools = [
    interaction_tool,
    edit_log_tool,
    search_history_tool,
    upload_file_tool,
    write_query_tool,
    follow_up_tool,
]

llm_with_tools = llm.bind_tools(tools)


# Without a reducer, LangGraph's default behavior for a plain dict field
# would wipe out every other field already in `form`/`followUp`.
# we use this function to make the form remain with the fields rather than wiping out for new request 
def merge_dicts(current: Dict[str, Any], update: Dict[str, Any]) -> Dict[str, Any]:
    if not current:
        current = {}
    if not update:
        return current
    merged = dict(current)
    merged.update(update)
    return merged


# State shared across all nodes in the graph
class State(TypedDict):
    messages: Annotated[List, add_messages]           # rolling conversation history
    form: Annotated[Dict[str, Any], merge_dicts]       # HCP interaction form data
    outcome: str                                       # result text (e.g. history lookups)
    followUp: Annotated[Dict[str, Any], merge_dicts]   # follow-up appointment data
    summary: str                                       # RAG / document query answers


# ---- node: agent ----
def interact(state: State):
    print("Entered agent")
    messages = state["messages"][-MAX_MESSAGES_TO_LLM:]

    # Give the model an explicit snapshot of current form/followUp state,
    # so tool selection and args (especially hcp_id) don't depend purely
    # on whatever survived the trimmed message window
    current_form = state.get("form", {})
    current_follow_up = state.get("followUp", {})

    context_note = (
        "INTERNAL REFERENCE ONLY — do not repeat, quote, or paraphrase any "
        "of the raw data below to the user. It exists only to help you "
        "decide which tool to call and what arguments to pass. Your reply "
        "to the user must always be a short natural sentence, never a "
        "dump of these fields.\n"
        f"Current logged interaction data: {current_form or 'none yet'}\n"
        f"Current follow-up data: {current_follow_up or 'none yet'}\n"
        "If the user is asking to change, update, correct, or fix any "
        "field in the data above, call edit_log_tool (using the hcp_id "
        "shown above if present) — do NOT call interaction_tool again, "
        "that is only for logging a brand new interaction."
    )

    response = llm_with_tools.invoke([
        ("system", SYSTEM_PROMPT),
        ("system", context_note),
        *messages,
    ])

    print("Response:", response)
    print("Tool calls:", response.tool_calls)
    print("Content:", response.content)

    return {
        "messages": [response]
    }


# ToolNode auto-detects tool calls, validates args, executes the right tool,
# updates directly — no extra parsing node needed.
tool_node = ToolNode(tools)


# ---- routing BEFORE "tools": does the agent want to call a tool at all? ----
def should_continue(state: State):
    print("entered should_continue")
    last_message = state["messages"][-1]
    tool_calls = getattr(last_message, "tool_calls", None)
    print("tool calls", tool_calls)

    if tool_calls:
        print("tool called")
        return "tools"
    return "trim"


# ---- routing AFTER "tools": does the agent need a turn to narrate, or can we end silently? ----
def after_tools(state: State):
    print("entered after_tools")
    messages = state["messages"]

    # find the most recent AIMessage that carried tool_calls, so we know
    tool_names = set()
    for msg in reversed(messages):
        if isinstance(msg, AIMessage) and getattr(msg, "tool_calls", None):
            tool_names = {tc["name"] for tc in msg.tool_calls}
            break

    print("tools just executed:", tool_names)

    if tool_names and tool_names.issubset(SILENT_TOOLS):
        
        return "trim"

    return "agent"


# ---- node: trim_history ----
# Keeps persisted state from growing unbounded. Trims the *stored*
# message list (what MongoDBSaver keeps), independent of the smaller
# slice sent to the LLM in `interact`.
def trim_history(state: State):
    print("Entered trim_history")
    messages = state["messages"]

    if len(messages) > MAX_MESSAGES_IN_STATE:
        to_remove = messages[:-MAX_MESSAGES_IN_STATE]
        return {"messages": [RemoveMessage(id=m.id) for m in to_remove if getattr(m, "id", None)]}

    return {}


# ---- graph wiring ----
graph_builder = StateGraph(State)

graph_builder.add_node("agent", interact)
graph_builder.add_node("tools", tool_node)
graph_builder.add_node("trim", trim_history)

graph_builder.add_edge(START, "agent")

graph_builder.add_conditional_edges("agent", should_continue, {
    "tools": "tools",
    "trim": "trim",
})

# tool always runs first; THEN decide whether to loop back to "agent"
# for narration, or skip straight to "trim" (e.g. for silent uploads)
graph_builder.add_conditional_edges("tools", after_tools, {
    "agent": "agent",
    "trim": "trim",
})

graph_builder.add_edge("trim", END)


# mongodb saver checkpoint stores updated state persistently
checkpoint_context = MongoDBSaver.from_conn_string(MONGODB_URL)
checkpoint = checkpoint_context.__enter__()

graph = graph_builder.compile(checkpointer=checkpoint)








































































