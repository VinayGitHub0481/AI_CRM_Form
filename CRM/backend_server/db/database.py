
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker,declarative_base
from dotenv import load_dotenv
load_dotenv()
import os 

url=os.getenv("DB_URL")
print("url checking",repr(url))

engine=create_engine(url,echo=True)

Sessiondata=sessionmaker(
    autoflush=False,
    autocommit=False,
    bind=engine
)

Base=declarative_base()


def get_db():
    db=Sessiondata()
    try:
      yield db
    finally:
       db.close()





































