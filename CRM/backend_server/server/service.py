
from db.database import engine, Sessiondata
from db.models import Base, Interaction_data, Follow_Up
from server.validatedt import validate_date_time
from typing import List, Optional
import logging
from sqlalchemy.orm import Session


Base.metadata.create_all(bind=engine)

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


# Interaction with the HCP and inserting the data into the MySQL db
def Interaction_details(
    hcp_name: str,
    interactionType: str,
    meeting_date: str,
    meeting_time: str,
    attendees: List[str],
    Hcp_sentiment: Optional[str],
    topics: List[str],
    materials_shared: List[str],
):
    db = Sessiondata()  # connecting with the mysql database

    try:
        valid_date, valid_time = validate_date_time(meeting_date, meeting_time)

        data = Interaction_data(
            hcp_name=hcp_name,
            interaction_type=interactionType,
            attendees=attendees,
            meeting_date=valid_date,
            meeting_time=valid_time,
            hcp_sentiment=Hcp_sentiment,
            topics=topics,
            materials=materials_shared,
        )

        db.add(data)  # here data gets inserted into db
        db.commit()  # data gets committed
        db.refresh(data)

        print(f"Interaction logged successfully for {hcp_name}")
        date_format = data.meeting_date.strftime("%Y-%m-%d") if data.meeting_date else None
        time_format = data.meeting_time.strftime("%I:%M %p") if data.meeting_time else None

        return {
            "success": True,
            "message": "Interaction logged successfully",
            "interaction": {
                "id": data.id_,
                "hcp_name": data.hcp_name,
                "interaction_type": data.interaction_type,
                "date": date_format,
                "time": time_format,
                "attendees": data.attendees,
                "hcp_sentiment": data.hcp_sentiment,
                "topics": data.topics,
                "materials": data.materials,
            },
        }

    except Exception as e:
        db.rollback()
        log.error(f"DB error {e}")

        return {
            "success": False,
            "message": "Unable to log interaction",
        }

    finally:
        db.close()


# think generally db id's can't be exposed to anyone, so
# editing info — resolves the record by hcp_id first (most reliable),
# falling back to hcp_name only when no id is available.
def edit_log_info(
    hcp_id: Optional[int] = None,
    hcp_name: Optional[str] = None,
    hcp_sentiment: Optional[str] = None,
    interaction_type:Optional[str]=None,
    meeting_date: Optional[str] = None,
    meeting_time: Optional[str] = None,
    attendees: Optional[List[str]] = None,
    topics: Optional[List[str]] = None,
    materials: Optional[List[str]] = None,
):
    db = Sessiondata()

    try:
        if hcp_id is not None:
            query = db.query(Interaction_data).filter(Interaction_data.id_ == hcp_id)
        elif hcp_name is not None:
            query = db.query(Interaction_data).filter(Interaction_data.hcp_name == hcp_name)
        else:
            return {
                "success": False,
                "message": "hcp_id or hcp_name is required to locate the interaction",
            }

        # most recent match first, in case multiple rows share a name
        data = query.order_by(Interaction_data.meeting_date.desc()).first()

        if data is None:
            return {
                "success": False,
                "message": "interaction not found",
            }

        if hcp_name is not None:
            data.hcp_name = hcp_name

        if hcp_sentiment is not None:
            data.hcp_sentiment = hcp_sentiment
        
        if interaction_type is not None:
            data.interaction_type = interaction_type

        if topics is not None:
            data.topics = topics

        if materials is not None:
            data.materials = materials

        if meeting_date is not None:
            valid_date, _ = validate_date_time(meeting_date, None)
            data.meeting_date = valid_date

        if meeting_time is not None:
            _, valid_time = validate_date_time(None, meeting_time)
            data.meeting_time = valid_time

        if attendees is not None:
            data.attendees = attendees

        print("Before commit")
        print("Date:", data.meeting_date)
        print("Time:", data.meeting_time)
        print("Topics:", data.topics)
        print("Materials:", data.materials)
        print("Attendees:", data.attendees)
        print("name", data.hcp_name)

        db.commit()
        db.refresh(data)

        print("Commit successful")

        date_format = data.meeting_date.strftime("%Y-%m-%d") if data.meeting_date else None
        time_format = data.meeting_time.strftime("%I:%M %p") if data.meeting_time else None

        return {
            "success": True,
            "message": "Interaction updated successfully",
            "interaction": {
            
                "id": data.id_,
                "hcp_name": data.hcp_name,
                "interaction_type": data.interaction_type,
                "hcp_sentiment": data.hcp_sentiment,
                "date": date_format,
                "time": time_format,
                "attendees": data.attendees,
                "topics": data.topics,
                "materials": data.materials,
            },
        }

    except Exception as e:
        db.rollback()
        print("Error", e)
        return {
            "success": False,
            "message": str(e),
        }

    finally:
        db.close()


# here this service will search the db and extract info to send to the tool
def search_history(hcp_name: str, db: Session):
    # based on the dates we are fetching what has been discussed
    results = (
        db.query(Interaction_data)
        .filter(Interaction_data.hcp_name.ilike(f"%{hcp_name}%"))
        .order_by(Interaction_data.meeting_date.desc())
        .limit(3)
        .all()
    )

    data = []
    for row in results:
        data.append({
            "hcp_name": row.hcp_name,
            "meeting_date": row.meeting_date.strftime("%Y-%m-%d") if row.meeting_date else "",
            "meeting_time": row.meeting_time.strftime("%I:%M %p") if row.meeting_time else "",
            "topics": row.topics,
            "hcp_sentiment": row.hcp_sentiment,
            "materials": row.materials,
        })

    print("search history service")

    return {
        "success": True,
        "message": "data searched successfully",
        "history": data,
    }


def follow_up_scedule(
    name: str,
    db: Session,
    meeting_date: Optional[str],
    meeting_time: Optional[str],
    purpose: str,
):
    # create a schedule with the hcp on e.g. thursday or the 19th of this month

    print("schedule called")
    result = (
        db.query(Interaction_data)
        .filter(Interaction_data.hcp_name.ilike(f"%{name}%"))
        .order_by(Interaction_data.meeting_date.desc())
        .first()
    )

    if result is None:
        return {
            "success": False,
            "message": "no interaction found",
        }

    try:
        # validating date and time
        valid_date, valid_time = validate_date_time(meeting_date, meeting_time)

        data = Follow_Up(
            hcp_id=result.id_,
            hcp_name=name,
            meeting_date=valid_date,
            meeting_time=valid_time,
            purpose=purpose,
            status="Scheduled",
        )

        db.add(data)  # new appointment is inserted into the db
        db.commit()
        db.refresh(data)

        date_format = data.meeting_date.strftime("%Y-%m-%d") if data.meeting_date else None
        time_format = data.meeting_time.strftime("%I:%M %p") if data.meeting_time else None

        response = {
            "success": True,
            "message": "follow up scheduled successfully",
            "appointment_id": data.a_id,
            "hcp_id": data.hcp_id,
            "name": data.hcp_name,
            "meeting_date": date_format,
            "meeting_time": time_format,
            "purpose": data.purpose,
            "status": data.status,
        }

        print(response)
        return response

    except Exception as e:
        db.rollback()
        log.error(f"DB error {e}")
        return {
            "success": False,
            "message": "Unable to schedule follow up",
        }










