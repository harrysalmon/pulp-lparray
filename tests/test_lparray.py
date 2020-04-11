import numpy as np
import numpy.random as npr
import pulp as pp

from pulp_lparray import lparray


def test_super_sudoku() -> None:
    """
    A Supersudoku board is a Sudoku board with the additional requirement that
    no single digit can be found at the same coordinates in two boxes.
    """

    def check_super_sudoku(arr: np.ndarray) -> bool:
        alldigits = frozenset([1, 2, 3, 4, 5, 6, 7, 8, 9])
        flat = arr.argmax(axis=-1) + 1

        for col in range(9):
            assert set(flat[:, col // 3, :, col % 3].ravel()) == alldigits

        for row in range(9):
            assert set(flat[row // 3, :, row % 3, :].ravel()) == alldigits

        for box in range(9):
            assert set(flat[box // 3, box % 3, :, :].ravel()) == alldigits

        for xy in range(9):
            assert set(flat[:, :, xy // 3, xy % 3].ravel()) == alldigits

        return True

    #                       name      R, C, r, c, n   lb ub type
    X = lparray.create_anon("Board", (3, 3, 3, 3, 9), cat=pp.LpBinary)
    prob = pp.LpProblem("SuperSudoku", pp.LpMinimize)
    (X.sum(axis=-1) == 1).constrain(prob, "OneDigitPerCell")
    (X.sum(axis=(1, 3)) == 1).constrain(prob, "MaxOnePerRow")
    (X.sum(axis=(0, 2)) == 1).constrain(prob, "MaxOnePerCol")
    (X.sum(axis=(2, 3)) == 1).constrain(prob, "MaxOnePerBox")
    (X.sum(axis=(0, 1)) == 1).constrain(prob, "MaxOnePerDust")
    prob.solve()
    board = X.values.argmax(axis=-1)
    print(board)

    assert check_super_sudoku(X.values)


def test_logical_clip() -> None:

    prob = pp.LpProblem("logical_clip", pp.LpMinimize)
    X = lparray.create_anon("arr", (5, 5), cat=pp.LpInteger, lowBound=0, upBound=5)
    (X.sum(axis=1) >= 6).constrain(prob, "colsum")
    (X.sum(axis=0) >= 6).constrain(prob, "rowsum")

    lclip = X.logical_clip(prob, "lclip")

    # dodging these
    bern = npr.binomial(3, 0.5, size=(5, 5))

    prob += (X * bern).sumit()
    prob.solve()

    assert X.values.max() > 1
    assert lclip.values.max() <= 1
    assert lclip.values.max() >= 0


def test_int_max() -> None:
    """
    "The Rook Problem", with maxes.
    """

    prob = pp.LpProblem("int_max", pp.LpMaximize)
    X = lparray.create_anon("arr", (8, 8), cat=pp.LpBinary)
    (X.sum(axis=1) == 1).constrain(prob, "colsum")
    (X.sum(axis=0) == 1).constrain(prob, "rowsum")

    colmax = X.lp_bin_max(prob, "colmax", axis=0)
    rowmax = X.lp_bin_max(prob, "rowmax", axis=1)

    prob += colmax.sumit() + rowmax.sumit()

    prob.solve()
    assert prob.objective == 16


def test_abs() -> None:

    N = 20

    prob = pp.LpProblem("wavechaser", pp.LpMaximize)
    X = lparray.create_anon("arr", (N,), cat=pp.LpInteger, lowBound=-1, upBound=1)
    wave = 2 * npr.binomial(1, 0.5, size=(N,)) - 1

    xp, xm = X.abs_decompose(prob, "abs")
    xabs = xp + xm

    prob += (wave * X).sumit()
    prob.solve()

    print(wave)
    print(xp.values)
    print(xm.values)

    assert prob.objective == N
    assert xabs.values.sum() == N

    assert np.all(xp.values * wave >= 0)
    assert np.all(-xm.values * wave >= 0)
