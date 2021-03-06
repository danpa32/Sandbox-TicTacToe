import sys

if sys.version_info >= (3, 0):
    from tkinter import Tk, Button
    from tkinter.font import Font
else:
    from Tkinter import Tk, Button
    from tkFont import Font
from copy import deepcopy


class Board:
    size = 3

    def __init__(self, other=None):
        self.player = 'X'
        self.opponent = 'O'
        self.empty = ' '
        self.grid = [[self.empty for x in range(self.size)] for y in range(self.size)]
        self.winning_cases = []
        self.finished = False

        # copy constructor
        if other:
            self.__dict__ = deepcopy(other.__dict__)

    def move(self, x, y):
        # board = Board(self)
        if self.grid[y][x] == self.empty:
            self.grid[y][x] = self.player
            (self.player, self.opponent) = (self.opponent, self.player)
            return True
        return False

    def undo(self, x, y):
        self.grid[y][x] = self.empty
        (self.player, self.opponent) = (self.opponent, self.player)
        return self

    def __minimax(self, player):
        if self.won():
            if player:
                return -1, None
            else:
                return +1, None
        elif self.tied():
            return 0, None
        elif player:
            best = (-2, None)
            for x in range(self.size):
                for y in range(self.size):
                    if self.grid[y][x] == self.empty:
                        value, __ = self.move(x, y).__minimax(not player)
                        self.undo(x, y)
                        if value > best[0]:
                            best = (value, (x, y))
            return best
        else:
            best = (+2, None)
            for x in range(self.size):
                for y in range(self.size):
                    if self.grid[y][x] == self.empty:
                        value, __ = self.move(x, y).__minimax(not player)
                        self.undo(x, y)
                        if value < best[0]:
                            best = (value, (x, y))
            return best

    def best(self):
        return self.__minimax(True)[1]

    def tied(self):
        for x in range(self.size):
            for y in range(self.size):
                if self.grid[y][x] == self.empty:
                    return False
        self.finished = True
        return True

    winPossibilities = [
        [(0, 0), (1, 0), (2, 0)],
        [(0, 1), (1, 1), (2, 1)],
        [(0, 2), (1, 2), (2, 2)],
        [(0, 0), (0, 1), (0, 2)],
        [(1, 0), (1, 1), (1, 2)],
        [(2, 0), (2, 1), (2, 2)],
        [(0, 0), (1, 1), (2, 2)],
        [(0, 2), (1, 1), (2, 0)]
    ]

    def won(self):
        for pos in Board.winPossibilities:
            winning = 0
            for x, y in pos:
                if self.grid[y][x] == self.opponent:
                    winning += 1
            if winning == self.size:
                self.winning_cases = pos
                self.finished = True
                return pos
        return self.winning_cases

    def __str__(self):
        string = ''
        for y in reversed(range(self.size)):
            for x in reversed(range(self.size)):
                string += self.grid[y][x]
            string += "\n"
        return string