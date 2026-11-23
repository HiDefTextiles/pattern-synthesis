"""Corpus access: load, trim and classify Sjónabók charts.

Exploratory prototype. The C++ core will replace this once the design settles.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image


@dataclass
class Pattern:
    """A chart: 2D uint8 array of colour indices (0 = background)."""

    name: str
    cells: np.ndarray

    @classmethod
    def load(cls, path: Path) -> "Pattern":
        rows = [line.strip() for line in path.read_text().splitlines() if line.strip()]
        cells = np.array([[int(c) for c in r] for r in rows], dtype=np.uint8)
        return cls(path.stem, cells)

    @property
    def shape(self) -> tuple[int, int]:
        return self.cells.shape

    def trimmed(self) -> "Pattern":
        rows = np.where(self.cells.any(1))[0]
        cols = np.where(self.cells.any(0))[0]
        if len(rows) == 0:
            return self
        return Pattern(self.name, self.cells[rows[0]:rows[-1] + 1, cols[0]:cols[-1] + 1])

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

    def save_txt(self, path: Path) -> None:
        path.write_text("\n".join("".join(str(v) for v in row) for row in self.cells) + "\n")

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
