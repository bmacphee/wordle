from collections import defaultdict
from copy import copy

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

    we should choose the guess that is likely to eliminate the most words each turn
    this may not be optimal because we might be "cornering" ourselves into a poor guess for next turn but looking ahead
    quickly gets expensive (it may be possible to generate all possible game states with fast enough hardware and large
    enough memory, but this is not done here, nor are shorter look-aheads)

    special case:
    bbb -> eliminations computed differently since the size of the bbb group is equal to the words eliminated

    for the other cases, the words eliminated is the inverse relative to the remaining possible words
    """
    def __init__(self, wordlist, possible_words):
        self.wordlist = wordlist
        self.possible_words = set(possible_words)
        self.char_excludes = set()
        self.position_excludes = {}
        self.char_includes = set()
        self.char_matches = {}
        self.guesses = 1

        # seems to work best on either guess list, but has a worse worst-case
        # TODO: figure out how to verify the best guess given a word list
        self.next_guess = 'roate'  # 'roate' was computed from self.make_guess()
        # from https://github.com/ttop/wordle_starting_guess
        # (this solution has interesting experiments, but isn't necessarily proven)
        # the best option is to look ahead some number of turns (maybe all of them) to determine the right guesses
        # SLATE: 8640
        # STARE: 8487
        # SANER: 8372
        # SNARE: 8363
        # SHARE: 8348
        # STALE: 8337
        # CRATE: 8322
        # CRANE: 8297
        # AROSE: 8275
        # SAUTE: 8271
        # RAISE: 8261
        # ARISE: 8258
        # TRACE: 8214

    def make_guess(self):
        self.guesses += 1
        ties = set()
        max_elims = self.wordlist[0], 0.0
        for i, word in enumerate(self.wordlist):
            expected_elims = self.compute_expected(guess_word=word)
            if expected_elims > max_elims[1]:
                ties.clear()
                max_elims = word, expected_elims
            elif expected_elims == max_elims[1]:
                ties.add(word)
        #     if i % 10 == 0:
        #         print(f"computed {i}")
        # print(f"best first guess: {max_elims[0]}\n")
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
        results = compute_results(self.possible_words, guess_word=guess_word)
        full_match_key = (Color.GREEN,) * len(guess_word)
        # this would actually increase the score of some guesses slightly - so sometimes it is best to guess a word
        full_match_prob = len(results[full_match_key]) / len(self.possible_words)
        full_match_expected = full_match_prob * (len(self.possible_words) - 1)  # can only ever be one full match

        results.pop(full_match_key, None)
        # E(full_elims) = P(full_elim) * count(full_elim)
        # E(full_elims) = count(full_elim)/count(all) * count(full_elim)
        # i.e 50 bbbbb results, 100 possible words -> 50 * 50 / 100 = 250/100 = 25
        full_elim_key = (Color.BLACK,) * 5

        # how many words can actually be eliminated if we choose {word}?
        elims = len(self.possible_words.difference(results[full_elim_key]))
        prob_full_elim = len(results[full_elim_key]) / len(self.possible_words)
        full_elims_expected = prob_full_elim * elims
        results.pop(full_elim_key)

        possible_match_elims_expected = 0

        for result_group, words in results.items():
            assert Color.GREEN in result_group or Color.ORANGE in result_group
            # for each of these groups, they are the only words that match, otherwise they'd appear in a different group
            # i.e. no word appearing in any result group could possibly be a correct guess for any other
            # the probability is fixed (we compute the exact proportion for this scenario)
            prob = len(words) / len(self.possible_words)
            elims = len(self.possible_words) - len(words)
            expected = elims * prob
            possible_match_elims_expected += expected
        return full_elims_expected + possible_match_elims_expected + full_match_expected

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