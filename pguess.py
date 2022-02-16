from collections import defaultdict

from server import Color, compute_result

ENABLE_FAST_GUESS = 0


class Guess:
    """
    probability calculation...
    worldlist : [cat, dog, ant, cow, pig, fly, bee, fox]

    for each word guess, compute the probability for each possible outcome (we can ignore letters in positions we
    already know to reduce the combinations required)
    for each of the remaining words, evaluate the result and count; guess = cat
    bbb => { dog, pig, fly, bee, fox } 62.5%, 12.5% for others
    bbg => {} 0%
    obg => { ant }
    bgg => {} 0%
    ggg => { cat }
    bgb => {} 0%
    gbg => {} 0%
    gbb => { cow }

    Expected elim(cat) = (.625 * 5 words + .125 * 7 + .125 * 7 + .125*7) = 5.75
    Expected elim(dog) = 0.5 * 4 + 0.25 * 6 + 0.125 * 7 * 2 = 5.25

    choose the guess that is likely to eliminate the most words each turn
    this may not be optimal because we might be "cornering" ourselves into worse guesses later
    """
    def __init__(self, wordlist, possible_words):
        self.wordlist = wordlist
        self.possible_words = set(possible_words)
        self.char_excludes = set()
        self.position_excludes = {}
        self.char_includes = set()
        self.char_matches = {}
        self.guesses = 1

        self.next_guess = 'slate'
        # 'roate' is computed from self.make_guess() on all possible answers; trace is another
        # the best option is to look ahead some number of turns (maybe all of them) to determine the right guesses
        # https://github.com/LaurentLessard/wordlesolver has a hard-mode solution that fully explores the solution space
        # and seems to have proven that a greedy approach is not optimal
        # it still seems possible to explore the whole solution space of guesses assuming there are some minimum
        # average proportion of eliminations per step - perhaps it could be done with the small word list;
        # the large one likely adds a few more orders of magnitude to the size of the graph of possible game states

    def make_guess(self):
        self.guesses += 1
        ties = set()
        max_elims = self.wordlist[0], 0.0

        for word in self.wordlist:
            expected_elims = self.compute_expected(guess_word=word)
            if expected_elims > max_elims[1]:
                ties.clear()
                max_elims = word, expected_elims
            elif expected_elims == max_elims[1]:
                ties.add(word)
        #     if i % 10 == 0:
        #         print(f"computed {i}")
        # print(f"best first guess: {max_elims[0]}\n")
        # print(sorted(expected_elim_map.items(), key=itemgetter(1), reverse=True))
        # exit(0)
        word_chosen, expected_elims = max_elims

        # this implements a special case of the "FAST GUESS" which we know is always the correct choice
        if word_chosen not in self.possible_words:
            ties_in_possible_words = ties.intersection(self.possible_words)
            if len(ties_in_possible_words):
                return ties_in_possible_words.pop()

        if not ENABLE_FAST_GUESS:
            return word_chosen
        # this is an approximation of a special case that could be properly computed somehow
        # it's not completely correct probabilistically speaking, so it remains as an option for experimenting
        threshold = 20
        max_guess_elims = list(self.possible_words)[0], 0.0
        if len(self.possible_words) < threshold:
            for i, word in enumerate(self.possible_words):
                expected_guess_elims = self.compute_expected(guess_word=word)
                if expected_guess_elims > max_guess_elims[1]:
                    max_guess_elims = word, expected_guess_elims
        expected_difference = expected_elims - max_guess_elims[1]
        difference_proportion = expected_difference / len(self.possible_words)
        now_guess_probability = 1/len(self.possible_words)
        if now_guess_probability > difference_proportion:
            return max_guess_elims[0]
        else:
            return word_chosen

    def compute_expected(self, guess_word):
        expected_elims = 0
        results = compute_results(self.possible_words, guess_word=guess_word)
        for result_group, words in results.items():
            prob = len(words) / len(self.possible_words)
            elims = len(self.possible_words) - len(words)
            expected = elims * prob
            expected_elims += expected
        return expected_elims

    def notify_result(self, result):
        last_guess = self.next_guess
        if result == [Color.GREEN] * 5:
            return

        self.possible_words = self.update_possible_words(self.possible_words, result, last_guess)
        if len(self.possible_words) <= 2:
            self.guesses += 1
            self.next_guess = list(self.possible_words)[0]
            return
        self.next_guess = self.make_guess()
        assert self.next_guess != last_guess

    @staticmethod
    def update_possible_words(possible_words, result, last_guess):
        return {w for w in possible_words if compute_result(actual_word=w, guess_word=last_guess) == result}


def compute_results(possible_words, guess_word):
    results = defaultdict(set)
    for pw in possible_words:
        result = compute_result(guess_word=guess_word, actual_word=pw)
        results[result].add(pw)
    return results
