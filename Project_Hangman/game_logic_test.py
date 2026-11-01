import _testenv # noqa F401 (explicitly import this module first)
from _testenv import make_user

import unittest
from unittest.mock import patch

from db import session, User
from hangman import (Game, Zen, Competition, Challenge, GUESSES_START_COUNT,
                     POINTS_WITH_HINT, POINTS_NO_HINT,
                     CHALLENGE_INVALID_WORD, CHALLENGE_INVALID_HINT)

START_POINTS = 1


class FakeGenerator:
    """Replaces WordGenerator so no test calls the dictionary API."""
    word = 'apple'
    definition = 'a round fruit'


class GameTestCase(unittest.TestCase):

    def setUp(self):
        self.user_id = make_user().id
        self.patcher = patch('hangman.WordGenerator', FakeGenerator)
        # patcher is started last!
        # tearDown doesn't run if an exception is raised in setUp, ergo, patcher.stop() won't be called
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()
        session.remove()

    def points(self):
        """Points as stored in the database, not as cached in the session."""
        session.expire_all()
        return session.get(User, self.user_id).points

    def make_game(self, word='apple', mode='Competition'):
        game = Game(self.user_id, mode)
        game.set_word(word, 'a definition')
        return game

    @staticmethod
    def guess_all(game, letters):
        for letter in letters:
            game.guess(letter)


class GuessTests(GameTestCase):

    def test_correct_letter_updates_mystery_word(self):
        game = self.make_game()
        self.assertTrue(game.guess('p'))
        self.assertEqual(game.mystery_word, '-pp--')

    def test_wrong_letter_returns_false(self):
        self.assertFalse(self.make_game().guess('z'))

    def test_every_valid_guess_costs_a_try(self):
        game = self.make_game()
        game.guess('p')
        game.guess('z')
        self.assertEqual(game.guesses_left, GUESSES_START_COUNT - 2)

    def test_win(self):
        game = self.make_game()
        self.guess_all(game, 'aple')
        self.assertTrue(game.word_guessed)
        self.assertEqual(game.mystery_word, 'apple')

    def test_loss(self):
        game = self.make_game()
        self.guess_all(game, 'bcdfghjkmn')
        self.assertEqual(game.guesses_left, 0)
        self.assertTrue(game.is_over)
        self.assertFalse(game.word_guessed)

    def test_uppercase_guess_is_accepted_and_lowercased(self):
        game = self.make_game()
        self.assertTrue(game.guess('A'))
        self.assertIn('a', game.used_letters)

    def test_invalid_input_is_free(self):
        for bad in ('', '-', '1', ' ', 'ab', None, 5):
            with self.subTest(bad=bad):
                game = self.make_game()
                self.assertFalse(game.guess(bad))
                self.assertEqual(game.guesses_left, GUESSES_START_COUNT)
                self.assertEqual(game.used_letters, set())

    def test_repeated_letter_is_free(self):
        game = self.make_game()
        game.guess('z')
        game.guess('z')
        game.guess('Z')
        self.assertEqual(game.guesses_left, GUESSES_START_COUNT - 1)
        self.assertEqual(game.used_letters, {'z'})

    def test_guesses_are_ignored_after_a_win(self):
        game = self.make_game()
        self.guess_all(game, 'aple')
        left = game.guesses_left
        self.assertFalse(game.guess('z'))
        self.assertEqual(game.guesses_left, left)

    def test_guesses_are_ignored_after_a_loss(self):
        game = self.make_game()
        self.guess_all(game, 'bcdfghjkmn')
        self.assertFalse(game.guess('a'))
        self.assertFalse(game.word_guessed)


class HintTests(GameTestCase):

    def test_hint_caps_guesses_at_letters_left(self):
        game = self.make_game() # 4 letters: a, p, l, e
        game.use_hint()
        self.assertTrue(game.hint_used)
        self.assertEqual(game.guesses_left, 4)

    def test_hint_leaves_no_room_for_mistakes(self):
        game = self.make_game()
        game.use_hint()
        game.guess('z') # one mistake after the hint...
        self.guess_all(game, 'apl')
        self.assertTrue(game.is_over) # ...and the word can no longer be finished
        self.assertFalse(game.word_guessed)

    def test_win_with_hint_and_no_mistakes(self):
        game = self.make_game()
        game.use_hint()
        self.guess_all(game, 'aple')
        self.assertTrue(game.word_guessed)

    def test_hint_after_game_over_is_ignored(self):
        game = self.make_game()
        self.guess_all(game, 'bcdfghjkmn')
        game.use_hint()
        self.assertFalse(game.hint_used)


class PointsTests(GameTestCase):

    def test_competition_win_without_hint(self):
        game = self.make_game()
        self.guess_all(game, 'aple')
        self.assertEqual(self.points(), START_POINTS + POINTS_NO_HINT)

    def test_competition_win_with_hint(self):
        game = self.make_game()
        game.use_hint()
        self.guess_all(game, 'aple')
        self.assertEqual(self.points(), START_POINTS + POINTS_WITH_HINT)

    def test_zen_awards_nothing(self):
        game = self.make_game(mode='Zen')
        self.guess_all(game, 'aple')
        self.assertTrue(game.word_guessed)
        self.assertEqual(self.points(), START_POINTS)

    def test_loss_awards_nothing(self):
        self.guess_all(self.make_game(), 'bcdfghjkmn')
        self.assertEqual(self.points(), START_POINTS)

    def test_points_cannot_be_farmed_after_winning(self):
        game = self.make_game()
        self.guess_all(game, 'aple')
        self.guess_all(game, 'zzaple')
        self.assertEqual(self.points(), START_POINTS + POINTS_NO_HINT)

    def test_two_wins_accumulate(self):
        for _ in range(2):
            self.guess_all(self.make_game(), 'aple')
        self.assertEqual(self.points(), START_POINTS + 2 * POINTS_NO_HINT)


class PropertyTests(GameTestCase):

    def test_is_over(self):
        game = self.make_game()
        self.assertFalse(game.is_over)
        self.guess_all(game, 'aple')
        self.assertTrue(game.is_over)

    def test_points_earned(self):
        game = self.make_game()
        self.assertEqual(game.points_earned, 0) # nothing earned mid-game
        self.guess_all(game, 'aple')
        self.assertEqual(game.points_earned, POINTS_NO_HINT)

        hinted = self.make_game()
        hinted.use_hint()
        self.guess_all(hinted, 'aple')
        self.assertEqual(hinted.points_earned, POINTS_WITH_HINT)

        zen = self.make_game(mode='Zen')
        self.guess_all(zen, 'aple')
        self.assertEqual(zen.points_earned, 0)

        lost = self.make_game()
        self.guess_all(lost, 'bcdfghjkmn')
        self.assertEqual(lost.points_earned, 0)


class ModeTests(GameTestCase):

    def test_zen_and_competition_use_the_generator(self):
        for cls, mode in ((Zen, 'Zen'), (Competition, 'Competition')):
            with self.subTest(mode=mode):
                game = cls(self.user_id)
                self.assertEqual(game.mode, mode)
                self.assertEqual(game.word, 'apple')
                self.assertEqual(game.mystery_word, '-----')
                self.assertEqual(game.definition, 'a round fruit')
                self.assertEqual(game.guesses_left, GUESSES_START_COUNT)


class ChallengeTests(GameTestCase):

    def test_cyrillic_word_is_playable(self):
        game = Challenge(self.user_id, 'бостан', 'диня; нива за дини')
        self.assertEqual(game.word, 'бостан')
        self.assertEqual(game.mystery_word, '------')
        self.assertTrue(game.guess('б'))
        self.assertEqual(game.mystery_word, 'б-----')

    def test_word_is_lowercased(self):
        self.assertEqual(Challenge(self.user_id, 'Apple', 'x').word, 'apple')

    def test_valid_hint_is_kept(self):
        self.assertEqual(Challenge(self.user_id, 'tree', 'a plant').definition, 'a plant')

    def test_invalid_words_are_replaced(self):
        for bad in ('ki4', 'Ki4', '', 'two words', 'a-b'):
            with self.subTest(word=bad):
                game = Challenge(self.user_id, bad, 'whatever')
                self.assertEqual(game.word, CHALLENGE_INVALID_WORD)
                self.assertEqual(game.definition, CHALLENGE_INVALID_HINT)
                self.assertEqual(game.guesses_left, GUESSES_START_COUNT) # still a playable game


if __name__ == '__main__':
    unittest.main()