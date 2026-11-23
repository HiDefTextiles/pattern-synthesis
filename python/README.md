Exploratory Python (numpy, Pillow).

* `sjonabok.py`: `Pattern` and `Corpus` (load, trim, D4 symmetry, band period).
* `wfc.py`: overlapping-model WFC with pinned cells and x-varying weights.
* `banner.py`: endless seeded banner. Slot k's motif depends on (seed, k); the
  stretch between slots k and k+1 depends only on those two motifs, so any
  window renders on its own. Presets: `manuscripts` (runs from one manuscript,
  seamless switch), `mix` (pure mix), `derived` (every other motif is new,
  generated from one manuscript's motifs and made D4-symmetric), `evolve`
  (originals only every 4th slot as anchors; the motifs between are new and
  morph from one anchor's patch statistics to the next, with wider gaps).
  Output is two-colour (pattern first). `--colour` applies the provisional
  `ColourPlan`, a separate later stage: it gives each knitted row background + one contrast colour, with a
  short dithered three-colour switch; four colours in total.

* `fillers.py`: interchangeable gap fillers behind one interface: `wfc`,
  `efros-leung`, `quilting`, `symmetric` (Efros-Leung on the left half, mirrored)
  and `cellular`. `python3 python/banner.py --filler compare` renders the same
  banner with each; `python3 python/compare_fillers.py` scores them.
