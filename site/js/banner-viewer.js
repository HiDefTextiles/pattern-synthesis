// Banner viewer: draws the generated banners in data/banners.json.
// Usage in a page:  <div class="banner-viewer" data-method="quilting"></div>
// The data file is found next to this script (../data/banners.json), so the
// viewer works from any page depth and under any site prefix.
(function () {
  const script = document.currentScript;
  const dataUrl = new URL("../data/banners.json", script.src).href;
  let cache = null;
  const load = () => (cache ||= fetch(dataUrl).then(r => r.json()));

  const cssVar = n => getComputedStyle(document.documentElement).getPropertyValue(n).trim();
  const pct = x => Math.round(x * 100) + "%";
  const rgb = hex => { const n = parseInt(hex.replace("#", ""), 16); return [(n >> 16) & 255, (n >> 8) & 255, n & 255]; };

  function palette(mode) {
    const g = cssVar("--bv-ground"), s = cssVar("--bv-stitch");
    if (mode === "pattern") return [g, s, g, s, g, s, g, s];
    return [g, cssVar("--bv-copied"), cssVar("--bv-ground-new"), cssVar("--bv-new"),
            cssVar("--bv-ground-new"), cssVar("--bv-echo"), cssVar("--bv-ground-clear"), cssVar("--bv-clear")];
  }

  function draw(canvas, v, mode, z) {
    const pal = palette(mode).map(rgb);
    canvas.width = v.cols * z;
    canvas.height = v.rows * z;
    const img = new ImageData(v.cols, v.rows);
    for (let i = 0; i < v.cells.length; i++) {
      const p = pal[v.cells.charCodeAt(i) - 48], o = i * 4;
      img.data[o] = p[0]; img.data[o + 1] = p[1]; img.data[o + 2] = p[2]; img.data[o + 3] = 255;
    }
    const tmp = document.createElement("canvas");
    tmp.width = v.cols; tmp.height = v.rows;
    tmp.getContext("2d").putImageData(img, 0, 0);
    const ctx = canvas.getContext("2d");
    ctx.imageSmoothingEnabled = false;
    ctx.drawImage(tmp, 0, 0, canvas.width, canvas.height);
  }

  function mount(el, list) {
    const id = el.dataset.method;
    const variants = list.filter(v => v.method === id);
    if (!variants.length) { el.textContent = "No banner data for " + id + "."; return; }
    const st = {
      mode: el.dataset.mode || "origin", zoom: 3,
      i: Math.max(0, variants.findIndex(v => v.label.includes("default")))
    };
    el.innerHTML = `
      <div class="bv-controls">
        <div class="bv-seg" role="group" aria-label="Colour mode">
          <button data-mode="pattern">Pattern only</button><button data-mode="origin">Copied vs new</button>
        </div>
        <label class="bv-zoom">Stitch size <input type="range" min="1" max="6" value="3" aria-label="Stitch size"></label>
        <div class="bv-legend">
          <span><i class="bv-sw" style="background:var(--bv-copied)"></i>copied from the book</span>
          <span><i class="bv-sw" style="background:var(--bv-new)"></i>new stitch</span>
          <span><i class="bv-sw" style="background:var(--bv-echo)"></i>new, but matches an 8×8 block in the book</span>
          <span class="bv-clear-key"><i class="bv-sw" style="background:var(--bv-clear)"></i>new, filled into a motif's empty space</span>
        </div>
      </div>
      ${variants.length > 1 ? `<div class="bv-chips" role="group" aria-label="Settings">${variants.map((v, k) => `<button data-i="${k}">${v.label}</button>`).join("")}</div>` : ""}
      <div class="bv-meter" aria-hidden="true"></div>
      <div class="bv-stats"></div>
      <div class="bv-chart"><canvas role="img" aria-label="Generated banner chart"></canvas></div>
      <p class="bv-caption"></p>`;
    const canvas = el.querySelector("canvas");

    function render() {
      const v = variants[st.i], s = v.stats;
      el.querySelectorAll(".bv-seg button").forEach(b => b.setAttribute("aria-pressed", String(b.dataset.mode === st.mode)));
      el.querySelectorAll(".bv-chips button").forEach(b => b.setAttribute("aria-pressed", String(+b.dataset.i === st.i)));
      el.querySelector(".bv-legend").hidden = st.mode === "pattern";
      el.querySelector(".bv-meter").innerHTML =
        `<i style="width:${pct(s.copied)};background:var(--bv-copied)"></i>` +
        `<i style="width:${pct(s.new)};background:var(--bv-new)"></i>` +
        `<i style="width:${pct(s.echo)};background:var(--bv-echo)"></i>` +
        `<i style="width:${pct(s.clear || 0)};background:var(--bv-clear)"></i>`;
      el.querySelector(".bv-stats").innerHTML =
        `<span>of all stitches: copied ${pct(s.copied)}</span><span>new ${pct(s.new)}</span>` +
        `<span>echo ${pct(s.echo)}</span>` + (s.clear ? `<span>empty space ${pct(s.clear)}</span>` : "") +
        `<span>${v.rows} needles × ${v.cols} rows</span>`;
      el.querySelector(".bv-clear-key").hidden = !variants.some(x => x.stats.clear);
      el.querySelector(".bv-caption").textContent = "Motifs, left to right: " + v.motifs.join(" · ");
      draw(canvas, v, st.mode, st.zoom);
    }

    el.querySelectorAll(".bv-seg button").forEach(b => b.addEventListener("click", () => { st.mode = b.dataset.mode; render(); }));
    el.querySelectorAll(".bv-chips button").forEach(b => b.addEventListener("click", () => { st.i = +b.dataset.i; render(); }));
    el.querySelector("input[type=range]").addEventListener("input", e => { st.zoom = +e.target.value; render(); });
    render();
  }

  function init() {
    const els = document.querySelectorAll(".banner-viewer");
    if (!els.length) return;
    load()
      .then(list => els.forEach(el => mount(el, list)))
      .catch(() => els.forEach(el => { el.textContent = "Banner data is missing. Run `make docs-data` and rebuild."; }));
  }

  document.readyState === "loading" ? document.addEventListener("DOMContentLoaded", init) : init();
})();
