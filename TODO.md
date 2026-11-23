# Before implementation: what to investigate or decide

Short list for Helga. Background for each item is in the Quarto review (`review/`).

1. **Credit line.** The Sjónabók patterns are ancient and public domain (Helga,
   2026-11-23), so no permission is needed. Decide only how generated work credits the source
   (Heimilisiðnaðarfélag Íslands, Listaháskóli Íslands, Þjóðminjasafn Íslands and the
   original manuscript or museum number). Keep the `.eps` files from the CD out of git
   unless their own licence is also clear.

2. **Curate the corpus.** The `_pN` splits are automatic and sometimes cut or merge
   motifs. Decide whether a one-off manual pass (keep, merge, drop, label as band or
   motif) is acceptable. Also push or discard the uncommitted edits in your local
   `Documents/Sjonabok` so the submodule pins the version you actually use.

3. **Pick the main motifs for the banner.** How many, which ones, and in what
   order. A clustering pass can propose candidates; the final choice is yours.

4. **Machine constraints on the Passap E6000.** Known (Helga, 2026-11-23): width at
   most 179 needles, up to 4 colours. Still open: maximum rows per pattern for the
   download path you use, colours per row (all 4, or 2 per row with changes between
   rows), the backing structure, and whether float length matters with that backing.
   Also: how to map the binary Sjónabók charts to 3 or 4 colours (by region, by row
   band, or by motif).

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
