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
        self.empty = '.'
        self.grid = [[self.empty for y in range(self.size)] for x in range(self.size)]

        # copy constructor
        if other:
            self.__dict__ = deepcopy(other.__dict__)

    def getPos(self, x, y):
        mask = int(1) << (x * 4 + y)
        for symbol, grid in self.bytesGrid.items():
            if grid & mask:
                return symbol
        return None

    def setPos(self, x, y, symbol):
        mask = int(1) << (x * 4 + y)
        self.bytesGrid[symbol] = self.bytesGrid[symbol] | mask

    def move(self, x, y):
        # board = Board(self)
        self.grid[x][y] = self.player
        (self.player, self.opponent) = (self.opponent, self.player)
        return self

    def undo(self, x, y):
        self.grid[x][y] = self.empty
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
                    if self.grid[x][y] == self.empty:
                        value, __ = self.move(x, y).__minimax(not player)
                        self.undo(x, y)
                        if value > best[0]:
                            best = (value, (x, y))
            return best
        else:
            best = (+2, None)
            for x in range(self.size):
                for y in range(self.size):
                    if self.grid[x][y] == self.empty:
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
                if self.grid[x][y] == self.empty:
                    return False
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
                if self.grid[x][y] == self.opponent:
                    winning += 1
            if winning == self.size:
                return pos

    def __str__(self):
        string = ''
        for y in range(self.size):
            for x in range(self.size):
                string += self.grid[x][y]
            string += "\n"
        return string