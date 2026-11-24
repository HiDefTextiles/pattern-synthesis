"""Render long banners for the method explainer (docs/explainer/).

Every variant uses the same motifs and seed, so only the method or one
parameter changes. Each cell is labelled:
    0/1 background/stitch copied from Sjónabók (motif or border band)
    2/3 background/stitch generated
    4/5 background/stitch generated but part of an 8x8 block that also occurs
        exactly somewhere in Sjónabók ("echo")
    6/7 background/stitch generated in a motif's clear space (clear_space.py)
Usage: python3 python/explainer_data.py [slots] > docs/explainer/banners.json
"""
import json
import sys
import time

import numpy as np
from numpy.lib.stride_tricks import sliding_window_view

from banner import CORPUS_DIR, Banner, MotifPolicy, presets
from fillers import (CellularFiller, EfrosLeungFiller, QuiltFiller, SymmetricFiller,
                     WfcFiller)
from clear_space import clear_motifs
from sjonabok import Corpus

E = 8  # echo window


def keys(a, n):
    w = sliding_window_view(a, (n, n)).reshape(-1, n * n).astype(np.uint64)
    return (w << np.arange(n * n, dtype=np.uint64)).sum(1, dtype=np.uint64)


slots = int(sys.argv[1]) if len(sys.argv) > 1 else 20
corpus = Corpus(CORPUS_DIR)
table, motifs = presets(corpus)
book = set()
for p in corpus.patterns.values():
    if min(p.shape) >= E:
        book.update(keys(p.cells, E).tolist())

VARIANTS = [
    # (method, label, preset, filler factory, gap[, clear ring])
    ("wfc", "window 2×2", "mix", lambda: WfcFiller(n=2), 14),
    ("wfc", "window 3×3 (default)", "mix", lambda: WfcFiller(n=3), 14),
    ("efros-leung", "window 5×5", "mix", lambda: EfrosLeungFiller(window=5), 14),
    ("efros-leung", "window 7×7, best match only (default)", "mix", lambda: EfrosLeungFiller(window=7), 14),
    ("efros-leung", "window 7×7, up to 3 stitches off", "mix", lambda: EfrosLeungFiller(window=7, tolerance=3), 14),
    ("efros-leung", "window 7×7, up to 8 stitches off", "mix", lambda: EfrosLeungFiller(window=7, tolerance=8), 14),
    ("quilting", "small blocks 6×6", "mix", lambda: QuiltFiller(block=6, overlap=2), 14),
    ("quilting", "blocks 10×10 (default)", "mix", lambda: QuiltFiller(block=10, overlap=3), 14),
    ("quilting", "large blocks 16×16", "mix", lambda: QuiltFiller(block=16, overlap=4), 14),
    ("symmetric", "mirrored sampling (default)", "mix", lambda: SymmetricFiller(EfrosLeungFiller()), 14),
    ("symmetric", "mirrored WFC", "mix", lambda: SymmetricFiller(WfcFiller()), 14),
    ("cellular", "rule 90", "mix", lambda: CellularFiller(90), 14),
    ("cellular", "rule 150", "mix", lambda: CellularFiller(150), 14),
    ("cellular", "rule 30", "mix", lambda: CellularFiller(30), 14),
    ("spacing", "narrow gaps (4)", "mix", lambda: EfrosLeungFiller(), 4),
    ("spacing", "medium gaps (14)", "mix", lambda: EfrosLeungFiller(), 14),
    ("spacing", "wide gaps (30)", "mix", lambda: EfrosLeungFiller(), 30),
    ("evolve", "new motifs between anchors", "evolve", lambda: EfrosLeungFiller(), 26),
    ("clear", "no clear space", "mix", lambda: EfrosLeungFiller(), 14, None),
    ("clear", "ring 1 (default)", "mix", lambda: EfrosLeungFiller(), 14, 1),
    ("clear", "ring 2", "mix", lambda: EfrosLeungFiller(), 14, 2),
]

out = []
for method, label, preset, make, gap, *rest in VARIANTS:
    t0 = time.time()
    cfg = table[preset]
    ring = rest[0] if rest else None
    b = Banner(preset, cfg["seed"], MotifPolicy(cfg["kind"], motifs), corpus.band_tile(cfg["band"]),
               corpus=corpus, filler=make(), gap=gap,
               clear=clear_motifs(motifs, ring) if ring is not None else {})
    chart, gen, _ = b.render(0, slots)
    clear = b.clear_cells
    echo = np.zeros_like(gen)
    k = keys(chart, E).reshape(chart.shape[0] - E + 1, chart.shape[1] - E + 1)
    hit = np.vectorize(lambda x: x in book)(k)
    for y, x in np.argwhere(hit):
        echo[y:y + E, x:x + E] = True
    cls = chart + 2 * gen + 2 * (gen & echo & ~clear) + 4 * clear
    st = chart == 1                                       # shares are of stitches, not cells

    def share(m):
        return round(float((m & st).sum() / st.sum()), 3)
    labels = b.labels(0, slots)
    out.append(dict(method=method, label=label, rows=int(chart.shape[0]), cols=int(chart.shape[1]),
                    motifs=labels, cells="".join(map(str, cls.ravel().tolist())),
                    stats=dict(copied=share(~gen), new=share(gen & ~echo & ~clear),
                               echo=share(gen & echo & ~clear), clear=share(clear))))
    print(f"{method:12s} {label:30s} {chart.shape} {time.time()-t0:5.1f}s", file=sys.stderr)
json.dump(out, sys.stdout, separators=(",", ":"))
