# Before implementation: what to investigate or decide

Short list for Helga. Background for each item is in the Quarto review (`review/`).

1. **Permission for derived works.** Ask Heimilisiðnaðarfélag Íslands,
   Listaháskóli Íslands and Þjóðminjasafn Íslands whether generating new designs
   from the Sjónabók charts, and publishing them on the site, is fine, and what
   credit line they want. The `.txt` matrices are already public in
   HiDefTextiles/Sjonabok; the `.eps` from the CD are not, and should stay out.

2. **Curate the corpus.** The `_pN` splits are automatic and sometimes cut or merge
   motifs. Decide whether a one-off manual pass (keep, merge, drop, label as band or
   motif) is acceptable. Also push or discard the uncommitted edits in your local
   `Documents/Sjonabok` so the submodule pins the version you actually use.

3. **Pick the main motifs for the banner.** How many, which ones, and in what
   order. A clustering pass can propose candidates; the final choice is yours.

4. **Machine constraints on the Passap E6000.** Maximum width in needles, maximum
   rows per pattern for the download path you use, two colours per row (yes for
   now), the backing structure (birdseye, stripes, ...) and whether float length
   matters at all with that backing. The NSN-2024 report is the place to check.

5. **Banner layout.** Target size in stitches and rows, whether it must repeat
   seamlessly horizontally, whether it has top and bottom border bands, and
   whether motifs sit on one centre line or vary.

6. **What "same vein" means to you.** Should output mix sources (e.g. natmus453
   with thjms5898) or stay within one? How much verbatim copying is acceptable?
   Agree on a small evaluation set and a blind test with HiDEF members.

7. **Method for version 1.** Recommendation (chapter 9): symmetry-group structure
   plus overlapping WFC with pinned motifs as the blender, image quilting as a second
   blender behind the same interface, and learned models left for later. Confirm or
   change.

8. **Outputs for the site.** Which formats the site needs (PNG preview, the `.txt`
   chart, a machine file), and whether generated banners get a gallery page under
   `mynsturgerd/` once this repo is a submodule.
