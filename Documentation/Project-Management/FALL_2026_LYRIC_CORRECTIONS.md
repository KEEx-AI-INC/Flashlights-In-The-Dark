# Fall 2026 Lyric Correction Inventory

This is the human-readable companion to the validated machine report
`Engraving/Scores/Fall2026-Provenance/FlashlightsInTheDark_Fall2026_TextCorrectionReport.json`. It enumerates all lyric-semantic
normalizations made before the Dorico import. The later direction and
duplicate-object corrections remain in
`Documentation/Project-Management/FALL_2026_ENGRAVING_CORRECTIONS.md`.

## Provenance and scope

- Source MusicXML SHA-256: `d9851e260dcb5a798fe9176e940beab16274c5e84459318fcfb486da169e9897`
- Corrected MusicXML SHA-256: `e7bc71c02f61fa09380c34da8c2668451b5ba5dd843e346f66a3fb01c7ccbff4`
- Enumerated lyric corrections: **60**
- Musical semantics and all lyric-anchor locations were preserved, as
  recorded by the validation block in the machine report.
- Authority: the validated Fall 2026 import and approved editorial
  normalization pass. The absent canonical Assembly source remains a
  provenance limitation; ambiguous wording was preserved for review.

Category totals:

- canonical case and punctuation: 20
- lyric lane and state: 13
- lyric spelling: 8
- lyric syllabification: 16
- lyric word and melisma: 3

## Complete correction ledger

| Measure | Part | Category | Before | After | Rationale |
| --- | --- | --- | --- | --- | --- |
| 18-19 | P1 | lyric word and melisma | m18 n1 v1 l1: text='lo', syllabic=single, extend=start, number=1; m18 n4 v1 l1: text=<none>, extend=stop, number=1; m19 n1 v1 l1: text='ove', syllabic=single, number=1 | m18 n1 v1 l1: text='love', syllabic=single, extend=start, number=1; m18 n4 v1 l1: text=<none>, extend=continue, number=1; m19 n1 v1 l1: text=<none>, extend=stop, number=1 | Re-encoded the one-syllable word 'love' as one text anchor with a continuous extender, without removing lyric anchors. |
| 18-19 | P2 | lyric word and melisma | m18 n1 v1 l1: text='lo', syllabic=single, extend=start, number=1; m18 n3 v1 l1: text=<none>, extend=stop, number=1; m19 n1 v1 l1: text='ove', syllabic=single, number=1 | m18 n1 v1 l1: text='love', syllabic=single, extend=start, number=1; m18 n3 v1 l1: text=<none>, extend=continue, number=1; m19 n1 v1 l1: text=<none>, extend=stop, number=1 | Re-encoded the one-syllable word 'love' as one text anchor with a continuous extender, without removing lyric anchors. |
| 18-19 | P3 | lyric word and melisma | m18 n1 v1 l1: text='lo', syllabic=single, extend=start, number=1; m18 n3 v1 l1: text=<none>, extend=stop, number=1; m19 n1 v1 l1: text='ove', syllabic=single, number=1 | m18 n1 v1 l1: text='love', syllabic=single, extend=start, number=1; m18 n3 v1 l1: text=<none>, extend=continue, number=1; m19 n1 v1 l1: text=<none>, extend=stop, number=1 | Re-encoded the one-syllable word 'love' as one text anchor with a continuous extender, without removing lyric anchors. |
| 51 | P3 | lyric spelling | m51 n2 v1 l1: text='ceed', syllabic=middle, number=1 | m51 n2 v1 l1: text='ced', syllabic=middle, number=1 | Corrected 'preceeding' to 'preceding' while retaining its note anchor. |
| 50 | P4 | lyric spelling | m50 n1 v1 l1: text='ceed', syllabic=middle, number=1 | m50 n1 v1 l1: text='ced', syllabic=middle, number=1 | Corrected 'preceeding' to 'preceding' while retaining its note anchor. |
| 50 | P5 | lyric spelling | m50 n1 v1 l1: text='ceed', syllabic=begin, number=1 | m50 n1 v1 l1: text='ced', syllabic=begin, number=1 | Corrected 'preceeding' to 'preceding' while retaining its note anchor. |
| 50 | P6 | lyric spelling | m50 n1 v2 l1: text='ceed', syllabic=middle, number=1 | m50 n1 v2 l1: text='ced', syllabic=middle, number=1 | Corrected 'preceeding' to 'preceding' while retaining its note anchor. |
| 99 | P4 | lyric spelling | m99 n1 v1 l1: text='wear', syllabic=begin, number=1, placement=above | m99 n1 v1 l1: text='wea', syllabic=begin, number=1, placement=above | Corrected the exported 'wear-ry' spelling to 'wea-ry'. |
| 99 | P4 | lyric spelling | m99 n3 v2 l2: text='wear', syllabic=begin, number=2 | m99 n3 v2 l2: text='wea', syllabic=begin, number=2 | Corrected the exported 'wear-ry' spelling to 'wea-ry'. |
| 99 | P5 | lyric spelling | m99 n2 v1 l1: text='wear', syllabic=begin, number=1, placement=above | m99 n2 v1 l1: text='wea', syllabic=begin, number=1, placement=above | Corrected the exported 'wear-ry' spelling to 'wea-ry'. |
| 99 | P6 | lyric spelling | m99 n2 v1 l1: text='wear', syllabic=begin, number=1, placement=above | m99 n2 v1 l1: text='wea', syllabic=begin, number=1, placement=above | Corrected the exported 'wear-ry' spelling to 'wea-ry'. |
| 103 | P6 | canonical case and punctuation | m103 n2 v1 l1: text='(yours', syllabic=single, extend=start, number=1, placement=above | m103 n2 v1 l1: text='(Yours', syllabic=single, extend=start, number=1, placement=above | Matched the unambiguous captured Fall cue '(Yours too.)'. |
| 103 | P6 | canonical case and punctuation | m103 n4 v1 l1: text='too)', syllabic=single, extend=start, number=1, placement=above | m103 n4 v1 l1: text='too.)', syllabic=single, extend=start, number=1, placement=above | Matched the unambiguous captured Fall cue '(Yours too.)'. |
| 140 | P4 | canonical case and punctuation | m140 n2 v1 l1: text='hmm', syllabic=single, extend=start, number=1 | m140 n2 v1 l1: text='Hmm.', syllabic=single, extend=start, number=1 | Matched the separately timed captured Fall cue 'Hmm.'. |
| 141 | P4 | canonical case and punctuation | m141 n2 v1 l1: text='hmm', syllabic=single, extend=start, number=1 | m141 n2 v1 l1: text='Hmm.', syllabic=single, extend=start, number=1 | Matched the separately timed captured Fall cue 'Hmm.'. |
| 142 | P4 | canonical case and punctuation | m142 n2 v1 l1: text='hmm', syllabic=single, extend=start, number=1 | m142 n2 v1 l1: text='Hmm.', syllabic=single, extend=start, number=1 | Matched the separately timed captured Fall cue 'Hmm.'. |
| 144 | P4 | canonical case and punctuation | m144 n2 v1 l1: text='hmm', syllabic=single, extend=start, number=1 | m144 n2 v1 l1: text='Hmm.', syllabic=single, extend=start, number=1 | Matched the separately timed captured Fall cue 'Hmm.'. |
| 148 | P4 | canonical case and punctuation | m148 n1 v1 l1: text='hmm', syllabic=single, number=1 | m148 n1 v1 l1: text='Hmm.', syllabic=single, number=1 | Matched the separately timed captured Fall cue 'Hmm.'. |
| 149 | P4 | canonical case and punctuation | m149 n1 v1 l1: text='hmm', syllabic=single, extend=start, number=1 | m149 n1 v1 l1: text='Hmm.', syllabic=single, extend=start, number=1 | Matched the separately timed captured Fall cue 'Hmm.'. |
| 140 | P5 | canonical case and punctuation | m140 n2 v1 l1: text='hmm', syllabic=single, extend=start, number=1 | m140 n2 v1 l1: text='Hmm.', syllabic=single, extend=start, number=1 | Matched the separately timed captured Fall cue 'Hmm.'. |
| 141 | P5 | canonical case and punctuation | m141 n2 v1 l1: text='hmm', syllabic=single, extend=start, number=1 | m141 n2 v1 l1: text='Hmm.', syllabic=single, extend=start, number=1 | Matched the separately timed captured Fall cue 'Hmm.'. |
| 142 | P5 | canonical case and punctuation | m142 n2 v1 l1: text='hmm', syllabic=single, extend=start, number=1 | m142 n2 v1 l1: text='Hmm.', syllabic=single, extend=start, number=1 | Matched the separately timed captured Fall cue 'Hmm.'. |
| 144 | P5 | canonical case and punctuation | m144 n2 v1 l1: text='hmm', syllabic=single, extend=start, number=1 | m144 n2 v1 l1: text='Hmm.', syllabic=single, extend=start, number=1 | Matched the separately timed captured Fall cue 'Hmm.'. |
| 148 | P5 | canonical case and punctuation | m148 n1 v1 l1: text='hmm', syllabic=single, number=1 | m148 n1 v1 l1: text='Hmm.', syllabic=single, number=1 | Matched the separately timed captured Fall cue 'Hmm.'. |
| 149 | P5 | canonical case and punctuation | m149 n1 v1 l1: text='hmm', syllabic=single, extend=start, number=1 | m149 n1 v1 l1: text='Hmm.', syllabic=single, extend=start, number=1 | Matched the separately timed captured Fall cue 'Hmm.'. |
| 140 | P6 | canonical case and punctuation | m140 n2 v1 l1: text='hmm', syllabic=single, extend=start, number=1 | m140 n2 v1 l1: text='Hmm.', syllabic=single, extend=start, number=1 | Matched the separately timed captured Fall cue 'Hmm.'. |
| 141 | P6 | canonical case and punctuation | m141 n2 v1 l1: text='hmm', syllabic=single, extend=start, number=1 | m141 n2 v1 l1: text='Hmm.', syllabic=single, extend=start, number=1 | Matched the separately timed captured Fall cue 'Hmm.'. |
| 142 | P6 | canonical case and punctuation | m142 n2 v1 l1: text='hmm', syllabic=single, extend=start, number=1 | m142 n2 v1 l1: text='Hmm.', syllabic=single, extend=start, number=1 | Matched the separately timed captured Fall cue 'Hmm.'. |
| 144 | P6 | canonical case and punctuation | m144 n2 v1 l1: text='hmm', syllabic=single, extend=start, number=1 | m144 n2 v1 l1: text='Hmm.', syllabic=single, extend=start, number=1 | Matched the separately timed captured Fall cue 'Hmm.'. |
| 148 | P6 | canonical case and punctuation | m148 n1 v1 l1: text='hmm', syllabic=single, number=1 | m148 n1 v1 l1: text='Hmm.', syllabic=single, number=1 | Matched the separately timed captured Fall cue 'Hmm.'. |
| 149 | P6 | canonical case and punctuation | m149 n1 v1 l1: text='hmm', syllabic=single, extend=start, number=1 | m149 n1 v1 l1: text='Hmm.', syllabic=single, extend=start, number=1 | Matched the separately timed captured Fall cue 'Hmm.'. |
| 61 | P1 | lyric syllabification | m61 n4 v1 l1: text='shad', syllabic=single, number=1 | m61 n4 v1 l1: text='shad', syllabic=begin, number=1 | Marked the first syllable of 'shadows' consistently. |
| 61 | P1 | lyric syllabification | m61 n5 v1 l1: text='ows', syllabic=single, number=1 | m61 n5 v1 l1: text='ows', syllabic=end, number=1 | Marked the final syllable of 'shadows' consistently. |
| 61 | P2 | lyric syllabification | m61 n4 v1 l1: text='shad', syllabic=single, number=1 | m61 n4 v1 l1: text='shad', syllabic=begin, number=1 | Marked the first syllable of 'shadows' consistently. |
| 61 | P2 | lyric syllabification | m61 n5 v1 l1: text='ows', syllabic=single, number=1 | m61 n5 v1 l1: text='ows', syllabic=end, number=1 | Marked the final syllable of 'shadows' consistently. |
| 61 | P3 | lyric syllabification | m61 n4 v1 l1: text='shad', syllabic=single, number=1 | m61 n4 v1 l1: text='shad', syllabic=begin, number=1 | Marked the first syllable of 'shadows' consistently. |
| 61 | P3 | lyric syllabification | m61 n5 v1 l1: text='ows', syllabic=single, number=1 | m61 n5 v1 l1: text='ows', syllabic=end, number=1 | Marked the final syllable of 'shadows' consistently. |
| 61 | P5 | lyric syllabification | m61 n4 v1 l1: text='shad', syllabic=single, number=1 | m61 n4 v1 l1: text='shad', syllabic=begin, number=1 | Marked the first syllable of 'shadows' consistently. |
| 61 | P5 | lyric syllabification | m61 n5 v1 l1: text='ows', syllabic=single, number=1 | m61 n5 v1 l1: text='ows', syllabic=end, number=1 | Marked the final syllable of 'shadows' consistently. |
| 61 | P6 | lyric syllabification | m61 n5 v2 l1: text='shad', syllabic=single, number=1 | m61 n5 v2 l1: text='shad', syllabic=begin, number=1 | Marked the first syllable of 'shadows' consistently. |
| 61 | P6 | lyric syllabification | m61 n6 v2 l1: text='ows', syllabic=single, number=1 | m61 n6 v2 l1: text='ows', syllabic=end, number=1 | Marked the final syllable of 'shadows' consistently. |
| 67 | P2 | lyric syllabification | m67 n3 v1 l1: text='flash', syllabic=single, extend=start, number=1 | m67 n3 v1 l1: text='flash', syllabic=begin, extend=start, number=1 | Marked the first syllable of 'flashlights' consistently. |
| 67 | P2 | lyric syllabification | m67 n5 v1 l1: text='lights', syllabic=single, extend=start, number=1 | m67 n5 v1 l1: text='lights', syllabic=end, extend=start, number=1 | Marked the final syllable of 'flashlights' consistently. |
| 68 | P2 | lyric syllabification | m68 n6 v1 l1: text='dark', syllabic=single, number=1 | m68 n6 v1 l1: text='dark', syllabic=begin, number=1 | Marked 'dark-ness' as a two-syllable word. |
| 69 | P2 | lyric syllabification | m69 n1 v1 l1: text='ness', syllabic=single, number=1 | m69 n1 v1 l1: text='ness', syllabic=end, number=1 | Marked 'dark-ness' as a two-syllable word. |
| 38 | P5 | lyric syllabification | m38 n5 v2 l1: text='Shin', syllabic=single, extend=start, number=1 | m38 n5 v2 l1: text='Shin', syllabic=begin, extend=start, number=1 | Marked voice 2 'Shin-ing' consistently. |
| 38 | P5 | lyric syllabification | m38 n7 v2 l1: text='ing', syllabic=single, number=1 | m38 n7 v2 l1: text='ing', syllabic=end, number=1 | Marked voice 2 'Shin-ing' consistently. |
| 54 | P4 | lyric lane and state | m54 n5 v2 l2: text='flur', syllabic=middle, number=1 | m54 n5 v2 l2: text='flur', syllabic=begin, number=2 | Moved the complete lower 'flur-ries' phrase into lyric line 2. |
| 54 | P4 | lyric lane and state | m54 n7 v2 l2: text='ries', syllabic=single, extend=start, number=2 | m54 n7 v2 l2: text='ries', syllabic=end, extend=start, number=2 | Closed the lower 'flur-ries' word in lyric line 2. |
| 100 | P4 | lyric lane and state | m100 n3 v2 l2: text="I'll", syllabic=end, number=1 | m100 n3 v2 l2: text="I'll", syllabic=end, number=2 | Kept the lower warmth phrase in stable lyric line 2. |
| 102 | P4 | lyric lane and state | m102 n9 v2 l2: text='yours', syllabic=single, extend=start, number=1 | m102 n9 v2 l2: text='yours', syllabic=single, extend=start, number=2 | Kept the lower warmth phrase in stable lyric line 2. |
| 100 | P4 | lyric lane and state | m100 n3 v2 l2: text="I'll", syllabic=end, number=2 | m100 n3 v2 l2: text="I'll", syllabic=single, number=2 | Repaired an impossible begin/middle/end state within its stable voice lane. |
| 101 | P4 | lyric lane and state | m101 n1 v1 l1: text='ry', syllabic=single, number=1 | m101 n1 v1 l1: text='ry', syllabic=end, number=1 | Repaired an impossible begin/middle/end state within its stable voice lane. |
| 99 | P5 | lyric lane and state | m99 n3 v2 l1: text='wea', syllabic=end, extend=start, number=1 | m99 n3 v2 l1: text='wea', syllabic=begin, extend=start, number=1 | Repaired an impossible begin/middle/end state within its stable voice lane. |
| 99 | P5 | lyric lane and state | m99 n4 v2 l1: text='ry', syllabic=single, extend=start, number=1 | m99 n4 v2 l1: text='ry', syllabic=end, extend=start, number=1 | Repaired an impossible begin/middle/end state within its stable voice lane. |
| 100 | P5 | lyric lane and state | m100 n1 v1 l1: text='ry', syllabic=single, number=1, placement=above | m100 n1 v1 l1: text='ry', syllabic=end, number=1, placement=above | Repaired an impossible begin/middle/end state within its stable voice lane. |
| 100 | P5 | lyric lane and state | m100 n4 v2 l1: text="I'll", syllabic=end, number=1 | m100 n4 v2 l1: text="I'll", syllabic=single, number=1 | Repaired an impossible begin/middle/end state within its stable voice lane. |
| 101 | P5 | lyric lane and state | m101 n2 v1 l1: text='ry', syllabic=single, number=1, placement=above | m101 n2 v1 l1: text='ry', syllabic=end, number=1, placement=above | Repaired an impossible begin/middle/end state within its stable voice lane. |
| 100 | P6 | lyric lane and state | m100 n5 v2 l1: text="I'll", syllabic=end, number=1 | m100 n5 v2 l1: text="I'll", syllabic=single, number=1 | Repaired an impossible begin/middle/end state within its stable voice lane. |
| 101 | P6 | lyric lane and state | m101 n2 v1 l1: text='ry', syllabic=single, number=1, placement=above | m101 n2 v1 l1: text='ry', syllabic=end, number=1, placement=above | Repaired an impossible begin/middle/end state within its stable voice lane. |

## Preserved ambiguities and review items

- P1 m.115: `rearticulate freely in aleatoric style` — Preserved the literal rea + rticulate concatenation; did not substitute 'articulate'.
- P1 m.130: `rearticulate freely in aleatoric style` — Preserved the literal rea + rticulate concatenation; did not substitute 'articulate'.
- P2 m.115: `rearticulate freely in aleatoric style` — Preserved the literal rea + rticulate concatenation; did not substitute 'articulate'.
- P2 m.130: `rearticulate freely in aleatoric style` — Preserved the literal rea + rticulate concatenation; did not substitute 'articulate'.
- P3 m.130: `rearticulate freely in aleatoric style` — Preserved the literal rea + rticulate concatenation; did not substitute 'articulate'.
- P1 m.20: `though` — Explicitly excluded from this definite-correction pass.
- uncertain phrase punctuation: No punctuation beyond the captured '(Yours too.)' and 'Hmm.' cues was changed.
