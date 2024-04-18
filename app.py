'''
app.py contains all of the server application
this is where you'll find all of the get/post request handlers
the socket event handlers are inside of socket_routes.py
'''

from flask import Flask, render_template, request, abort, url_for, redirect, flash, session, jsonify
from flask_socketio import SocketIO
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.exceptions import Conflict
import db
import secrets

# import logging

# this turns off Flask Logging, uncomment this to turn off Logging
# log = logging.getLogger('werkzeug')
# log.setLevel(logging.ERROR)

app = Flask(__name__)
app.secret_key = 'secret_key'
socketio = SocketIO(app)

# secret key used to sign the session cookie
app.config['SECRET_KEY'] = secrets.token_hex()
socketio = SocketIO(app)

# don't remove this!!
import socket_routes

# index page
@app.route("/")
def index():
    return render_template("index.jinja")

# login page
@app.route("/login")
def login():    
    return render_template("login.jinja")

# handles a post request when the user clicks the log in button
@app.route("/login/user", methods=["POST"])
def login_user():
    username = request.json.get("username")
    password = request.json.get("password")
    
    user = db.get_user(username)
    if user is None:
        return jsonify({"error": "No such user exists. Please sign up."}), 401
    elif not check_password_hash(user.password, password):
        return jsonify({"error": "Invalid username or password."}), 401
    
    session["user"] = username
    return jsonify({"message": url_for('show_friend_list')}), 200

#handles sending friend requests
@app.route("/friend_list")
def show_friend_list():
    username = session.get("user")  # Retrieve the current user's username from the session
    if not username:
        flash("Please log in to view the friend list.")
        return redirect(url_for('login'))

    friends = db.get_friends(username)
    incoming_requests = db.get_incoming_friend_requests(username)
    return render_template("friend_list.html", username=username, friends=friends, requests=incoming_requests)

# handles sending friend request
@app.route("/send_friend_request", methods=["POST"])
def send_friend_request_route():
    username1 = session.get("user")
    username2 = request.form.get("username2")

    if db.send_friend_request(username1, username2):
        flash("Friend request sent successfully!")
    else:
        flash("Failed to send friend request.")

    return redirect(url_for('show_friend_list'))

# handles accepting friend request
@app.route("/accept_friend_request/<int:request_id>", methods=["POST"])
def accept_friend_request(request_id):
    if db.respond_to_friend_request(request_id, accept=True):
        flash("Friend request accepted.")
    else:
        flash("Failed to accept friend request.")
    return redirect(url_for('show_friend_list'))

# handles rejecting friend request
@app.route("/reject_friend_request/<int:request_id>", methods=["POST"])
def reject_friend_request(request_id):
    if db.respond_to_friend_request(request_id, accept=False):
        flash("Friend request rejected.")
    else:
        flash("Failed to reject friend request.")
    return redirect(url_for('show_friend_list'))

# handles a get request to the signup page
@app.route("/signup")
def signup():
    return render_template("signup.jinja")

# handles a post request when the user clicks the signup button
@app.route("/signup/user", methods=["POST"])
def signup_user():
    username = request.json.get("username")
    password = request.json.get("password")

    existing_user = db.get_user(username)
    if existing_user:
        # Raise a 409 Conflict exception
        raise Conflict(description="Username already taken. Please choose another one.")
   
   # password is hashed before stored in the database when signing up
    hashed_password = generate_password_hash(password)      
    # Assume db.insert_user handles the actual database insertion
    if db.insert_user(username, hashed_password):
        session["user"] = username # Automatically log the user in 
        return jsonify({"message": url_for('show_friend_list')}), 200
    else:
        return jsonify({"error": "Signup failed"}), 400

# handler when a "404" error happens
@app.errorhandler(404)
def page_not_found(e):
    return jsonify(error=str(e)), 404

# handler when a "409" error happens
@app.errorhandler(409)
def conflict_error(e):
    return jsonify(error=str(e.description)), 409

# handler when a "500" error happens
@app.errorhandler(500)
def internal_server_error(e):
    return jsonify(error=str(e)), 500

# home page, where the messaging app is
@app.route("/home")
def home():
    if request.args.get("username") is None:
        abort(404)
    return render_template("home.jinja", username=request.args.get("username"))

# logout of account
@app.route("/logout")
def logout():
    session.pop("user", None) # Remove user from session
    return redirect(url_for('login'))

@app.route('/chat/<friend_username>')
def chat(friend_username):
    current_user_username = session.get("user")
    if not current_user_username:
        flash("Please log in to access chat rooms.")
        return redirect(url_for('login'))

    # Instead of redirecting, render the chat template directly with both usernames
    return render_template("home.jinja", username=current_user_username, friend_username=friend_username)

@app.route('/upload_public_key', methods=['POST'])
def upload_public_key():
    # Assuming authentication is handled elsewhere
    username = session.get('user')
    public_key = request.form.get('public_key')
    # Store the public key in the database associated with the username
    db.store_public_key(username, public_key)
    return 'Public key stored successfully', 200

@app.route('/get_public_key/<username>', methods=['GET'])
def get_public_key(username):
    # Fetch and return the user's public key
    public_key = db.get_public_key(username)
    if public_key:
        return public_key
    else:
        return 'Public key not found', 404

if __name__ == '__main__':
    ssl_context = ('certificate/localhost.crt', 'certificate/localhost.key')
    socketio.run(app, host='127.0.0.1', port=5001, debug=True, ssl_context = ssl_context)
