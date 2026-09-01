# Stage J global-polish visual QA

Audited proof: `FlashlightsInTheDark_Fall2026_PerformerScore_StageJ_GlobalPolish.pdf`

Audit date: 2026-08-22

## Result

**The Stage J proof improves the imported score's hierarchy, but it is not yet
print-ready.** The intended 31-page music cast remains intact, all six staves
remain five-line, page 1 still has exactly two systems, and the two choruses now
have correct labels and separate brackets. Lyrics now print at the approved
10.5 pt size, and the directions at measures 115 and 130 are complete, singular,
and clear.

The principal publication blockers are page 1, actual inter-system overlaps on
pages 6 and 27, the unresolved lyric/extender field on page 21, the chord-symbol
row on page 20, and `Cmaj9/Esubito` on page 24. The barlines are also still not
joined within the two chorus groups, and player names still print at 8.5 pt,
below the planned 9.5-10 pt floor.

This proof contains only the 31 music pages. The prepared nonblank page-32
colophon was not appended or audited in this stage.

## Audit method

- Rendered all 31 pages at 300 dpi (2550 x 3300 pixels) and inspected every page
  in a full-page view.
- Inspected native-resolution close-ups of page 1, the system boundaries on
  pages 6 and 27, the chord and lyric passages on pages 20-21 and 24, measures
  115 and 130, and the final system.
- Cross-checked page count, dimensions, page text/nonblank status, sampled text
  sizes, and embedded font resources from the PDF.
- Compared every finding with the Stage I raw-import report. No changes were
  made to the Dorico project or proof.

## Structural and typography checks

- **31 nonblank Letter pages:** pass. Every page is 612 x 792 points and contains
  score content; no page-edge clipping was found.
- **System map:** pass. The proof retains 36 systems. Pages 1, 6, 20, 21, and 27
  have two systems; all other pages have one.
- **Page 1:** exactly two systems, as required.
- **Staves:** all six are visible and five-line throughout, including page 1,
  measures 89-97, and the finale.
- **Grouping:** `Shadow Chorus` and `Light Chorus` appear as two clearly labelled
  three-staff groups with separate brackets. Full player names appear on page 1
  and sensible abbreviations later; the L1/L2 names are corrected.
- **Group barlines:** fail. Internal measure barlines remain isolated to each
  staff instead of joining the three staves within each chorus.
- **Fonts:** Academico, Academico Bold/Italic, Bravura, and Bravura Text are
  embedded.
- **Printed sizes:** sampled lyrics are Academico 10.5 pt, directions are 10 pt,
  and chord symbols are 9.5 pt. Player names remain 8.5 pt and need enlargement.
- **Running furniture:** later pages consistently carry a centered running title
  and outside folio. Page 1 has a title and copyright, but its required subtitle,
  commission line, and composer credit are absent.

## Comparison with Stage I

### Material improvements

- The continuous unlabelled six-staff bracket has been replaced by the correct
  Shadow/Light labels and separate primary brackets.
- Lyrics have increased from 9.5 pt to 10.5 pt; performance directions remain
  readable at 10 pt.
- The duplicate second title on page 1 is gone, and the copyright line is now
  present.
- `rearticulate freely in aleatoric style` is complete and appears once above
  the ensemble at both measures 115 and 130.

### New or worsened regressions

- Enlarged typography without a corresponding vertical recast has created real
  system-on-system collisions on pages 6 and 27, both of which passed that test
  in Stage I.
- Page 1's already crowded opening is less readable at the larger lyric size.
- One-system vertical justification remains inconsistent: pages 2, 7, 11, 25,
  and 31 spread the six staves excessively, while several other pages remain
  top-heavy with large lower white fields.

## Blocking passages

1. **Page 1 / measures 1-10:** The tempo and `nighttime sounds mixed with`
   instruction print through the title, and rehearsal mark 2 sits inside the
   title field. `Set in 2076`, the commission line, and `Jon D. Nelson` are
   missing. In the first system, lyrics and dynamics run through notes and each
   other (`Herenow`, `wake`, `Who sees beyond this dark`). In the second system,
   `listen for primer tone`, `Life, light`, `we are connected by`, and the final
   Tenor/Bass text collide or fuse. The page has two systems but does not have a
   usable title/opening hierarchy.
2. **Page 6 / measures 21-25:** The first system's Tenor/Bass L staff and label
   overlap the second system's Soprano S staff and label at measure 23. This is a
   literal system collision, not merely tight spacing.
3. **Page 20 / measures 93-97:** The chord row remains run-on. The tightest span
   is `C(add flat 9)/E` through `Cmaj9/E`; `Abmaj7(add11)` and
   `Ebaug(maj7)/Ab` have no usable separation. The notes and lyrics remain
   readable, but the harmonic line does not meet publication spacing standards.
4. **Page 21 / measures 98-103:** This remains the largest print blocker.
   Duplicate lyric lanes, long continuation rules, hairpins, and dynamics cross
   through `hands grow weary`, `I'll carry your`, `yours`, and `too`. Several
   words print twice only a few points apart, and horizontal rules run through
   both text and staff material. The passage cannot be reliably read in
   performance.
5. **Page 24 / measures 110-112:** `Cmaj9/E` and `subito` still touch and read as
   `Cmaj9/Esubito`; the nearby `mp` does not resolve the ambiguity. The direction
   must be moved away from the chord-symbol lane.
6. **Page 27 / measures 119-129:** The upper system's Light Chorus Tenor/Bass L
   staff and lyrics collide with the lower system's Shadow Chorus Soprano S
   staff at measure 125. Player labels and group brackets overlap as well. Long
   empty-looking lyric rules compound the failure.

## Page-by-page findings

| Page | Measures / systems | Stage J finding |
| ---: | --- | --- |
| 1 | 1-6 / 7-10 | **Fail.** Exactly two systems and correct group labels, but title furniture and opening lyrics collide extensively; required subtitle, commission, and composer lines are absent. |
| 2 | 11-12 | Readable, but the single system is vertically over-stretched. The Light multi-voice entrance needs routine lane refinement. |
| 3 | 13-14 | Pass structurally and locally; directions and lyric lanes are readable. |
| 4 | 15-16 | Pass structurally. Dense text remains horizontally readable; retain the generous width. |
| 5 | 17-20 | Pass structurally. Multi-voice Light extenders need routine normalization. |
| 6 | 21-22 / 23-25 | **Fail.** Actual overlap between the first system's Tenor/Bass L and the second system's Soprano S, including labels, bracket, staff, and music. |
| 7 | 26-31 | Readable, including rehearsal 31, Andante, tempo, and `clock ticking sounds`; single-system vertical spreading is excessive. |
| 8 | 32-36 | Pass. Multi-voice Light routing is legible; inherited continuation rules remain prominent. |
| 9 | 37-39 | Pass. Hairpins, dynamics, and entrances are clear. |
| 10 | 40-42 | Pass with cleanup. The dense Light texture is readable, but the stacked lyric/extender field remains visually heavy. |
| 11 | 43-45 | Pass structurally; system-start text fragments remain awkward and the system is vertically over-stretched. |
| 12 | 46-49 | Cleanup required. Empty-looking parenthesis pairs remain in Alto S and Alto L; determine whether they are semantic or imported artifacts. |
| 13 | 50-52 | Pass. `What are wonders` and the changing-meter material are readable. |
| 14 | 53-56 | Pass with cleanup. `reversed-impact sound event` is clear; three Light lyric lanes and long rules remain crowded. |
| 15 | 57-61 | Pass. `Where sleeps the light?` and `Deep shadows` are clear. |
| 16 | 62-66 | Pass structurally. Rehearsal 66 is clear, but adjacent `p`/`mf` and the Light `We carry on` entrance need local direction spacing. |
| 17 | 67-70 | Pass. Dense music and text remain readable; normalize isolated continuation marks. |
| 18 | 71-76 | Pass. Changing meters and `new world` / `Bright world` lanes are clear. |
| 19 | 77-83 | Cleanup required. All three Light staves still read `Bright,_shared`; shorten or reroute the extender. `musique concrète` is correct and clear. |
| 20 | 84-92 / 93-97 | **Fail locally.** Two systems remain separate, but the lower chord-symbol row is run-on from `C(add flat 9)/E` through `Cmaj9/E`. |
| 21 | 98-101 / 102-103 | **Fail.** Duplicated lyrics, long rules, hairpins, and dynamics create extensive collisions across both systems. |
| 22 | 104-107 | Pass. Chords, repeated `One light` entries, ties, and dynamics are clear. |
| 23 | 108-109 | Pass structurally. `with love,` is clear; Light continuation rules still need normalization. |
| 24 | 110-112 | **Fail locally.** `Cmaj9/Esubito` remains fused. The rest of the page is readable, though the many long lyric rules are visually dominant. |
| 25 | 113-114 | Pass structurally, but single-system vertical spreading and long Light continuation rules need refinement. |
| 26 | 115-118 | Pass. The aleatoric instruction is singular, complete, and clear; the multi-voice text is readable. |
| 27 | 119-124 / 125-129 | **Fail.** The two systems overlap at the Light Tenor/Bass L / Shadow Soprano S boundary, and long empty-looking continuation rules remain. |
| 28 | 130-134 | Pass. The second aleatoric instruction is singular, complete, and clear; Light entries are readable. |
| 29 | 135-139 | Pass. Final-transition text and music are clear; long rules remain visually prominent. |
| 30 | 140-145 | Pass. Rehearsal 140 and `shimmering polytonal sound chandelier` are clear and non-colliding. |
| 31 | 146-151 | Pass. The finale is uncompressed, readable, unclipped, and ends with clear final barlines; vertical spreading is generous but safe. |

## Page-turn audit

The measure cast and therefore the musical page-turn opportunities are
unchanged from Stage I. The visual failures on pages 21 and 27 must be repaired
without disturbing their otherwise useful turn boundaries.

| Turn after page | Boundary | Rating |
| ---: | --- | --- |
| 1 | m.10 / m.11 | Marginal; one Light voice ties and there is no shared rest. |
| 3 | m.14 / m.15 | Marginal; Baritone Shadow ties. |
| 5 | m.20 / m.21 | Unsafe, but preferable to recompressing the opening. |
| 7 | m.31 / m.32 | Strong; substantial shared clearance. |
| 9 | m.39 / m.40 | Unsafe, but protects the dense material. |
| 11 | m.45 / m.46 | Workable; no cross-bar tie. |
| 13 | m.52 / m.53 | Unsafe, but protects measures 46-52. |
| 15 | m.61 / m.62 | Strong; shared clearance and no ties. |
| 17 | m.70 / m.71 | Workable; brief shared space and no ties. |
| 19 | m.83 / m.84 | Ideal; inside the tacet block. |
| 21 | m.103 / m.104 | Musically strong, but page 21 is not visually usable yet. |
| 23 | m.109 / m.110 | Workable but fast; no tie and a textual comma. |
| 25 | m.114 / m.115 | Workable; no ties and the instruction begins on the next page. |
| 27 | m.129 / m.130 | Musically workable, but page 27's system collision must be fixed. |
| 29 | m.139 / m.140 | Unsafe; all six parts sustain into the final texture. |
| 31 | m.151 / colophon | End of music; no live turn. |

## Recommended next pass

1. Rebuild page 1's title frame and opening band, restore the missing furniture,
   and locally re-route all opening lyrics while retaining two systems.
2. Reduce single-system staff-gap justification and create explicit inter-system
   clearance on pages 6 and 27; re-export before any local nudging.
3. Join barlines within each chorus and raise player names to at least 9.5 pt.
4. Reset and reconstruct the page-21 lyric lanes, then clean page 19 and the
   remaining long or empty-looking continuation rules.
5. Re-space the page-20 chord row and separate `Cmaj9/E` from `subito` on page 24.
6. Export and inspect all 31 pages again at print resolution before appending the
   colophon.

## Acceptance status

- **31-page music cast / no blank music pages:** pass.
- **Page 1 exactly two systems:** pass structurally; fail typographically.
- **All six staves five-line and visible:** pass.
- **Shadow/Light labels and separate brackets:** pass.
- **Joined group barlines:** fail.
- **Lyrics and directions at approved size:** pass.
- **Player labels at approved size:** fail; sampled at 8.5 pt.
- **No system-on-system collisions:** fail on pages 6 and 27.
- **No local object collisions:** fail on pages 1, 20, 21, and 24.
- **Measures 115 and 130:** pass.
- **Finale readability:** pass.
- **Modern publication-ready engraving:** fail pending the corrections above.
