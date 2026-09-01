# Fall 2026 Engraving Correction Log

This log records text-semantic corrections made during the Dorico publication
pass. Pure position, spacing, casting-off, and typography changes are not
listed here.

The complete editorial record has two linked layers:

- [`FALL_2026_LYRIC_CORRECTIONS.md`](FALL_2026_LYRIC_CORRECTIONS.md) enumerates
  all 60 pre-import lyric corrections, including every measure, part, anchor,
  before/after state, and rationale.
- The table below records the eight later direction, spelling, and duplicate-
  object corrections made during the Dorico cleanup stage.

Together these two tables are the human-readable companion to
`Engraving/Scores/Fall2026-Provenance/FlashlightsInTheDark_Fall2026_TextCorrectionReport.json`
and the Stage E cleanup report. The final semantic validation must account for
all 68 logged corrections and report no additional text difference.

| Measure | Part / scope | Before | After | Authority and rationale |
| --- | --- | --- | --- | --- |
| 2 | Soprano S | `cacouphonous` | `cacophonous` | Standard English orthography in a prose performance direction. |
| 55 | Soprano S / ensemble | `reversed -impact sound event` plus a trailing space | `reversed-impact sound event` | Removed the erroneous space before the existing compound hyphen and the trailing space so the instruction remains a single readable semantic object. |
| 81 | Soprano S | `musique concréte` | `musique concrète` | Correct French spelling of *musique concrète*. |
| 115 | Soprano S / ensemble | `rea` + `rticulate freely in aleatoric style` | `rearticulate freely in aleatoric style` | Rejoined one word that Finale exported as two adjacent objects and retained the resulting ensemble-wide instruction once above the top staff. |
| 115 | Alto S | duplicate `rearticulate freely in aleatoric style` | removed | Exact duplicate of the ensemble-wide instruction retained on Soprano S; removal prevents a second printed instruction without changing its wording or timing. |
| 130 | Soprano S / ensemble | `rea` + `rticulate freely in aleatoric style` | `rearticulate freely in aleatoric style` | Rejoined one word that Finale exported as two adjacent objects and retained the resulting ensemble-wide instruction once above the top staff. |
| 130 | Alto S | duplicate `rearticulate freely in aleatoric style` | removed | Exact duplicate of the ensemble-wide instruction retained on Soprano S. |
| 130 | Baritone S | duplicate `rearticulate freely in aleatoric style` | removed | Exact duplicate of the ensemble-wide instruction retained on Soprano S. |

## Unresolved editorial questions

The canonical source file named by `FALL_2026_WORKING_TEXT.md` was not present
in the active checkout during this pass. The validated 88-cue compiled copy
corroborates the imported Fall wording, but it is a generated artifact rather
than the editorial authority. No ambiguous wording was changed on that basis;
future punctuation or wording questions must remain unchanged until resolved
from the restored canonical working-text source or an approved editorial
decision.
