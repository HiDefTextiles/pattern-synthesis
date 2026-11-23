"""Interchangeable gap fillers for the banner prototype.

Every filler solves the same problem: given the top half of a stretch with some
cells pinned (motif cells, seam columns; -1 = free) and sample charts for the
left and right neighbours, return a fully filled uint8 array that keeps every
pinned cell. Style should drift from the left samples to the right ones.
All randomness comes from the Generator passed in, so a seed fixes the result.

Fillers:
    WfcFiller        overlapping wave function collapse (Gumin 2016)
    EfrosLeungFiller non-parametric pixel sampling (Efros & Leung 1999)
    QuiltFiller      image quilting with minimum-error seams (Efros & Freeman 2001)
    SymmetricFiller  any filler on the left half, mirrored to the right (D2 connector)
    CellularFiller   elementary cellular automaton along the banner (Wolfram 1983)
"""
from __future__ import annotations

import numpy as np
from numpy.lib.stride_tricks import sliding_window_view

from wfc import Contradiction, OverlapModel, OverlapSolver


def _drift(width: int) -> np.ndarray:
    """0 at the left edge, 1 at the right edge."""
    return np.linspace(0.0, 1.0, width)


def _windows(samples: list[np.ndarray], size: int, reflect: bool = True) -> np.ndarray:
    out = []
    for s in samples:
        for v in ([s, s[:, ::-1], s[::-1], s[::-1, ::-1]] if reflect else [s]):
            if v.shape[0] >= size and v.shape[1] >= size:
                out.append(sliding_window_view(v, (size, size)).reshape(-1, size, size))
    return np.concatenate(out) if out else np.zeros((0, size, size), np.uint8)


class Filler:
    name = "base"

    def fill(self, pinned: np.ndarray, left: list[np.ndarray], right: list[np.ndarray],
             rng: np.random.Generator) -> np.ndarray:
        raise NotImplementedError


class WfcFiller(Filler):
    name = "wfc"

    def __init__(self, n: int = 3, attempts: int = 40):
        self.n, self.attempts = n, attempts

    def fill(self, pinned, left, right, rng):
        model = OverlapModel(left + right, n=self.n)
        wl = np.mean(model.counts_by_sample[:len(left)], 0)
        wr = np.mean(model.counts_by_sample[len(left):], 0)
        t = _drift(pinned.shape[1] - self.n + 1)[:, None]
        weights = (1 - t) * wl + t * wr + 1e-4
        for _ in range(self.attempts):
            try:
                return OverlapSolver(model, pinned, weights).solve(rng)
            except Contradiction:
                continue
        return np.where(pinned >= 0, pinned, 0).astype(np.uint8)


class EfrosLeungFiller(Filler):
    """Grow free cells from the known ones outward. Each new cell copies the centre
    of a sample window whose known cells match best (within `eps` of the best).
    Windows are bit-packed so matching is a popcount."""

    name = "efros-leung"

    def __init__(self, window: int = 7, eps: float = 0.15):
        assert window % 2 == 1 and window * window <= 64
        self.w, self.eps = window, eps

    def _pack(self, wins: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        bits = wins.reshape(len(wins), -1).astype(np.uint64)
        weights = (np.uint64(1) << np.arange(bits.shape[1], dtype=np.uint64))
        packed = (bits * weights).sum(1, dtype=np.uint64)
        centre = wins[:, self.w // 2, self.w // 2]
        uniq, inv, counts = np.unique(packed, return_inverse=True, return_counts=True)
        cen = np.zeros(len(uniq), np.uint8)
        cen[inv] = centre
        return uniq, cen, counts

    def fill(self, pinned, left, right, rng):
        w, r = self.w, self.w // 2
        sides = [self._pack(_windows(s, w)) for s in (left, right)]
        H, W = pinned.shape
        grid = np.where(pinned >= 0, pinned, 0).astype(np.uint8)
        known = pinned >= 0
        g = np.pad(grid, r)
        k = np.pad(known, r)
        place = (np.uint64(1) << np.arange(w * w, dtype=np.uint64)).reshape(w, w)
        t = _drift(W)
        while not k[r:r + H, r:r + W].all():
            kk = k[r:r + H, r:r + W]
            nb = sliding_window_view(k, (3, 3))[r - 1:r - 1 + H, r - 1:r - 1 + W].sum((2, 3))
            frontier = np.argwhere(~kk & (nb > 0)) if (nb[~kk] > 0).any() else np.argwhere(~kk)
            order = rng.permutation(len(frontier))
            score = nb[frontier[:, 0], frontier[:, 1]][order]
            for y, x in frontier[order[np.argsort(-score, kind="stable")]]:
                win = g[y:y + w, x:x + w]
                msk = k[y:y + w, x:x + w]
                val = (win.astype(np.uint64) * place).sum(dtype=np.uint64)
                m = (msk.astype(np.uint64) * place).sum(dtype=np.uint64)
                uniq, cen, counts = sides[int(rng.random() < t[x])]
                if len(uniq) == 0:
                    uniq, cen, counts = sides[0] if len(sides[0][0]) else sides[1]
                d = np.bitwise_count((uniq ^ val) & m).astype(float)
                ok = d <= d.min() * (1 + self.eps) + 1e-9
                p = counts * ok
                choice = rng.choice(len(uniq), p=p / p.sum())
                g[y + r, x + r] = cen[choice]
                k[y + r, x + r] = True
        return g[r:r + H, r:r + W].copy()


class QuiltFiller(Filler):
    """Cover the free area with sample blocks, left to right and top to bottom.
    Each block is picked among the best matches to what is already there and is
    cut into place along minimum-error seams; pinned cells are never overwritten."""

    name = "quilting"

    def __init__(self, block: int = 10, overlap: int = 3, tolerance: float = 0.1):
        self.b, self.o, self.tol = block, overlap, tolerance

    @staticmethod
    def _seam(err: np.ndarray) -> np.ndarray:
        """Min-cost vertical path through err (rows x cols); mask True = take new."""
        h, w = err.shape
        cost = err.astype(float).copy()
        for y in range(1, h):
            prev = np.pad(cost[y - 1], 1, constant_values=np.inf)
            cost[y] += np.minimum(np.minimum(prev[:-2], prev[1:-1]), prev[2:])
        mask = np.zeros_like(err, bool)
        x = int(np.argmin(cost[-1]))
        for y in range(h - 1, -1, -1):
            mask[y, x:] = True
            if y:
                lo, hi = max(x - 1, 0), min(x + 2, w)
                x = lo + int(np.argmin(cost[y - 1, lo:hi]))
        return mask

    def fill(self, pinned, left, right, rng):
        b, o = self.b, self.o
        sides = [np.unique(_windows(s, b), axis=0) for s in (left, right)]
        H, W = pinned.shape
        out = np.where(pinned >= 0, pinned, 0).astype(np.uint8)
        known = pinned >= 0
        filled = known.copy()
        t = _drift(W)
        ys = list(range(0, max(H - o, 1), b - o))
        xs = list(range(0, max(W - o, 1), b - o))
        for y in ys:
            for x in xs:
                y0, x0 = min(y, H - b), min(x, W - b)
                tgt = out[y0:y0 + b, x0:x0 + b]
                fm = filled[y0:y0 + b, x0:x0 + b]
                pm = known[y0:y0 + b, x0:x0 + b]
                if pm.all():
                    continue
                cands = sides[int(rng.random() < t[min(x0 + b // 2, W - 1)])]
                if len(cands) == 0:
                    cands = sides[0] if len(sides[0]) else sides[1]
                err = ((cands != tgt[None]) & fm[None]).sum((1, 2)) + 4 * \
                      ((cands != tgt[None]) & pm[None]).sum((1, 2))
                ok = np.where(err <= err.min() * (1 + self.tol) + 1e-9)[0]
                blk = cands[rng.choice(ok)]
                take = ~pm
                diff = (blk != tgt) & fm
                if x0 > 0 and fm[:, :o].any():
                    take &= np.pad(self._seam(diff[:, :o]), ((0, 0), (0, b - o)), constant_values=True)
                if y0 > 0 and fm[:o].any():
                    take &= np.pad(self._seam(diff[:o].T).T, ((0, b - o), (0, 0)), constant_values=True)
                take |= ~fm & ~pm
                tgt[take] = blk[take]
                fm[:] = True
        return out


class SymmetricFiller(Filler):
    """Fill the left half with `base`, mirror it onto the right half (pinned cells
    on the right win). Gives a left-right symmetric connector between motifs."""

    def __init__(self, base: Filler):
        self.base = base
        self.name = f"symmetric-{base.name}"

    def fill(self, pinned, left, right, rng):
        H, W = pinned.shape
        half = (W + 1) // 2
        lhs = self.base.fill(pinned[:, :half], left + right, left + right, rng)
        mirrored = np.hstack([lhs, lhs[:, :W - half][:, ::-1]])
        return np.where(pinned >= 0, pinned, mirrored).astype(np.uint8)


class CellularFiller(Filler):
    """Elementary CA along the banner: each column (= knitted row) is the next
    generation of the previous one; pinned cells are written back every step.
    The rule is drawn from the seed; samples are not used."""

    name = "cellular"
    RULES = [18, 22, 26, 30, 45, 54, 57, 60, 73, 90, 105, 110, 126, 146, 150, 182]

    def fill(self, pinned, left, right, rng):
        rule = int(rng.choice(self.RULES))
        table = np.array([(rule >> i) & 1 for i in range(8)], np.uint8)
        H, W = pinned.shape
        out = np.zeros((H, W), np.uint8)
        state = np.where(pinned[:, 0] >= 0, pinned[:, 0], rng.integers(0, 2, H)).astype(np.uint8)
        for x in range(W):
            if x:
                ext = np.concatenate([state[1:2], state, state[-2:-1]])   # reflecting edges
                state = table[4 * ext[:-2] + 2 * ext[1:-1] + ext[2:]]
            state = np.where(pinned[:, x] >= 0, pinned[:, x], state).astype(np.uint8)
            out[:, x] = state
        return out


FILLERS = {
    "wfc": lambda: WfcFiller(),
    "efros-leung": lambda: EfrosLeungFiller(),
    "quilting": lambda: QuiltFiller(),
    "symmetric": lambda: SymmetricFiller(EfrosLeungFiller()),
    "cellular": lambda: CellularFiller(),
}
