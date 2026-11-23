"""Overlapping-model wave function collapse with pinned cells and blended weights.

Follows Gumin (2016): patterns are the N x N windows of the samples, two patterns
are compatible at offset d when they agree on their overlap. Output cell (y, x)
takes the top-left value of the pattern chosen at wave position (y, x); the wave
is non-periodic, so the output is (H, W) with (H - N + 1) x (W - N + 1) positions.

Additions for the banner prototype:
* pinned output cells (value >= 0) restrict every window that covers them;
* weights may vary along x (left sample set -> right sample set), which makes
  the texture drift from one motif's style to the next.
Everything is driven by an explicit numpy Generator, so a seed fixes the output.
"""
from __future__ import annotations

import numpy as np

DIRS = [(0, 1), (1, 0), (0, -1), (-1, 0)]


class Contradiction(Exception):
    pass


class OverlapModel:
    def __init__(self, samples: list[np.ndarray], n: int = 3, reflect: bool = True):
        self.n = n
        index: dict[bytes, int] = {}
        windows: list[np.ndarray] = []
        self.counts_by_sample: list[np.ndarray] = []
        per_sample: list[dict[int, int]] = []
        for s in samples:
            variants = [s, s[:, ::-1], s[::-1], s[::-1, ::-1]] if reflect else [s]
            counts: dict[int, int] = {}
            for v in variants:
                h, w = v.shape
                for y in range(h - n + 1):
                    for x in range(w - n + 1):
                        win = np.ascontiguousarray(v[y:y + n, x:x + n])
                        key = win.tobytes()
                        if key not in index:
                            index[key] = len(windows)
                            windows.append(win)
                        counts[index[key]] = counts.get(index[key], 0) + 1
            per_sample.append(counts)
        self.patterns = np.array(windows)            # (P, n, n)
        p = len(windows)
        for counts in per_sample:
            c = np.zeros(p)
            for k, v in counts.items():
                c[k] = v
            self.counts_by_sample.append(c / c.sum())
        # compat[d][a, b]: pattern b may sit at offset DIRS[d] from pattern a
        self.compat = np.zeros((4, p, p), dtype=bool)
        pats = self.patterns
        for d, (dy, dx) in enumerate(DIRS):
            a = pats[:, max(dy, 0):n + min(dy, 0), max(dx, 0):n + min(dx, 0)]
            b = pats[:, max(-dy, 0):n + min(-dy, 0), max(-dx, 0):n + min(-dx, 0)]
            self.compat[d] = (a.reshape(p, 1, -1) == b.reshape(1, p, -1)).all(-1)

    @property
    def size(self) -> int:
        return len(self.patterns)


class OverlapSolver:
    """Solve one region. `pinned` is an int array, -1 = free, otherwise a fixed value."""

    def __init__(self, model: OverlapModel, pinned: np.ndarray, weights: np.ndarray):
        self.m = model
        self.pinned = pinned
        self.H, self.W = pinned.shape
        n = model.n
        self.h, self.w = self.H - n + 1, self.W - n + 1
        self.weights = weights                        # (w, P): weight per wave column

    def _initial_wave(self) -> np.ndarray:
        n, pats = self.m.n, self.m.patterns
        wave = np.ones((self.h, self.w, self.m.size), dtype=bool)
        ys, xs = np.where(self.pinned >= 0)
        for y, x in zip(ys, xs):
            v = self.pinned[y, x]
            for oy in range(n):
                for ox in range(n):
                    py, px = y - oy, x - ox
                    if 0 <= py < self.h and 0 <= px < self.w:
                        wave[py, px] &= pats[:, oy, ox] == v
        return wave

    def _propagate(self, wave: np.ndarray, stack: list[tuple[int, int]]) -> None:
        compat = self.m.compat
        while stack:
            y, x = stack.pop()
            here = wave[y, x]
            for d, (dy, dx) in enumerate(DIRS):
                ny, nx = y + dy, x + dx
                if not (0 <= ny < self.h and 0 <= nx < self.w):
                    continue
                allowed = compat[d][here].any(0)
                new = wave[ny, nx] & allowed
                if not new.any():
                    raise Contradiction
                if (new != wave[ny, nx]).any():
                    wave[ny, nx] = new
                    stack.append((ny, nx))

    def solve(self, rng: np.random.Generator) -> np.ndarray:
        wave = self._initial_wave()
        if not wave.any(-1).all():
            raise Contradiction
        self._propagate(wave, [(y, x) for y in range(self.h) for x in range(self.w)])
        while True:
            counts = wave.sum(-1)
            open_ = counts > 1
            if not open_.any():
                break
            # weighted Shannon entropy per cell, plus tiny seeded noise for tie-breaking
            w = wave * self.weights[None, :, :] + 1e-12 * wave
            tot = w.sum(-1, keepdims=True)
            pr = np.where(wave, w / tot, 1.0)
            ent = -(pr * np.log(pr)).sum(-1)
            ent = np.where(open_, ent + 1e-6 * rng.random(ent.shape), np.inf)
            y, x = np.unravel_index(np.argmin(ent), ent.shape)
            choice_w = w[y, x] / w[y, x].sum()
            k = rng.choice(self.m.size, p=choice_w)
            wave[y, x] = False
            wave[y, x, k] = True
            self._propagate(wave, [(y, x)])
        k = wave.argmax(-1)                            # (h, w)
        n = self.m.n
        out = np.zeros((self.H, self.W), dtype=np.uint8)
        pats = self.m.patterns
        out[:self.h, :self.w] = pats[k, 0, 0]
        out[self.h:, :self.w] = pats[k[-1], 1:, 0].T     # last rows from bottom windows
        out[:self.h, self.w:] = pats[k[:, -1], 0, 1:]    # last cols from right windows
        out[self.h:, self.w:] = pats[k[-1, -1], 1:, 1:]
        return out
