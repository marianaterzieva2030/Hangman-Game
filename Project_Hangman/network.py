import itertools
import socket

from constants import NO_CHALLENGES_MSG
from game_state import GameState
from protocol import send_message, recv_message

CONNECT_TIMEOUT = 5
DEFAULT_TIMEOUT = 5
ACTION_TIMEOUTS = {'new_game': 15}       # must exceed the server's worst case (~10 s, Pitfall 1)


class Network:
    """Thin client for the hangman server. Holds one socket and the login state.

    Not thread-safe: call it only from the pygame main thread.
    """

    def __init__(self, host, port):
        self.addr = (host, port)
        self.sock = None
        self.username = None
        self.points = None
        self._ids = itertools.count(1)

    @property
    def logged_in(self):
        return self.sock is not None and self.username is not None

    def connect(self):
        """Open a new connection (closing any old one). Returns True on success."""
        self.close()
        try:
            self.sock = socket.create_connection(self.addr, timeout=CONNECT_TIMEOUT)
            return True
        except OSError:
            self.sock = None
            return False

    def close(self):
        """Drop the socket. Server-side login state dies with it, so forget this login state too."""
        if self.sock is not None:
            try:
                self.sock.close()
            except OSError:
                pass
        self.sock = None
        self.username = None
        self.points = None

    def disconnect(self):
        """Sign out and drop the socket."""
        if self.sock is not None:
            self.request('logout')
        self.close()

    def request(self, action, **data):
        """Send one request to the server and return the reply dict. Never raises."""
        if self.sock is None and not self.connect():
            return {'ok': False, 'error': 'Server unavailable.', 'connection_lost': True}

        req_id = next(self._ids)
        try:
            self.sock.settimeout(ACTION_TIMEOUTS.get(action, DEFAULT_TIMEOUT))
            send_message(self.sock, {'action': action, 'id': req_id, **data})
            reply = recv_message(self.sock)
            if not isinstance(reply, dict):
                raise ValueError('Reply is not an object.')
            if 'id' not in reply and reply.get('ok') is False:
                # a notice the server sends on its own, e.g. "Server is full."
                self.close()
                reply['connection_lost'] = True
                return reply
            if reply.get('id') != req_id:
                raise ValueError('Reply does not match request.')
            return reply
        except (OSError, ValueError): # timeout, reset, bad JSON, bad framing, bad id
            self.close()
            return {'ok': False, 'error': 'Connection lost.', 'connection_lost': True}


    # Wrappers: these replace the old Network methods
    # A wrapper returns None on success or an error string to show the player

    def _auth(self, action, username, password):
        if not self.connect(): # always use a new connection to log in
            return 'Server unavailable.'
        reply = self.request(action, username=username, password=password)
        if not reply['ok']:
            return reply['error']
        self.username = reply['username']
        self.points = reply['points']
        return None

    def login(self, username, password):
        return self._auth('login', username, password)

    def register(self, username, password):
        return self._auth('register', username, password)

    def new_game(self, mode):
        """Returns a GameState, or an error string (NO_CHALLENGES_MSG for an empty inbox)."""
        reply = self.request('new_game', mode=mode)
        if not reply['ok']:
            return reply['error']
        try:
            return GameState(reply['game'])
        except KeyError:
            self.close()
            return 'Connection lost.'

    def _update_game(self, game, action, **data):
        reply = self.request(action, **data)
        if not reply['ok']:
            return reply['error']
        try:
            game.update(reply['game'])
        except KeyError:
            self.close()
            return 'Connection lost.'
        return None

    def guess(self, game, letter):
        return self._update_game(game, 'guess', letter=letter)

    def hint(self, game):
        return self._update_game(game, 'hint')

    def leaderboard(self):
        """List of {'username', 'points'}, or None on failure."""
        reply = self.request('leaderboard')
        return reply.get('users') if reply['ok'] else None

    def friends(self):
        reply = self.request('friends')
        return reply.get('friends') if reply['ok'] else None

    def send_challenge(self, friend, word, hint):
        reply = self.request('send_challenge', friend=friend, word=word, hint=hint)
        return None if reply['ok'] else reply['error']