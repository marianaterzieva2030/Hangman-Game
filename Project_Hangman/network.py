import socket
import pickle
from db import *
from hangman import *

RECV_FAILED_MSG = 'Failed to receive data from client.'
SEND_FAILED_MSG = 'Failed to send to server.'
NO_CHALLENGES_MSG = 'No challenges yet...'

class Network:
    """A class dealing with connections from the server."""
    def __init__(self, server, port):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server = server #"192.168.1.148"
        self.port = port #9999
        self.addr = (self.server, self.port)
        self.user = None

    def connect(self):
        """Connect to client."""
        try:
            self.client.connect(self.addr)
            return pickle.loads(self.client.recv(4096))
        except:
            return RECV_FAILED_MSG

    def send(self, data):
        try:
            self.client.sendall(pickle.dumps(data))
            return pickle.loads(self.client.recv(4096))
        except socket.error as e:
            print(e)
            return SEND_FAILED_MSG

    def recv_login_user_info(self, info):
        if info == RECV_FAILED_MSG or info == SEND_FAILED_MSG:
            return False
        if isinstance(info, list):
            user_auth = session.query(UserAuth).filter_by(username=info[0]).first()
            if isinstance(user_auth, type(None)):
                return False
            if user_auth.check_password(info[1]):
                self.user = user_auth.user
                return True
        return False
    
    def register_user(self, info):
        if info == RECV_FAILED_MSG or info == SEND_FAILED_MSG:
            return False
        if isinstance(info, list):
            user = session.query(UserAuth).filter_by(username=info[0]).first()

            # no players with this username => OK
            if isinstance(user, type(None)):
                print('No other users with this username.')
                new_user = User(info[0], info[1])
                session.add(new_user)
                session.commit()
                self.user = new_user
                return True
        return False
    
    def get_user_id(self, username):
        user_auth = session.query(UserAuth).filter_by(username=username).first()
        user_id = user_auth.user.id
        return user_id

    def create_game(self, game_mode):
        if game_mode == 'Zen':
            return Zen(self.user.id)
        if game_mode == 'Competition':
            return Competition(self.user.id)
        if game_mode == 'Challenge':
            unused_challenges = [challenge for challenge in self.user.challenges_list if not challenge.is_used]
            if len(unused_challenges) == 0:
                return NO_CHALLENGES_MSG
            for challenge in self.user.challenges_list:
                if not challenge.is_used:
                    challenge.is_used = True
                    session.commit()
                    return Challenge(self.user.id, challenge.word, challenge.hint)
        
    def send_challenge(self, challenge_info):
        if challenge_info == RECV_FAILED_MSG or challenge_info == SEND_FAILED_MSG:
            return False
        if isinstance(challenge_info, list):
            sender_auth = session.query(UserAuth).filter_by(username=challenge_info[0]).first()
            sender = sender_auth.user
            if sender in self.user.friends:
                print('Found friend!')
                new_challenge = FriendChallenge(self.user.id, challenge_info[1], challenge_info[2])
                sender.challenges_list.append(new_challenge)
                session.commit()
                return True
        return False
    
    def get_leaderboard(self):
        """Get the top 5 players."""
        users_list = session.query(User).order_by(User.points.desc()).all()
        if len(users_list) < 5:
            return users_list
        
        leaderboard_list = []
        for i in range(5):
            leaderboard_list.append(users_list[i])
        return leaderboard_list
    
    def get_friends(self):
        friend_list = []
        for friend in self.user.friends:
            friend_list.append(friend)
        return friend_list
    
    def disconnect(self):
        self.user = None
    


# n = Network()
# dictionary = {1: 'hi', 2: 'there'}

# print(n.send(dictionary))
# print(n.send("working"))