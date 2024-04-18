'''
models
defines sql alchemy data models
also contains the definition for the room class used to keep track of socket.io rooms

Just a sidenote, using SQLAlchemy is a pain. If you want to go above and beyond, 
do this whole project in Node.js + Express and use Prisma instead, 
Prisma docs also looks so much better in comparison

or use SQLite, if you're not into fancy ORMs (but be mindful of Injection attacks :) )
'''

import datetime
from sqlalchemy import DateTime, String, Table, Column, ForeignKey, Integer, CheckConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from typing import Dict, Text

# data models
class Base(DeclarativeBase):
    pass

friendship_association = Table('friendship', Base.metadata,
    Column('user_id', String, ForeignKey('user.username'), primary_key=True),
    Column('friend_id', String, ForeignKey('user.username'), primary_key=True)
)

# model to store user information
class User(Base):
    __tablename__ = "user"
    
    # looks complicated but basically means
    # I want a username column of type string,
    # and I want this column to be my primary key
    # then accessing john.username -> will give me some data of type string
    # in other words we've mapped the username Python object property to an SQL column of type String 
    username: Mapped[str] = mapped_column(String, primary_key=True)
    password: Mapped[str] = mapped_column(String)
    friends = relationship("User",
                           secondary=friendship_association,
                           primaryjoin=username == friendship_association.c.user_id,
                           secondaryjoin=username == friendship_association.c.friend_id,
                           backref="added_friends")

# stateful counter used to generate the room id
class Counter():
    def __init__(self):
        self.counter = 0
    
    def get(self):
        self.counter += 1
        return self.counter

# Room class, used to keep track of which username is in which room
class Room():
    def __init__(self):
        self.counter = Counter()
        # dictionary that maps the username to the room id
        # for example self.dict["John"] -> gives you the room id of 
        # the room where John is in
        self.dict: Dict[str, int] = {}

    def create_room(self, sender: str, receiver: str) -> int:
        room_id = self.counter.get()
        self.dict[sender] = room_id
        self.dict[receiver] = room_id
        return room_id
    
    def join_room(self,  sender: str, room_id: int) -> int:
        self.dict[sender] = room_id

    def leave_room(self, user):
        if user not in self.dict.keys():
            return
        del self.dict[user]

    # gets the room id from a user
    def get_room_id(self, user: str):
        if user not in self.dict.keys():
            return None
        return self.dict[user]
    
class FriendRequest(Base):
    __tablename__ = 'friend_request'
    id = Column(Integer, primary_key=True)
    sender_username = Column(String, ForeignKey('user.username'), nullable=False)
    receiver_username = Column(String, ForeignKey('user.username'), nullable=False)
    status = Column(String, default="pending")  # Default status is 'pending'

    # Enforce that status is one of 'pending', 'accepted', 'rejected'
    __table_args__ = (
        CheckConstraint(status.in_(['pending', 'accepted', 'rejected'])),
    )
    
    sender = relationship("User", foreign_keys=[sender_username], backref="sent_requests")
    receiver = relationship("User", foreign_keys=[receiver_username], backref="received_requests")
    
# class Message(Base):
#     __tablename__ = 'message'
#     id = Column(Integer, primary_key=True)
#     sender_id = Column(Integer, ForeignKey('user.id'))
#     receiver_id = Column(Integer, ForeignKey('user.id'))
#     content = Column(Text, nullable=False)
#     timestamp = Column(DateTime, default=datetime.utcnow)

#     sender = relationship("User", foreign_keys=[sender_id])
#     receiver = relationship("User", foreign_keys=[receiver_id])
