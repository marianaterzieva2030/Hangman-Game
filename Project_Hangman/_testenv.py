"""This module is meant to be imported first-line in every other *test.py file.

Should be marked with # noqa F401 to avoid linters and import sorters from changing the import order.
"""
import os
import uuid

os.environ['HANGMAN_DB_URL'] = 'sqlite://' # in-memory so that the tests never touch database.db
os.environ['SDL_VIDEODRIVER'] = 'dummy' # pygame without a window
os.environ['SDL_AUDIODRIVER'] = 'dummy'

import bcrypt
_real_gensalt = bcrypt.gensalt
bcrypt.gensalt = lambda *args, **kwargs: _real_gensalt(rounds=4) # cost 4 instead of 12 for faster tests

import db                       # noqa: E402
from db import session, User    # noqa: E402

assert db.DB_URL == 'sqlite://', 'tests must never run against the real database'


def unique_name(prefix='user'):
    return f'{prefix}_{uuid.uuid4().hex[:8]}' # <= 20 chars, passes the server's username rule


def make_user(prefix='user', password='pass1234'):
    user = User(unique_name(prefix), password)
    session.add(user)
    session.commit()
    return user