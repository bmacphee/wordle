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


def compute_result(actual_word, guess_word):
    result = [Color.BLACK] * len(actual_word)
    positions_used = set()
    for i, (guess, actual) in enumerate(zip(guess_word, actual_word)):
        if guess == actual:
            positions_used.add(i)
            result[i] = Color.GREEN
    marked_word = [c for c in actual_word]
    for i in positions_used:
        marked_word[i] = '_'
    for i, (guess, actual) in enumerate(zip(guess_word, marked_word)):
        if i in positions_used:
            continue
        if guess in marked_word:
            result[i] = Color.ORANGE
    return result


class Server:
    def __init__(self, word):
        self.word = word

    def guess(self, word_guess):
        return compute_result(self.word, word_guess)


def prompt():
    print(f"Enter 5-letter response to continue; b for BLACK/nomatch, g for GREEN/match, o for ORANGE/partial")
    print(f"Example: bgbog")


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
