from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI,Form,UploadFile,File
from pydantic import BaseModel
from server.langgraph_agent import graph
from pathlib import Path
import shutil
from langchain_core.messages import HumanMessage
from fastapi.middleware.cors import CORSMiddleware
import os 

app=FastAPI()

URL=os.getenv("REACT_URL")

#here enabling the CORS  for sharing between frontend and backend 

app.add_middleware(
    CORSMiddleware,
    allow_origins=[URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


class ChatRequest(BaseModel):
    user_id: int
    user_query: str


#here passing the user query to the lang-graph where it calls the llm to handle 
@app.post("/chat")
async def user_input(user_request:ChatRequest):
    #here graph is a compiled graph where all the nodes are connected through edges 
    #compiled graph is invoking the human messages 

    #by this thread_id each user have his own conversation history
    config={
        "configurable":{
            "thread_id":str(user_request.user_id)
        },
    }
    
    result=graph.invoke(
        {
            "messages":[
                HumanMessage(content=user_request.user_query) 
            ],
            "form":{},

            "outcome": "",

            "summary":"",

            "followUp": {}

        },
        config=config,
    )
    
    print(result["form"])
    print("\n========== FINAL MESSAGES ==========")

    for i, msg in enumerate(result["messages"]):
        print(f"\nMESSAGE {i}")
        print("TYPE:", type(msg).__name__)
        print("CONTENT:", repr(msg.content))
        print("TOOL CALLS:", getattr(msg, "tool_calls", None))

    print("====================================\n")
    print(result["outcome"])
    print(result["followUp"])
    print(result["summary"])

    return {
        "chat_response":result["messages"][-1].content,  #here last message will be shown as response
         
         "form":result.get("form",{}),

         "outcome":result.get("outcome",""),

         "summary":result.get("summary",""),

         "followUp":result.get(
             
              "followUp",
                {
            "required": False,
            "date": "",
            "purpose": ""
        }
             
         )
    }



UPLOAD_DIR = "uploads" #considering temporary directory 

@app.post("/upload")
async def upload_file(
    user_id: int = Form(...),
    file: UploadFile = File(...)
):

    Path(UPLOAD_DIR).mkdir(exist_ok=True)

    file_path = f"{UPLOAD_DIR}/{file.filename}"

    with open(file_path, "wb") as byte_data:
        shutil.copyfileobj(file.file, byte_data)

    config = {
        "configurable": {
            "thread_id": str(user_id)
        }
    }

    result = graph.invoke(   #here graph will invoke and call the respective tool 
        {
            "messages": [
                HumanMessage(
                    content=f"I uploaded a PDF located at {file_path}. Please process it."
                )
            ]
        },
        config=config
    )

    return {
        "chat_response": result["messages"][-1].content,
        "form":result.get("form",{})
    }






























































