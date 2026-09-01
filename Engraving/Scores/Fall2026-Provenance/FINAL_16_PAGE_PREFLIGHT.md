# Fall 2026 performer-score PDF preflight

## Assembly gate

The standalone colophon is a fallback for page 16. Do not append it until the
validated score body is exactly 15 pages in normal reading order.

The body must first pass all of these gates:

- 15 portrait US Letter pages, each exactly 612 by 792 points and rotation 0.
- Page 1 contains exactly two musical systems.
- Every musical page contains real notation and lyrics; no hollow import and no
  blank page is present.
- All six vocal staves are visible and use five staff lines throughout.
- The final Dorico project, not Stage A or the hollow Stage B proof, is the PDF
  source.
- Flow headings, running titles, page numbers, staff labels, margins, and gutter
  clearance have been visually approved.

If the validated score body is not 15 pages, do not force this colophon into
the edition. Recast the score in Dorico so the final count remains divisible by
four without blank pages.

## Lossless assembly

1. Reopen the chosen 15-page body PDF and this standalone colophon with
   `pypdf`.
2. Copy body pages 1-15 without scaling, cropping, rasterizing, or changing
   their rotation.
3. Copy the colophon unchanged as page 16.
4. Save the reader-order master as
   `Engraving/Scores/FlashlightsInTheDark_Fall2026_PerformerScore.pdf`.
5. Do not impose printer spreads in the archival master. A printer or a separate
   production copy may impose the saddle-stitch pairs 16-1 / 2-15, 14-3 /
   4-13, 12-5 / 6-11, and 10-7 / 8-9.

## Structural and font checks

- Reopen the written PDF; require exactly 16 pages.
- Require every page box to be 612 by 792 points, portrait, with rotation 0.
- Require no encryption, JavaScript, AcroForm, or page annotations.
- Require every listed font to be embedded. Confirm Bravura and Academico in
  the score body and embedded Academico regular, bold, and italic on page 16.
- Confirm no page was rescaled or clipped during concatenation.
- Record SHA-256 hashes for the final PDF, final Dorico project, final MusicXML
  export, correction log, and semantic-validation report.

## Visual checks

Render all 16 pages at 300 dpi and inspect both full pages and reader spreads.
Text extraction and ink-coverage metrics may detect failures but do not replace
visual review of music notation.

Audit the following:

- Page 1: two systems; title, `Set in 2076`, commission line, composer, and
  copyright; no duplicate flow title.
- Pages 2-15: centered running title; page numbers on the outside edge; adequate
  inside gutter; no clipped frames.
- Page 16: substantive colophon content, centered optical alignment, embedded
  fonts, and page number 16 at the lower outside (left) corner.
- Every page: no blank page, collision, obscured lyric, split direction,
  malformed accidental, missing staff line, or unintentional single-line staff.
- Measures 1-20, 38-57, 81-96, and 104-139 at 100 percent, with special focus
  on chord-symbol congestion near measure 89 and the aleatoric instruction near
  measure 115.
- Reader spreads 2-3, 4-5, 6-7, 8-9, 10-11, 12-13, and 14-15 for balanced
  vertical density and gutter clearance.
- Imposition preview for the four saddle-stitch sheets, especially 16-1 and
  2-15, without altering the archival reader-order PDF.

Print page 1, the densest lyric spread, and the page containing measure 115 at
actual Letter size. Confirm choir-folder readability and that the smallest lyric
and direction text remains comfortable at normal music-stand distance.

## Semantic release checks

Re-export MusicXML from the final Dorico project and require:

- six parts and 151 measures per part;
- the canonical v26 musical-structure fingerprint;
- 1,376 lyric anchors;
- all 388 approved Fall replacements;
- no unlogged textual difference.

The correction log must identify substantive wording changes and preserve
unresolved ambiguities. Show-control recipes and runtime assets remain outside
this engraving pass.

## Exact page-16 copy

```text
FLASHLIGHTS IN THE DARK / FALL 2026 PERFORMER SCORE

FLASHLIGHTS IN THE DARK
Fall 2026 Performer-Score Edition
Set in 2076

Music by Jon D. Nelson
Text by Clare Malinowski & Jon Nelson
Commissioned by the Philharmonic Chorus of Madison

EDITORIAL BASIS
Lyrics: Fall 2026 Working Text
Musical structure: canonical v26 score fingerprint

This engraving pass preserves the notes, rhythms, measure structure,
and cue timing. Show-control and runtime assets remain unchanged.

Text-semantic changes are recorded in the Fall 2026 engraving correction log.

© 2025

16
```
