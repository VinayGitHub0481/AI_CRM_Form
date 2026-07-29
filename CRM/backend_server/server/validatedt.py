
import dateparser

# #validating date and time 
def validate_date_time(
    meeting_date: str | None,
    meeting_time: str | None
):

    PARSE_SETTINGS = {
        "PREFER_DATES_FROM": "future"
    }

    final_date = None
    final_time = None

    if meeting_date:

        parsed_date = dateparser.parse(
            meeting_date,
            settings=PARSE_SETTINGS
        )

        if parsed_date is None:
            raise ValueError("Invalid date")

        final_date = parsed_date.date()

    if meeting_time:

        parsed_time = dateparser.parse(
            meeting_time,
            settings=PARSE_SETTINGS
        )

        if parsed_time is None:
            raise ValueError("Invalid time")

        final_time = parsed_time.time()

    return final_date, final_time
