"""Layout helpers. Boards are laid out top to bottom on a running y; these keep that tidy.

    st = VStack(y=110)
    for k in rows:
        y = st.take(26)            # y of this row, then advance by 26
    cols = Columns(10, [145, 156, 110, 52], gap=6)   # x of each column: cols[0], cols[1] ...
    grid = Grid(x=6, y=112, cell_w=96, cell_h=270, gap_x=2, per_row=5)
    x, y = grid.cell(i)
"""


class VStack:
    def __init__(self, y=0, gap=0):
        self.y, self.gap = y, gap

    def take(self, h, gap=None):
        y = self.y
        self.y += h + (self.gap if gap is None else gap)
        return y

    def skip(self, h):
        self.y += h
        return self.y


class HStack:
    def __init__(self, x=0, gap=0):
        self.x, self.gap = x, gap

    def take(self, w, gap=None):
        x = self.x
        self.x += w + (self.gap if gap is None else gap)
        return x


class Columns:
    def __init__(self, x0, widths, gap=0):
        self.widths = list(widths)
        self.xs = []
        x = x0
        for w in self.widths:
            self.xs.append(x)
            x += w + gap
        self.right = x - gap

    @classmethod
    def at(cls, xs, widths):
        """Columns at explicit x positions."""
        c = cls(0, widths)
        c.xs = list(xs)
        c.right = xs[-1] + widths[-1]
        return c

    def __getitem__(self, i):
        return self.xs[i]

    def width(self, i):
        return self.widths[i]


class Grid:
    def __init__(self, x, y, cell_w, cell_h, gap_x=0, gap_y=0, per_row=None):
        self.x, self.y, self.cw, self.ch, self.gx, self.gy, self.per_row = x, y, cell_w, cell_h, gap_x, gap_y, per_row

    def cell(self, i):
        r, c = divmod(i, self.per_row) if self.per_row else (0, i)
        return self.x + c * (self.cw + self.gx), self.y + r * (self.ch + self.gy)

    def bottom(self, n):
        rows = -(-n // self.per_row) if self.per_row else 1
        return self.y + rows * self.ch + (rows - 1) * self.gy
