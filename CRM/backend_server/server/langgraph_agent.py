
import logging
import sys

from dotenv import load_dotenv
load_dotenv()

from typing_extensions import TypedDict
from typing import List, Annotated, Dict, Any

from langchain_core.messages import AIMessage, RemoveMessage, HumanMessage, ToolMessage
from langchain_groq import ChatGroq

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.mongodb import MongoDBSaver

import os

logging.basicConfig(level=logging.DEBUG)
logging.getLogger("pymongo").setLevel(logging.WARNING)

log = logging.getLogger(__name__)

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


SILENT_TOOLS = {"upload_file_tool"}

llm = ChatGroq(
    model="llama-3.3-70b-versatile",            # "llama-3.1-8b-instant",
    api_key=secret_key,
    temperature=0,
    max_tokens=800,
    max_retries=4,
)

tools = [
    interaction_tool,
    edit_log_tool,
    search_history_tool,
    upload_file_tool,
    write_query_tool,
    follow_up_tool,
]

# ---------------------------------------------------------------------
# TWO SEPARATE LLM BINDINGS — this is the core structural fix.
#
#   llm_with_tools -> used ONLY by the "agent" (decide) node.
#   llm            -> used ONLY by the "responder" (narrate) node,
#                      with NO tools bound.
# ---------------------------------------------------------------------
llm_with_tools = llm.bind_tools(tools)


def merge_dicts(current: Dict[str, Any], update: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(current, dict):
        current = {}
    if not update:
        return current
    if not isinstance(update, dict):
        return current

    merged = dict(current)
    merged.update(update)
    return merged


class State(TypedDict):
    messages: Annotated[List, add_messages]
    form: Annotated[Dict[str, Any], merge_dicts]
    outcome: str
    followUp: Annotated[Dict[str, Any], merge_dicts]
    summary: str


# =====================================================================
# Message windowing fix
# ---------------------------------------------------------------------
# Slicing by a flat integer count can cut a tool_calls AIMessage off
# from its ToolMessage result, which confuses the model about what's
# already been resolved.
# =====================================================================
def get_safe_llm_window(messages: List, max_messages: int) -> List:
    if len(messages) <= max_messages:
        return messages

    window = messages[-max_messages:]

    while window and isinstance(window[0], ToolMessage):
        idx_in_full = len(messages) - len(window)
        if idx_in_full > 0:
            window = messages[idx_in_full - 1:]
        else:
            window = window[1:]
            break

    return window


def build_context_note(state: State) -> str:
    current_form = state.get("form", {})
    current_follow_up = state.get("followUp", {})
    current_outcome = state.get("outcome", "")
    current_summary = state.get("summary", "")

    return (
        "INTERNAL REFERENCE ONLY — do not repeat, quote, or paraphrase this "
        "to the user; reply in one short natural sentence.\n"
        f"Logged interaction: {current_form or 'none yet'}\n"
        f"Follow-up: {current_follow_up or 'none yet'}\n"
        f"Document summary: {current_summary or 'none yet'}\n"
        f"CRM history (already fetched, reference only): {current_outcome or 'none yet'}"
    )


# =====================================================================
# NODE: agent  — the ONLY node allowed to decide on a tool call.
# =====================================================================
def interact(state: State):
    log.debug("state keys: %s", list(state.keys()))
    log.debug("total messages: %d", len(state.get("messages", [])))
    log.debug("current form: %s", state.get("form", {}))

    messages = get_safe_llm_window(state["messages"], MAX_MESSAGES_TO_LLM)
    context_note = build_context_note(state)

    try:
        response = llm_with_tools.invoke([
            ("system", SYSTEM_PROMPT),
            ("system", context_note),
            *messages,
        ])
        log.info("agent invoked ok")
    except Exception:
        log.exception("unexpected exception while invoking llm in agent node")
        response = AIMessage(content="Sorry, I had trouble processing that.")

    log.info("response: %s", response)
    log.info("tool calls: %s", getattr(response, "tool_calls", None))
    log.info("content: %s", response.content)

    return {"messages": [response]}


# ToolNode auto-detects tool calls, validates args, executes the right tool.
tool_node = ToolNode(tools)


# =====================================================================
# NODE: responder — narrates the tool result. NO TOOLS BOUND.
# =====================================================================
def respond(state: State):
    messages = get_safe_llm_window(state["messages"], MAX_MESSAGES_TO_LLM)
    context_note = build_context_note(state)

    try:
        response = llm.invoke([
            ("system", SYSTEM_PROMPT),
            ("system", context_note),
            ("system", "A tool has already run and its result is in the "
                        "conversation above. Reply to the user in one short, "
                        "natural sentence based on that result. Do not ask "
                        "to run anything else."),
            *messages,
        ])
        log.info("responder invoked ok")
    except Exception:
        log.exception("unexpected exception while invoking llm in responder node")
        response = AIMessage(content="Done — let me know if you need anything else.")

    log.info("responder content: %s", response.content)

    return {"messages": [response]}


# ---- routing AFTER "agent": did it call a tool, or is it done? ----
def should_continue(state: State):
    last_message = state["messages"][-1]
    tool_calls = getattr(last_message, "tool_calls", None)
    log.debug("should_continue tool_calls: %s", tool_calls)

    if tool_calls:
        return "tools"
    return "trim"


# ---- routing AFTER "tools": narrate, or end silently? ----
def after_tools(state: State):
    messages = state["messages"]

    tool_names = set()
    for msg in reversed(messages):
        if isinstance(msg, AIMessage) and getattr(msg, "tool_calls", None):
            tool_names = {tc["name"] for tc in msg.tool_calls}
            break

    log.info("tools just executed: %s", tool_names)

    if tool_names and tool_names.issubset(SILENT_TOOLS):
        return "trim"

    return "respond"


def trim_history(state: State):
    messages = state["messages"]

    if len(messages) > MAX_MESSAGES_IN_STATE:
        to_remove = messages[:-MAX_MESSAGES_IN_STATE]
        return {"messages": [RemoveMessage(id=m.id) for m in to_remove if getattr(m, "id", None)]}

    return {}


# =====================================================================
# GRAPH WIRING
#
#   START -> agent -> [tools -> respond -> trim -> END]
#                   -> [trim -> END]   
# =====================================================================
graph_builder = StateGraph(State)

graph_builder.add_node("agent", interact)
graph_builder.add_node("tools", tool_node)
graph_builder.add_node("respond", respond)
graph_builder.add_node("trim", trim_history)

graph_builder.add_edge(START, "agent")

graph_builder.add_conditional_edges("agent", should_continue, {
    "tools": "tools",
    "trim": "trim",
})

graph_builder.add_conditional_edges("tools", after_tools, {
    "respond": "respond",
    "trim": "trim",
})

graph_builder.add_edge("respond", "trim")
graph_builder.add_edge("trim", END)


checkpoint_context = MongoDBSaver.from_conn_string(MONGODB_URL)
checkpoint = checkpoint_context.__enter__()

graph = graph_builder.compile(checkpointer=checkpoint)





































































































