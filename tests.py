import pytest

from pguess import Guess
from server import Color


def test_a():
    result = Guess.compute_result('index', 'steep')
    assert [Color.BLACK, Color.BLACK, Color.BLACK, Color.GREEN, Color.BLACK] == result

def test_b():
    result = Guess.compute_result('index', 'panda')
    assert [Color.BLACK, Color.BLACK, Color.ORANGE, Color.ORANGE, Color.BLACK] == result

def test_c():
    result = Guess.compute_result('abbey', 'about')
    assert [Color.GREEN, Color.GREEN, Color.BLACK, Color.BLACK, Color.BLACK] == result

def test_d():
    result = Guess.compute_result('crust','trust')
    assert [Color.BLACK, Color.GREEN, Color.GREEN, Color.GREEN, Color.GREEN] == result

def test_e():
    result = Guess.compute_result('trust', 'crust')
    assert [Color.BLACK, Color.GREEN, Color.GREEN, Color.GREEN, Color.GREEN] == result

def test_f():
    result = Guess.compute_result('trust', 'outdo')
    assert [Color.BLACK, Color.ORANGE, Color.ORANGE, Color.BLACK, Color.BLACK] == result

def test_g():
    result = Guess.compute_result('batty', 'treat')
    assert [Color.ORANGE, Color.BLACK, Color.BLACK, Color.ORANGE, Color.ORANGE] == result

def test_h():
    result = Guess.compute_result('abyss', 'hissy')
    assert [Color.BLACK, Color.BLACK, Color.ORANGE, Color.GREEN, Color.ORANGE] == result