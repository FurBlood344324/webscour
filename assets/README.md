# assets

The mark, in a light and a dark file, plus a favicon. No text, no font file, no raster, no gradient,
no external reference, no build step: each file is a small set of paths that renders in any browser
and in any renderer that reads SVG 1.1.

The idea is a terminal tool that looks like one. A 4 by 4 page of cells with one cell per row
replaced by a diagonal blade: the grid is the page being read, the four blades are what scrapes it.
Nothing leans on a corner radius, a shadow or a highlight, because none of those survive a 16 pixel
box.

There is deliberately no wordmark. An image of the name is a picture of a word, it has to be
redrawn whenever the name changes, and a README already says the name in text one line below. The
drawing carries the idea; the text carries the name.

| file | what it is | intended size |
|---|---|---|
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
  <source media="(prefers-color-scheme: dark)" srcset="assets/mark-dark.svg">
  <img src="assets/mark-light.svg" alt="webscour" width="112">
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
