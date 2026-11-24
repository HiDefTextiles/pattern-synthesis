# pattern-synthesis

Reproducible generation of new knitting patterns in the vein of
*Íslensk sjónabók*, the Icelandic pattern collection digitised in
[HiDefTextiles/Sjonabok](https://github.com/HiDefTextiles/Sjonabok).

Goal: given a seed and a configuration, produce the same new two-colour chart
every time, built from the corpus's motifs and style. The first concrete target
is a long **banner** (in the spirit of a *refilsaumur* hanging) that contains
the main Sjónabók motifs and blends smoothly between them.

The method is deliberately open. The literature review in `review/` compares
wave function collapse, texture synthesis, symmetry and grammar based
generation, and learned models, and argues for a composable pipeline (see
`review/09-recommendation.qmd`). A first **Python prototype** (`python/banner.py`, `make banners`) renders an
endless, seeded banner: border bands, Sjónabók motifs pinned on a centre line,
overlapping WFC filling the stretches between them, with two-colour output (colouring is a
separate, later stage). Previews are in `previews/`. Version-1 decisions are in [`DECISIONS.md`](DECISIONS.md) and the defaults in
[`banner.yml`](banner.yml); `make banner` writes the full output set
(`banner.png`, `banner-grid.png`, `banner.txt`, `banner.json`, `banner.meta.json`,
`banner.validation.json`). The C++ core comes after the open items in [`TODO.md`](TODO.md).

This repository is meant to become a git submodule of the HiDEF site
(HiDefTextiles/hidefTextiles.github.io).

## Docs website

`site/` is a Quarto website with the same HÍ look as the
[Sjónabók gallery](https://hideftextiles.github.io/Sjonabok/): one page per
method in plain words, each with an interactive banner, plus the literature
review. It will be published at https://hideftextiles.github.io/pattern-synthesis/
once the Pages workflow is added.

```sh
make docs-data   # generate site/data/banners.json (about two minutes)
make docs        # render site/ and the review book into site/_site
make docs-preview
```

## Layout

| Path | Purpose |
|------|---------|
| `data/sjonabok/` | Submodule: HiDefTextiles/Sjonabok (input corpus, `patterns/txt/*.txt`, 0/1 matrices) |
| `src/`, `include/` | C++ core (later): pattern type, seeded RNG, synthesis stages |
| `python/` | Exploration and prototypes |
| `R/` | tidyverse analysis of the corpus and of generated output |
| `scripts/` | Small shell helpers called from the Makefile |
| `review/` | Quarto book: literature review and recommendation |
| `site/` | Quarto docs website (methods, banners, roadmap) |
| `out/` | Generated files (git-ignored) |

## Usage

```sh
git clone --recurse-submodules https://github.com/HiDefTextiles/pattern-synthesis-
make stats      # corpus sizes and fill ratios -> out/corpus-stats.tsv
make banners    # prototype banners -> out/banners/ (needs numpy, Pillow)
make banner SEED=1 FIRST=0   # one knitted piece + chart, provenance and validation files
make review     # render the Quarto book -> review/_book/
make preview    # live preview of the book
```

## Pattern format

Inherited from Sjonabok: one text file per pattern, one line per row, `1` =
contrast colour (black in the source), `0` = background, no header. Files are
named `<source>_<page>[_pN].txt`, where `_pN` is a sub-pattern split from a
page.

## Licence

Code: GPL-3.0, matching Sjonabok and the site. Generated patterns:
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/), created by Helga Ingimundardóttir, Háskóli Íslands.

The source patterns (Þjóðminjasafn Íslands and Nationalmuseet manuscripts, via
*Íslensk sjónabók*, 2009) are public domain. The charts were digitised in 2024
(NSN summer project) from the pattern files on the CD that comes with the book. Each banner's `banner.meta.json`
lists the manuscript numbers it draws on and a short credit line.
