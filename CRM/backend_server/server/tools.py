
from dotenv import load_dotenv
load_dotenv()
from langchain_core.tools import tool, InjectedToolCallId
from langchain_core.messages import ToolMessage
from langgraph.types import Command
from server.service import Interaction_details, edit_log_info, search_history, follow_up_scedule
from typing import List, Optional, Annotated
from pathlib import Path
from server.rag_form.rag_service import upload_material
from server.rag_form.rag_extract import query_service
from db.database import get_db


@tool
def interaction_tool(
    hcp_name: str,
    tool_call_id: Annotated[str, InjectedToolCallId],
    interactionType: Optional[str] = None,
    meeting_date: str = "",
    meeting_time: Optional[str] = None,
    attendees: Optional[List[str]] = None,
    hcp_sentiment: Optional[str] = None,
    topics: Optional[List[str]] = None,
    materials: Optional[List[str]] = None,
):
    """
    Log a NEW HCP interaction that already happened or is currently
    happening. attendees, topics, and materials must be arrays, never
    comma-joined strings.

    Do NOT use this if a "Current logged interaction data" state is
    already shown for this HCP and the user wants to change any of its
    fields — that is an edit; call edit_log_tool instead.
    Do NOT use for future/scheduled meetings — use follow_up_tool.
    Only call this when the user's current message describes a
    completed or in-progress meeting.
    """

    print("Interaction tool called")
    result = Interaction_details(
        hcp_name, interactionType, meeting_date, meeting_time,
        attendees, hcp_sentiment, topics, materials,
    )

    if not result.get("success"):
        return Command(update={
            "messages": [
                ToolMessage(
                    content=result.get("message", "Unable to log interaction"),
                    tool_call_id=tool_call_id,
                )
            ]
        })

    interaction = result["interaction"]

    form_update = {
        "hcpId": interaction["id"],
        "hcpName": interaction["hcp_name"],
        "interactionType": interaction["interaction_type"],
        "date": interaction["date"],
        "time": interaction["time"],
        "attendees": interaction["attendees"] or [],
        "sentiment": interaction["hcp_sentiment"] or "neutral",
        "topicsDiscussed": interaction["topics"] or [],
        "materialsShared": interaction["materials"] or [],
    }

    return Command(update={
        "form": form_update,
        "messages": [
            ToolMessage(content=f"Logged interaction with {hcp_name}.", tool_call_id=tool_call_id)
        ],
    })


@tool
def edit_log_tool(
    tool_call_id: Annotated[str, InjectedToolCallId],
    hcp_id: Optional[int] = None,
    hcp_name: Optional[str] = None,
    interaction_type:Optional[str]=None,
    hcp_sentiment: Optional[str] = None,
    meeting_date: Optional[str] = None,
    meeting_time: Optional[str] = None,
    attendees: Optional[List[str]] = None,
    topics: Optional[List[str]] = None,
    materials: Optional[List[str]] = None,
):
    """
    Update an EXISTING logged HCP interaction. Use hcp_id from current
    state when available (most reliable); fall back to hcp_name only if
    no hcp_id is shown. hcp_name here means "whose record to edit," not
    a rename field — for an actual rename, pass the NEW name as hcp_name
    and still locate the record via hcp_id.

    Update only fields the user explicitly mentioned. Never invent values.

    Do NOT call this just because interaction/follow-up/CRM-history state
    is visible to you — only call it when the user's CURRENT message
    explicitly asks to change, correct, update, or fix a field.
    Never call this for a question about an uploaded document's content —
    use write_query_tool for that instead, even if a topic name overlaps
    with existing state.
    """

    print("edit tool called")
    result = edit_log_info(
        hcp_id=hcp_id,
        hcp_name=hcp_name,
        interaction_type=interaction_type,
        hcp_sentiment=hcp_sentiment,
        meeting_date=meeting_date,
        meeting_time=meeting_time,
        attendees=attendees,
        topics=topics,
        materials=materials,
    )

    if not result.get("success"):
        return Command(update={
            "messages": [
                ToolMessage(
                    content=result.get("message", "Unable to update interaction"),
                    tool_call_id=tool_call_id,
                )
            ]
        })

    updated_interaction = result["interaction"]
    

    form_update = {
        "hcpId": updated_interaction["id"],
        "hcpName": updated_interaction["hcp_name"],
        "interactionType": updated_interaction["interaction_type"],
        "date": updated_interaction["date"],
        "time": updated_interaction["time"],
        "attendees": updated_interaction["attendees"],
        "sentiment": updated_interaction["hcp_sentiment"],
        "topicsDiscussed": updated_interaction["topics"],
        "materialsShared": updated_interaction["materials"],
    }

    return Command(update={
        "form": form_update,
        "messages": [
            ToolMessage(content="Interaction updated.", tool_call_id=tool_call_id)
        ],
    })


@tool
def search_history_tool(hcp_name: str, tool_call_id: Annotated[str, InjectedToolCallId]):

    """
    Look up PAST CRM interactions/meeting history for an HCP. Use ONLY
    when the user's current message explicitly asks about previous
    meetings, past discussions, or interaction history (e.g. "what did
    we discuss before", "past visits").

    Do NOT call this automatically after another tool (edit_log_tool,
    follow_up_tool, interaction_tool) just ran — a prior tool succeeding
    is never itself a reason to also fetch history.
    Do NOT call this for document/PDF content questions — use
    write_query_tool for those instead.
    """
     
    db = None
    print("search history entered")
    try:
        db = next(get_db())
        result = search_history(hcp_name, db)
        history = result["history"]

        if not history:
            return Command(update={
                "messages": [ToolMessage(content=f"No history found for {hcp_name}.", tool_call_id=tool_call_id)]
            })

        history_text = ""
        for item in history:
            history_text += f"""
            Hcp_name:{item["hcp_name"]}
            Date:{item["meeting_date"]}
            Time:{item["meeting_time"]}
            Topics Discussed:{", ".join(item['topics'] or [])}
            Sentiment:{item['hcp_sentiment']}
            Materials:{",".join(item['materials'] or [])}
            """

        return Command(update={
            "outcome": history_text,
            "messages": [ToolMessage(content=history_text, tool_call_id=tool_call_id)],
        })
    except Exception as e:
        return Command(update={
            "messages": [ToolMessage(content=f"History lookup failed: {e}", tool_call_id=tool_call_id)]
        })
    finally:
        if db:
            db.close()



@tool
def upload_file_tool(pdf_path: str, tool_call_id: Annotated[str, InjectedToolCallId]):
    """
    Process a file the user actually just uploaded/attached. Never invent
    or guess a file path. Do not answer questions about the file's
    content here — that happens via write_query_tool once the user asks.
    """
    print("upload file entered")

    try:
        upload_material(pdf_path)
    except Exception as e:
        return Command(update={
            "messages": [ToolMessage(content=f"Upload failed: {e}", tool_call_id=tool_call_id)]
        })

    filename = Path(pdf_path).name


    return Command(update={
        "form": {"materialsShared": [filename]},
        "messages": [ToolMessage(content=f"Uploaded {filename}.", tool_call_id=tool_call_id)],
    })






@tool
def write_query_tool(question: str, tool_call_id: Annotated[str, InjectedToolCallId]):
    """
    Answer a question about the CONTENT of an uploaded document — dosage,
    contraindications, indications, adverse effects, a summary/explanation
    of the file. Answer only from retrieved document content, never from
    general knowledge.

    Use this whenever the user's current message is about what a file/PDF
    says, means, or contains — even if a topic name in the question also
    appears in existing form/followUp/outcome state. A document question
    is never an edit and never a history lookup.
    """
    print("write query entered")
    result = query_service(question)

    if isinstance(result, dict):
        summary = result.get("summary", "The information was not found in uploaded materials.")
        form_patch = result.get("form", {})
    else:
        summary = str(result) if result else "The information was not found in uploaded materials."
        form_patch = {}

    return Command(update={
        "summary": summary,
        "form": form_patch,
        "messages": [ToolMessage(content=summary, tool_call_id=tool_call_id)],
    })


@tool
def follow_up_tool(
    hcp_name: str,
    tool_call_id: Annotated[str, InjectedToolCallId],
    meeting_date: Optional[str] = None,
    meeting_time: Optional[str] = None,
    purpose: str = "",
):
    """
    Schedule a NEW future follow-up appointment. Use ONLY when the user's
    current message explicitly requests scheduling/booking/planning a
    future meeting. Cannot look up, modify, reschedule, or cancel an
    existing follow-up — if asked to do any of those, do not call this
    tool; tell the user that isn't supported yet.

    Never use for a completed/in-progress meeting — use interaction_tool.
    Do not call search_history_tool or any other tool alongside this one
    unless the user separately asked for that too.
    """
    db = next(get_db())
    try:
        result = follow_up_scedule(hcp_name, db, meeting_date, meeting_time, purpose)

        if not result.get("success"):
            
            return Command(update={
                "messages": [
                    ToolMessage(
                        content=result.get("message", "Unable to schedule follow up"),
                        tool_call_id=tool_call_id,
                    )
                ]
            })

        return Command(update={
            "followUp": {
                "required": True,
                "hcpName": result["name"],
                "date": result["meeting_date"],
                "time": result["meeting_time"],
                "purpose": result["purpose"],
            },
            "messages": [
                ToolMessage(
                    content=f"Follow-up scheduled with {result['name']} on {result['meeting_date']} at {result['meeting_time']}.",
                    tool_call_id=tool_call_id,
                )
            ],
        })
    finally:
        db.close()
