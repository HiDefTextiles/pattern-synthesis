# Todo

Most pre-implementation questions are now answered in
[`DECISIONS.md`](DECISIONS.md) (Helga, 2026-11-24). Background is in the
Quarto review (`review/`).

## Decided

- [x] 85 needles wide (179 maximum), endless along its length; a knitted piece is a window of rows.
- [x] Two colours on ordinary rows, three on marked accent rows (at most 15%), never four; four colours across the banner.
- [x] Double-bed birdseye / DBJ as the first backing to try.
- [x] One manual corpus curation pass, recorded in a manifest.
- [x] One source group per banner by default; mixed sources is an explicit setting.
- [x] Row-band palette schedule with an accent mask.
- [x] Border bands on both long edges, motifs in a centre corridor.
- [x] Deterministic compositor first; WFC only inside transition masks; quilting later; learned models deferred.
- [x] Required outputs: PNG, grid PNG, TXT, JSON, metadata JSON, validation JSON.
- [x] Patterns are public domain; derived patterns are CC BY 4.0.

## Still open for Helga

1. **Pick the main motifs for the banner.** How many, which ones, and in what order.
   A clustering pass can propose candidates; the final choice is yours.
2. **Curation pass.** Do the keep / merge / drop / band / motif review and commit
   the local `Documents/Sjonabok` changes so the submodule can pin them.
3. **Machine checks** (see "To verify" in `DECISIONS.md`): transfer path, console
   memory, technique, float swatches, one full test banner.

## Next in code

- [x] Settings file (`banner.yml`) with the defaults in `DECISIONS.md`, and limit checks.
- [x] Row-colour validator and float-span report (`banner.validation.json`).
- [x] Output set and provenance sidecar (`banner.meta.json`).
- [ ] Source scope setting (single manuscript by default) and bounded transition masks in the endless layout.
- [ ] Row-band palette schedule with accent mask (after the pattern work).
- [ ] Machine adapters, one per transfer path, each with an end-to-end test.
