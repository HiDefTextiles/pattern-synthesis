"""Corpus access: load, trim and classify Sjónabók charts.

Exploratory prototype. The C++ core will replace this once the design settles.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image


CLEAR = "."   # text-file symbol for a clear (free, fillable) cell


def clear_mask(cells: np.ndarray, ring: int = 1) -> np.ndarray:
    """Cells of a motif's square that are free for the fill step.

    Kept: every stitch, a ring of background `ring` stitches wide around each
    stitch (8-neighbourhood), and background holes the motif closes in.
    Clear: the remaining background that is connected to the edge of the square.
    A motif that fills its square has no clear cells."""
    stitch = cells > 0
    near = stitch.copy()
    for _ in range(ring):
        p = np.pad(near, 1)
        near = np.zeros_like(near)
        for dy in (0, 1, 2):
            for dx in (0, 1, 2):
                near |= p[dy:dy + stitch.shape[0], dx:dx + stitch.shape[1]]
    open_bg = ~near
    reach = np.zeros_like(open_bg)
    reach[0], reach[-1], reach[:, 0], reach[:, -1] = open_bg[0], open_bg[-1], open_bg[:, 0], open_bg[:, -1]
    while True:                                   # flood fill from the edge, 4-connected
        p = np.pad(reach, 1)
        grown = (p[:-2, 1:-1] | p[2:, 1:-1] | p[1:-1, :-2] | p[1:-1, 2:] | reach) & open_bg
        if (grown == reach).all():
            return reach
        reach = grown


@dataclass
class Pattern:
    """A chart: 2D uint8 array of colour indices (0 = background).

    `clear` optionally marks free cells; in text files they are written as "."."""

    name: str
    cells: np.ndarray
    clear: np.ndarray | None = None

    @classmethod
    def load(cls, path: Path) -> "Pattern":
        rows = [line.strip() for line in path.read_text().splitlines() if line.strip()]
        clear = np.array([[c == CLEAR for c in r] for r in rows])
        cells = np.array([[0 if c == CLEAR else int(c) for c in r] for r in rows], dtype=np.uint8)
        return cls(path.stem, cells, clear if clear.any() else None)

    @property
    def shape(self) -> tuple[int, int]:
        return self.cells.shape

    def trimmed(self) -> "Pattern":
        rows = np.where(self.cells.any(1))[0]
        cols = np.where(self.cells.any(0))[0]
        if len(rows) == 0:
            return self
        cut = np.s_[rows[0]:rows[-1] + 1, cols[0]:cols[-1] + 1]
        return Pattern(self.name, self.cells[cut], None if self.clear is None else self.clear[cut])

    def is_d4(self) -> bool:
        """Square with both mirrors and the diagonal mirror (dihedral D4)."""
        c = self.cells
        return (c.shape[0] == c.shape[1]
                and (c == c[:, ::-1]).all() and (c == c[::-1]).all() and (c == c.T).all())

    def horizontal_period(self) -> int | None:
        c = self.cells
        for p in range(2, c.shape[1] // 2 + 1):
            if (c[:, p:] == c[:, :-p]).all():
                return p
        return None

    def with_clear(self, ring: int = 1) -> "Pattern":
        return Pattern(self.name, self.cells, clear_mask(self.cells, ring))

    def save_txt(self, path: Path) -> None:
        clear = self.clear if self.clear is not None else np.zeros(self.shape, bool)
        path.write_text("\n".join("".join(CLEAR if c else str(v) for v, c in zip(row, crow))
                                   for row, crow in zip(self.cells, clear)) + "\n")

    def save_png(self, path: Path, palette: list[tuple[int, int, int]], zoom: int = 6) -> None:
        rgb = np.array(palette, dtype=np.uint8)[self.cells]
        img = Image.fromarray(rgb, "RGB").resize(
            (self.shape[1] * zoom, self.shape[0] * zoom), Image.NEAREST)
        img.save(path)


class Corpus:
    """All charts in the Sjonabok submodule, with simple classification."""

    def __init__(self, directory: Path):
        self.patterns = {p.stem: Pattern.load(p).trimmed() for p in sorted(directory.glob("*.txt"))}

    def __getitem__(self, name: str) -> Pattern:
        return self.patterns[name]

    def motifs(self, min_size: int = 15, max_size: int = 45) -> list[Pattern]:
        return [p for p in self.patterns.values()
                if p.is_d4() and min_size <= p.shape[0] <= max_size]

    def band_tile(self, name: str) -> Pattern:
        """One horizontal period of a repeating border band."""
        band = self[name]
        period = band.horizontal_period()
        if period is None:
            raise ValueError(f"{name} is not horizontally periodic")
        return Pattern(f"{name}_tile", band.cells[:, :period].copy())
