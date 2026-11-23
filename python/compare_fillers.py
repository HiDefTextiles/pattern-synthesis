"""Score each filler on the same banner: closeness of 3x3 patch statistics to the
corpus (KL, lower = more Sjónabók-like) and verbatim copying (share of generated
9x9 windows that occur exactly in the corpus, lower = more new).
Usage: python3 python/compare_fillers.py [slots]"""
import sys
from pathlib import Path

import numpy as np
from numpy.lib.stride_tricks import sliding_window_view

from banner import CORPUS_DIR, Banner, MotifPolicy, presets
from fillers import FILLERS
from sjonabok import Corpus


def windows(a, n):
    return sliding_window_view(a, (n, n)).reshape(-1, n * n)


def keys(w):
    return (w.astype(np.uint64) << np.arange(w.shape[1], dtype=np.uint64)).sum(1, dtype=np.uint64)


slots = int(sys.argv[1]) if len(sys.argv) > 1 else 4
corpus = Corpus(CORPUS_DIR)
table, motifs = presets(corpus)
cfg = table["mix"]
ref3 = np.concatenate([keys(windows(p.cells, 3)) for p in corpus.patterns.values() if min(p.shape) >= 3])
u, c = np.unique(ref3, return_counts=True)
pref = dict(zip(u, c / c.sum()))
ref9 = set(np.concatenate([keys(windows(p.cells, 8)) for p in corpus.patterns.values() if min(p.shape) >= 8]).tolist())
print(f"{'filler':<14}{'KL(3x3) vs corpus':>20}{'verbatim 8x8 share':>20}{'fill density':>14}")
for name in FILLERS:
    b = Banner("mix", cfg["seed"], MotifPolicy(cfg["kind"], motifs), corpus.band_tile(cfg["band"]),
               corpus=corpus, filler=FILLERS[name]())
    chart, gen, _ = b.render(0, slots)
    w3, g3 = windows(chart, 3), windows(gen, 3).any(1)
    k3 = keys(w3[g3])
    uu, cc = np.unique(k3, return_counts=True)
    q = cc / cc.sum()
    kl = float(np.sum(q * np.log(q / np.array([pref.get(x, 1e-6) for x in uu]))))
    w8, g8 = windows(chart, 8), windows(gen, 8).all(1)
    verb = np.mean([x in ref9 for x in keys(w8[g8]).tolist()]) if g8.any() else float("nan")
    print(f"{name:<14}{kl:>20.3f}{verb:>20.2f}{chart[gen].mean():>14.2f}")
