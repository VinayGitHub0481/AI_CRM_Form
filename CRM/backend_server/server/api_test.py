
#lets check does the api is responding properly or not 

from dotenv import load_dotenv
load_dotenv()
import pytest
import httpx 
from server.api import app 
import logging 

log =logging.getLogger(__name__)

@pytest.mark.asyncio
async def test_api():

    payload={
        "user_id":1,
        "user_query":"interact with dr.mike"
    }

    #bridge between pytest and fastapi application
    #asynchronous server gateway interface 
    transport=httpx.ASGITransport(app=app)

     #this will send the request to the api before starting the server 
    async with httpx.AsyncClient(transport=transport,base_url="http://test") as client:
        response=await client.post("/chat",json=payload)
        log.info("sent request")
    
    assert response.status_code==200

    log.debug("response code ",response.status_code)
    

    response_data=response.json()



    assert isinstance(response_data,dict)

    assert "chat_response" in response_data

    assert "summary" in response_data
    assert "followUp" in response_data 

    assert "form" in response_data
    assert "outcome" in response_data

    print(response_data)











































