# assets

The visual identity is a wordmark drawn as geometry, a mark, and a favicon. There is no font file,
no raster, no gradient, no external reference and no build step: each file is a small set of paths
that renders in any browser and in any renderer that reads SVG 1.1.

The idea is a terminal tool that looks like one. The wordmark is monoline geometry, drawn from
circles and straight strokes at one weight, with a `w` that is four sharp diagonals instead of a
curve: the only angular letter in the word, and the one that reads first. The mark takes the other
half of the same idea, a 2 by 2 cell grid with the fourth cell replaced by a diagonal blade. The
grid is a page of lines, the missing cell is a scoured strip, and the whole thing stays inside a
square so it survives being scaled to a tab icon. Nothing about either shape leans on a corner
radius, a shadow or a highlight, because none of those survive a 16 pixel box.

| file | what it is | intended size |
|---|---|---|
| `logo-light.svg` | the wordmark on a light surface | 800 by 140; legible down to about 240 pixels wide |
| `logo-dark.svg` | the same drawing for a dark surface | same |
| `mark-light.svg` | the mark alone, light surface | 32 by 32; the grid and the blade still separate at 16 |
| `mark-dark.svg` | the mark alone, dark surface | same |
| `favicon.svg` | the mark on a 16 unit grid, so every edge lands on a whole pixel | 16 by 16 |

## Colour, and why there are two files per drawing

The first version used `currentColor` everywhere, on the theory that the consumer decides. That
works when the SVG is inlined into a document, and it fails in the place it matters most: a
Markdown README loads the file through `<img>`, where `currentColor` resolves to the initial value,
black, with no page background to adapt to. On GitHub's dark theme that is black on near-black.

So each drawing ships in two files with the ink baked in: `#1f2328` for light surfaces, `#e6edf3`
for dark ones. README.md picks between them with `<picture>`:

```html
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/logo-dark.svg">
  <img src="assets/logo-light.svg" alt="webscour" width="460">
</picture>
```

`assets/favicon.svg` keeps the light ink, because a favicon sits on a browser tab, not on a page
theme.

There are exactly two colours in every file: the ink and transparent. Nothing else is defined, so
there is nothing to override and no theme to maintain beyond the pair.

## Rules the files follow

- No gradients, no filters, no clip paths, no embedded fonts, no `<image>`.
- No rounded corners. Every corner in the mark is 90 degrees or 45 degrees.
- One weight: the wordmark is drawn at a single stroke width, so it reads as a diagram rather
  than as a typeface imitation.
- Square geometry. The mark occupies a full square with a one unit margin, so it aligns to a grid
  at any size.
- If a drawing changes, change the pair. A single-theme file is the bug this directory exists to
  avoid.
