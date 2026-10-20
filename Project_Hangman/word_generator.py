import requests
import re
import random

WORDS = []
URL_REQUEST = 'https://freedictionaryapi.com/api/v1/entries/en/'
ERROR_MESSAGE = 'No definition found. Better luck next time!'

with open('english_words.txt', 'r') as file:
    for line in file:
        word = line.strip()
        if ' ' in word or '-' in word or bool(re.search(r'\d', word)):
            continue
        if len(word) in range(3, 10):
            WORDS.append(word)


class WordGenerator:
    """Random word generator."""

    def __init__(self):
        self.word = None
        self.definition = ERROR_MESSAGE
        self.generate_valid_word()

    def generate_word(self):
        rand_index = random.randint(0, len(WORDS) - 1)
        return WORDS[rand_index]
    
    def get_definition(self):
        url = URL_REQUEST + self.word
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()

            # The API returns a dictionary
            entries = data.get('entries', [])

            for entry in entries:
                senses = entry.get('senses', [])
                for sense in senses:
                    definition = sense.get('definition')

                    if definition:
                        return definition
            return ERROR_MESSAGE
        
        except (requests.exceptions.RequestException, 
                ValueError) as error:
            print(f'API request failed for "{self.word}": {error}')
            return ERROR_MESSAGE
    
    def generate_valid_word(self):
        # Avoid an infinite loop if many words don't have definitions.
        max_attempts = min(20, len(WORDS))

        for _ in range(max_attempts):
            self.word = self.generate_word()
            self.definition = self.get_definition()

            if self.definition != ERROR_MESSAGE:
                return

        self.word = None
        self.definition = ERROR_MESSAGE


# Code for testing purposes:
# generator = WordGenerator()
# if generator.word is not None:
#     print(f'word: {generator.word}')
#     print(f'definition: {generator.definition}')
# else:
#     print('Failed to generate a valid word with a definition.')