class GameState:
    """Read-only snapshot of a game, as reported by the server."""

    FIELDS = ('mode', 'mystery_word', 'used_letters', 'guesses_left', 'hint_used',
              'definition', 'word_guessed', 'is_over', 'points_earned', 'points', 'word')

    def __init__(self, data):
        self.update(data)

    def update(self, data):
        """Replace this snapshot in place, so the UI keeps the same object."""
        for field in self.FIELDS:
            setattr(self, field, data[field])