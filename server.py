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
    marked_actual = [c for c in actual_word]
    for i, (guess, actual) in enumerate(zip(guess_word, actual_word)):
        if guess == actual:
            result[i] = Color.GREEN
            marked_actual[i] = '_'

    for i, guess in enumerate(guess_word):
        if result[i] == Color.GREEN:
            continue
        try:
            idx = marked_actual.index(guess)
            marked_actual[idx] = '_'
            result[i] = Color.ORANGE
        except ValueError:
            pass

    return tuple(result)


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
                result = tuple([Color.from_char(c) for c in text])
                if len(result) == 5:
                    return result
            except ValueError:
                pass
