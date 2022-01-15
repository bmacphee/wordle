#!/usr/bin/python

from collections import defaultdict
from operator import itemgetter

from server import Color


class Guess:
    def __init__(self, wordlist):
        self.wordlist = wordlist
        self.possible_words = set(wordlist)
        self.char_excludes = set()
        self.position_excludes = {}
        self.char_includes = set()
        self.char_matches = {}
        self.guesses = 0
        self.next_guess = None
        self.make_guess()

    def make_guess(self):
        self.guesses += 1
        if self.next_guess is None:
            self.next_guess = 'sores'
        # for every word in the wordlist, we can figure out how much it's worth making a guess using it
        # to do that, we need to look at what's remaining and determine which guess shares the most in common with
        # the remaining words
        # we'll calculate as follows
        # look at each guess character and count how many words it would possibly match on that position, ignoring known
        # characters
        # the count of word matches determines the score(some characters may match the same word, so we only count that word once)

        pos_alpha_idx = [defaultdict(set) for _ in range(5)]
        for word_i, word in enumerate(self.possible_words):
            for letter_i, letter in enumerate(word[:5]):
                pos_alpha_idx[letter_i][letter].add(word_i)

        match_counts = {}
        for word_i, guess_word in enumerate(self.wordlist):
            matches = set()
            for letter_i, letter in enumerate(guess_word[:5]):
                if letter_i in self.char_matches:
                    # skip the score if the letter already matches in known positions
                    continue
                matches = matches | pos_alpha_idx[letter_i][letter]
            match_counts[word_i] = len(matches)

        guess_scores = sorted(match_counts.items(), key=itemgetter(1), reverse=True)
        highest = max(guess_scores, key=itemgetter(1))[1]
        choose_from = [self.wordlist[word_i] for word_i, c in guess_scores if c == highest]
        prefer = [word for word in choose_from if word in self.possible_words]
        self.next_guess = prefer[0] if prefer else choose_from[0]

    def notify_result(self, result):
        last_guess = self.next_guess
        if result == [Color.GREEN] * 5:
            return

        for i, r in enumerate(result):
            char_result = last_guess[i]
            if r == Color.GREEN:
                self.char_matches[i] = char_result
            if r == Color.ORANGE:
                self.char_includes.add(char_result)
                self.position_excludes[i] = char_result
            if r == Color.BLACK:
                self.char_excludes.add(char_result)
        self.char_excludes = self.char_excludes - self.char_includes - set(self.char_matches.values())

        self.update_possible_words()
        if len(self.possible_words) <= 2:
            self.next_guess = list(self.possible_words)[0]
            return

        self.make_guess()

    def letter_frequencies_of_remaining(self):
        frequencies = [defaultdict(int) for _ in range(5)]
        for word in self.possible_words:  # used to just look at all words
            for i, letter in enumerate(word[:5]):
                frequencies[i][letter] += 1
        return frequencies

    def update_possible_words(self):
        # do definite eliminations
        self.possible_words = {word for word in self.possible_words
                               if not any(c in word for c in self.char_excludes) and
                               not any(word[idx] == c for idx, c in self.position_excludes.items())}
        # filter for possible matches
        self.possible_words = {word for word in self.possible_words if
                               all(c in word for c in self.char_includes) and all(
                                   word[idx] == c for idx, c in self.char_matches.items())}


