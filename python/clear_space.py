"""Post-processing step on the motifs: mark the space around each motif as clear.

For every motif, keep its stitches, a ring of background `ring` stitches wide
around them, and any background holes the motif closes in. The rest of its
square becomes clear ("." in text files), so the fill step can grow new patterns
there. Motifs that fill their square are left unchanged. The generator itself
does not change: it simply leaves clear cells free.

Usage (from the repo root):
    python3 python/clear_space.py --ring 1 --out out/clear      # dotted templates + summary
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

from banner import CORPUS_DIR
from sjonabok import Corpus, Pattern, clear_mask


def clear_motifs(motifs: list[Pattern], ring: int = 1) -> dict[str, np.ndarray]:
    """Motif name -> clear mask, only for motifs that have clear cells."""
    out = {}
    for m in motifs:
        mask = clear_mask(m.cells, ring)
        if mask.any():
            out[m.name] = mask
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ring", type=int, default=1)
    ap.add_argument("--out", type=Path, default=Path("out/clear"))
    args = ap.parse_args()
    corpus = Corpus(CORPUS_DIR)
    motifs = [m for m in corpus.motifs(19, 45) if m.shape[0] % 2]
    masks = clear_motifs(motifs, args.ring)
    args.out.mkdir(parents=True, exist_ok=True)
    rows = ["motif\theight\twidth\tclear_share"]
    for m in motifs:
        mask = masks.get(m.name, np.zeros(m.shape, bool))
        Pattern(m.name, m.cells, mask).save_txt(args.out / f"{m.name}.txt")
        rows.append(f"{m.name}\t{m.shape[0]}\t{m.shape[1]}\t{mask.mean():.3f}")
    (args.out / "summary.tsv").write_text("\n".join(rows) + "\n")
    print(f"{len(masks)} of {len(motifs)} motifs have clear space (ring {args.ring}); "
          f"templates in {args.out}")


if __name__ == "__main__":
    main()
