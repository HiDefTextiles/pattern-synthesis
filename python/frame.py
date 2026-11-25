"""Frames from four border bands, with a corner connector.

Each side is whole repeat units plus `close` columns (repeats.csv), so it is
mirrored exactly end to end. The band's first row is the outer edge. The four
sides meet in square corners as tall as the band, filled by one of:

    mitre   the bands continue into the corner and meet on the 45-degree diagonal
    motif   a small diagonal-symmetric motif from the book, centred in the corner
    grown   the mitre with a disc in the middle cleared and grown again by the
            WFC filler from the band, mirrored across the diagonal (seeded)

The cut (where a side starts within the repeat) is "best" by default: every cut
that still mirrors exactly is tried and the one with the cleanest corner is kept.
cut="stored" uses the cut from the Sjonabok repository.

Usage (from the repo root):
    python3 python/frame.py --band thjms1105_38_p2 --nx 4 --ny 3 --corner all --out out/frame
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from banner import CORPUS_DIR, source_of
from fillers import EfrosLeungFiller, WfcFiller
from sjonabok import Corpus, Pattern

CORNERS = ("mitre", "motif", "grown")
HI_PALETTE = [(255, 255, 255), (16, 9, 159), (16, 9, 159), (16, 9, 159)]


def palindrome(strip: np.ndarray) -> bool:
    return bool((strip == strip[:, ::-1]).all())


def components(mask: np.ndarray) -> list[int]:
    """Sizes of the 8-connected components of a boolean mask."""
    seen = np.zeros_like(mask, bool)
    H, W = mask.shape
    sizes = []
    for y, x in zip(*np.nonzero(mask)):
        if seen[y, x]:
            continue
        stack, n = [(y, x)], 0
        seen[y, x] = True
        while stack:
            a, b = stack.pop()
            n += 1
            for da in (-1, 0, 1):
                for db in (-1, 0, 1):
                    u, v = a + da, b + db
                    if 0 <= u < H and 0 <= v < W and mask[u, v] and not seen[u, v]:
                        seen[u, v] = True
                        stack.append((u, v))
        sizes.append(n)
    return sizes


def longest_float(chart: np.ndarray) -> int:
    """Longest run of equal cells in any row."""
    best = 0
    for row in chart:
        edges = np.flatnonzero(np.diff(row)) + 1
        runs = np.diff(np.concatenate([[0], edges, [len(row)]]))
        best = max(best, int(runs.max()))
    return best


@dataclass
class Cut:
    """Where a side starts within the repeat unit, and how many columns close it."""
    shift: int
    close: int
    stored: bool = False


class Band:
    """A repeat unit that can be laid out as an exactly mirrored side."""

    def __init__(self, corpus: Corpus, name: str):
        if not corpus.is_unit(name):
            raise ValueError(f"{name} is not a stored repeat unit")
        self.name = name
        self.unit = corpus.band_tile(name).cells.astype(np.uint8)
        self.height, self.period = self.unit.shape
        close = corpus.repeats[name].get("close", "")
        self.stored_close = int(close) if close != "" else None

    def strip(self, n: int, cut: Cut) -> np.ndarray:
        u = np.roll(self.unit, -cut.shift, axis=1)
        return np.hstack([np.tile(u, (1, n)), u[:, :cut.close]])

    def cuts(self) -> list[Cut]:
        """Every (shift, close) that gives a mirrored side, the stored cut first."""
        out = []
        if self.stored_close is not None and palindrome(self.strip(2, Cut(0, self.stored_close))):
            out.append(Cut(0, self.stored_close, stored=True))
        for k in range(self.period):
            for c in (0, 1):
                if (k, c) != (0, self.stored_close) and palindrome(self.strip(2, Cut(k, c))):
                    out.append(Cut(k, c))
        return out


@dataclass
class Frame:
    """A rectangular frame: chart in machine orientation (row = knitted row)."""
    band: Band
    nx: int
    ny: int
    corner: str = "mitre"
    cut: Cut = field(default_factory=lambda: Cut(0, 0))
    seed: int = 1
    corpus: Corpus | None = None
    notes: dict = field(default_factory=dict)

    def __post_init__(self):
        h = self.band.height
        self.top = self.band.strip(self.nx, self.cut)
        self.side = self.band.strip(self.ny, self.cut)
        self.Lx, self.Ly = self.top.shape[1], self.side.shape[1]
        self.W, self.H = 2 * h + self.Lx, 2 * h + self.Ly

    @staticmethod
    def _reflect(a: int, L: int, close: int) -> int:
        """Index along a mirrored side, continued past its ends by reflection."""
        if close == 1:                              # axis through the end columns
            m = 2 * (L - 1)
            a %= m
            return a if a < L else m - a
        m = 2 * L                                   # axis between columns
        a %= m
        return a if a < L else m - 1 - a

    def mitre_corner(self) -> np.ndarray:
        """Top-left corner square: both bands run on and meet on the diagonal."""
        h, c = self.band.height, self.cut.close
        sq = np.zeros((h, h), np.uint8)
        for r in range(h):
            for q in range(h):
                if q >= r:   # nearer the top band
                    sq[r, q] = self.top[r, self._reflect(q - h, self.Lx, c)]
                else:        # nearer the left band
                    sq[r, q] = self.side[q, self._reflect(r - h, self.Ly, c)]
        return sq

    def motif_corner(self) -> np.ndarray:
        h = self.band.height
        group = source_of(self.band.name)
        pool = [p for p in self.corpus.patterns.values()
                if not self.corpus.is_unit(p.name) and p.shape[0] == p.shape[1] <= h - 2
                and p.shape[0] >= 5 and (p.cells == p.cells.T).all()
                and (p.cells == p.cells[::-1, ::-1].T).all()]
        same = [p for p in pool if source_of(p.name) == group]
        pool = sorted(same or pool, key=lambda p: (-p.shape[0], p.name))
        if not pool:
            self.notes["corner_fallback"] = "no small symmetric motif, used mitre"
            return self.mitre_corner()
        biggest = pool[0].shape[0]
        choices = [p for p in pool if p.shape[0] >= biggest - 2]
        m = choices[np.random.default_rng(self.seed).integers(len(choices))]
        self.notes["corner_motif"] = m.name
        sq = np.zeros((h, h), np.uint8)
        o = (h - m.shape[0]) // 2
        sq[o:o + m.shape[0], o:o + m.shape[0]] = m.cells
        return sq

    def grown_corner(self) -> np.ndarray:
        """Start from the mitre, clear a disc in the middle of the square, grow it
        again from the band (WFC, seeded) and mirror it across the diagonal."""
        h = self.band.height
        r, q = np.indices((h, h))
        free = (r - (h - 1) / 2) ** 2 + (q - (h - 1) / 2) ** 2 < (h / 3) ** 2
        mitre = self.mitre_corner()
        pinned = np.where(free, -1, mitre.astype(int))
        # The mitre square is a sample too: the straight band alone has no
        # diagonal neighbourhoods, and WFC then cannot close the corner.
        samples = [self.top, mitre]
        rng = np.random.default_rng(self.seed)
        grown = WfcFiller(n=3).fill(pinned, samples, samples, rng)
        self.notes["corner_filler"] = "wfc"
        if not grown[free].any():   # WFC gave up and returned the background
            grown = EfrosLeungFiller().fill(pinned, samples, samples, rng)
            self.notes["corner_filler"] = "efros-leung"
        return np.where(q >= r, grown, grown.T).astype(np.uint8)

    def corner_square(self) -> np.ndarray:
        return {"mitre": self.mitre_corner, "motif": self.motif_corner,
                "grown": self.grown_corner}[self.corner]()

    def chart(self) -> np.ndarray:
        h = self.band.height
        F = np.zeros((self.H, self.W), np.uint8)
        F[:h, h:h + self.Lx] = self.top
        F[self.H - h:, h:h + self.Lx] = self.top[::-1]
        F[h:h + self.Ly, :h] = self.side.T
        F[h:h + self.Ly, self.W - h:] = self.side.T[:, ::-1]
        sq = self.corner_square()
        F[:h, :h] = sq
        F[:h, self.W - h:] = sq[:, ::-1]
        F[self.H - h:, :h] = sq[::-1]
        F[self.H - h:, self.W - h:] = sq[::-1, ::-1]
        return F

    def corner_score(self) -> tuple[int, int]:
        """Lower is cleaner: stitches in fragments of 1-3 cells near the corner,
        then the longest float there."""
        h = self.band.height
        F = self.chart()
        win = F[:2 * h, :2 * h]
        small = sum(s for s in components(win > 0) if s <= 3)
        return small, longest_float(F[:h, :2 * h])


def best_cut(band: Band, nx: int, ny: int, corner: str, seed: int, corpus: Corpus) -> tuple[Cut, list]:
    tried = []
    for cut in band.cuts():
        score = Frame(band, nx, ny, corner, cut, seed, corpus).corner_score()
        tried.append({"shift": cut.shift, "close": cut.close, "stored": cut.stored,
                      "fragments": score[0], "longest_float": score[1]})
    if not tried:
        raise ValueError(f"{band.name} has no cut that mirrors exactly")
    i = min(range(len(tried)), key=lambda j: (tried[j]["fragments"], tried[j]["longest_float"],
                                              not tried[j]["stored"]))
    return Cut(tried[i]["shift"], tried[i]["close"], tried[i]["stored"]), tried


def labelled(images: list[tuple[str, np.ndarray]], path: Path, zoom: int = 4) -> None:
    """Frames side by side, each with a caption, in the HÍ blue."""
    pal = np.array(HI_PALETTE, np.uint8)
    tiles = [(t, Image.fromarray(pal[c], "RGB").resize((c.shape[1] * zoom, c.shape[0] * zoom),
                                                        Image.NEAREST)) for t, c in images]
    pad, top = 16, 22
    W = sum(i.width for _, i in tiles) + pad * (len(tiles) + 1)
    H = max(i.height for _, i in tiles) + top + pad
    out = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(out)
    x = pad
    for t, i in tiles:
        d.text((x, 4), t, fill=(16, 9, 159))
        out.paste(i, (x, top))
        x += i.width + pad
    out.save(path)


def build(corpus: Corpus, band_name: str, nx: int, ny: int, corner: str, cut_mode: str,
          seed: int) -> tuple[Frame, list]:
    band = Band(corpus, band_name)
    if cut_mode == "best":   # judged on the mitre, so every corner type shares the cut
        cut, tried = best_cut(band, nx, ny, "mitre", seed, corpus)
    else:
        cuts = [c for c in band.cuts() if c.stored]
        if not cuts:
            raise ValueError(f"{band_name}: the stored cut does not mirror (close is empty)")
        cut, tried = cuts[0], []
    return Frame(band, nx, ny, corner, cut, seed, corpus), tried


SITE_BANDS = ["thjms1105_38_p2", "natmus453_732_p1", "natmus453_710_p1",
              "thjms1997-123_448_p3", "thjms1105_88_p4"]


def site_data(corpus: Corpus, out: Path, needles: int = 179, seed: int = 1) -> None:
    """Small 1-bit PNGs (one pixel per stitch) and an index for the docs page.
    Each band gets as many repeats as fit in `needles`."""
    out.mkdir(parents=True, exist_ok=True)
    index = []
    for name in SITE_BANDS:
        band = Band(corpus, name)
        nx = max(1, (needles - 2 * band.height - 1) // band.period)
        ny = max(1, nx - 1)
        entry = {"band": name, "credit": credit_short(name), "cuts": {}}
        for mode in ("stored", "best"):
            frames = {}
            for corner in CORNERS:
                f, _ = build(corpus, name, nx, ny, corner, mode, seed)
                img = Image.fromarray((f.chart() > 0).astype(np.uint8), "P")
                img.putpalette([255, 255, 255, *HI_PALETTE[1]])
                fn = f"{name}-{mode}-{corner}.png"
                img.save(out / fn, optimize=True)
                frames[corner] = {"src": fn, "rows": f.H, "needles": f.W, **f.notes}
            entry["cuts"][mode] = {"shift": f.cut.shift, "close": f.cut.close, "frames": frames}
        index.append(entry)
    (out / "frames.json").write_text(json.dumps(index, indent=1, ensure_ascii=False))


def credit_short(name: str) -> str:
    from make_banner import museum_no
    return museum_no(source_of(name))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--band", default="thjms1105_38_p2")
    ap.add_argument("--nx", type=int, default=4, help="repeats along the top and bottom")
    ap.add_argument("--ny", type=int, default=3, help="repeats along the sides")
    ap.add_argument("--corner", default="mitre", choices=CORNERS + ("all",))
    ap.add_argument("--cut", default="best", choices=("best", "stored"))
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--needles", type=int, default=179)
    ap.add_argument("--out", type=Path, default=Path("out/frame"))
    ap.add_argument("--site", type=Path, help="write the docs page images to this folder and stop")
    args = ap.parse_args()
    if args.site:
        site_data(Corpus(CORPUS_DIR), args.site, args.needles, args.seed)
        return

    from make_banner import CREATOR, credit, git_rev, grid_png
    corpus = Corpus(CORPUS_DIR)
    args.out.mkdir(parents=True, exist_ok=True)
    shown = []
    for corner in (CORNERS if args.corner == "all" else (args.corner,)):
        f, tried = build(corpus, args.band, args.nx, args.ny, corner, args.cut, args.seed)
        chart = f.chart()
        o = args.out / corner
        o.mkdir(exist_ok=True)
        Pattern("frame", chart).save_txt(o / "frame.txt")
        Pattern("frame", chart).save_png(o / "frame.png", HI_PALETTE, zoom=4)
        grid_png(chart, o / "frame-grid.png", HI_PALETTE)
        small, flt = f.corner_score()
        meta = {
            "band": f.band.name, "repeats": {"top_bottom": f.nx, "sides": f.ny},
            "corner": corner, **f.notes,
            "cut": {"mode": args.cut, "shift": f.cut.shift, "close": f.cut.close,
                    "stored": f.cut.stored, "candidates": tried},
            "size": {"rows": f.H, "needles": f.W, "band_height": f.band.height,
                     "period": f.band.period},
            "corner_check": {"stitches_in_small_fragments": small, "longest_float": flt},
            "seed": args.seed,
            "orientation": "row = knitted row, column = needle",
            "commits": {"pattern_synthesis": git_rev("."), "sjonabok": git_rev("data/sjonabok")},
            "creator": CREATOR,
            "rights": {"source_patterns": "public domain", "generated_output": "CC BY 4.0"},
            "credit": credit([source_of(f.band.name)]),
        }
        (o / "frame.meta.json").write_text(json.dumps(meta, indent=1, ensure_ascii=False))
        warn = f" (wider than {args.needles} needles)" if f.W > args.needles else ""
        print(f"{o}: {f.H} rows x {f.W} needles{warn}, cut shift {f.cut.shift} close {f.cut.close}, "
              f"corner fragments {small}, longest corner float {flt}")
        shown.append((corner, chart))
    if len(shown) > 1:
        labelled(shown, args.out / "corners.png")
        print(f"wrote {args.out / 'corners.png'}")


if __name__ == "__main__":
    main()
