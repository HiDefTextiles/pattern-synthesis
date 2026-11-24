// Frames page: pick a band and a cut, see the three corner types side by side.
// Images are 1 pixel per stitch and scaled up by CSS, so the page stays light.
(async function () {
  const root = document.querySelector(".frames-viewer");
  if (!root) return;
  const base = "../data/frames/";
  const data = await (await fetch(base + "frames.json")).json();
  const names = { mitre: "Mitre", motif: "Motif block", grown: "Grown" };
  const notes = {
    mitre: "The bands run on into the corner and meet on the diagonal.",
    motif: "A small symmetric motif from the book sits in the corner.",
    grown: "The middle of the mitre is cleared and grown again from the band.",
  };
  let band = 0, cut = "stored";

  root.innerHTML = `
    <div class="fv-controls">
      <label>Band <select class="fv-band">${data.map((d, i) =>
        `<option value="${i}">${d.band} (${d.credit})</option>`).join("")}</select></label>
      <span class="bv-seg" role="group" aria-label="Cut">
        <button type="button" data-cut="stored" aria-pressed="true">Stored cut</button>
        <button type="button" data-cut="best" aria-pressed="false">Best cut</button>
      </span>
    </div>
    <p class="fv-cutnote bv-caption"></p>
    <div class="fv-grid"></div>`;

  const grid = root.querySelector(".fv-grid");
  function draw() {
    const d = data[band], c = d.cuts[cut];
    root.querySelector(".fv-cutnote").textContent =
      `Side starts ${c.shift} stitches into the repeat and closes with ${c.close} column${c.close === 1 ? "" : "s"}.` +
      (cut === "best" && c.shift === d.cuts.stored.shift ? " The stored cut is already the best." : "");
    grid.innerHTML = Object.entries(c.frames).map(([k, f]) => `
      <figure>
        <img src="${base + f.src}" alt="${names[k]} frame from ${d.band}" loading="lazy"
             width="${f.needles}" height="${f.rows}">
        <figcaption><strong>${names[k]}</strong> · ${f.needles} needles × ${f.rows} rows<br>
          ${f.corner_motif ? "Corner motif " + f.corner_motif : f.corner_fallback ? "No motif small enough, mitre shown" : notes[k]}
        </figcaption>
      </figure>`).join("");
  }
  root.querySelector(".fv-band").addEventListener("change", e => { band = +e.target.value; draw(); });
  root.querySelectorAll("[data-cut]").forEach(b => b.addEventListener("click", () => {
    cut = b.dataset.cut;
    root.querySelectorAll("[data-cut]").forEach(x => x.setAttribute("aria-pressed", x === b));
    draw();
  }));
  draw();
})();
