# Version-1 decisions

Agreed defaults for the first banner generator (Helga, 2026-11-24). Shape: 85 needles
wide and endless along its length (Helga chose this over the 160 × 240 finite
banner proposed in the same document). They answer
most of the questions in [`TODO.md`](TODO.md). Anything marked *to verify* needs a
swatch, the machine or a written answer before it can be relied on.

| Topic | Version-1 default |
|---|---|
| Width | 85 needles, centred on the bed. Warn above 168, reject above 179 (the needle count) |
| Length | Endless and seeded: any stretch can be rendered on its own. A knitted piece is a window of rows, set by `window_rows` or by `finished_length_cm × rows_per_cm` from a swatch |
| Colours | 4-colour palette for the whole banner. Ordinary rows use exactly 2 colours; marked accent rows may use 3 (at most 15% of rows, a design default rather than a machine limit). No 4-colour rows |
| Structure | Double-bed birdseye / DBJ backing as the first candidate, *to verify* by swatching |
| Floats | Always measure unanchored spans per row and colour. No universal limit in code: a threshold is calibrated per yarn, gauge and backing profile from swatches. Until then, warn only |
| Palette mapping | Row-band schedule (one background/foreground pair per band), plus an explicit accent mask for the third colour. Switch pairs at low-information rows |
| Corpus | One manual keep / merge / drop / band / motif pass, recorded in an append-only manifest in the Sjonabok repo. `_pN` files are never edited without recording parent and operation |
| Source groups | One source group (manuscript) per banner by default. `source_scope: mixed` is an explicit setting and keeps per-motif attribution |
| Layout | Border bands along both long edges (the outer needles). Motifs follow a centre corridor across the width, with small controlled offsets. No wrap across the width |
| Generation | A deterministic, symmetry-aware compositor places motifs and bands. Overlapping WFC fills only bounded transition masks. A no-blend mode is always available |
| Quilting | Keep the interface; implement after the first knitted test |
| Learned models | Deferred |
| Outputs | `banner.png`, `banner-grid.png`, `banner.txt`, `banner.json`, `banner.meta.json` (sources, seed, parameters, commits, credit), `banner.validation.json` (colours per row, float spans, size, backing profile) |
| Machine export | Separate adapters per transfer path (own controller stream, E6000 console, DesignaKnit). Nothing is called "machine-ready" until its adapter has been tested end to end |
| Gallery | Only accepted or physically tested banners are published |

## Settings

```yaml
layout:
  width: 85                   # needles
  endless: true
  window_rows: 400            # rows rendered for one knitted piece
  border: edge_bands          # bands on the outer needles, both sides
  alignment: centre_corridor
  corridor_jitter: 0          # needles of controlled offset (0 in the prototype)
  source_scope: single        # or mixed, with allowed_source_groups
  copy_novelty_ratio: 0.35    # share of area that is pinned / verbatim

colour:
  palette_size: 4
  normal_row_colours: 2
  max_row_colours: 3
  allow_four_colour_rows: false
  three_colour_row_fraction_max: 0.15

float_policy:
  report_all_spans: true
  hard_limit_stitches: null   # set from a calibrated swatch profile
  calibrated_profile: null

machine_profile:
  transfer_path: passapi_stream   # or e6000_console, designaknit
  console_memory: unknown         # 8k | 32k
  technique: double_bed_birdseye
```

`copy_novelty_ratio` is a provenance measure, not a test of legal originality.

## Credit and rights

Record four things separately rather than labelling everything "public domain":

1. the historical motifs (centuries old);
2. the source digital assets (the CD `.eps` files and their transcriptions), *to verify*;
3. the code licence (GPL-3.0);
4. the licence for generated output.

The project has written permission to use the Sjónabók material for this work.
That is permission to use it, not a licence to redistribute the CD files. So the
`.eps` files stay out of git until redistribution is confirmed in writing. Every
generated banner carries its source manuscripts and pattern IDs in
`banner.meta.json`, and its credit states that it is a computational adaptation
that the institutions have not endorsed.

## To verify on the machine

- Console memory and download path; choose the controller stream, the console or DesignaKnit for version 1.
- The exact double-bed technique and colour-change sequence.
- Float and backing swatches in the four yarns, saved as a named profile.
- One 85-needle banner window, mostly two colours, knitted end to end, checking edges and carriage travel.
- The local `Documents/Sjonabok` changes are committed and the submodule pins that commit.
- Written confirmation of whether the CD `.eps` files may be redistributed.
