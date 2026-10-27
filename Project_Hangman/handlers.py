import functools
import logging
import re
import time

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload
from constants import NO_CHALLENGES_MSG
from db import session, User, UserAuth, FriendsAssociation, FriendChallenge
from hangman import Zen, Challenge, Competition

log = logging.getLogger('hangman.handlers')

USERNAME_REGEX = re.compile(r'[\w.\-]{3,20}$')
MIN_PASS_LENGTH = 4
MAX_PASS_BYTES = 72 # bcrypt's limit
MIN_CHALLENGE_WORD_LENGTH = 2
MAX_CHALLENGE_WORD_LENGTH = 9
MAX_HINT_LENGTH = 80
MAX_FAILED_LOGINS = 5

HANDLERS = {} # dict of handler functions

def new_state():
    """Returns the state of the current connection. One of these per client thread."""

    return {'user': None, 'game': None, 'failed_logins': 0}

def ok(**data):
    return {'ok': True, **data}

def fail(message):
    return {'ok': False, 'error': message}

def action(name):
    """Decorator for registering a function as the handler for request['action'] == name."""

    def register_handler(func):
        HANDLERS[name] = func
        return func
    return register_handler

def login_required(func):
    """Decorator to ensure that the user is logged in prior to executing func."""

    @functools.wraps(func) # keep the original wrapped function's (func) name and docstring
    def wrapper(request, state):
        if state['user'] is None:
            return fail('Please log in first.')
        return func(request, state)
    return wrapper

def text(request, key):
    """Returns request[key] if it is a string, else ''."""
    value = request.get(key, '')
    return value if isinstance(value, str) else ''

@action('ping')
def ping(request, state):
    return ok() # {ok: True}

@action('register')
def register_user(request, state):
    username = text(request, 'username').strip()
    password = text(request, 'password')

    if not USERNAME_REGEX.fullmatch(username):
        return fail('Username must be 3-20 characters (letters, digits, . _ -).')
    if len(password) < MIN_PASS_LENGTH:
        return fail(f'Password must be at least {MIN_PASS_LENGTH} characters.')
    if len(password.encode('utf-8')) > MAX_PASS_BYTES:
        return fail('Password is too long.')
    if session.query(UserAuth).filter_by(username=username).first() is not None:
        return fail('This username is already taken.')

    user = User(username, password)
    session.add(user)
    try:
        session.commit()
    except IntegrityError: # if two clients registered the same name simultaneously
        session.rollback()
        return fail('This username is already taken.')

    state['user'] = user
    state['game'] = None
    return ok(username=username, points=user.points)

@action('login')
def login(request, state):
    if state['failed_logins'] >= MAX_FAILED_LOGINS:
        time.sleep(2) # slows brute force attacks only on this client's thread

    username = text(request, 'username').strip()
    password = text(request, 'password')
    auth = session.query(UserAuth).filter_by(username=username).first()

    if auth is None or not auth.check_password(password):
        state['failed_logins'] += 1
        return fail('Incorrect username or password.')

    state['failed_logins'] = 0
    state['user'] = auth.user
    state['game'] = None
    return ok(username=auth.username, points=auth.user.points)

@action('logout')
def logout(request, state):
    state['user'] = state['game'] = None
    return ok()


def game_to_dict(g):
    return {
        'mode': g.mode,
        'mystery_word': g.mystery_word,
        'used_letters': sorted(g.used_letters), # returns sorted list rather than a set
        'guesses_left': g.guesses_left,
        'hint_used': g.hint_used,
        'definition': g.definition if g.hint_used else '',
        'word_guessed': g.word_guessed,
        'is_over': g.is_over,
        'points_earned': g.points_earned,
        'points': g.user.points,
        'word': g.word if g.is_over else '',
    }

def current_game(state):
    return state['game']

@action('new_game')
@login_required
def new_game(request, state):
    user = state['user']
    mode = request.get('mode')

    if mode == 'Zen':
        game = Zen(user.id)
    elif mode == 'Competition':
        game = Competition(user.id)
    elif mode == 'Challenge':
        challenge = next((word for word in user.challenges_list if not word.is_used), None)
        if challenge is None:
            return fail(NO_CHALLENGES_MSG)
        game = Challenge(user.id, challenge.word, challenge.hint)
        challenge.is_used = True
        session.commit()
    else:
        return fail('Unknown game mode.')

    state['game'] = game
    return ok(game=game_to_dict(game))

@action('guess')
@login_required
def guess(request, state):
    game = state['game']
    if game is None:
        return fail('No game in progress.')
    letter = request.get('letter')
    if not isinstance(letter, str):
        return fail('Invalid guess.')
    game.guess(letter)
    return ok(game=game_to_dict(game))

@action('hint')
@login_required
def hint(request, state):
    game = state['game']
    if game is None:
        return fail('No game in progress.')
    game.use_hint()
    return ok(game=game_to_dict(game))

def user_summary(u):
    return {'username': u.auth.username, 'points': u.points}

@action('leaderboard')
@login_required
def leaderboard(request, state):
    users = (session.query(User)
             .options(selectinload(User.auth))
             .order_by(User.points.desc(), User.id)
             .limit(5)
             .all())
    return ok(users=[user_summary(u) for u in users])

@action('friends')
@login_required
def friends(request, state):
    result = [user_summary(f) for f in state['user'].friends]
    result.sort(key=lambda f: f['username'])
    return ok(friends=result)

@action('send_challenge')
@login_required
def send_challenge(request, state):
    me = state['user']
    friend_name = text(request, 'friend').strip()
    word = text(request, 'word').strip().lower()
    hint = text(request, 'hint').strip()

    friend_auth = session.query(UserAuth).filter_by(username=friend_name).first()
    if friend_auth is None or friend_auth.user not in me.friends:
        return fail('No such friend in your friend list.')
    if not (MIN_CHALLENGE_WORD_LENGTH <= len(word) <= MAX_CHALLENGE_WORD_LENGTH and word.isalpha()):
        return fail(f'Word must be {MIN_CHALLENGE_WORD_LENGTH}-{MAX_CHALLENGE_WORD_LENGTH} characters only.')
    if not hint or len(hint) > MAX_HINT_LENGTH:
        return fail(f'Hint must be 1-{MAX_HINT_LENGTH} characters only.')

    friend_auth.user.challenges_list.append(FriendChallenge(me.id, word, hint))
    session.commit()
    return ok()

@action('add_friend')
@login_required
def add_friend(request, state):
    friend_auth = session.query(UserAuth).filter_by(username=text(request, 'username').strip()).first()
    if friend_auth is None:
        return fail('No such user.')
    if not state['user'].add_friend(friend_auth.user):
        return fail('Already friends, or that is you.')
    session.commit()
    return ok()

def dispatch(request, state):
    try:
        if not isinstance(request, dict):
            return fail('Invalid request.')
        handler = HANDLERS.get(request.get('action'))
        if handler is None:
            return fail('Unknown action.')
        session.expire_all()
        return handler(request, state)
    except Exception:
        session.rollback()
        log.exception('Handler failed.')
        return fail('Server error.')