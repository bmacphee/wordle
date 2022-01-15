from collections import defaultdict

from server import Color


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
        #self.next_guess = 'raise'  # computed from self.make_guess() on all possible words
        self.next_guess = 'roate'
        #self.next_guess = self.make_guess()

    def make_guess(self):
        self.guesses += 1
        max_elims = self.wordlist[0], 0.0
        for i, word in enumerate(self.wordlist):
            expected_elims = self.compute_expected(guess_word=word)
            if expected_elims > max_elims[1]:
                max_elims = word, expected_elims
        #     if i % 10 == 0:
        #         print(f"computed {i}")
        # print(f"best first guess: {max_elims[0]}\n")
        return max_elims[0]

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

        # TODO replace with correct probability calculations when matches are known
        # so far this only works on first guess, so the skip here prevents infinite loops
        # if word not in self.possible_words:
        #     return full_elims_expected + full_match_expected

        # TODO: seems we need to evaluate each letter position independently for the number of words eliminated by each possible outcome
        # note that some letter positions returned may be redundant, so for each position in the guess word `word` we need to build
        # a subset of the possible words that it would eliminate (some positions can almost be skipped if we already know the letter - but we still need
        # to consider whether a black return value would give us other eliminations from the remaining possible words)
        # the cases of [green]*5 and [black]*5 above are just special cases where we may not actually need to evaluate each letter independently
        # TODO
        # not sure how to determine the expected value from the count in this case when multiple character choices can eliminate the same set of words

        # since we have a set of all possible outcomes - and they're all independent - we don't really care which letter actually eliminates
        # which word - perhaps all we have to do is assign each position a distinct set of eliminations, from left to right until we run out?

        # better get an example

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
            elims = len(self.possible_words) - len(words)
            expected = elims * prob
            possible_match_elims_expected += expected
        return full_elims_expected + possible_match_elims_expected + full_match_expected

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
                self.position_excludes[i] = char_result
                self.char_excludes.add(char_result)
        self.char_excludes = self.char_excludes - self.char_includes - set(self.char_matches.values())

        self.update_possible_words()
        if len(self.possible_words) <= 2:
            self.guesses += 1
            self.next_guess = list(self.possible_words)[0]
            return
        self.next_guess = self.make_guess()
        assert self.next_guess != last_guess

    def compute_results(self, guess_word):
        results = defaultdict(set)
        for pw in self.possible_words:
            result = self.compute_result(guess_word=guess_word, actual_word=pw)
            results[tuple(result)].add(pw)
        return results

    @staticmethod
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

    def update_possible_words(self):
        # do definite eliminations
        self.possible_words = {word for word in self.possible_words
                               if not any(c in word for c in self.char_excludes) and
                               not any(word[idx] == c for idx, c in self.position_excludes.items())}
        # filter for possible matches
        self.possible_words = {word for word in self.possible_words if
                               all(c in word for c in self.char_includes) and all(
                                   word[idx] == c for idx, c in self.char_matches.items())}