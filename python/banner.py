"""Prototype: an endless, seeded Sjónabók banner (refill).

Layout, across the banner (needle direction, default 85, machine max 179):
    border band | spacer | centre strip with motifs | spacer | border band
Along the banner (row direction) the motif slots k = 0, 1, 2, ... never end.

Random access: slot k's motif depends only on (seed, k); the stretch between
slots k and k+1 depends only on those two motifs and (seed, k). So any window
of the banner can be rendered without generating what comes before it.

Usage (from the repo root):
    python3 python/banner.py --preset all --out out/banners
"""
from __future__ import annotations

import argparse
import re
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from sjonabok import Corpus, Pattern
from wfc import Contradiction, OverlapModel, OverlapSolver

CORPUS_DIR = Path("data/sjonabok/patterns/txt")
MAX_NEEDLES = 179
# yarn preview palette: background + three contrasts (four colours in total)
PALETTE4 = [(240, 232, 214), (122, 30, 38), (34, 52, 99), (176, 120, 30)]
PALETTE2 = [(240, 232, 214), (40, 30, 30), (40, 30, 30), (40, 30, 30)]
# diagnostic palette: background, original cells, -, generated cells
ORIGIN = [(240, 232, 214), (60, 60, 60), (60, 60, 60), (214, 90, 40)]


def source_of(name: str) -> str:
    m = re.match(r"^(.*?)_\d+(_p\d+)?$", name)
    return m.group(1) if m else name


def sub_rng(seed: int, *key: int) -> np.random.Generator:
    return np.random.default_rng(np.random.SeedSequence([seed, *key]))


@dataclass
class MotifPolicy:
    """How slot k chooses its motif."""

    kind: str                       # "mix", "manuscripts" or "derived"
    pool: list[Pattern]
    run_length: int = 3             # slots per manuscript in "manuscripts" mode
    derived_every: int = 2          # in "derived" mode, every n-th slot is new

    def __post_init__(self):
        self.by_source: dict[str, list[Pattern]] = {}
        for p in self.pool:
            self.by_source.setdefault(source_of(p.name), []).append(p)
        self.sources = sorted(self.by_source)

    def _raw(self, seed: int, k: int) -> tuple[list[Pattern], int]:
        rng = sub_rng(seed, 1, k)
        if self.kind == "manuscripts":
            run = k // self.run_length
            group = self.by_source[self.sources[sub_rng(seed, 2, run).integers(len(self.sources))]]
        else:
            group = self.pool
        return group, int(rng.integers(len(group)))

    def original(self, seed: int, k: int) -> Pattern:
        group, i = self._raw(seed, k)
        if k == 0:
            return group[i]
        prev_group, j = self._raw(seed, k - 1)
        if prev_group is group and i == j and len(group) > 1:   # no immediate repeats
            i = (i + 1) % len(group)
        return group[i]


class DerivedMotif:
    """A new D4-symmetric motif with the 'DNA' of originals from one source."""

    def __init__(self, parents: list[Pattern], size: int, n: int = 3):
        self.parents = parents
        self.size = size if size % 2 else size + 1
        self.model = OverlapModel([p.cells for p in parents], n=n)

    def generate(self, rng: np.random.Generator, attempts: int = 30) -> np.ndarray:
        s = self.size
        r = s // 2 + 1
        for _ in range(attempts):
            pinned = -np.ones((r, r), dtype=int)
            pinned[0, :] = 0                                  # outer edge background
            pinned[:, 0] = 0
            weights = np.tile(np.mean(self.model.counts_by_sample, 0), (r - self.model.n + 1, 1))
            try:
                q = OverlapSolver(self.model, pinned, weights).solve(rng)
            except Contradiction:
                continue
            q = np.triu(q) + np.triu(q, 1).T                  # diagonal mirror -> D4 quarter
            top = np.hstack([q, q[:, -2::-1]])
            full = np.vstack([top, top[-2::-1]])
            if full.mean() > 0.15:
                return full.astype(np.uint8)
        raise Contradiction


@dataclass
class Banner:
    name: str
    seed: int
    policy: MotifPolicy
    band: Pattern                   # one period of the border band
    strip: int = 45                 # centre strip height (cells across)
    gap: int = 14                   # free columns between neighbouring motifs
    needles: int = 85               # total knit width; spacers absorb the slack
    n: int = 3
    extras_per_source: int = 3
    corpus: Corpus | None = None
    _cache: dict = field(default_factory=dict, repr=False)

    # ---- motifs -------------------------------------------------------------
    def motif(self, k: int) -> tuple[np.ndarray, str, bool]:
        """Cells, label and whether slot k is derived (generated)."""
        if ("m", k) in self._cache:
            return self._cache[("m", k)]
        orig = self.policy.original(self.seed, k)
        result = (orig.cells, orig.name, False)
        if self.policy.kind == "derived" and k % self.policy.derived_every == 1:
            parents = self.policy.by_source[source_of(orig.name)]
            size = int(np.clip(orig.shape[0], 21, self.strip))
            try:
                cells = DerivedMotif(parents, size, n=self.n).generate(sub_rng(self.seed, 3, k))
                result = (cells, f"new~{source_of(orig.name)}", True)
            except Contradiction:
                pass
        self._cache[("m", k)] = result
        return result

    def width(self, k: int) -> int:
        return self.motif(k)[0].shape[1]

    def _padded(self, cells: np.ndarray) -> tuple[np.ndarray, int]:
        h, w = cells.shape
        top = (self.strip - h) // 2
        out = np.zeros((self.strip, w), dtype=np.uint8)
        out[top:top + h] = cells
        return out, top

    def _extras(self, name: str) -> list[np.ndarray]:
        if self.corpus is None:
            return []
        src = source_of(name) if not name.startswith("new~") else name[4:]
        same = [p for p in self.corpus.patterns.values()
                if source_of(p.name) == src and min(p.shape) >= 5]
        rng = sub_rng(self.seed, 7, sum(map(ord, src)))       # fixed per (seed, source)
        idx = rng.permutation(len(same))[: self.extras_per_source]
        return [same[i].cells for i in idx]

    # ---- the stretch between slot k and k+1 ----------------------------------
    def stretch(self, k: int) -> tuple[np.ndarray, np.ndarray]:
        """Centre-strip cells from the middle of motif k to the middle of motif k+1.

        Returns (cells, generated_mask)."""
        if ("s", k) in self._cache:
            return self._cache[("s", k)]
        (a, an, _), (b, bn, _) = self.motif(k), self.motif(k + 1)
        pa, ta = self._padded(a)
        pb, tb = self._padded(b)
        ca, cb = a.shape[1] // 2, b.shape[1] // 2
        left = pa[:, ca:]
        right = pb[:, :cb + 1]
        width = left.shape[1] + self.gap + right.shape[1]
        pinned = -np.ones((self.strip, width), dtype=int)
        # pin the motif bounding boxes, and the two seam columns, to make stretches agree
        pinned[ta:ta + a.shape[0], :left.shape[1]] = left[ta:ta + a.shape[0]]
        pinned[tb:tb + b.shape[0], width - right.shape[1]:] = right[tb:tb + b.shape[0]]
        pinned[:, 0] = left[:, 0]
        pinned[:, -1] = right[:, -1]

        left_samples = [pa] + self._extras(an)
        right_samples = [pb] + self._extras(bn)
        model = OverlapModel(left_samples + right_samples, n=self.n)
        wl = np.mean(model.counts_by_sample[:len(left_samples)], 0)
        wr = np.mean(model.counts_by_sample[len(left_samples):], 0)
        t = np.linspace(0, 1, width - self.n + 1)[:, None]
        weights = (1 - t) * wl + t * wr + 1e-4                  # style drifts A -> B
        rng = sub_rng(self.seed, 4, k)
        half = self.strip // 2 + 1                         # solve the top half, mirror it
        for _ in range(40):
            try:
                top = OverlapSolver(model, pinned[:half], weights).solve(rng)
                cells = np.vstack([top, top[-2::-1]])
                break
            except Contradiction:
                continue
        else:
            cells = np.where(pinned >= 0, pinned, 0).astype(np.uint8)
        generated = pinned < 0
        self._cache[("s", k)] = (cells, generated)
        return cells, generated

    # ---- render a window of slots -------------------------------------------
    def render(self, first: int, last: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Binary chart for slots first..last, plus a generated-cell mask and,
        per column (= knitted row), the slot that owns it (switch at mid-gap)."""
        parts, gens, owner = [], [], []
        for k in range(first, last):
            cells, gen = self.stretch(k)
            keep = cells.shape[1] - (1 if k < last - 1 else 0)
            parts.append(cells[:, :keep])
            gens.append(gen[:, :keep])
            mid = cells.shape[1] // 2
            owner += [k] * min(mid, keep) + [k + 1] * (keep - min(mid, keep))
        centre = np.hstack(parts).astype(np.uint8)
        generated = np.hstack(gens)
        tile = self.band.cells
        # band phase is a pure function of the first slot, so far windows stay seamless
        phase = int(sub_rng(self.seed, 5, first).integers(tile.shape[1])) if first else 0
        cols = (np.arange(centre.shape[1]) + phase) % tile.shape[1]
        band = tile[:, cols]
        slack = self.needles - self.strip - 2 * band.shape[0]
        if slack < 0:
            raise ValueError(f"band too tall for {self.needles} needles")
        s1, s2 = slack // 2, slack - slack // 2
        sp1 = np.zeros((s1, centre.shape[1]), dtype=np.uint8)
        sp2 = np.zeros((s2, centre.shape[1]), dtype=np.uint8)
        chart = np.vstack([band, sp1, centre, sp2, band[::-1]])
        gmask = np.vstack([np.zeros_like(band, bool), np.zeros_like(sp1, bool), generated,
                           np.zeros_like(sp2, bool), np.zeros_like(band, bool)])
        assert chart.shape[0] <= MAX_NEEDLES, chart.shape
        return chart, gmask, np.array(owner)

    def labels(self, first: int, last: int) -> list[str]:
        return [self.motif(k)[1] for k in range(first, last + 1)]


class ColourPlan:
    """Assign up to four colours (0 = background + three contrasts).

    Knitted rows run across the banner, i.e. down one column of the chart. Each
    column gets background plus ONE contrast colour, chosen per slot; where the
    colour changes, a short dithered switch uses three colours for a few rows."""

    def __init__(self, seed: int, contrasts=(1, 2, 3), switch_rows: int = 4, by=None):
        self.seed, self.contrasts, self.switch_rows, self.by = seed, contrasts, switch_rows, by

    def colour_of_slot(self, k: int) -> int:
        key = self.by(k) if self.by else k
        return self.contrasts[int(sub_rng(self.seed, 6, key).integers(len(self.contrasts)))]

    def apply(self, chart: np.ndarray, owner: np.ndarray) -> np.ndarray:
        col = np.array([self.colour_of_slot(k) for k in owner])
        out = np.where(chart == 1, col[None, :], 0).astype(np.uint8)
        h = self.switch_rows
        for x in np.where(col[1:] != col[:-1])[0] + 1:
            for i in range(-h // 2, h // 2):          # dithered switch around x
                xi = x + i
                if 0 <= xi < chart.shape[1]:
                    frac = (i + h / 2 + 0.5) / h
                    rows = np.arange(chart.shape[0])
                    use_new = ((rows * 7 + xi * 3) % h) < frac * h
                    c = np.where(use_new, col[x], col[x - 1])
                    out[:, xi] = np.where(chart[:, xi] == 1, c, 0)
        return out

    @staticmethod
    def colours_per_row(coloured: np.ndarray) -> np.ndarray:
        return np.array([len(set(coloured[:, x]) | {0}) for x in range(coloured.shape[1])])


def presets(corpus: Corpus) -> dict[str, dict]:
    motifs = [m for m in corpus.motifs(19, 45) if m.shape[0] % 2]   # odd: centred exactly
    return {
        "manuscripts": dict(kind="manuscripts", band="thjms1105_38_p2", seed=11),
        "mix": dict(kind="mix", band="natmus453_734_p3", seed=22),
        "derived": dict(kind="derived", band="natmus453_766_p5", seed=33),
    }, motifs


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--preset", default="all")
    ap.add_argument("--slots", type=int, default=6)
    ap.add_argument("--out", type=Path, default=Path("out/banners"))
    ap.add_argument("--far", type=int, default=1000, help="also render slots starting here")
    ap.add_argument("--colour", action="store_true",
                    help="also apply the (provisional) colour plan; patterns come first")
    args = ap.parse_args()

    corpus = Corpus(CORPUS_DIR)
    table, motifs = presets(corpus)
    args.out.mkdir(parents=True, exist_ok=True)
    names = table if args.preset == "all" else {args.preset: table[args.preset]}
    for name, cfg in names.items():
        policy = MotifPolicy(cfg["kind"], motifs)
        banner = Banner(name, cfg["seed"], policy, corpus.band_tile(cfg["band"]), corpus=corpus)
        windows = [(0, args.slots)]
        if name == "mix":
            windows.append((args.far, args.far + 3))
        plan = None
        if args.colour:                                   # optional later stage
            by = None
            if cfg["kind"] == "manuscripts":
                by = lambda k, b=banner: sum(map(ord, source_of(b.motif(k)[1].replace("new~", ""))))
            plan = ColourPlan(cfg["seed"], by=by)
        for first, last in windows:
            chart, gen, owner = banner.render(first, last)
            stem = f"{name}_seed{cfg['seed']}_slots{first}-{last}"
            Pattern(stem, chart).save_txt(args.out / f"{stem}.txt")
            Pattern(stem, chart).save_png(args.out / f"{stem}.png", PALETTE2, zoom=5)
            Pattern(stem, np.where(chart == 1, np.where(gen, 3, 1), 0).astype(np.uint8)).save_png(
                args.out / f"{stem}_origin.png", ORIGIN, zoom=5)
            extra = ""
            if plan:
                coloured = plan.apply(chart, owner)
                Pattern(stem, coloured).save_txt(args.out / f"{stem}_colour.txt")
                Pattern(stem, coloured).save_png(args.out / f"{stem}_colour.png", PALETTE4, zoom=5)
                extra = f"; rows with 3 colours: {(ColourPlan.colours_per_row(coloured) > 2).sum()}"
            print(f"{stem}: {chart.shape[0]} needles x {chart.shape[1]} rows{extra}; motifs:",
                  ", ".join(banner.labels(first, last)))


if __name__ == "__main__":
    main()
