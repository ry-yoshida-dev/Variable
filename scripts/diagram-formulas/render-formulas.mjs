// Renders each formula with MathJax and replaces the matching <svg class="math" id="formula-..."> element
// in the diagram, so the formulas display without MathJax at view time.
import { readFileSync, writeFileSync } from "node:fs";
import { mathjax } from "mathjax-full/js/mathjax.js";
import { TeX } from "mathjax-full/js/input/tex.js";
import { SVG } from "mathjax-full/js/output/svg.js";
import { liteAdaptor } from "mathjax-full/js/adaptors/liteAdaptor.js";
import { RegisterHTMLHandler } from "mathjax-full/js/handlers/html.js";
import { AllPackages } from "mathjax-full/js/input/tex/AllPackages.js";

const FORMULAS = {
  "formula-extensive": String.raw`x_1 + x_2`,
  "formula-intensive": String.raw`\frac{w_1 x_1 + w_2 x_2}{w_1 + w_2}`,
  "formula-maximal-minimal": String.raw`\max(x_1, x_2)\ \text{or}\ \min(x_1, x_2)`,
  "formula-first-last": String.raw`x_1\ \text{or}\ x_2`,
  "formula-non-additive": String.raw`f(\text{raw data}),\ \text{not}\ f(x_1, x_2)`,
};

// Formula band inside each additivity box, in the box's own coordinates.
const BAND_CENTER_X = 86;
const BAND_TOP = 55;
const BAND_HEIGHT = 32;
const MAX_WIDTH = 144;
// Pixels per MathJax unit (1000 units per em), close to a 12px font.
const SCALE = 0.012;

const diagramPath = process.argv[2];
if (diagramPath === undefined) {
  throw new TypeError("Usage: node render-formulas.mjs <diagram.svg>");
}

const adaptor = liteAdaptor();
RegisterHTMLHandler(adaptor);
const document = mathjax.document("", {
  InputJax: new TeX({ packages: AllPackages }),
  OutputJax: new SVG({ fontCache: "none" }),
});

function renderFormula(id, tex) {
  const rendered = adaptor.outerHTML(adaptor.firstChild(document.convert(tex, { display: true })));
  const viewBox = rendered.match(/viewBox="([^"]+)"/)?.[1];
  if (viewBox === undefined) {
    throw new Error(`MathJax output for ${id} has no viewBox`);
  }
  const [, , viewWidth, viewHeight] = viewBox.split(" ").map(Number);
  const scale = Math.min(SCALE, MAX_WIDTH / viewWidth);
  const width = viewWidth * scale;
  const height = viewHeight * scale;
  const x = BAND_CENTER_X - width / 2;
  const y = BAND_TOP + BAND_HEIGHT / 2 - height / 2;
  const content = rendered.replace(/^<svg[^>]*>/, "");
  return (
    `<svg class="math" id="${id}" x="${x.toFixed(1)}" y="${y.toFixed(1)}" ` +
    `width="${width.toFixed(1)}" height="${height.toFixed(1)}" viewBox="${viewBox}">${content}`
  );
}

let diagram = readFileSync(diagramPath, "utf8");
for (const [id, tex] of Object.entries(FORMULAS)) {
  const element = new RegExp(`<svg class="math" id="${id}"[^>]*>[\\s\\S]*?</svg>`, "g");
  const matchCount = diagram.match(element)?.length ?? 0;
  if (matchCount !== 1) {
    throw new Error(`Expected one element with id ${id} in ${diagramPath}, found ${matchCount}`);
  }
  const replacement = renderFormula(id, tex);
  diagram = diagram.replace(element, () => replacement);
}
writeFileSync(diagramPath, diagram);
