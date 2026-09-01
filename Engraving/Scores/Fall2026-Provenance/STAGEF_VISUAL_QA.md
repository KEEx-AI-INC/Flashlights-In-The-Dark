# Stage F visual QA

Audited source: `FlashlightsInTheDark_Fall2026_PerformerScore_StageF.pdf`

Comparison source: `FlashlightsInTheDark_Fall2026_PerformerScore_StageE.pdf`

Audit date: 2026-08-22

Method: all 23 Stage F pages were rendered as complete Letter pages at 120 dpi and inspected individually. Every page's densest passage was then re-inspected from a 300 dpi render; pages 1, 3, 5, 10, 16, 17, 19, 20, 22, and 23 were inspected in multiple 300 dpi crops. PDF dimensions, page count, visible page content, page edges, and embedded font objects were checked separately.

## Verdict

**Fail - substantially better cast-off, but not publishable or rehearsal-ready.** The 23-page music cast is a meaningful improvement over Stage E: the five Stage E system-boundary collisions are gone, most one-system pages are readable, m.115 and m.130 each carry one clear system-wide aleatoric instruction, and m.93-97 chord symbols are individually legible at 300 dpi. However, two new literal system collisions occur at m.14/15 on page 3 and m.134/135 on page 22. Page 1 remains unusable, local lyric/dynamic/extender collisions remain severe on pages 5, 10, 17, 19, and 23, ensemble names and group barlines are still missing, and the intended nonblank page 24 has not been added. The delivered 23-page PDF is therefore neither divisible by four nor saddle-stitch ready.

The correct next move is not to recast the readable one-system pages. Retain the 23-page musical map, repair the two colliding two-system pages and the named local passages, rebuild page 1, then add the intended native Dorico colophon as page 24.

## Basic preflight

- Pass: 23 US Letter portrait pages (612 x 792 pt).
- Pass: no blank pages among the 23 exported pages; every page contains music.
- Pass: 34 musical systems; page 1 has exactly two systems.
- Pass: all six staves are visible and five-line throughout.
- Pass: Academico, Academico Bold, Academico Italic, Bravura, and Bravura Text are present with embedded font-file objects.
- Pass: no hard clipping was found at the page edges.
- Pass: later-page running titles are centered and page numbers alternate to the outside correctly.
- Partial: separate Shadow and Light brackets are visible on every system.
- Fail: 23 pages is not divisible by four. The required nonblank page 24 colophon is absent.
- Fail: page 1 has exactly two systems but its title, credits, instructions, and music collide.
- Fail: the two ensembles are printed only as numeric `1` and `2` markers; `Shadow Chorus` and `Light Chorus` do not appear.
- Fail: barlines are not joined through the three staves of either ensemble.
- Fail: abbreviated Light staff labels remain awkward or truncated, notably `Sop. L1/L` instead of an unambiguous `Sop. L1/L2`.

## Stage E to Stage F comparison

| Test | Stage E | Stage F | Result |
| --- | ---: | ---: | --- |
| Music pages | 15 | 23 | Readability-first expansion achieved |
| Musical systems | 29 | 34 | Denser systems were subdivided |
| Pages with literal system-on-system collisions | 5 | 2 | Three fewer pages; 60 percent reduction |
| Former Stage E collision boundaries | 5 | 0 | All five are structurally resolved |
| New collision boundaries | 5 | 2 | M.14/15 and m.134/135 now collide |
| M.115 direction instances | 2 | 1 | Fixed |
| M.130 direction instances | 3 | 1 | Fixed |
| Separate three-staff brackets | Yes | Yes | Retained |
| Readable ensemble names and joined group barlines | No | No | Unresolved |
| M.93-97 chord string | Crowded and near-continuous | Legible but still under-spaced | Improved, still needs local work |
| Booklet-compatible final page count | No | No | Page 24 remains absent |

The two new collision boundaries are:

1. page 3, m.14/15: the upper system's Tenor/Bass L staff and label are superimposed on the lower system's Soprano S staff and label;
2. page 22, m.134/135: the upper system's Tenor/Bass L staff and label are superimposed on the lower system's Soprano S staff and label.

## Actual Stage F cast-off

| Page | Systems | Inclusive measure range by system |
| ---: | ---: | --- |
| 1 | 2 | 1-6; 7-10 |
| 2 | 1 | 11-12 |
| 3 | 2 | 13-14; 15-16 |
| 4 | 1 | 17-20 |
| 5 | 2 | 21-25; 26-31 |
| 6 | 1 | 32-36 |
| 7 | 1 | 37-39 |
| 8 | 1 | 40-42 |
| 9 | 1 | 43-45 |
| 10 | 2 | 46-52; 53-56 |
| 11 | 1 | 57-61 |
| 12 | 1 | 62-66 |
| 13 | 1 | 67-70 |
| 14 | 1 | 71-76 |
| 15 | 2 | 77-80; 81-88 |
| 16 | 2 | 89-92; 93-97 |
| 17 | 2 | 98-101; 102-103 |
| 18 | 1 | 104-107 |
| 19 | 2 | 108-112; 113-114 |
| 20 | 1 | 115-118 |
| 21 | 2 | 119-124; 125-129 |
| 22 | 2 | 130-134; 135-139 |
| 23 | 2 | 140-145; 146-151 |

## Page-by-page findings

| Page | Measures | Visual result |
| ---: | --- | --- |
| 1 | 1-10 | **Severe fail.** Exactly two systems are present, with the improved 1-6 / 7-10 balance, but the page furniture is unusable. `Moderato`, the metronome mark, title, `nighttime sounds mixed with`, rehearsal mark 2, composer/credit text, and `Begin in darkness` occupy the same title band. `Set in 2076` and the commission line are not legible. Both systems have fused or doubled lyrics (`Here now`, `wake`, `with no light`, `Who sees beyond`, `This world is loud`, `listen for primer tone`, `we are connected by`) and dynamics/notes strike lyric lanes. Copyright is visible and not clipped. |
| 2 | 11-12 | **Pass with minor qualifications.** The single system is physically clean and the soloist material is readable. Large vertical gaps are acceptable for this uniquely layered passage. Multi-voice text is spread over several lanes but does not collide at print zoom. |
| 3 | 13-16 | **Catastrophic m.14/15 overlap.** The Tenor/Bass L staff and label at the end of the upper system occupy the same vertical band as the Soprano S staff and label at the beginning of the lower system. Notes, staff lines, clefs, labels, and `Look at this!` merge. The rest of both systems is reasonably readable away from the boundary. |
| 4 | 17-20 | **Pass.** One complete system with clear Shadow text and adequately separated Light multi-voice lanes. The isolated lower-voice `oh` extender is visually odd, but it does not collide. |
| 5 | 21-31 | **Fail for local collisions, although the two systems do not overlap.** In m.21-25, a dynamic strikes `the night`, `a-las` touches notation, and Light text prints as `inthenight` and `atlast`; hairpins and `mp`/`pp` markings compete with the lower lanes. In m.26-31, hairpins cross `less`, and `mp`/`we rest` are superimposed in Alto L1/L2. Rehearsal 31, `Andante`, and `clock ticking sounds` remain legible in the inter-system space. |
| 6 | 32-36 | **Pass.** The single-system cast gives `Who can feel?`, `look here`, `look at this!`, and `new light` usable separation. No meaningful collision was found at 300 dpi. |
| 7 | 37-39 | **Pass with cleanup still desirable.** The one-system cast removes the former boundary problem. Three Light lyric lanes are stable enough to follow and do not strike notes, though long extenders and hairpins remain visually heavy. The page turn after m.39 is musically unsafe because the phrase and a tie continue into m.40. |
| 8 | 40-42 | **Pass with minor extender cleanup.** `fall on dreary dawns`, `where is the sun`, `bloom`, and `autumn` are readable. Long extenders and hairpins dominate the left half but remain clear of words at 300 dpi. |
| 9 | 43-45 | **Pass visually.** Sparse one-system page with no collision and a workable turn. Isolated continuation fragments (`-tumn` and `as au-...-tumn`) look editorially awkward but are not a spacing failure. |
| 10 | 46-56 | **Severe fail.** In the upper system, `What are wonders` prints through Alto S and Baritone S notation, while Shadow lyric strings around `With color preceding night` fuse and overwrite one another. `impact sound event reversed` is fragmented at the lower right of the system. In the lower system, long horizontal lines cross `Where...wonders without stars?` and the Light `flurries of color in the sky` lanes; dynamics and syllables are superimposed. The two staff systems are physically separate, but local objects remain unreadable. |
| 11 | 57-61 | **Pass with a routing concern.** Shadow `Where sleeps the light?` and `Deep shadows` are clear. Light lower voices are readable. The isolated `light` line and hairpins in the otherwise empty Soprano L1/L2 staff create an unexplained extra lane, but do not collide. The turn after m.61 is strong. |
| 12 | 62-66 | **Pass.** The one-system cast isolates the m.66 entrance successfully. `live in night` and `We carry on` are readable; the Baritone S `mf` sits close to the lyric but remains distinct. |
| 13 | 67-70 | **Pass with small local clearances needed.** Multi-voice Light lanes are consistent and readable. A few dynamics sit close to `lights`/`darkness`, but no object is obscured. |
| 14 | 71-76 | **Pass.** Changing meters, dynamics, and `new world`/`Bright world` text are clear. No collision was found. |
| 15 | 77-88 | **Pass.** M.77-80 is readable, and the tacet m.81-88 system is clean. `musique concrete` is clear. This provides the best right-hand page turn in the score before m.89. |
| 16 | 89-97 | **Partial pass.** Both systems are vertically clean. M.89-92 chord symbols are comfortable. Every m.93-97 chord identity is legible at 300 dpi and no glyphs literally overlap, an improvement over Stage E; however, adjacent long symbols around `C(add flat 9)/E` / `Cm/E flat` and `Abmaj7(add flat 11)` / `E flat aug(maj7)/Ab` have insufficient breathing room for a polished print score. Local horizontal spacing is still required. |
| 17 | 98-103 | **Severe fail for lyric extenders.** Systems and staves are physically separated, but imported extension lines run through `hands grow weary`, `I'll carry`, `yours too`, alternate lyric lanes, and dynamics in both systems. Several near-parallel lines extend almost the full system and make voice routing visually ambiguous. The musical turn after m.103 is strong, but the page itself is not readable enough to print. |
| 18 | 104-107 | **Pass with a voice-label concern.** Chord symbols and notes are clear. Repeated `One light, though dim` lanes remain visually redundant, especially around Baritone S and Soprano L1/L2, and would benefit from explicit entrance/voice labels, but they do not collide. |
| 19 | 108-114 | **Severe fail in m.108-112.** Baritone S prints doubled `with`, `love`, and `can` syllables directly on top of one another; `pierce`/extender lines overlap; Alto S prints `night` and `subito` as one fused word; several `subito mp` markings occupy lyric space. The short m.113-114 system is clearer, although long extenders remain. |
| 20 | 115-118 | **Pass for the named instruction.** `rearticulate freely in aleatoric style` appears once above the ensemble, is large enough, and has clear space. Notes and principal lyrics are readable. Long lower-voice extenders remain visually heavy but do not obstruct text. |
| 21 | 119-129 | **Pass with minor cleanup.** The two systems are physically separate and the repeated aleatoric `who`/`Where are we?`/`Warm hearts light` fields are followable. Long horizontal lyric lines dominate some empty staves but do not cross words. The turn after `new home.` is musically complete but fast for Shadow singers. |
| 22 | 130-139 | **Catastrophic m.134/135 overlap.** The m.130 `rearticulate freely in aleatoric style` direction appears once and is readable. At the system boundary, however, the upper Tenor/Bass L staff and label are superimposed on the lower Soprano S staff and label; clefs, notes, ties, and staff lines merge. This page cannot be used in rehearsal or print. |
| 23 | 140-151 | **Fail for local dynamic/lyric collisions.** The two systems are physically separated, `shimmering polytonal sound chandelier` is legible, and the final barline is present. In the final system, `ppp` is printed directly over `night` on all three Shadow staves, producing `pppnight`-like collisions. Light `Hmmm.` lanes and their dynamics are clearer, though their extenders remain long. There is no page 24 colophon. |

## Ensemble grouping and labels

The two three-staff brackets are structurally clear and persist on every system. The engraving plan's remaining grouping requirements still fail:

- the printed group identifiers are tiny `1` and `2` markers, not `Shadow Chorus` and `Light Chorus`;
- full and abbreviated Light staff names are inconsistent or truncated;
- internal barlines stop at each staff and do not join the three staves within either group.

These are global setup/engraving changes, not local collision edits.

## Focused high-risk audit

### Page 1 / m.1-10

- Exactly two systems: **pass**.
- Rebalanced 1-6 / 7-10 split: **pass structurally**.
- Two ensemble brackets: **pass**.
- Title/credit/instruction hierarchy: **fail**.
- `Set in 2076`, commission line, and Jon D. Nelson credit: **fail as readable furniture**.
- Lyric and direction readability: **fail**.

### M.93-97 chord symbols

- Vertical separation from m.89-92: **pass**.
- Individual chord identity at 300 dpi: **pass**.
- Publication-quality horizontal clearance between adjacent long symbols: **fail**.

### M.115 and m.130 aleatoric directions

- M.115: **pass**. One clear system-wide instruction.
- M.130: **pass**. One clear system-wide instruction.
- Page 22 immediately below m.130: **fail** because the m.134/135 system boundary collides.

### Lyrics and extenders

- Stable enough to print on pages 2, 4, 6-9, 11-15, 18, 20, and 21.
- Local cleanup still needed on pages 12, 13, and 18, but those pages are readable.
- Not print-ready on pages 1, 5, 10, 17, 19, and 23.

## Right-hand page-turn audit

The Stage F page boundaries match the planned 23-music-page cast. The musical assessment therefore remains:

| Turn after page | Boundary | Rating | Visual/musical implication |
| ---: | --- | --- | --- |
| 1 | m.10 / m.11 | Marginal | One Light voice ties across and the title page is visually overloaded. |
| 3 | m.16 / m.17 | Unsafe | The phrase continues, and page 3 also has a literal m.14/15 collision. |
| 5 | m.31 / m.32 | Strong | Clock/Andante reset with at least 4.5 quarter-note beats in every part. |
| 7 | m.39 / m.40 | Unsafe | Tenor/Bass L ties across and the Shining/bloom texture continues. |
| 9 | m.45 / m.46 | Workable | No cross-bar tie and most parts have at least 2.5 beats. |
| 11 | m.61 / m.62 | Strong | Every active part has at least two beats of rest and no ties. |
| 13 | m.70 / m.71 | Workable | One shared beat, no ties, and a formal colon/new-world return. |
| 15 | m.88 / m.89 | Ideal | At least six beats of silence in every part. |
| 17 | m.103 / m.104 | Strong musically | One shared beat and no ties, although page 17's extender field is unreadable. |
| 19 | m.114 / m.115 | Workable | No ties; m.115 begins at the top of a clean one-system page. |
| 21 | m.129 / m.130 | Workable but fast | Complete `new home.` cadence; Shadow singers have only a half-beat. |
| 23 | m.151 / page 24 | End of music | No live musical turn; the nonblank colophon is still missing. |

## Required corrections before the next proof

1. Rebuild page 1's title, subtitle, commission, composer, opening instructions, and music-frame spacing while retaining exactly two systems.
2. Eliminate the m.14/15 collision on page 3 and the m.134/135 collision on page 22. These require vertical/system-frame intervention, not object nudging.
3. Remove or reroute legacy lyric extension lines and duplicate lyric objects on pages 5, 10, 17, and 19.
4. Move the final-system `ppp` dynamics away from `night` on page 23.
5. Give the m.93-97 chord symbols explicit horizontal clearance without changing chord identities.
6. Replace numeric group markers with readable Shadow/Light naming, restore joined group barlines, and fix truncated Light staff abbreviations.
7. Add a real, nonblank native Dorico colophon as page 24; do not leave a blank or deliver 23 pages.
8. Re-export and inspect all 24 pages again at full-page size and at 300 dpi before calling the score print-ready.

Stage F is the right musical cast-off foundation, but it remains an intermediate proof rather than the Fall 2026 performer-score deliverable.
