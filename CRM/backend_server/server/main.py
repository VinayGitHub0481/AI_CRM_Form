
from server.api import app 
import uvicorn 

def main():

    uvicorn.run(app,host='0.0.127.0',port=8000,reload=True)


if __name__=="__main__":
    main()

























