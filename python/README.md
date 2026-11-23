Exploratory Python (numpy, Pillow).

* `sjonabok.py`: `Pattern` and `Corpus` (load, trim, D4 symmetry, band period).
* `wfc.py`: overlapping-model WFC with pinned cells and x-varying weights.
* `banner.py`: endless seeded banner. Slot k's motif depends on (seed, k); the
  stretch between slots k and k+1 depends only on those two motifs, so any
  window renders on its own. Presets: `manuscripts` (runs from one manuscript,
  seamless switch), `mix` (pure mix), `derived` (every other motif is new,
  generated from one manuscript's motifs and made D4-symmetric).
  `ColourPlan` gives each knitted row background + one contrast colour, with a
  short dithered three-colour switch; four colours in total.
