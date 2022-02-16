import pguess
import numpy as np
from simulations import get_word_buckets, get_entropies

if __name__ == '__main__':
    with open("all_valid_guesses.txt") as wordlist:
        guess_words = wordlist.read().splitlines()

    with open("possible.txt") as possible:
        possible_words = possible.read().splitlines()

    for guess_word in guess_words:

        g = pguess.Guess([guess_word], possible_words)

        results = g.compute_results(guess_word=guess_word)
        #for x in sorted(results.items(), key=lambda x: len(x[1]), reverse=True):
            #print(x[0], len(x[1]))

        r = get_word_buckets(guess_word, possible_words, guess_words)

        #for x in sorted(r, key=len, reverse=True):
            #print(len(x))

        for x, y in zip(sorted(results.items(), key=lambda x: len(x[1]), reverse=True), sorted(r, key=len, reverse=True)):
            if len(x[1]) != len(y):
                print(x)
                print(y)
                raise Exception(f"{guess_word}")

    #e = get_entropies(["soare", "roate"], possible_words, weights=np.ones(len(possible_words)))
    #print(e)
