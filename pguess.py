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
    bbg => { }
    obg => { ant } <= orange for one letter may be treated as non-matching for probability until a better model is made
    bgg => {}
    ggg => {cat}
    bgb => {}
    gbg => {}
    gbb => {cow}

    Expected elim(cat) = (.625 * 5 words + .125 * 7 + .125 * 7 + .125*7) = 5.75
    Expected elim(dog) = 0.5 * 4 + 0.25 * 6 + 0.125 * 7 * 2 = 5.25
    bbb => {fly, bee, cat, ant}
    bgb => {cow, fox}
    bbg => {pig}
    ggg => {dog}

    pig




    if we guess cat, these are the possible outcomes.  the exact match outcome eliminates possible_words-1 with low
    probability but all guesses have this property, so we can ignore it
    what is the best outcome?  we should choose the guess that eliminates the most words.
    bbb -> easy to compute since the count of bbb results is identical to the words eliminated; we can't do anything more
    with that information (maybe we can have a data structure that lets use quickly know the word count for completely distinct words?
    it probably looks like some kind of graph since many words may be related through others?)
    [cat, ant, |   dog, cow,  |   pig, | bee | fox fly, ]

    any o matches eliminate all words that are missing that letter. g characters exclude all words that have any other character in that position

    if a letter is g, we don't necessarily get an o for other identical characters out of position but present elsewhere
    """
    def __init__(self, wordlist, possible_words):
        self.wordlist = wordlist
        self.possible_words = set(possible_words)
        self.char_excludes = set()
        self.position_excludes = {}
        self.char_includes = set()
        self.char_matches = {}
        self.guesses = 1
        if len(wordlist) > len(possible_words):
            self.next_guess = 'roate'  # computed from self.make_guess() on full word list
        else:
            self.next_guess = 'raise'  # computed from self.make_guess() on all possible answers
        assert self.next_guess in wordlist

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
        word_chosen, expected_elims = max_elims
        #     if i % 10 == 0:
        #         print(f"computed {i}")
        # print(f"best first guess: {max_elims[0]}\n")
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
        results = self.compute_results(guess_word=guess_word)
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
        prob_total = prob_full_elim
        full_elims_expected = prob_full_elim * elims
        results.pop(full_elim_key)

        possible_match_elims_expected = 0

        for result_group, words in results.items():
            assert Color.GREEN in result_group or Color.ORANGE in result_group
            # for each of these groups, they are the only words that match, otherwise they'd appear in a different group
            # i.e. no word appearing in any result group could possibly be a correct guess for any other
            # the probability is fixed (we compute the exact proportion for this scenario)
            prob = len(words) / len(self.possible_words)
            prob_total += prob
            # the eliminations are opposite what is computed for the all-no-match group which is handled already
            # (the words in this group are potential matches,
            #  so the elim count is the difference between that and the whole set)
            if Color.GREEN in result_group:
                elims = self.elim_count(result_group, guess_word)
            else:
                # quicker way to do the elim count  TODO come back and optimize for the G case - there's probably a fast way
                elims = len(self.possible_words) - len(words)

            expected = elims * prob
            possible_match_elims_expected += expected
        return full_elims_expected + possible_match_elims_expected + full_match_expected

    def notify_result(self, result):
        last_guess = self.next_guess
        if result == [Color.GREEN] * 5:
            return

        self.char_excludes = self.compute_exclude_characters(
            self.char_matches, self.char_includes, self.position_excludes, self.char_excludes, last_guess, result
        )
        self.possible_words = self.update_possible_words(
            self.possible_words, self.char_excludes, self.position_excludes, self.char_includes, self.char_matches
        )
        if len(self.possible_words) <= 2:
            self.guesses += 1
            self.next_guess = list(self.possible_words)[0]
            return
        self.next_guess = self.make_guess()
        assert self.next_guess != last_guess

    @staticmethod
    def compute_exclude_characters(char_matches, char_includes, position_excludes, char_excludes, last_guess, result):
        for i, r in enumerate(result):
            char_result = last_guess[i]
            if r == Color.GREEN:
                char_matches[i] = char_result
            if r == Color.ORANGE:
                char_includes.add(char_result)
                position_excludes[i] = char_result
            if r == Color.BLACK:
                position_excludes[i] = char_result
                char_excludes.add(char_result)

        # return the revised set of excludes
        # (BLACK does not necessarily mean it's to be excluded because it might be a character that matched elsewhere)
        return char_excludes - char_includes - set(char_matches.values())

    def compute_results(self, guess_word):
        results = defaultdict(set)
        for pw in self.possible_words:
            result = compute_result(guess_word=guess_word, actual_word=pw)
            results[tuple(result)].add(pw)
        return results

    @staticmethod
    def update_possible_words(possible_words, char_excludes, position_excludes, char_includes, char_matches):
        # do definite eliminations
        possible_words = {
            word for word in possible_words
            if not any(c in word for c in char_excludes) and
            not any(word[idx] == c for idx, c in position_excludes.items())
        }
        # filter for possible matches
        possible_words = {
            word for word in possible_words if
            all(c in word for c in char_includes) and
            all(word[idx] == c for idx, c in char_matches.items())
        }
        return possible_words

    def elim_count(self, result_group, guess_word):
        new_char_matches = copy(self.char_matches)
        new_char_includes = copy(self.char_includes)
        new_position_includes = copy(self.position_excludes)
        new_char_excludes = copy(self.char_excludes)
        new_char_excludes = self.compute_exclude_characters(
            new_char_matches, new_char_includes, new_position_includes, new_char_excludes, guess_word, result_group
        )

        new_possible_words = self.update_possible_words(
            self.possible_words, new_char_excludes, new_position_includes, new_char_includes, new_char_matches
        )

        return len(self.possible_words) - len(new_possible_words)
