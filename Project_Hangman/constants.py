import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
FONT_DIR = BASE_DIR / 'font'
IMAGE_DIR = BASE_DIR / 'images'

NO_CHALLENGES_MSG = 'No challenges yet...'

# where the client connects, these are not the server's bind settings
SERVER_HOST = os.environ.get('HANGMAN_SERVER_HOST', '127.0.0.1')
SERVER_PORT = int(os.environ.get('HANGMAN_SERVER_PORT', 9999))

MODES = {
    'start': 0, 'login': 1, 'register': 2, 'home': 3, 'game_modes': 4,
    'leaderboard': 5, 'friends': 6, 'send_challenge': 7, 'play': 8,
}
LOGGED_IN_MODES = {MODES[m] for m in
                   ('home', 'game_modes', 'leaderboard', 'friends', 'send_challenge', 'play')}