import unittest
from hangman import *

class GameTests(unittest.TestCase):
    """Base game test class."""

    def setUp(self):
        self.game = Game(1, 'Zen')
        self.game.word = 'apple'
        self.game.mystery_word = '-----'
    
    def test_update_mystery_word(self):
        self.game.guess('p')
        self.assertEqual(self.game.mystery_word, '-pp--')
    
    def test_guesses_left_diminue(self):
        count_before_guess = self.game.guesses_left
        self.game.guess('b')
        self.assertEqual(self.game.guesses_left, count_before_guess - 1)
    
    def test_win(self):
        self.game.guess('a')
        self.game.guess('p')
        self.game.guess('l')
        self.game.guess('e')
        self.assertTrue(self.game.word_guessed)
    
    def test_loss(self):
        self.game.guess('b')
        self.game.guess('c')
        self.game.guess('d')
        self.game.guess('f')
        self.game.guess('g')
        self.game.guess('h')
        self.game.guess('i')
        self.game.guess('a')
        self.game.guess('l')
        self.game.guess('e')
        self.assertFalse(self.game.word_guessed)
    
    def test_uppercase_guess(self):
        self.assertTrue(self.game.guess('A'))
    
    def test_non_letter_guess(self):
        self.assertFalse(self.game.guess('-'))
    

class ZenGameTests(unittest.TestCase):
    """Zen mode test class."""

    def setUp(self):
        self.game = Zen(1)
        self.game.word = 'dry'
    
    def test_no_addition_of_points(self):
        points_before_guess = self.game.user.points
        self.game.guess('d')
        self.game.guess('r')
        self.game.guess('y')
        self.assertEqual(points_before_guess, self.game.user.points)


class CompetitionGameTests(unittest.TestCase):
    """Competition mode test class."""

    def setUp(self):
        self.game = Competition(1)
        self.game.word = 'spy'
    
    def test_addition_of_points_no_hint(self):
        points_before_guess = self.game.user.points
        self.game.guess('s')
        self.game.guess('p')
        self.game.guess('y')
        self.assertEqual(points_before_guess + POINTS_NO_HINT, self.game.user.points)
    
    def test_addition_of_points_with_hint(self):
        points_before_guess = self.game.user.points
        self.game.guess('s')
        self.game.guess('p')
        self.game.use_hint()
        self.game.guess('y')
        self.assertEqual(points_before_guess + POINTS_WITH_HINT, self.game.user.points)


class ChallengeGameTests(unittest.TestCase):
    """Challenge mode test class."""

    def setUp(self):
        self.game = Challenge(1, 'ki4', 'kitsch-y')
    
    def test_invalid_word(self):
        self.assertEqual(self.game.word, CHALLENGE_INVALID_WORD)
    
    def test_invalid_word(self):
        self.assertEqual(self.game.word, CHALLENGE_INVALID_HINT)

if __name__ == '__main__':
    unittest.main()