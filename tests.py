from pguess import Guess
from server import Color, compute_result


def test_a():
    result = compute_result('index', 'steep')
    assert (Color.BLACK, Color.BLACK, Color.BLACK, Color.GREEN, Color.BLACK) == result


def test_b():
    result = compute_result('index', 'panda')
    assert (Color.BLACK, Color.BLACK, Color.ORANGE, Color.ORANGE, Color.BLACK) == result


def test_c():
    result = compute_result('abbey', 'about')
    assert (Color.GREEN, Color.GREEN, Color.BLACK, Color.BLACK, Color.BLACK) == result


def test_d():
    result = compute_result('crust','trust')
    assert (Color.BLACK, Color.GREEN, Color.GREEN, Color.GREEN, Color.GREEN) == result


def test_e():
    result = compute_result('trust', 'crust')
    assert (Color.BLACK, Color.GREEN, Color.GREEN, Color.GREEN, Color.GREEN) == result


def test_f():
    result = compute_result('trust', 'outdo')
    assert (Color.BLACK, Color.ORANGE, Color.ORANGE, Color.BLACK, Color.BLACK) == result


def test_g():
    result = compute_result('batty', 'treat')
    assert (Color.ORANGE, Color.BLACK, Color.BLACK, Color.ORANGE, Color.ORANGE) == result


def test_h():
    result = compute_result('abyss', 'hissy')
    assert (Color.BLACK, Color.BLACK, Color.ORANGE, Color.GREEN, Color.ORANGE) == result


def test_j():
    possible = ['waste', 'asset', 'beset', 'roate', 'raise']
    g = Guess(possible, possible)
    g.next_guess = 'sissy'
    g.notify_result((Color.BLACK, Color.BLACK, Color.GREEN, Color.BLACK, Color.BLACK))
    assert g.possible_words == {'waste', 'beset'}
