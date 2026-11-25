# pattern-synthesis

Seeded, reproducible generation of new knitting patterns in the style of
*Íslensk sjónabók*. The first target is an endless **banner**, 85 needles wide,
that blends the Sjónabók motifs into each other. Same seed, same banner.

Docs, with every method explained in plain words:
**https://hideftextiles.github.io/pattern-synthesis/**

## Quick start

```sh
git clone --recurse-submodules https://github.com/HiDefTextiles/pattern-synthesis
cd pattern-synthesis
make setup          # corpus submodule + Python packages
make banner         # one knitted piece -> out/banner-seed1-from0/
```

`make` on its own lists every target.

## Everyday commands

| Command | What you get |
|---|---|
| `make banner SEED=7` | A banner piece from another seed |
| `make banner FIRST=100` | A piece further along the same endless banner |
| `make frame BAND=thjms1105_38_p2` | A frame from four border bands, with mitre, motif and grown corners |
| `make clear RING=1` | Motif templates with their empty space marked as `.` |
| `make banners` | Preview banners for every preset in `out/banners/` |
| `make compare` | The same banner with every fill method, side by side |
| `make docs` / `make docs-preview` | Build or preview the docs website |
| `make review` | Render the literature review (Quarto book) |
| `make clean` | Remove everything generated |

Settings live in [`banner.yml`](banner.yml) (width, colours, empty-space ring,
manuscript). The reasons behind them are in [`DECISIONS.md`](DECISIONS.md), and
the open items are in [`TODO.md`](TODO.md).

## What `make banner` writes

| File | Contents |
|---|---|
| `banner.png` | Preview |
| `banner-grid.png` | Enlarged chart with row and needle numbers |
| `banner.txt` | Chart: one line per knitted row, `0` background, `1` stitch |
| `banner.json` | Same chart plus the empty-space layer |
| `banner.meta.json` | Seed, settings, source manuscripts, credit line |
| `banner.validation.json` | Colours per row and float lengths |

## Pattern files

One text file per chart, one line per row: `1` stitch, `0` background, and `.`
empty space (knitted as `0` unless something is filled in). The corpus is the
[Sjonabok](https://github.com/HiDefTextiles/Sjonabok) repository, included as
the submodule `data/sjonabok/`.

## Licence and credit

Code: GPL-3.0. Generated patterns: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/),
by Helga Ingimundardóttir, Háskóli Íslands.

The source patterns come from manuscripts at Þjóðminjasafn Íslands and
Nationalmuseet. They were published in *Íslensk sjónabók* (2009) and are in the
public domain. HiDef Textiles digitised them in 2024 (NSN summer project) from
the CD that comes with the book. Each banner lists the manuscripts it draws on
in `banner.meta.json`.
