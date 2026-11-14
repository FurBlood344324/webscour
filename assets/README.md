# assets

The visual identity is three hand-written SVGs. There is no font file, no raster, no gradient, no
external reference and no build step: each file is a small set of paths that renders in any
browser and in any renderer that reads SVG 1.1.

The idea is a terminal tool that looks like one. The wordmark is monoline geometry, drawn from
circles and straight strokes at one weight, with a `w` that is four sharp diagonals instead of a
curve: the only angular letter in the word, and the one that reads first. The mark takes the
other half of the same idea, a 2 by 2 cell grid with the fourth cell replaced by a diagonal
blade. The grid is a page of lines, the missing cell is a scoured strip, and the whole thing
stays inside a square so it survives being scaled to a tab icon. Nothing about either shape
leans on a corner radius, a shadow or a highlight, because none of those survive a 16 pixel box.

| file | what it is | intended size |
|---|---|---|
| `logo.svg` | the wordmark `webscour`, for a README header or a site header | 800 by 140; keep the aspect ratio, it stays legible down to about 240 pixels wide |
| `mark.svg` | the mark alone, for an avatar, a package icon or a terminal banner | 32 by 32 by default; the grid and the blade still separate at 16 |
| `favicon.svg` | the same mark on a 16 unit grid, so every edge lands on a whole pixel | 16 by 16; a browser scales it up without softening the cells |

## Colour

Every fill and every stroke is `currentColor`, so the consumer decides the colour and the file
never does. That is what makes one file work on a light README and on a dark terminal:

```html
<img src="assets/logo.svg" alt="webscour" width="400">
<svg class="logo"><use href="assets/mark.svg"></use></svg>
```

In an `<img>` tag the colour is the document's text colour, because `currentColor` inside a
standalone SVG resolves to `color: black` unless the file is styled. Embedded inline, or loaded
through `<use>`, it inherits the surrounding `color` property, which is the case the files are
drawn for:

```css
.logo { color: #e6e6e6; }
```

There are exactly two colours in each file: the ink, and transparent. Nothing else is defined, so
there is nothing to override and no second theme to maintain. For a reversed lockup on a dark
surface, set `color` to the light value; do not edit the SVG.

## Rules the files follow

- No gradients, no filters, no clip paths, no embedded fonts, no `<image>`.
- No rounded corners. Every corner in the mark is 90 degrees or 45 degrees.
- One weight: the wordmark is drawn at a single stroke width, so it reads as a diagram rather
  than as a typeface imitation.
- Square geometry. The mark occupies a full square with a one unit margin, so it aligns to a grid
  instead of floating inside a padding box.
- `viewBox` plus `width` and `height`, so a consumer can scale either way without a second file.
- A `<title>` element carries the name for assistive technology. The mark and the favicon also
  carry `role="img"` and `aria-label`.
