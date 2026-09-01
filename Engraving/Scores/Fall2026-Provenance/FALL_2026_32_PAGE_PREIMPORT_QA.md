# Fall 2026 32-page pre-import QA

Audited source: `FlashlightsInTheDark_Fall2026_Dorico32PageCasted.musicxml`

SHA-256: `28eaade134594b196efd38d1d1f5a40504ba12176aaa373046ee6e0a3567b844`

Audit date: 2026-08-22

## Result

Pass for Dorico import. The file contains the intended 31 music pages and 36
systems, preserves the Stage E semantics except for the three approved changes,
and contains no one-line or hidden-staff state.

## Casting verified directly from MusicXML

| Page | System measure ranges |
| ---: | --- |
| 1 | 1-6 / 7-10 |
| 2 | 11-12 |
| 3 | 13-14 |
| 4 | 15-16 |
| 5 | 17-20 |
| 6 | 21-22 / 23-25 |
| 7 | 26-31 |
| 8 | 32-36 |
| 9 | 37-39 |
| 10 | 40-42 |
| 11 | 43-45 |
| 12 | 46-49 |
| 13 | 50-52 |
| 14 | 53-56 |
| 15 | 57-61 |
| 16 | 62-66 |
| 17 | 67-70 |
| 18 | 71-76 |
| 19 | 77-83 |
| 20 | 84-92 / 93-97 |
| 21 | 98-101 / 102-103 |
| 22 | 104-107 |
| 23 | 108-109 |
| 24 | 110-112 |
| 25 | 113-114 |
| 26 | 115-118 |
| 27 | 119-124 / 125-129 |
| 28 | 130-134 |
| 29 | 135-139 |
| 30 | 140-145 |
| 31 | 146-151 |

- Page-break starts: 11, 13, 15, 17, 21, 26, 32, 37, 40, 43, 46, 50,
  53, 57, 62, 67, 71, 77, 84, 98, 104, 108, 110, 113, 115, 119, 130,
  135, 140, 146.
- Within-page system-break starts: 7, 23, 93, 102, 125.
- Break directives are identical in all six parts. There are no `blank-page`
  or explicit page-number attributes.
- Page 1 has exactly two systems. The other two-system pages are 6, 20, 21,
  and 27.

## Structural and editorial invariants

- Six parts, 151 measures in every part, 2,787 notes, and 1,376 lyric anchors.
- Canonical musical fingerprint:
  `82a6cfbb1b1856cf5af9a733c04df58ee2eeaacd2e611213de1b45ec6df3e111`.
- Lyric routing remains 579 anchors above and 797 below and is byte-for-byte
  semantically identical to Stage E.
- The original 388-row Fall lyric ledger was independently re-read from its
  archived source (ledger SHA-256
  `f33e27238669628a4e2a0845f7b0b163523f952e05794da382e92e1e80f91da3`).
  All 388 target coordinates exist uniquely, all baseline preconditions match,
  and every final target text or special extender directive matches. The only
  later differences at ledger targets are eight logged `shad`/`ows`
  syllabification normalizations at measure 61; the replacement text is
  unchanged. Ledger distribution is P1 62, P2 75, P3 94, P4 30, P5 59, and
  P6 68.
- Exact correction text is present at P1 m.2 (`cacophonous`), P1 m.55
  (`reversed-impact sound event`), and P1 m.81 (`musique concrète`). The former
  spellings/forms are absent.
- `rearticulate freely in aleatoric style` occurs only on P1 at measures 115
  and 130. The three logged lower-Shadow duplicates remain absent.

After removing only casting break attributes, the two approved page-furniture
credits/metadata fields, and the approved P1 m.55 word-span normalization, the
full output XML tree is exactly equal to Stage E. Both normalized trees hash to
`84f853109f67009d6ade8ecf9cc53ae5586bbd750eeab71e5abc99ac8f3d539f`.

## Names, groups, and staves

- Shadow Chorus / Shadow: Soprano S / Sop. S, Alto S / Alto S, Baritone S /
  Bar. S.
- Light Chorus / Light: Soprano L1/L2 / Sop. L1/L2, Alto L1/L2 / Alto L1/L2,
  Tenor/Bass L / Ten./Bass L.
- Both groups use `bracket` and `group-barline=yes` directives.
- All 18 explicit staff states are five-line; no non-five-line, malformed, or
  hidden-staff state exists. Explicit resets occur at m.1-2 in every part and
  at m.89 and m.97 in the three Light parts.

## Page furniture and inherited formatting

- No visible MusicXML credit remains. `Set in 2076` and the commission line are
  preserved in identification miscellaneous fields for manual Dorico page
  furniture.
- There are zero `default-x`, `default-y`, `relative-x`, `relative-y`,
  `font-size`, `font-family`, or color overrides; there are also no local
  system/staff/measure layout nodes.
- Semantic typography retained: 30 `font-style` attributes (24 italic words,
  six normal dynamics) and 19 `font-weight` attributes (two bold words, 16
  bold rehearsal marks, one normal metronome).
- Page size is Letter portrait at 6.0 mm full-staff size. Source margins are
  mirrored 19 mm inside, 14 mm outside, and 15 mm top/bottom.
- The default `word-font` and `lyric-font` elements are empty, so the intended
  Academico sizes must be set in Dorico.

## Import-time UI checks

1. Confirm Dorico honors every imported page/system break: 31 music pages,
   36 systems, and exactly two systems on page 1 before appending the nonblank
   page-32 colophon.
2. Set the outside margin to the planned 15 mm; the source carries 14 mm.
3. Confirm the two player groups, brackets, and separate group barline joins.
   MusicXML group barline directives are not sufficient visual proof in Dorico.
4. Confirm all staves remain five-line, especially measures 1-2 and 89-97.
5. Populate the subtitle and commission fields/page template manually; Dorico
   may not map miscellaneous fields. Also prevent the retained arranger credit
   (`Text By Clare Malinowski & Jon Nelson`) from appearing as unwanted page
   furniture, and set the visible copyright exactly as approved.
6. Apply Bravura/Academico globally, set lyrics to 10.5 pt absolute, and audit
   direction text at 9.5-10 pt. The MusicXML deliberately contains no local
   font size/family overrides.
7. Visually verify imported lyric routing and third-lane behavior in P4-P6,
   group/player-name indentation, and the dense direction stack on page 1.
