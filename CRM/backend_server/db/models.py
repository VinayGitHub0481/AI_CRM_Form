
from sqlalchemy import Column,Integer,String,Text,ForeignKey,Date,Time,JSON
from db.database import Base



#new interaction details gets inserted in to db 
class Interaction_data(Base):

    __tablename__="interact"


    id_=Column(Integer,primary_key=True,index=True)

    hcp_name=Column(String(50))

    interaction_type=Column(String(50))

    meeting_date=Column(Date)

    meeting_time=Column(Time)

    attendees=Column(JSON)

    hcp_sentiment=Column(String(50))

    topics=Column(JSON)

    materials=Column(JSON)




class Follow_Up(Base):

    __tablename__="appointment"

    a_id=Column(Integer,primary_key=True)
    hcp_id=Column(Integer,ForeignKey("interact.id_"))#setting the relation between interact table and this table 
    hcp_name=Column(String(50))
    meeting_date=Column(Date)
    meeting_time=Column(Time)
    purpose=Column(String(100))
    status=Column(String(30),default="Scheduled")

























































