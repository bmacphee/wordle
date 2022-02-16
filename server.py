from enum import IntEnum

RESULT_MAP = {}
RESULTS = [(), ]
RESULT_MATRIX = None
TO_RESULT = {}


def generate(elements):
    new_elements = []
    for e in elements:
        new_elements.extend((e + (Color.BLACK,), e + (Color.GREEN,), e + (Color.ORANGE,)))
    return new_elements


def init_maps():
    """
    B = 0
    O = 1
    G = 2
    int_repr = COLOR5*3^4 + COLOR4*3^3 + COLOR3*3^2 + COLOR2*3^1 + COLOR1*3^0
    BBBBB = 0 + 0 + 0 + 0 + 0 = 0
    BBBBO = 0 + 0 + 0 + 0 + 1 = 1
    BBBBG = 0 + 0 + 0 + 0 + 2 = 2
    BBBOB = 0 + 0 + 0 + 3 + 0 = 3
    BBBOO = 0 + 0 + 0 + 3 + 1 = 4
    BBBOG = 0 + 0 + 0 + 3 + 2 = 5
    BBBGB = 0 + 0 + 0 + 6 + 0 = 6
    """
    global RESULTS, RESULT_MAP, RESULT_MATRIX, TO_RESULT
    for _ in range(5):
        RESULTS = generate(RESULTS)

    for r in RESULTS:
        RESULT_MAP[r] = to_int(r)

    for r, i in RESULT_MAP.items():
        TO_RESULT[i] = r

    with open("all_valid_guesses.txt") as wordlist:
        guess_words = wordlist.read().splitlines()

    with open("possible.txt") as solutions:
        solution_words = solutions.read().splitlines()

    RESULT_MATRIX = [[-1 for _ in range(len(solution_words))] for _ in range(len(guess_words))]

    for i, g in enumerate(guess_words):
        for j, p in enumerate(solution_words):
            RESULT_MATRIX[i][j] = to_int(compute_result(g, p))
    # print('done')


class Color(IntEnum):
    BLACK = 0
    ORANGE = 1
    GREEN = 2

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


def to_int(r):
    return r[0] * 3 ** 4 + r[1] * 3 ** 3 + r[2] * 3 ** 2 + r[3] * 3 + r[4] * 1


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

init_maps()

#if __name__ == "__main__":
#    init_maps()