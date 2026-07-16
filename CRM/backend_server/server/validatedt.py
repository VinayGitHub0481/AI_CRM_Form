
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










































# def validate_date_time(meeting_date:str,meeting_time:str):
   
#    DEFAULT_TIME=time(9,0)
#    PARSE_SETTINGS={"PREFER_DATES_FROM":"future"}
   
#    #checking for date 

#    if meeting_date:
#        parsed_date=dateparser.parse(meeting_date,settings=PARSE_SETTINGS)
#        if parsed_date is None:
#            raise ValueError("Invalid date")
#        final_date=parsed_date.date()
#    else:
#        final_date=datetime.now().date()   #default date 
#        print(final_date)

    
#    #checking for time 
   
#    if meeting_time:
#        parsed_time=dateparser.parse(meeting_time, settings=PARSE_SETTINGS)
#        if parsed_time is None:
#            raise ValueError("Invalid time ")
#        final_time=parsed_time.time()
#    else:
#        final_time=DEFAULT_TIME


#    return final_date,final_time
















































#-----------------------------------------------------

# import json
# import ast 

# #validating the response for the too_message 

# def parse_data(data):

#     if isinstance(data,dict):
#         return data 
    
#     if isinstance(data,str):

#         try:

#             #validating json 
#             return json.loads(data)
        
#         except json.JSONDecodeError:
#             pass 
        

#         try:
#                 #python dict String then 
#             return ast.literal_eval(data)
            
#         except Exception:
#              return {}
            

#     return {}

