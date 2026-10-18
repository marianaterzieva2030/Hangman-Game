import requests
import re
import random

WORDS = []
URL_REQUEST = 'https://api.dictionaryapi.dev/api/v2/entries/en/'
ERROR_MESSAGE = 'No definition found. Better luck next time!'

with open('english_words.txt', 'r') as file:
    for line in file:
        if line.count(' ') or line.count('-') or bool(re.search(r'\d', line)):
            continue
        if len(line) <= 10:
            WORDS.append(line[0:len(line) - 1])


class WordGenerator:
    """Random word generator."""

    def __init__(self):
        self.word = self.generate_word()
        self.definition = self.get_definition()
        self.validate_definition()
    
    def generate_word(self):
        rand_index = random.randint(0, len(WORDS) - 1)
        return WORDS[rand_index]
    
    def get_definition(self):
        url = URL_REQUEST + self.word
        response = requests.get(url)
        data = response.json()
        meanings = None
        try:
            meanings = data[0]['meanings']
        except KeyError:
            return ERROR_MESSAGE
        
        first_definition = meanings[0]['definitions'][0]['definition']
        return first_definition
    
    def validate_definition(self):
        while self.definition == ERROR_MESSAGE:
            self.word = self.generate_word()
            self.definition = self.get_definition()


# generator = WordGenerator()
# print(f'word: {generator.word}')
# print(f'definition: {generator.definition}')