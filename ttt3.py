import sys

if sys.version_info >= (3, 0):
    from tkinter import Tk, Button
    from tkinter.font import Font
else:
    from Tkinter import Tk, Button
    from tkFont import Font
from copy import deepcopy


class Board:

    def __init__(self, other=None):
        self.player = 'X'
        self.opponent = 'O'
        self.empty = '.'
        self.size = 3
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


class GUI:

    def __init__(self):
        self.app = Tk()
        self.app.title('TicTacToe')
        self.app.resizable(width=True, height=True)
        self.board = Board()
        self.font = Font(family="Helvetica", size=32)
        self.buttons = {}
        for x in range(self.board.size):
            for y in range(self.board.size):
                handler = lambda x=x, y=y: self.move(x, y)
                button = Button(self.app, command=handler, font=self.font, width=2, height=1)
                button.grid(row=y, column=x)
                self.buttons[x, y] = button
        handler = lambda: self.reset()
        button = Button(self.app, text='reset', command=handler)
        button.grid(row=self.board.size + 1, column=0, columnspan=self.board.size, sticky="WE")
        self.update()

    def reset(self):
        self.board = Board()
        self.update()

    def move(self, x, y):
        self.app.config(cursor="watch")
        self.app.update()
        self.board = self.board.move(x, y)
        self.update()
        move = self.board.best()
        if move:
            self.board = self.board.move(*move)
            self.update()
        self.app.config(cursor="")

    def update(self):
        for x in range(self.board.size):
            for y in range(self.board.size):
                text = self.board.grid[x][y]
                self.buttons[x, y]['text'] = text
                self.buttons[x, y]['disabledforeground'] = 'black'
                if text == self.board.empty:
                    self.buttons[x, y]['state'] = 'normal'
                else:
                    self.buttons[x, y]['state'] = 'disabled'
        winning = self.board.won()
        if winning:
            for x, y in winning:
                self.buttons[x, y]['disabledforeground'] = 'red'
            for x, y in self.buttons:
                self.buttons[x, y]['state'] = 'disabled'
        for x in range(self.board.size):
            for y in range(self.board.size):
                self.buttons[x, y].update()

    def mainloop(self):
        self.app.mainloop()


if __name__ == '__main__':
    GUI().mainloop()
