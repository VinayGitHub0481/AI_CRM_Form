
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
    Log a new HCP interaction that has already occurred or is currently happening.
    Use ONLY for recording a completed meeting or discussion, saving topics,
    materials, or HCP sentiment. Do NOT use for future appointments — use
    follow_up_tool for that.
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
    Update an existing HCP interaction. Use when the user wants to modify
    saved interaction data.

    Identify the interaction using hcp_id when it is known (from the
    current logged interaction data shown to you) — this is the reliable
    identifier. Only fall back to hcp_name when no hcp_id is available.

    hcp_name here always means "the HCP this edit applies to." If the
    user wants to rename the HCP on file, pass the NEW name as hcp_name
    and rely on hcp_id (not the old name) to locate the record.

    Update only fields provided by the user.
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
    Use only when the user explicitly asks about past/previous CRM interactions:
    previous meetings, discussions, materials shared, sentiment history.
    Return CRM data only. Do not invent information.
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
    Process an uploaded pharmaceutical document. Use ONLY when a real file
    is uploaded by the user. Never create fake file paths.
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
    Answer questions using uploaded documents: dosage, contraindications,
    indications, adverse effects, summary.
    Answer only from retrieved documents.
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
    Schedule a new future follow-up appointment. Use only when the user
    explicitly requests scheduling a future appointment. This tool cannot
    look up, modify, or cancel an existing follow-up.
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
