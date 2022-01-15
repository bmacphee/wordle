from enum import Enum


class Color(Enum):
    BLACK = 1
    ORANGE = 2
    GREEN = 3

    @staticmethod
    def from_char(char):
        if char == 'b':
            return Color.BLACK
        if char == 'o':
            return Color.ORANGE
        if char == 'g':
            return Color.GREEN
        raise ValueError()

    def __repr__(self):
        return self.name[0]


class Server:
    def __init__(self, word):
        self.word = word

    def guess(self, word_guess):
        result = [Color.BLACK] * len(self.word)
        for i, (guess_char, word_char) in enumerate(zip(word_guess, self.word)):
            if guess_char == word_char:
                result[i] = Color.GREEN
            elif guess_char in self.word:
                result[i] = Color.ORANGE
        return result


def prompt():
    print(f"Enter 5-letter response to continue; b for BLACK/nomatch, g for green/match, o for orange/partial")
    print(f"Example:")
    print(f"  bgbog")


class RemoteServer():
    def guess(self, word_guess):
        print(f"Try {word_guess}")
        while True:
            prompt()
            text = input()

            try:
                result = [Color.from_char(c) for c in text]
                if len(result) == 5:
                    return result
            except ValueError:
                pass
