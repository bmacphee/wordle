import json
import logging
import math
import os

import itertools as it
import numpy as np


MISS = np.uint8(0)
MISPLACED = np.uint8(1)
EXACT = np.uint8(2)

DATA_DIR = os.path.dirname(os.path.realpath(__file__))

PATTERN_MATRIX_FILE = os.path.join(DATA_DIR, "pattern_matrix.npy")

# To store the large grid of patterns at run time
PATTERN_GRID_DATA = dict()


def words_to_int_arrays(words):
    return np.array([[ord(c)for c in w] for w in words], dtype=np.uint8)


def generate_pattern_matrix(words1, words2):
    """
    A pattern for two words represents the wordle-similarity
    pattern (grey -> 0, yellow -> 1, green -> 2) but as an integer
    between 0 and 3^5. Reading this integer in ternary gives the
    associated pattern.

    This function computes the pairwise patterns between two lists
    of words, returning the result as a grid of hash values. Since
    this can be time-consuming, many operations that can be are vectorized
    (perhaps at the expense of easier readibility), and the the result
    is saved to file so that this only needs to be evaluated once, and
    all remaining pattern matching is a lookup.
    """

    # Number of letters/words
    nl = len(words1[0])
    nw1 = len(words1)  # Number of words
    nw2 = len(words2)  # Number of words

    # Convert word lists to integer arrays
    word_arr1, word_arr2 = map(words_to_int_arrays, (words1, words2))

    # equality_grid keeps track of all equalities between all pairs
    # of letters in words. Specifically, equality_grid[a, b, i, j]
    # is true when words[i][a] == words[b][j]
    equality_grid = np.zeros((nw1, nw2, nl, nl), dtype=bool)
    for i, j in it.product(range(nl), range(nl)):
        equality_grid[:, :, i, j] = np.equal.outer(word_arr1[:, i], word_arr2[:, j])

    # full_pattern_matrix[a, b] should represent the 5-color pattern
    # for guess a and answer b, with 0 -> grey, 1 -> yellow, 2 -> green
    full_pattern_matrix = np.zeros((nw1, nw2, nl), dtype=np.uint8)

    # Green pass
    for i in range(nl):
        matches = equality_grid[:, :, i, i].flatten()  # matches[a, b] is true when words[a][i] = words[b][i]
        full_pattern_matrix[:, :, i].flat[matches] = EXACT

        for k in range(nl):
            # If it's a match, mark all elements associated with
            # that letter, both from the guess and answer, as covered.
            # That way, it won't trigger the yellow pass.
            equality_grid[:, :, k, i].flat[matches] = False
            equality_grid[:, :, i, k].flat[matches] = False

    # Yellow pass
    for i, j in it.product(range(nl), range(nl)):
        matches = equality_grid[:, :, i, j].flatten()
        full_pattern_matrix[:, :, i].flat[matches] = MISPLACED
        for k in range(nl):
            # Similar to above, we want to mark this letter
            # as taken care of, both for answer and guess
            equality_grid[:, :, k, j].flat[matches] = False
            equality_grid[:, :, i, k].flat[matches] = False

    # Rather than representing a color pattern as a lists of integers,
    # store it as a single integer, whose ternary representations corresponds
    # to that list of integers.
    pattern_matrix = np.dot(
        full_pattern_matrix,
        (3**np.arange(nl)).astype(np.uint8)
    )

    return pattern_matrix


def generate_full_pattern_matrix(wordlist):
    pattern_matrix = generate_pattern_matrix(wordlist, wordlist)
    # Save to file
    np.save(PATTERN_MATRIX_FILE, pattern_matrix)
    return pattern_matrix


def get_pattern_matrix(words1, words2, wordlist):
    if not PATTERN_GRID_DATA:
        if not os.path.exists(PATTERN_MATRIX_FILE):
            logging.info("\n".join([
                "Generating pattern matrix. This takes a minute, but",
                "the result will be saved to file so that it only",
                "needs to be computed once.",
            ]))
            generate_full_pattern_matrix(wordlist)
        PATTERN_GRID_DATA['grid'] = np.load(PATTERN_MATRIX_FILE)
        PATTERN_GRID_DATA['words_to_index'] = dict(zip(
            wordlist, it.count()
        ))

    full_grid = PATTERN_GRID_DATA['grid']
    words_to_index = PATTERN_GRID_DATA['words_to_index']

    indices1 = [words_to_index[w] for w in words1]
    indices2 = [words_to_index[w] for w in words2]
    return full_grid[np.ix_(indices1, indices2)]


def pattern_from_string(pattern_string):
    return sum((3**i) * int(c) for i, c in enumerate(pattern_string))


def pattern_to_int_list(pattern):
    result = []
    curr = pattern
    for x in range(5):
        result.append(curr % 3)
        curr = curr // 3
    return result


def pattern_to_string(pattern):
    d = {MISS: "⬛", MISPLACED: "🟨", EXACT: "🟩"}
    return "".join(d[x] for x in pattern_to_int_list(pattern))


def patterns_to_string(patterns):
    return "\n".join(map(pattern_to_string, patterns))


def get_possible_words(guess, pattern, word_list):
    all_patterns = get_pattern_matrix([guess], word_list).flatten()
    return list(np.array(word_list)[all_patterns == pattern])


def get_weights(words, priors):
    frequencies = np.array([priors[word] for word in words])
    total = frequencies.sum()
    if total == 0:
        return np.zeros(frequencies.shape)
    return frequencies / total


# Functions associated with entropy calculation


def get_word_buckets(guess, possible_words, wordlist):
    buckets = [[] for x in range(3**5)]
    hashes = get_pattern_matrix([guess], possible_words, wordlist).flatten()
    for index, word in zip(hashes, possible_words):
        buckets[index].append(word)
    return buckets


def get_pattern_distributions(allowed_words, possible_words, weights):
    """
    For each possible guess in allowed_words, this finds the probability
    distribution across all of the 3^5 wordle patterns you could see, assuming
    the possible answers are in possible_words with associated probabilities
    in weights.

    It considers the pattern hash grid between the two lists of words, and uses
    that to bucket together words from possible_words which would produce
    the same pattern, adding together their corresponding probabilities.
    """
    pattern_matrix = get_pattern_matrix(allowed_words, possible_words, allowed_words)

    n = len(allowed_words)
    distributions = np.zeros((n, 3**5))
    n_range = np.arange(n)
    for j, prob in enumerate(weights):
        distributions[n_range, pattern_matrix[:, j]] += prob
    return distributions




def max_bucket_size(guess, possible_words, weights):
    dist = get_pattern_distributions([guess], possible_words, weights)
    return dist.max()


def get_bucket_sizes(allowed_words, possible_words):
    """
    Returns a (len(allowed_words), 243) shape array reprenting the size of
    word buckets associated with each guess in allowed_words
    """
    weights = np.ones(len(possible_words))
    return get_pattern_distributions(allowed_words, possible_words, weights)


def get_bucket_counts(allowed_words, possible_words):
    """
    Returns the number of separate buckets that each guess in allowed_words
    would separate possible_words into
    """
    bucket_sizes = get_bucket_sizes(allowed_words, possible_words)
    return (bucket_sizes > 0).sum(1)


def entropy_to_expected_score(ent):
    """
    Based on a regression associating entropies with typical scores
    from that point forward in simulated games, this function returns
    what the expected number of guesses required will be in a game where
    there's a given amount of entropy in the remaining possibilities.
    """
    # Assuming you can definitely get it in the next guess,
    # this is the expected score
    min_score = 2**(-ent) + 2 * (1 - 2**(-ent))

    # To account for the likely uncertainty after the next guess,
    # and knowing that entropy of 11.5 bits seems to have average
    # score of 3.5, we add a line to account
    # we add a line which connects (0, 0) to (3.5, 11.5)
    return min_score + 1.5 * ent / 11.5



def get_score_lower_bounds(allowed_words, possible_words):
    """
    Assuming a uniform distribution on how likely each element
    of possible_words is, this gives the a lower boudn on the
    possible score for each word in allowed_words
    """
    bucket_counts = get_bucket_counts(allowed_words, possible_words)
    N = len(possible_words)
    # Probabilities of getting it in 1
    p1s = np.array([w in possible_words for w in allowed_words]) / N
    # Probabilities of getting it in 2
    p2s = bucket_counts / N - p1s
    # Otherwise, assume it's gotten in 3 (which is optimistics)
    p3s = 1 - bucket_counts / N
    return p1s + 2 * p2s + 3 * p3s


def get_two_step_score_lower_bound(first_guess, allowed_words, possible_words):
    """
    Useful to prove what the minimum possible average score could be
    for a given initial guess
    """
    N = len(possible_words)
    buckets = get_word_buckets(first_guess, possible_words)
    min_score = 0
    for bucket in buckets:
        if len(bucket) == 0:
            continue
        lower_bounds = get_score_lower_bounds(allowed_words, bucket)
        min_score += (len(bucket) / N) * lower_bounds.min()
    p = (1 / len(possible_words)) * (first_guess in possible_words)
    return p + (1 - p) * (1 + min_score)


def get_entropies(allowed_words, possible_words, weights):
    if weights.sum() == 0:
        return np.zeros(len(allowed_words))
    distributions = get_pattern_distributions(allowed_words, possible_words, weights)
    return entropy_of_distributions(distributions)


def entropy_of_distributions(distributions, atol=1e-12):
    from scipy.stats import entropy
    axis = len(distributions.shape) - 1
    return entropy(distributions, base=2, axis=axis)
