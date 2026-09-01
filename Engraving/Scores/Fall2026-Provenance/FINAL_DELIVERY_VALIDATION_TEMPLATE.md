# Fall 2026 Performer-Score Final-Delivery Validation

**Status:** `PENDING - FINAL MUSICXML AND PDF NOT YET VALIDATED`

**Final-delivery pass:** `NO`

This is the report shell for the final Dorico export of *Flashlights in the
Dark*. It deliberately makes no final-pass claim. Replace this file with the
validator-generated Markdown report only after the intended final MusicXML and
the complete saddle-stitch PDF have both been frozen.

## Intended final inputs

- Dorico project: `Engraving/Scores/FlashlightsInTheDark_Fall2026_PerformerScore_PrintFinal.dorico`
- MusicXML: `PENDING FINAL DORICO EXPORT`
- PDF: `PENDING FINAL 40-PAGE ASSEMBLY (39 MUSIC PAGES + PAGE-40 COLOPHON)`
- Provenance directory: `Engraving/Scores/Fall2026-Provenance`

## Required invocation

```sh
python3 Operations/Scripts/validate_fall2026_performer_score.py \
  --musicxml Engraving/Scores/FlashlightsInTheDark_Fall2026_PerformerScore_PrintFinal.musicxml \
  --pdf Engraving/Scores/FlashlightsInTheDark_Fall2026_PerformerScore_PrintFinal.pdf \
  --final-delivery \
  --report-json Engraving/Scores/Fall2026-Provenance/FlashlightsInTheDark_Fall2026_FinalValidation.json \
  --report-md Engraving/Scores/Fall2026-Provenance/FlashlightsInTheDark_Fall2026_FinalValidation.md
```

Use the bundled workspace Python if the ordinary `python3` environment lacks
`pypdf`. Poppler remains the preferred PDF backend; the validator also has a
recursive pypdf font-embedding fallback.

## Required semantic results

| Check | Required result | Current result |
| --- | --- | --- |
| Parts | 6 (`P1`-`P6`) | pending |
| Measures | 151 in every part | pending |
| MusicXML note elements | 2,787 | pending |
| Lyric anchors | 1,376 | pending |
| Canonical musical fingerprint | `82a6cfbb1b1856cf5af9a733c04df58ee2eeaacd2e611213de1b45ec6df3e111` | pending |
| Approved Fall replacements | all 388, with retained provenance chain | pending |
| Canonical lyric content | exact retained text, syllabification, extenders, voices, and lane numbers | pending |
| Lyric placement | 579 above and 797 below | pending |
| Additional lower lane | 17 stable P4 voice-2 / lyric-number-2 anchors, all below | pending |
| Staff lines | five throughout, with no hidden staff state | pending |

## Required PDF results

| Check | Required result | Current result |
| --- | --- | --- |
| Format | Letter portrait, 612 x 792 points, zero rotation | pending |
| Booklet count | exactly 40 pages: 39 music pages plus one nonblank colophon | pending |
| Blank pages | none | pending |
| Fonts | every referenced font embedded | pending |
| Page boxes | Media/Crop/Bleed/Trim/Art boxes valid and contained | pending |
| Safe content | at least 18 points from every page edge in the low-resolution preflight | pending |

## Human visual acceptance

Automated validation does not prove collision-free engraving, typography, or
performer readability. Before delivery, retain the staged full-page and
100-percent passage audit, including page 1, the densest lyric spread, measures
93-97, measure 115, measure 130, and the final system.
