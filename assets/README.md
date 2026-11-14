# assets

Two drawings, each in a light and a dark file. No font file, no raster, no gradient, no external
reference, no build step: each file is a small set of paths that renders in any browser and in any
renderer that reads SVG 1.1.

The idea is a terminal tool that looks like one. The wordmark is monoline geometry, one stroke
weight, with a `w` built from four sharp diagonals instead of a curve: the only angular letter, and
the one the eye lands on first. The mark takes the other half of the same idea: a 4 by 4 page of
cells with one cell per row replaced by a diagonal blade. The grid is the page being read, the four
blades are what scrapes it. Neither shape leans on a corner radius, a shadow or a highlight, because
none of those survive a 16 pixel box.

| file | what it is | intended size |
|---|---|---|
| `logo-light.svg` | the wordmark, ink `#1f2328`, for a light surface | 800 by 140; legible down to about 240 wide |
| `logo-dark.svg` | the same drawing, ink `#e6edf3`, for a dark surface | same |
| `mark-light.svg` | the mark alone, light surface | 128 by 128; the grid and the blades still separate at 16 |
| `mark-dark.svg` | the mark alone, dark surface | same |
| `favicon.svg` | the mark on a 16 unit grid, so every edge lands on a whole pixel | 16 by 16 |

## Why the colour is baked in

The first version used `currentColor` everywhere, on the theory that the consumer decides. That
works for an SVG inlined into a document and fails in the place that matters: a Markdown README
loads the file through `<img>`, where `currentColor` resolves to the initial value, black, with no
page background to adapt to. On GitHub's dark theme the logo was black on near-black.

So each drawing ships twice with the ink written into the file, and README.md picks between them:

```html
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/logo-dark.svg">
  <img src="assets/logo-light.svg" alt="webscour" width="460">
</picture>
```

A `prefers-color-scheme` block inside the SVG does not help here: a file loaded through `<img>` is
a separate document and GitHub's renderer does not evaluate media queries against the host page's
theme. Two files is the only form that works in every README on every host.

`favicon.svg` keeps the light ink: a favicon sits on a browser tab, not on a page theme.

## Rules the files follow

- No gradients, no filters, no clip paths, no embedded fonts, no `<image>`, no `<text>`.
- No rounded corners. Every corner is 90 or 45 degrees.
- One weight, so the wordmark reads as a diagram rather than an imitation of a typeface.
- If a drawing changes, change the pair. A single-theme file is the bug this directory exists to
  prevent.
