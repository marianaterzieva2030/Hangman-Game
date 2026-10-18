from db import *
from word_generator import *

GUESSES_START_COUNT = 10
POINTS_WITH_HINT = 5
POINTS_NO_HINT = 10

CHALLENGE_INVALID_WORD = 'oops'
CHALLENGE_INVALID_HINT = 'invalid word and/or definition, pal...'

class Game:
    """Base hangman game class."""

    def __init__(self, user_id, mode):
        self.user = session.query(User).filter_by(id=user_id).first()
        self.mode = mode
        self.word = ''
        self.mystery_word = ''
        self.definition = ''
        self.used_letters = set()

        self.guesses_left = 0
        self.to_guess = set()
        self.hint_used = False
        self.word_guessed = False

    def guess_(self, letter, hint_points, no_hint_points):
        if re.search(r'[A-Z]', letter):
            letter = letter.lower()
        elif re.search(r'[^a-zA-z]', letter):
            return False
        self.guesses_left -= 1
        self.used_letters.add(letter)

        if letter in self.to_guess:
            self.to_guess.remove(letter)
            self.update_mystery_word(letter)
            if len(self.to_guess) == 0:
                self.word_guessed = True
                if self.hint_used:
                    self.user.points += hint_points
                else:
                    self.user.points += no_hint_points
                session.commit()
            return True
        return False

    def guess(self, letter):
        if self.mode == "Zen":
            return self.guess_(letter, 0, 0)
        return self.guess_(letter, POINTS_WITH_HINT, POINTS_NO_HINT)
    
    def use_hint(self):
        self.hint_used = True
        self.guesses_left = min(self.guesses_left, len(self.to_guess))
        print(self.definition)
    
    def update_mystery_word(self, letter):
        for i in range(len(self.word)):
            if self.word[i] == letter:
                self.mystery_word = self.mystery_word[:i] + letter + self.mystery_word[i + 1:]
    

class Challenge(Game):
    """Friend challenge mode class."""

    def __init__(self, user_id, word, definition):
        super().__init__(user_id, 'Challenge')
        if re.search(r'[A-Z]', word):
            word = word.lower()
        elif re.search(r'[^a-zA-z]', word):
            word = CHALLENGE_INVALID_WORD
            definition = CHALLENGE_INVALID_HINT
        self.word = word
        self.mystery_word = '-' * len(self.word)
        self.definition = definition

        self.to_guess = set(self.word)
        self.guesses_left = GUESSES_START_COUNT
    

class Zen(Game):
    """Zen mode class."""

    def __init__(self, user_id):
        super().__init__(user_id, 'Zen')
        generator = WordGenerator()
        self.word = generator.word
        self.mystery_word = '-' * len(self.word)
        self.definition = generator.definition

        self.to_guess = set(self.word)
        self.guesses_left = GUESSES_START_COUNT


class Competition(Game):
    """Competition mode class."""

    def __init__(self, user_id):
        super().__init__(user_id, 'Competition')
        generator = WordGenerator()
        self.word = generator.word
        self.mystery_word = '-' * len(self.word)
        self.definition = generator.definition

        self.to_guess = set(self.word)
        self.guesses_left = GUESSES_START_COUNT
    


# def replace_letters(source, word, letter):
#     for i in range(len(source)):
#         if source[i] == letter:
#             word = word[:i] + letter + word[i + 1:]
#     return word


# game = Challenge(1, 'бостан', 'Диня; Място, където се садят дини.')
# mystery_word = '-' * len(game.word)

# print('Game started!')
# print(mystery_word)

# letter = input('Enter your guess: ')
# if (game.guess(letter)):
#     mystery_word = replace_letters(game.word, mystery_word, letter)
#     print(mystery_word)
# print(f'Guesses left: {game.guesses_left}')

# while game.guesses_left > 0:
#     letter = input('Enter your guess: ')
#     if letter == 'Q':
#         break

#     if letter == 'H': # hint
#         game.use_hint()
#         letter = input('Enter your guess: ')
#         continue

#     if (game.guess(letter)):
#         mystery_word = replace_letters(game.word, mystery_word, letter)
#         print(mystery_word)
#         if game.word_guessed:
#             print('You guessed the word!')
#             session.commit()
#             break
#     print(f'Guesses left: {game.guesses_left}')

# print(game.word)
# print(f'User {game.user.auth.username} points: {game.user.points}')