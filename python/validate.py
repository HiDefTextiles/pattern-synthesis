"""Settings, limit checks and knittability report for a finished chart.

A chart here is in machine orientation: a 2D array of colour indices with one
row per knitted row and one column per needle. (banner.py builds its charts
the other way round; pass `chart.T`.)

Usage:
    python3 python/validate.py out/banner/banner.txt [--settings banner.yml]
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import yaml

SOFT_WIDTH = 168


@dataclass
class Settings:
    layout: dict
    colour: dict
    float_policy: dict
    machine_profile: dict

    @classmethod
    def load(cls, path: Path = Path("banner.yml")) -> "Settings":
        return cls(**yaml.safe_load(path.read_text()))

    def check(self) -> list[str]:
        """Reject impossible settings; return warnings for risky ones."""
        width, needles = self.layout["width"], self.machine_profile["needles"]
        if width > needles:
            raise ValueError(f"width {width} exceeds the {needles} needles")
        if self.colour["max_row_colours"] > 3 and not self.colour["allow_four_colour_rows"]:
            raise ValueError("max_row_colours above 3 needs allow_four_colour_rows")
        warnings = []
        if width > SOFT_WIDTH:
            warnings.append(f"width {width} is above {SOFT_WIDTH}: the outermost needles are in use")
        return warnings


def runs(mask: np.ndarray) -> list[tuple[int, int]]:
    """(start, length) of each run of True in a 1D boolean array."""
    padded = np.concatenate([[False], mask, [False]])
    d = np.diff(padded.astype(int))
    starts, ends = np.where(d == 1)[0], np.where(d == -1)[0]
    return list(zip(starts.tolist(), (ends - starts).tolist()))


@dataclass
class Report:
    rows: int
    width: int
    colours_used: list[int]
    colours_per_row: list[int]
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    floats: dict = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return not self.errors

    def to_dict(self) -> dict:
        d = self.__dict__.copy()
        d["ok"] = self.ok
        return d


def validate(chart: np.ndarray, s: Settings) -> Report:
    rows, width = chart.shape
    per_row = [len(np.unique(r)) for r in chart]
    rep = Report(rows, width, sorted(np.unique(chart).tolist()), per_row)
    rep.warnings += s.check()
    c = s.colour
    if width > s.machine_profile["needles"]:
        rep.errors.append(f"chart is {width} stitches wide; the machine has {s.machine_profile['needles']}")
    if len(rep.colours_used) > c["palette_size"]:
        rep.errors.append(f"{len(rep.colours_used)} colours used; palette has {c['palette_size']}")
    worst = c["max_row_colours"] if not c["allow_four_colour_rows"] else 4
    over = [i for i, n in enumerate(per_row) if n > worst]
    if over:
        rep.errors.append(f"{len(over)} rows use more than {worst} colours (first: row {over[0]})")
    accent = [i for i, n in enumerate(per_row) if n > c["normal_row_colours"]]
    share = len(accent) / rows if rows else 0.0
    if share > c["three_colour_row_fraction_max"]:
        rep.warnings.append(f"{share:.0%} of rows use 3 colours; the design default is at most "
                            f"{c['three_colour_row_fraction_max']:.0%}")
    rep.floats = float_report(chart, s.float_policy.get("hard_limit_stitches"))
    limit = s.float_policy.get("hard_limit_stitches")
    if limit is not None and rep.floats["max_interior"] > limit:
        rep.errors.append(f"float of {rep.floats['max_interior']} stitches exceeds the calibrated "
                          f"limit of {limit}")
    elif limit is None:
        rep.warnings.append("no calibrated float limit yet: spans are reported, not judged")
    return rep


def float_report(chart: np.ndarray, limit: int | None = None) -> dict:
    """Unanchored spans: for each row and each colour knitted in it, the runs of
    needles where that colour is carried behind instead of knitted."""
    interior, edge, islands = [], [], 0
    worst_rows: list[dict] = []
    for y, row in enumerate(chart):
        for colour in np.unique(row):
            here = row == colour
            islands += sum(1 for _, n in runs(here) if n == 1)
            for start, n in runs(~here):
                touches_edge = start == 0 or start + n == len(row)
                (edge if touches_edge else interior).append(n)
                if not touches_edge:
                    worst_rows.append({"row": y, "colour": int(colour), "start": start, "length": n})
    worst_rows.sort(key=lambda r: -r["length"])
    hist = np.bincount(interior).tolist() if interior else []
    vertical = max((n for x in range(chart.shape[1])
                    for _, n in runs(chart[:, x] == chart[0, x])), default=0)
    return {
        "max_interior": max(interior, default=0),
        "max_edge": max(edge, default=0),
        "interior_histogram": hist,            # index = span length, value = count
        "longest": worst_rows[:20],
        "single_stitch_islands": islands,
        "longest_vertical_run_from_first_row": vertical,
        "over_limit": sum(n > limit for n in interior) if limit else None,
    }


def load_chart(path: Path) -> np.ndarray:
    rows = [l.strip() for l in path.read_text().splitlines() if l.strip()]
    return np.array([[int(ch) for ch in r] for r in rows], dtype=np.uint8)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("chart", type=Path)
    ap.add_argument("--settings", type=Path, default=Path("banner.yml"))
    args = ap.parse_args()
    rep = validate(load_chart(args.chart), Settings.load(args.settings))
    print(json.dumps(rep.to_dict(), indent=1))
    raise SystemExit(0 if rep.ok else 1)


if __name__ == "__main__":
    main()
