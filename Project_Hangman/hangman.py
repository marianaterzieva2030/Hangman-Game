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
        self.used_letters = set()

        self.hint_used = False
        self.word_guessed = False

    @property
    def is_over(self): 
        return self.word_guessed or self.guesses_left <= 0
        
    @property
    def points_earned(self):
        if self.mode == 'Zen' or not self.word_guessed: 
            return 0
        return POINTS_WITH_HINT if self.hint_used else POINTS_NO_HINT

    def set_word(self, word, definition):
        self.word = word.lower()
        self.definition = definition
        self.mystery_word = '-' * len(self.word)
        self.to_guess = set(self.word)
        self.guesses_left = GUESSES_START_COUNT

    def guess_(self, letter, hint_points, no_hint_points):
        """Helper function for guess()"""
        letter = letter.lower() if isinstance(letter, str) else ''
        if len(letter) != 1 or not letter.isalpha():
            return False

        if self.word_guessed or self.guesses_left <= 0 or letter in self.used_letters:
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
        if self.hint_used or self.word_guessed or self.guesses_left <= 0:
            return
        self.hint_used = True
        self.guesses_left = min(self.guesses_left, len(self.to_guess))
    
    def update_mystery_word(self, letter):
        for i in range(len(self.word)):
            if self.word[i] == letter:
                self.mystery_word = self.mystery_word[:i] + letter + self.mystery_word[i + 1:]
    

class Challenge(Game):
    """Friend challenge mode class."""

    def __init__(self, user_id, word, definition):
        super().__init__(user_id, 'Challenge')
        if not word:
            word = CHALLENGE_INVALID_WORD
            definition = CHALLENGE_INVALID_HINT
        else:
            for letter in word:
                if not letter.isalpha():
                    word = CHALLENGE_INVALID_WORD
                    definition = CHALLENGE_INVALID_HINT
        self.set_word(word, definition)
    

class Zen(Game):
    """Zen mode class."""

    def __init__(self, user_id):
        super().__init__(user_id, 'Zen')
        generator = WordGenerator()
        self.set_word(generator.word, generator.definition)


class Competition(Game):
    """Competition mode class."""

    def __init__(self, user_id):
        super().__init__(user_id, 'Competition')
        generator = WordGenerator()
        self.set_word(generator.word, generator.definition)
