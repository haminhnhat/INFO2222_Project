'''
db
database file, containing all the logic to interface with the sql database
'''

import sqlalchemy
from sqlalchemy import create_engine, exc
from sqlalchemy.orm import Session
from werkzeug.security import generate_password_hash, check_password_hash
from models import *

from pathlib import Path

# creates the database directory
Path("database") \
    .mkdir(exist_ok=True)

# "database/main.db" specifies the database file
# change it if you wish
# turn echo = True to display the sql output
engine = create_engine("sqlite:///database/main.db", echo=False)

# initializes the database
Base.metadata.create_all(engine)

# inserts a user to the database
def insert_user(username: str, password: str):
    with Session(engine) as session:
        user = User(username=username, password=password)
        session.add(user)
        try:
            session.commit()
            return True
        except sqlalchemy.exc.IntegrityError:
            session.rollback()
            return False

# gets a user from the database
def get_user(username: str):
    with Session(engine) as session:
        user = session.query(User).filter_by(username=username) .one_or_none()
        return user

# add friend for users
def send_friend_request(sender_username: str, receiver_username: str):
    with Session(engine) as session:
        # Check if request already exists
        existing_request = session.query(FriendRequest).filter_by(
            sender_username=sender_username,
            receiver_username=receiver_username).first()
        
        if existing_request:
            print("Friend request already sent.")
            return False

        friend_request = FriendRequest(sender_username=sender_username, receiver_username=receiver_username)
        session.add(friend_request)
        session.commit()
        return True

def get_friends(username: str):
    with Session(engine) as session:
        user = session.query(User).filter_by(username=username).first()
        if user:
            return [friend.username for friend in user.friends]
        else:
            return []

def get_incoming_friend_requests(receiver_username: str):
    with Session(engine) as session:
        # Query for friend requests where the current user is the receiver
        # and the status is still "pending"
        incoming_requests = session.query(FriendRequest).filter_by(
            receiver_username=receiver_username,
            status="pending"
        ).all()
        
        return [{
            'id': request.id,
            'sender_username': request.sender_username,
            'receiver_username': request.receiver_username,
            'status': request.status
        } for request in incoming_requests]

def respond_to_friend_request(request_id: int, accept: bool):
    with Session(engine) as session:
        # Fetch the friend request by ID
        friend_request = session.query(FriendRequest).get(request_id)
        
        if not friend_request:
            print("Friend request not found.")
            return False

        if accept:
            # If accepted, update the request status and create a new friendship
            friend_request.status = "accepted"
            
            sender_user = session.query(User).filter_by(username=friend_request.sender_username).first()
            receiver_user = session.query(User).filter_by(username=friend_request.receiver_username).first()
            
            if sender_user and receiver_user:
                sender_user.friends.append(receiver_user)
                receiver_user.friends.append(sender_user)  # Because of backref, this might be optional
            else:
                print("One of the users involved in the friend request does not exist.")
                return False
        else:
            # If rejected, just update the request status
            friend_request.status = "rejected"
        
        session.commit()
        return True
