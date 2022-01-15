#!/usr/bin/python
import concurrent.futures
from collections import defaultdict

import pguess
from server import Color, Server, RemoteServer
from concurrent.futures import ProcessPoolExecutor


PARALLEL = 10

def run_guess(word, words, possible_words):
    server = Server(word)
    guesser = pguess.Guess(words, possible_words)
    while True:
        guess_word = guesser.next_guess
        result = server.guess(guess_word)
        if result == [Color.GREEN] * 5:
            return guess_word, guesser.guesses
        guesser.notify_result(result)


def self_eval(guess_words, possible_words):
    total = 0
    six_or_less = 0
    guess_results = defaultdict(int)
    with ProcessPoolExecutor(max_workers=PARALLEL) as executor:
        futures = []
        for word in possible_words:
        # for word in ['crust']:
            futures.append(executor.submit(run_guess, word, guess_words, possible_words))

        for future in concurrent.futures.as_completed(futures):
            word, guesses = future.result()
            total += 1
            six_or_less += 1 if guesses <= 6 else 0
            print(f"success rate {six_or_less}/{total} - {six_or_less/total*100}%; guessed {word} in {guesses} guesses")
            guess_results[guesses] += 1
        print(guess_results)


def interactive(guess_words, possible_words):
    server = RemoteServer()
    guesser = pguess.Guess(guess_words, possible_words)
    while True:
        guess_word = guesser.next_guess
        result = server.guess(guess_word)
        if result == [Color.GREEN] * 5:
            return guess_word, guesser.guesses
        guesser.notify_result(result)


if __name__ == '__main__':
    choice = input("Run test? [N/y] ")
    with open("wordle.txt") as wordlist:
        guess_words = wordlist.read().splitlines()

    with open("possible.txt") as possible:
        possible_words = possible.read().splitlines()

    if choice.lower() == 'y':
        self_eval(guess_words, possible_words)
    else:
        interactive(guess_words, possible_words)
