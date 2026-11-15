# Diagram Formulas

## Overview

Renders the LaTeX formulas in [docs/images/variable-types.svg](../../docs/images/variable-types.svg) with MathJax and embeds them as SVG paths, so the diagram shows them without MathJax at view time. Edit a formula in the script, then run it to update the diagram in place.

## Components

| Component | Description |
|---|---|
| [render-formulas.mjs](render-formulas.mjs) | Formulas keyed by element id, and their placement in each additivity box |

## Examples

Requires Node.js. From this directory:

```bash
npm ci
npm run render
```
